#!/bin/bash

echo "🚀 Запуск Diagram Generator Telegram Bot"
echo "======================================="

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Виртуальное окружение не найдено."
    echo "Запустите сначала: ./install.sh"
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден."
    echo "Скопируйте .env.example в .env и настройте переменные окружения."
    exit 1
fi

# Активируем виртуальное окружение
echo "🔄 Активация виртуального окружения..."
source venv/bin/activate

# Проверяем установлены ли зависимости
echo "🔍 Проверка зависимостей..."
if ! python -c "import aiogram" 2>/dev/null; then
    echo "❌ Зависимости не установлены. Запуск установки..."
    pip install -r requirements.txt
fi

# Создаем необходимые директории
mkdir -p temp diagrams

# Запускаем бота
echo "▶️ Запуск бота..."
python main.py