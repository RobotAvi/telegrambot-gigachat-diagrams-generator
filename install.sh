#!/bin/bash

echo "🚀 Установка Diagram Generator Telegram Bot"
echo "==========================================="

# Проверяем версию Python
echo "🔍 Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Требуется Python 3.8 или выше. Текущая версия: $python_version"
    exit 1
fi

echo "✅ Python версия $python_version подходит"

# Проверяем наличие python3-venv
echo "🔍 Проверка python3-venv..."
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ python3-venv не найден."
    
    # Пытаемся установить python3-venv без sudo если возможно
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "💡 Попробуйте установить: apt-get install python3-venv python3-dev"
        echo "💡 Или: yum install python3-devel"
        echo "💡 Или: dnf install python3-devel"
    fi
    
    echo "ℹ️ Продолжаем установку..."
fi

# Создаем виртуальное окружение
echo "📦 Создание виртуального окружения..."
if ! python3 -m venv venv; then
    echo "❌ Ошибка создания виртуального окружения"
    echo "💡 Убедитесь, что установлен python3-venv"
    exit 1
fi

# Активируем виртуальное окружение
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости по одной для лучшей диагностики
echo "📥 Установка основных зависимостей..."
pip install wheel setuptools

echo "📥 Установка aiogram..."
pip install aiogram

echo "📥 Установка aiohttp..."
pip install aiohttp

echo "📥 Установка python-dotenv..."
pip install python-dotenv

echo "📥 Установка requests..."
pip install requests

echo "📥 Установка asyncio-throttle..."
pip install asyncio-throttle

echo "📥 Установка Pillow..."
pip install Pillow

echo "📥 Установка diagrams..."
pip install diagrams

# Проверяем наличие Graphviz
echo "🔍 Проверка Graphviz..."
if ! command -v dot &> /dev/null; then
    echo "⚠️ Graphviz не найден."
    echo "💡 Для установки Graphviz:"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  • Ubuntu/Debian: apt-get install graphviz"
        echo "  • CentOS/RHEL: yum install graphviz"
        echo "  • Fedora: dnf install graphviz"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  • macOS: brew install graphviz"
    else
        echo "  • Загрузите с: https://graphviz.org/download/"
    fi
    
    echo "⚠️ Graphviz необходим для работы библиотеки diagrams"
else
    echo "✅ Graphviz найден: $(dot -V 2>&1)"
fi

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p temp diagrams

# Копируем пример конфигурации
echo "⚙️ Настройка конфигурации..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Файл .env создан из примера"
    else
        echo "⚠️ .env.example не найден, создаю базовый .env"
        cat > .env << 'EOF'
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# GigaChat API Configuration  
# Получите API ключ на https://developers.sber.ru/gigachat
GIGACHAT_CLIENT_SECRET=your_gigachat_client_secret_here
EOF
    fi
    echo "❗ Не забудьте указать BOT_TOKEN в файле .env"
else
    echo "✅ Файл .env уже существует"
fi

# Проверяем установку
echo "🧪 Проверка установки..."
python3 -c "
try:
    import aiogram
    import aiohttp
    import diagrams
    from PIL import Image
    print('✅ Все основные библиотеки импортированы успешно')
except ImportError as e:
    print(f'❌ Ошибка импорта: {e}')
    exit(1)
"

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Получите токен бота у @BotFather в Telegram"
echo "2. Отредактируйте файл .env и укажите BOT_TOKEN"
echo "3. Получите API ключ GigaChat на https://developers.sber.ru/gigachat"
echo "4. Запустите бота: ./run.sh"
echo ""
if ! command -v dot &> /dev/null; then
    echo "⚠️ ВНИМАНИЕ: Не забудьте установить Graphviz для работы диаграмм!"
    echo ""
fi
echo "✨ Готово к использованию!"