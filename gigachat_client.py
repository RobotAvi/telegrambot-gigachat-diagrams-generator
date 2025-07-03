import asyncio
import aiohttp
import json
import time
from typing import Optional, Dict, Any
from config import GIGACHAT_AUTH_URL, GIGACHAT_BASE_URL, GIGACHAT_SYSTEM_PROMPT


class GigaChatClient:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires_at: float = 0
        self.client_secret: Optional[str] = None
        self.selected_model: str = "GigaChat-Pro"  # Модель по умолчанию
        
    def set_credentials(self, client_secret: str):
        """Устанавливает учетные данные для API"""
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = 0
    
    def set_model(self, model_id: str):
        """Устанавливает модель для генерации"""
        self.selected_model = model_id
    
    def get_current_model(self) -> str:
        """Возвращает текущую выбранную модель"""
        return self.selected_model
    
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
            'RqUID': str(int(time.time())),
            'Authorization': f'Basic {self.client_secret}'
        }
        
        data = {
            'scope': 'GIGACHAT_API_PERS'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GIGACHAT_AUTH_URL,
                headers=headers,
                data=data,
                ssl=False
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ошибка авторизации: {response.status}")
                    
                result = await response.json()
                self.access_token = result['access_token']
                # Токен действует 30 минут, обновляем за 5 минут до истечения
                self.token_expires_at = time.time() + result['expires_in'] - 300
                
                return self.access_token
    
    async def check_credentials(self) -> bool:
        """Проверяет валидность учетных данных"""
        try:
            await self._get_access_token()
            return True
        except Exception:
            return False
    
    async def get_available_models(self) -> list:
        """Получает список доступных моделей"""
        if not self.client_secret:
            raise ValueError("API ключ не установлен")
            
        access_token = await self._get_access_token()
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GIGACHAT_BASE_URL}/models",
                headers=headers,
                ssl=False
            ) as response:
                if response.status != 200:
                    # Если API не поддерживает /models, возвращаем известные модели
                    return [
                        {"id": "GigaChat", "description": "Базовая модель GigaChat"},
                        {"id": "GigaChat-Pro", "description": "Продвинутая модель GigaChat-Pro"},
                        {"id": "GigaChat-Max", "description": "Максимальная модель GigaChat-Max"}
                    ]
                    
                result = await response.json()
                
                if 'data' in result:
                    return [
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
                else:
                    # Фолбэк к известным моделям
                    return [
                        {"id": "GigaChat", "description": "Базовая модель GigaChat"},
                        {"id": "GigaChat-Pro", "description": "Продвинутая модель GigaChat-Pro"},
                        {"id": "GigaChat-Max", "description": "Максимальная модель GigaChat-Max"}
                    ]
    
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GIGACHAT_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                ssl=False
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ошибка API: {response.status}")
                    
                result = await response.json()
                
                if 'choices' not in result or not result['choices']:
                    raise Exception("Пустой ответ от API")
                    
                content = result['choices'][0]['message']['content']
                
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


# Глобальный экземпляр клиента
gigachat_client = GigaChatClient()