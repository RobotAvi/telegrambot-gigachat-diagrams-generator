# Job Assistant - Автоматический помощник для поиска работы

Веб-приложение для автоматизации поиска работы с использованием LLM и интеграции с популярными job boards.

## Возможности

- 📄 **Загрузка и анализ резюме** с помощью LLM
- 🔍 **Автоматический поиск вакансий** на HeadHunter и SuperJob
- 🤖 **Оценка соответствия** вакансий вашему резюме с помощью ИИ
- 📱 **Telegram уведомления** о найденных вакансиях
- ✉️ **Автоматическая подача заявок** с персонализированными сопроводительными письмами
- 👥 **Поиск и контакт с HR-менеджерами**
- 📊 **Отслеживание статуса заявок**

## Технологии

### Backend
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **PostgreSQL** - основная база данных
- **OpenAI/Anthropic** - LLM для анализа резюме и генерации писем
- **Celery + Redis** - фоновые задачи
- **Python Telegram Bot** - уведомления

### Frontend
- **React 18** - пользовательский интерфейс
- **Tailwind CSS** - стилизация
- **React Router** - маршрутизация
- **React Query** - управление состоянием сервера
- **React Hook Form** - работа с формами

## Установка

### Требования
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Redis

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/job-assistant.git
cd job-assistant
```

### 2. Настройка Backend

#### Создание виртуального окружения
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

#### Установка зависимостей
```bash
pip install -r requirements.txt
```

#### Настройка переменных окружения
```bash
cp .env.example .env
```

Отредактируйте `.env` файл:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/job_assistant

# JWT Secret
SECRET_KEY=your-super-secret-key-here

# LLM API Keys
OPENAI_API_KEY=your-openai-api-key
# или
ANTHROPIC_API_KEY=your-anthropic-api-key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Email Settings
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Job Board APIs
SUPERJOB_API_KEY=your-superjob-api-key
```

#### Создание базы данных
```bash
# Создайте базу данных PostgreSQL
createdb job_assistant

# Запустите миграции
alembic upgrade head
```

### 3. Настройка Frontend

#### Установка зависимостей
```bash
cd frontend
npm install
```

#### Настройка переменных окружения
```bash
# Создайте .env файл в папке frontend
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
```

### 4. Запуск приложения

#### Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm start
```

#### Celery (фоновые задачи)
```bash
cd backend
celery -A app.celery worker --loglevel=info
celery -A app.celery beat --loglevel=info
```

## Настройка интеграций

### 1. Telegram Bot

1. Создайте бота через [@BotFather](https://t.me/botfather)
2. Получите токен и добавьте в `.env`
3. Получите свой chat_id через [@userinfobot](https://t.me/userinfobot)

### 2. API ключи для job boards

#### HeadHunter
- Регистрация: https://dev.hh.ru/
- Создайте приложение и получите client_id и client_secret

#### SuperJob
- Регистрация: https://api.superjob.ru/
- Получите API ключ

### 3. LLM API

#### OpenAI
- Регистрация: https://platform.openai.com/
- Создайте API ключ

#### Anthropic (альтернатива)
- Регистрация: https://console.anthropic.com/
- Создайте API ключ

### 4. Email настройки

Для Gmail:
1. Включите двухфакторную аутентификацию
2. Создайте пароль приложения
3. Используйте пароль приложения в настройках

## Использование

### 1. Регистрация и настройка

1. Откройте http://localhost:3000
2. Зарегистрируйтесь или войдите
3. Загрузите резюме в разделе "Резюме"
4. Настройте параметры поиска в "Настройках"
5. Укажите Telegram chat_id для уведомлений

### 2. Автоматический поиск

1. Система автоматически ищет вакансии каждое утро
2. Анализирует их соответствие вашему резюме
3. Отправляет уведомления в Telegram
4. Вы выбираете интересные вакансии
5. Система автоматически подает заявки и связывается с HR

### 3. Мониторинг

- Отслеживайте статус заявок в разделе "Заявки"
- Просматривайте найденные вакансии в разделе "Вакансии"
- Управляйте HR-контактами в соответствующем разделе

## Docker (альтернативный запуск)

```bash
# Создайте docker-compose.yml файл
docker-compose up -d
```

## Разработка

### Структура проекта
```
job-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── routers/
│   ├── models/
│   ├── services/
│   └── utils/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── contexts/
│   └── public/
└── requirements.txt
```

### API документация

После запуска backend, документация доступна:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Безопасность

⚠️ **Важные замечания по безопасности:**

1. **API ключи** - храните в переменных окружения
2. **Пароли email** - используйте пароли приложений
3. **JWT секрет** - используйте сложный случайный ключ
4. **База данных** - настройте правильные права доступа

## Поддержка

- 📧 Email: support@jobassistant.com
- 💬 Telegram: @jobassistant_support
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/job-assistant/issues)

## Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

## Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Создайте Pull Request

## Roadmap

- [ ] Интеграция с LinkedIn
- [ ] Мобильное приложение
- [ ] Расширенная аналитика
- [ ] Поддержка международных job boards
- [ ] Видеопрезентация резюме
- [ ] AI-собеседования

---

Сделано с ❤️ для автоматизации поиска работы