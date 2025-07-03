#!/bin/bash

echo "🚀 Установка Diagram Generator Telegram Bot"
echo "==========================================="

# Функция для установки пакетов
install_package() {
    local package=$1
    local use_venv=${2:-true}
    
    echo "📥 Установка $package..."
    
    if [ "$use_venv" = true ] && [ -d "venv" ]; then
        # Пытаемся установить в виртуальное окружение
        if source venv/bin/activate && pip install "$package"; then
            echo "✅ $package установлен в виртуальное окружение"
            return 0
        else
            echo "⚠️ Ошибка установки $package в виртуальное окружение"
            return 1
        fi
    else
        # Пытаемся установить глобально с --break-system-packages
        if pip install --break-system-packages "$package"; then
            echo "✅ $package установлен глобально"
            return 0
        else
            echo "❌ Ошибка установки $package"
            return 1
        fi
    fi
}

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

# Проверяем на externally managed environment
echo "🔍 Проверка окружения Python..."
USE_VENV=true
EXTERNALLY_MANAGED=false

if pip install --help 2>&1 | grep -q "externally-managed-environment" || 
   python3 -c "import sys; exit(0 if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix else 1)" 2>/dev/null; then
    echo "⚠️ Обнаружено externally managed environment"
    EXTERNALLY_MANAGED=true
fi

# Пытаемся создать виртуальное окружение
echo "📦 Настройка окружения Python..."
if python3 -m venv --help &> /dev/null; then
    echo "🔄 Создание виртуального окружения..."
    if python3 -m venv venv 2>/dev/null; then
        echo "✅ Виртуальное окружение создано"
        USE_VENV=true
    else
        echo "⚠️ Не удалось создать виртуальное окружение"
        echo "📝 Будет использована глобальная установка с --break-system-packages"
        USE_VENV=false
    fi
else
    echo "⚠️ python3-venv недоступен"
    echo "📝 Будет использована глобальная установка с --break-system-packages"
    USE_VENV=false
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "💡 Для установки venv выполните:"
        echo "  • Ubuntu/Debian: sudo apt install python3-venv python3-dev"
        echo "  • CentOS/RHEL: sudo yum install python3-devel"
        echo "  • Fedora: sudo dnf install python3-devel"
    fi
fi

# Активируем виртуальное окружение если оно доступно
if [ "$USE_VENV" = true ] && [ -d "venv" ]; then
    echo "🔄 Активация виртуального окружения..."
    source venv/bin/activate
    
    # Обновляем pip в виртуальном окружении
    echo "⬆️ Обновление pip..."
    pip install --upgrade pip
else
    echo "🔄 Использование глобального окружения..."
fi

# Устанавливаем базовые зависимости
echo "� Установка базовых зависимостей..."
if [ "$USE_VENV" = true ] && [ -d "venv" ]; then
    source venv/bin/activate
    pip install wheel setuptools
else
    pip install --break-system-packages wheel setuptools 2>/dev/null || echo "⚠️ Не удалось установить wheel/setuptools"
fi

# Список основных пакетов
CORE_PACKAGES=(
    "aiogram==3.10.0"
    "python-dotenv==1.0.0"
    "requests==2.31.0"
    "asyncio-throttle==1.0.2"
)

# Список дополнительных пакетов (могут не установиться в ограниченных средах)
OPTIONAL_PACKAGES=(
    "pillow==10.0.0"
    "diagrams==0.23.4"
)

# Устанавливаем основные пакеты
echo "� Установка основных пакетов..."
CORE_SUCCESS=true
for package in "${CORE_PACKAGES[@]}"; do
    if ! install_package "$package" "$USE_VENV"; then
        CORE_SUCCESS=false
        echo "❌ Критическая ошибка: не удалось установить $package"
    fi
done

if [ "$CORE_SUCCESS" = false ]; then
    echo "❌ Установка основных пакетов завершилась с ошибками"
    echo "💡 Попробуйте:"
    echo "  • Установить python3-dev: sudo apt install python3-dev"
    echo "  • Обновить pip: python3 -m pip install --upgrade pip"
    echo "  • Или установить пакеты вручную"
    exit 1
fi

# Устанавливаем дополнительные пакеты
echo "� Установка дополнительных пакетов..."
OPTIONAL_SUCCESS=true
for package in "${OPTIONAL_PACKAGES[@]}"; do
    if ! install_package "$package" "$USE_VENV"; then
        OPTIONAL_SUCCESS=false
        echo "⚠️ Пакет $package не установлен (возможно, требуются системные зависимости)"
    fi
done

