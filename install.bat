@echo off
chcp 65001 >nul

:: 🚀 Установка Diagram Generator Telegram Bot

echo ===========================================
echo [1/7] Проверка Python...
where python >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден. Установите Python 3.8 или выше.
    pause
    exit /b 1
)

for /f "tokens=2 delims=. " %%v in ('python --version 2^>^&1') do set PY_VER=%%v
if %PY_VER% LSS 3 (
    echo [ОШИБКА] Требуется Python 3.8 или выше.
    pause
    exit /b 1
)

echo [2/7] Создание виртуального окружения...
if not exist venv (
    python -m venv venv
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ОШИБКА] Не удалось активировать виртуальное окружение.
    pause
    exit /b 1
)

echo [3/7] Обновление pip, wheel, setuptools...
python -m pip install --upgrade pip wheel setuptools
if errorlevel 1 (
    echo [ОШИБКА] Не удалось обновить pip/wheel/setuptools.
    pause
    exit /b 1
)

echo [4/7] Установка зависимостей из requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

echo [5/7] Проверка наличия Graphviz...
where dot >nul 2>nul
if errorlevel 1 (
    echo [ВНИМАНИЕ] Graphviz не найден.
    echo Скачайте и установите Graphviz: https://graphviz.org/download/
    echo Без Graphviz библиотека diagrams работать не будет.
) else (
    dot -V
)

echo [6/7] Создание директорий temp и diagrams...
if not exist temp mkdir temp
if not exist diagrams mkdir diagrams

echo [7/7] Настройка .env...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [OK] Файл .env создан из примера.
    ) else (
        echo BOT_TOKEN=your_telegram_bot_token_here> .env
        echo GIGACHAT_CLIENT_SECRET=your_gigachat_client_secret_here>> .env
        echo [OK] Базовый .env файл создан.
    )
    echo [ВНИМАНИЕ] Не забудьте указать BOT_TOKEN и GIGACHAT_CLIENT_SECRET в .env
) else (
    echo [OK] Файл .env уже существует.
)

echo Установка завершена!
pause 