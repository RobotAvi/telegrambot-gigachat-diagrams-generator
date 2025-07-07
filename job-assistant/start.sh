#!/bin/bash

# Job Assistant Startup Script

echo "🚀 Запуск Job Assistant..."

# Check if required tools are installed
command -v docker >/dev/null 2>&1 || { echo "❌ Docker не установлен. Установите Docker и повторите попытку."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose не установлен. Установите Docker Compose и повторите попытку."; exit 1; }

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📋 Создаю .env файл из шаблона..."
    cp .env.example .env
    echo "⚠️  Пожалуйста, отредактируйте .env файл и добавьте ваши API ключи:"
    echo "   - OPENAI_API_KEY или ANTHROPIC_API_KEY"
    echo "   - TELEGRAM_BOT_TOKEN"
    echo "   - EMAIL_ADDRESS и EMAIL_PASSWORD"
    echo "   - Другие необходимые настройки"
    echo ""
    read -p "Нажмите Enter после настройки .env файла..."
fi

# Start services
echo "🐳 Запускаю Docker контейнеры..."
docker-compose up -d

# Wait for services to start
echo "⏳ Ожидание запуска сервисов..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Сервисы запущены успешно!"
    echo ""
    echo "🌐 Приложение доступно по адресам:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 Для просмотра логов используйте:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Для остановки сервисов используйте:"
    echo "   docker-compose down"
else
    echo "❌ Ошибка запуска сервисов. Проверьте логи:"
    echo "   docker-compose logs"
fi