# Проверяем наличие Graphviz (требуется для diagrams)
echo "🔍 Проверка Graphviz..."
if ! command -v dot &> /dev/null; then
    echo "⚠️ Graphviz не найден."
    echo "💡 Для установки Graphviz:"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  • Ubuntu/Debian: sudo apt install graphviz"
        echo "  • CentOS/RHEL: sudo yum install graphviz"
        echo "  • Fedora: sudo dnf install graphviz"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  • macOS: brew install graphviz"
    else
        echo "  • Загрузите с: https://graphviz.org/download/"
    fi
    
    echo "⚠️ Без Graphviz библиотека diagrams не будет работать"
else
    echo "✅ Graphviz найден: $(dot -V 2>&1 | head -1)"
fi

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p temp diagrams

# Создаем .env файл если его нет
echo "⚙️ Настройка конфигурации..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Файл .env создан из примера"
    else
        echo "📝 Создание базового .env файла..."
        cat > .env << 'EOF'
# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# GigaChat API Configuration  
# Получите API ключ на https://developers.sber.ru/gigachat
GIGACHAT_CLIENT_SECRET=your_gigachat_client_secret_here
EOF
        echo "✅ Базовый .env файл создан"
    fi
    echo "❗ Не забудьте указать BOT_TOKEN и GIGACHAT_CLIENT_SECRET в файле .env"
else
    echo "✅ Файл .env уже существует"
fi

# Проверяем установку
echo "🧪 Проверка установки..."
IMPORT_TEST=$(python3 -c "
import sys
errors = []
success = []

try:
    import aiogram
    success.append('aiogram')
except ImportError as e:
    errors.append(f'aiogram: {e}')

try:
    import aiohttp  
    success.append('aiohttp')
except ImportError as e:
    errors.append(f'aiohttp: {e}')

try:
    from dotenv import load_dotenv
    success.append('python-dotenv')
except ImportError as e:
    errors.append(f'python-dotenv: {e}')

try:
    import requests
    success.append('requests')
except ImportError as e:
    errors.append(f'requests: {e}')

try:
    import asyncio_throttle
    success.append('asyncio-throttle')
except ImportError as e:
    errors.append(f'asyncio-throttle: {e}')

try:
    import diagrams
    success.append('diagrams')
except ImportError as e:
    errors.append(f'diagrams: {e}')

try:
    from PIL import Image
    success.append('Pillow')
except ImportError as e:
    errors.append(f'Pillow: {e}')

print(f'SUCCESS:{len(success)}')
print(f'ERRORS:{len(errors)}')
for s in success:
    print(f'✅ {s}')
for e in errors:
    print(f'❌ {e}')
" 2>&1)

echo "$IMPORT_TEST"

# Анализируем результаты проверки
SUCCESS_COUNT=$(echo "$IMPORT_TEST" | grep "SUCCESS:" | cut -d: -f2)
ERROR_COUNT=$(echo "$IMPORT_TEST" | grep "ERRORS:" | cut -d: -f2)

echo ""
echo "📊 Результаты установки:"
echo "✅ Успешно: $SUCCESS_COUNT пакетов"
echo "❌ Ошибки: $ERROR_COUNT пакетов"

if [ "$ERROR_COUNT" -eq 0 ]; then
    echo ""
    echo "🎉 Установка полностью завершена!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Получите токен бота у @BotFather в Telegram"
    echo "2. Отредактируйте файл .env и укажите BOT_TOKEN"
    echo "3. Получите API ключ GigaChat на https://developers.sber.ru/gigachat"
    echo "4. Укажите GIGACHAT_CLIENT_SECRET в файле .env"
    echo "5. Запустите бота: ./run.sh"
    echo ""
    echo "✨ Готово к использованию!"
elif [ "$SUCCESS_COUNT" -ge 5 ]; then
    echo ""
    echo "🎉 Основная установка завершена!"
    echo ""
    echo "⚠️ Некоторые пакеты не установились, но бот может работать в ограниченном режиме"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Получите токен бота у @BotFather в Telegram"
    echo "2. Отредактируйте файл .env и укажите BOT_TOKEN"
    echo "3. Запустите бота: ./run.sh"
    echo ""
    if ! command -v dot &> /dev/null; then
        echo "⚠️ ВНИМАНИЕ: Для создания диаграмм установите Graphviz!"
        echo "💡 sudo apt install graphviz  # Ubuntu/Debian"
        echo ""
    fi
    echo "✨ Частично готово к использованию!"
else
    echo ""
    echo "❌ Установка завершилась с критическими ошибками"
    echo ""
    echo "💡 Рекомендации для решения проблем:"
    echo "• Установите системные зависимости: sudo apt install python3-dev python3-venv"
    echo "• Обновите pip: python3 -m pip install --upgrade pip"
    echo "• Попробуйте установить пакеты вручную:"
    echo "  pip install --break-system-packages aiogram python-dotenv requests"
    echo ""
    exit 1
fi