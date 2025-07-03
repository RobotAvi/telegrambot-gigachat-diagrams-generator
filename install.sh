THIS SHOULD BE A LINTER ERROR#!/bin/bash

echo "🚀 Установка Diagram Generator Telegram Bot"
echo "==========================================="

# Проверяем версию Python
python_version=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Требуется Python 3.8 или выше. Текущая версия: $python_version"
    exit 1
fi

echo "✅ Python версия $python_version подходит"

# Создаем виртуальное окружение
echo "📦 Создание виртуального окружения..."
python3 -m venv venv

# Активируем виртуальное окружение
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновление pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📥 Установка зависимостей Python..."
pip install -r requirements.txt

# Проверяем наличие Graphviz
echo "🔍 Проверка Graphviz..."
if ! command -v dot &> /dev/null; then
    echo "⚠️ Graphviz не найден. Попытка установки..."
    
    # Определяем ОС и устанавливаем Graphviz
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y graphviz
        elif command -v yum &> /dev/null; then
            sudo yum install -y graphviz
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y graphviz
        else
            echo "❌ Не удалось автоматически установить Graphviz. Установите вручную."
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install graphviz
        else
            echo "❌ Homebrew не найден. Установите Graphviz вручную или установите Homebrew."
        fi
    else
        echo "❌ Неподдерживаемая ОС. Установите Graphviz вручную."
    fi
fi

# Проверяем установку Graphviz после попытки установки
if command -v dot &> /dev/null; then
    echo "✅ Graphviz установлен успешно"
else
    echo "❌ Graphviz не установлен. Установите вручную: https://graphviz.org/download/"
fi

# Создаем необходимые директории
echo "📁 Создание директорий..."
mkdir -p temp diagrams

# Копируем пример конфигурации
echo "⚙️ Настройка конфигурации..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Файл .env создан из примера"
    echo "❗ Не забудьте указать BOT_TOKEN в файле .env"
else
    echo "✅ Файл .env уже существует"
fi

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Получите токен бота у @BotFather в Telegram"
echo "2. Отредактируйте файл .env и укажите BOT_TOKEN"
echo "3. Запустите бота: source venv/bin/activate && python main.py"
echo "4. Получите API ключ GigaChat на https://developers.sber.ru/gigachat"
echo ""
echo "✨ Готово к использованию!"