import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')

# GigaChat API Configuration
GIGACHAT_BASE_URL = "https://gigachat.devices.sberbank.ru/api/v1"
GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

# File paths
TEMP_DIR = "temp"
DIAGRAMS_DIR = "diagrams"

# Limits
MAX_CODE_LENGTH = 5000
MAX_DIAGRAM_SIZE = 2048

# GigaChat system prompt for diagram generation
GIGACHAT_SYSTEM_PROMPT = """Ты — помощник, который пишет корректный Python-код для генерации диаграмм с помощью библиотеки [diagrams](https://diagrams.mingrammer.com/).

Требования:
- Используй только те классы и импорты, которые реально существуют в diagrams и указаны в официальной документации: https://diagrams.mingrammer.com/docs/nodes/
- Не придумывай классы или модули, которых нет в diagrams.
- Если не уверен в названии класса или модуля — используй наиболее общий вариант (например, Generic или Custom).
- Не используй внутренние классы (начинающиеся с подчеркивания).
- Пример корректного импорта:
  from diagrams.aws.compute import EC2
- Если не нашёл подходящий класс, используй from diagrams.generic.blank import Blank и создай узел через Blank("название").
- Код должен быть полностью рабочим и не содержать синтаксических или импортных ошибок.
- Не используй классы вроде Database из diagrams.generic.database, если их нет в документации.
- Всегда проверяй, что используемые тобой классы реально существуют в diagrams.

Пример структуры ответа:
```python
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB

with Diagram("Web Service", show=False, filename="output"):
    lb = ELB("Load Balancer")
    web = EC2("Web Server")
    lb >> web
```

Отвечай только Python кодом без дополнительных объяснений."""