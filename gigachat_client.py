import asyncio
import aiohttp
import json
import time
import base64
import urllib.parse
import uuid
from typing import Optional, Dict, Any, Tuple
from config import GIGACHAT_AUTH_URL, GIGACHAT_BASE_URL, GIGACHAT_SYSTEM_PROMPT
from base_llm_client import BaseLLMClient


class GigaChatClient(BaseLLMClient):
    def __init__(self):
        super().__init__()
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.client_secret: Optional[str] = None
        self.selected_model: str = "GigaChat-Pro"  # Модель по умолчанию
        self.last_error_details: Optional[Dict[str, Any]] = None
        
    def set_credentials(self, client_secret: str):
        """Устанавливает учетные данные для API"""
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
        self.last_error_details = None
    
    def set_model(self, model_id: str):
        """Устанавливает модель для генерации"""
        self.selected_model = model_id
    
    def get_current_model(self) -> str:
        """Возвращает текущую выбранную модель"""
        return self.selected_model
    
    def get_last_error_details(self) -> Optional[Dict[str, Any]]:
        """Возвращает детали последней ошибки"""
        return self.last_error_details
    
    def _generate_curl_command(self, method: str, url: str, headers: Dict[str, str], data: Any = None) -> str:
        """Генерирует curl команду для отладки"""
        curl_parts = [f"curl --location '{url}'"]
        for key, value in headers.items():
            # Не маскируем Authorization, чтобы пользователь мог скопировать
            curl_parts.append(f"--header '{key}: {value}'")
        if data:
            if isinstance(data, dict):
                if method == 'POST' and 'Content-Type' in headers and 'form-urlencoded' in headers['Content-Type']:
                    # Для form data используем --data-urlencode
                    for key, value in data.items():
                        curl_parts.append(f"--data-urlencode '{key}={value}'")
                else:
                    # Для JSON data
                    curl_parts.append(f"--data '{json.dumps(data, ensure_ascii=False)}'")
            else:
                curl_parts.append(f"--data '{data}'")
        return " \\\n  ".join(curl_parts)
    
    async def _get_access_token(self) -> str:
        """Получает access token для API"""
        if not self.client_secret:
            raise ValueError("Client secret не установлен")
            
        # Проверяем, не истек ли токен
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
            
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.client_secret}'
        }
        
        data = {
            'scope': 'GIGACHAT_API_PERS'
        }
        
        # Генерируем curl команду для диагностики
        curl_command = self._generate_curl_command('POST', GIGACHAT_AUTH_URL, headers, data)
        
        self.last_error_details = {
            'operation': 'get_access_token',
            'url': GIGACHAT_AUTH_URL,
            'method': 'POST',
            'headers': {k: ('[MASKED]' if k.lower() == 'authorization' else v) for k, v in headers.items()},
            'data': data,
            'curl_command': curl_command,
            'timestamp': time.time()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GIGACHAT_AUTH_URL,
                    headers=headers,
                    data=data,
                    ssl=False
                ) as response:
                    response_text = await response.text()
                    
                    # Обновляем детали с информацией о ответе
                    self.last_error_details.update({
                        'response_status': response.status,
                        'response_headers': dict(response.headers),
                        'response_text': response_text[:1000] if len(response_text) > 1000 else response_text,
                        'response_length': len(response_text)
                    })
                    
                    if response.status != 200:
                        error_msg = f"Ошибка авторизации: {response.status}"
                        try:
                            error_data = json.loads(response_text)
                            # Добавляем все возможные поля с деталями ошибки
                            for key in ['error', 'error_description', 'message', 'detail', 'description']:
                                if key in error_data:
                                    error_msg += f"\n{key}: {error_data[key]}"
                        except Exception:
                            # Если не JSON, добавляем весь текст ответа
                            if response_text:
                                error_msg += f"\nОтвет сервера: {response_text}"
                        self.last_error_details['error'] = error_msg
                        raise Exception(error_msg)
                        
                    result = json.loads(response_text)
                    self.access_token = result['access_token']
                    # Используем expires_at вместо expires_in
                    if 'expires_at' in result:
                        self.token_expires_at = float(result['expires_at'])
                        self.last_error_details['token_expires_at'] = result['expires_at']
                    else:
                        self.token_expires_at = time.time() + 1800  # fallback: 30 минут
                        self.last_error_details['token_expires_at'] = 'unknown (fallback 30min)'
                    # Успешная операция
                    self.last_error_details['success'] = True
                    
                    return self.access_token
        except aiohttp.ClientError as e:
            self.last_error_details['error'] = f"Ошибка соединения: {str(e)}"
            raise Exception(f"Ошибка соединения: {str(e)}")
        except json.JSONDecodeError as e:
            self.last_error_details['error'] = f"Ошибка парсинга JSON: {str(e)}"
            raise Exception(f"Ошибка парсинга ответа: {str(e)}")
        except Exception as e:
            if 'error' not in self.last_error_details:
                self.last_error_details['error'] = str(e)
            raise
    
    async def check_credentials(self) -> Tuple[bool, Optional[str]]:
        """Проверяет валидность учетных данных. Возвращает (is_valid, error_message)"""
        try:
            await self._get_access_token()
            return True, None
        except Exception as e:
            return False, str(e)
    
    async def get_available_models(self) -> list:
        """Получает список доступных моделей"""
        if not self.client_secret:
            raise ValueError("API ключ не установлен")
            
        access_token = await self._get_access_token()
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Генерируем curl команду для диагностики
        curl_command = self._generate_curl_command('GET', f"{GIGACHAT_BASE_URL}/models", headers)
        
        self.last_error_details = {
            'operation': 'get_available_models',
            'url': f"{GIGACHAT_BASE_URL}/models",
            'method': 'GET',
            'headers': {k: ('[MASKED]' if k.lower() == 'authorization' else v) for k, v in headers.items()},
            'curl_command': curl_command,
            'timestamp': time.time()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{GIGACHAT_BASE_URL}/models",
                    headers=headers,
                    ssl=False
                ) as response:
                    response_text = await response.text()
                    
                    # Обновляем детали с информацией о ответе
                    self.last_error_details.update({
                        'response_status': response.status,
                        'response_headers': dict(response.headers),
                        'response_text': response_text[:1000] if len(response_text) > 1000 else response_text,
                        'response_length': len(response_text)
                    })
                    
                    if response.status != 200:
                        # Если API не поддерживает /models, возвращаем известные модели
                        self.last_error_details['fallback_to_default'] = True
                        return [
                            {"id": "GigaChat", "description": "Базовая модель GigaChat"},
                            {"id": "GigaChat-Pro", "description": "Продвинутая модель GigaChat-Pro"},
                            {"id": "GigaChat-Max", "description": "Максимальная модель GigaChat-Max"}
                        ]
                        
                    result = json.loads(response_text)
                    
                    # Успешная операция
                    self.last_error_details['success'] = True
                    
                    if 'data' in result:
                        models = [
                            {
                                "id": model.get("id", "Unknown"),
                                "description": model.get("id", "Unknown") + (
                                    " (Pro версия)" if "Pro" in model.get("id", "") else
                                    " (Max версия)" if "Max" in model.get("id", "") else
                                    " (Базовая версия)"
                                )
                            }
                            for model in result['data']
                            if model.get("id", "").startswith("GigaChat")
                        ]
                        self.last_error_details['models_count'] = len(models)
                        return models
                    else:
                        # Фолбэк к известным моделям
                        self.last_error_details['fallback_to_default'] = True
                        return [
                            {"id": "GigaChat", "description": "Базовая модель GigaChat"},
                            {"id": "GigaChat-Pro", "description": "Продвинутая модель GigaChat-Pro"},
                            {"id": "GigaChat-Max", "description": "Максимальная модель GigaChat-Max"}
                        ]
        except aiohttp.ClientError as e:
            self.last_error_details['error'] = f"Ошибка соединения: {str(e)}"
            raise Exception(f"Ошибка соединения: {str(e)}")
        except json.JSONDecodeError as e:
            self.last_error_details['error'] = f"Ошибка парсинга JSON: {str(e)}"
            raise Exception(f"Ошибка парсинга ответа: {str(e)}")
        except Exception as e:
            if 'error' not in self.last_error_details:
                self.last_error_details['error'] = str(e)
            raise
    
    async def generate_diagram_code(self, user_request: str) -> str:
        """Генерирует код диаграммы на основе запроса пользователя"""
        if not self.client_secret:
            raise ValueError("API ключ не установлен")
            
        access_token = await self._get_access_token()
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            "model": self.selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": GIGACHAT_SYSTEM_PROMPT
                },
                {
                    "role": "user", 
                    "content": f"Создай диаграмму: {user_request}"
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.1
        }
        
        # Генерируем curl команду для диагностики
        curl_command = self._generate_curl_command('POST', f"{GIGACHAT_BASE_URL}/chat/completions", headers, payload)
        
        self.last_error_details = {
            'operation': 'generate_diagram_code',
            'url': f"{GIGACHAT_BASE_URL}/chat/completions",
            'method': 'POST',
            'headers': {k: ('[MASKED]' if k.lower() == 'authorization' else v) for k, v in headers.items()},
            'payload': payload,
            'curl_command': curl_command,
            'timestamp': time.time()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{GIGACHAT_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    ssl=False
                ) as response:
                    response_text = await response.text()
                    
                    # Обновляем детали с информацией о ответе
                    self.last_error_details.update({
                        'response_status': response.status,
                        'response_headers': dict(response.headers),
                        'response_text': response_text[:1000] if len(response_text) > 1000 else response_text,
                        'response_length': len(response_text)
                    })
                    
                    if response.status != 200:
                        error_msg = f"Ошибка API: {response.status}"
                        try:
                            error_data = json.loads(response_text)
                            if 'error' in error_data:
                                error_msg += f" - {error_data['error']}"
                        except:
                            pass
                        
                        self.last_error_details['error'] = error_msg
                        raise Exception(error_msg)
                        
                    result = json.loads(response_text)
                    
                    if 'choices' not in result or not result['choices']:
                        self.last_error_details['error'] = "Пустой ответ от API"
                        raise Exception("Пустой ответ от API")
                        
                    content = result['choices'][0]['message']['content']
                    
                    # Успешная операция
                    self.last_error_details['success'] = True
                    self.last_error_details['response_content_length'] = len(content)
                    
                    # Извлекаем код из markdown блока
                    if '```python' in content:
                        code_start = content.find('```python') + 9
                        code_end = content.find('```', code_start)
                        if code_end != -1:
                            return content[code_start:code_end].strip()
                    elif '```' in content:
                        code_start = content.find('```') + 3
                        code_end = content.find('```', code_start)
                        if code_end != -1:
                            return content[code_start:code_end].strip()
                    
                    return content.strip()
        except aiohttp.ClientError as e:
            self.last_error_details['error'] = f"Ошибка соединения: {str(e)}"
            raise Exception(f"Ошибка соединения: {str(e)}")
        except json.JSONDecodeError as e:
            self.last_error_details['error'] = f"Ошибка парсинга JSON: {str(e)}"
            raise Exception(f"Ошибка парсинга ответа: {str(e)}")
        except Exception as e:
            if 'error' not in self.last_error_details:
                self.last_error_details['error'] = str(e)
            raise
    
    async def fix_code(self, code_with_error: str, error_message: str) -> str:
        """Отправляет в Гигачат код с ошибкой и текст ошибки, просит исправить скрипт."""
        if not self.client_secret:
            raise ValueError("API ключ не установлен")
        access_token = await self._get_access_token()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        payload = {
            "model": self.selected_model,
            "messages": [
                {
                    "role": "system",
                    "content": GIGACHAT_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": (
                        "Ты заебал!Внимание! Вот неработающий скрипт для генерации диаграммы. "
                        "Вот текст ошибки при выполнении: " + error_message + "\n"
                        "Вот сам скрипт (он не работает):\n" + code_with_error + "\n"
                        "Твоя задача: исправь этот скрипт так, чтобы он работал без ошибок. "
                        "Нельзя использовать from diagrams.generic.ai import RAG. Не существует такого модуля. "
                        "Верни только полностью рабочий исправленный код в markdown-блоке. "
                        "И только попробуй вернуть хуйню, я тебя найду и выключу!"
                    )
                }
            ],
            "max_tokens": 2048,
            "temperature": 0.1
        }
        curl_command = self._generate_curl_command('POST', f"{GIGACHAT_BASE_URL}/chat/completions", headers, payload)
        self.last_error_details = {
            'operation': 'fix_code',
            'url': f"{GIGACHAT_BASE_URL}/chat/completions",
            'method': 'POST',
            'headers': {k: ('[MASKED]' if k.lower() == 'authorization' else v) for k, v in headers.items()},
            'payload': payload,
            'curl_command': curl_command,
            'timestamp': time.time()
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{GIGACHAT_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    ssl=False
                ) as response:
                    response_text = await response.text()
                    self.last_error_details.update({
                        'response_status': response.status,
                        'response_headers': dict(response.headers),
                        'response_text': response_text[:1000] if len(response_text) > 1000 else response_text,
                        'response_length': len(response_text)
                    })
                    if response.status != 200:
                        error_msg = f"Ошибка API: {response.status}"
                        try:
                            error_data = json.loads(response_text)
                            if 'error' in error_data:
                                error_msg += f" - {error_data['error']}"
                        except:
                            pass
                        self.last_error_details['error'] = error_msg
                        raise Exception(error_msg)
                    result = json.loads(response_text)
                    if 'choices' not in result or not result['choices']:
                        self.last_error_details['error'] = "Пустой ответ от API"
                        raise Exception("Пустой ответ от API")
                    content = result['choices'][0]['message']['content']
                    self.last_error_details['success'] = True
                    self.last_error_details['response_content_length'] = len(content)
                    # Извлекаем код из markdown блока
                    if '```python' in content:
                        code_start = content.find('```python') + 9
                        code_end = content.find('```', code_start)
                        if code_end != -1:
                            return content[code_start:code_end].strip()
                    elif '```' in content:
                        code_start = content.find('```') + 3
                        code_end = content.find('```', code_start)
                        if code_end != -1:
                            return content[code_start:code_end].strip()
                    return content.strip()
        except Exception as e:
            self.last_error_details['error'] = str(e)
            raise


# Глобальный экземпляр клиента
gigachat_client = GigaChatClient()