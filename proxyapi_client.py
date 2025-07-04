from base_llm_client import BaseLLMClient
import aiohttp
import json

class ProxyApiClient(BaseLLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gpt-3.5-turbo"  # Можно сделать настраиваемым

    async def generate_diagram_code(self, user_request: str) -> str:
        url = "https://proxyapi.ru/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты — помощник, который пишет только рабочий Python-код для генерации диаграмм с помощью библиотеки diagrams. Не используй несуществующие классы и пространства имён. Возвращай только рабочий Python-код."},
                {"role": "user", "content": f"Создай диаграмму: {user_request}"}
            ],
            "max_tokens": 2048,
            "temperature": 0.1
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, ssl=False) as response:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
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

    async def fix_code(self, code_with_error: str, error_message: str) -> str:
        url = "https://proxyapi.ru/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Ты — помощник, который пишет только рабочий Python-код для генерации диаграмм с помощью библиотеки diagrams. Не используй несуществующие классы и пространства имён. Возвращай только рабочий Python-код."},
                {"role": "user", "content": (
                    "Внимание! Вот неработающий скрипт для генерации диаграммы. "
                    "Вот текст ошибки при выполнении: " + error_message + "\n"
                    "Вот сам скрипт (он не работает):\n" + code_with_error + "\n"
                    "Твоя задача: исправь этот скрипт так, чтобы он работал без ошибок. "
                    "Верни только полностью рабочий исправленный код в markdown-блоке."
                )}
            ],
            "max_tokens": 2048,
            "temperature": 0.1
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, ssl=False) as response:
                result = await response.json()
                content = result["choices"][0]["message"]["content"]
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