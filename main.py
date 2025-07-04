import asyncio
import logging
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile

from config import BOT_TOKEN, PROXYAPI_KEY
from gigachat_client import gigachat_client, GigaChatClient
from diagram_generator import diagram_generator, generate_diagram_with_retries
from base_llm_client import BaseLLMClient
from proxyapi_client import ProxyApiClient


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

USER_DATA_FILE = "user_data.json"

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("api_keys", {}), data.get("models", {})
    except Exception:
        return {}, {}

def save_user_data():
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"api_keys": user_api_keys, "models": user_models}, f)

# Загрузка при старте
user_api_keys, user_models = load_user_data()

# Состояния для FSM
class UserStates(StatesGroup):
    waiting_api_key = State()
    waiting_diagram_request = State()
    selecting_model = State()


# Хранилище выбранных моделей пользователей
user_models = {}

# Словарь клиентов LLM
llm_clients = {
    "gigachat": GigaChatClient(),
    "proxyapi": ProxyApiClient(api_key=PROXYAPI_KEY),
    # "openai": OpenAIClient(),  # пример для будущего расширения
}
# Хранилище выбранных провайдеров пользователями
user_llm_provider = {}  # user_id: "gigachat" / "openai" / ...


def get_main_keyboard():
    """Возвращает основную клавиатуру бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 Выбрать провайдера LLM", callback_data="select_llm_provider")],
        [InlineKeyboardButton(text="🔑 Установить API ключ", callback_data="set_api_key")],
        [InlineKeyboardButton(text="🤖 Выбрать модель", callback_data="select_model")],
        [InlineKeyboardButton(text="📊 Создать диаграмму", callback_data="create_diagram")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])
    return keyboard


def format_error_details(error_details: dict, show_sensitive=False) -> str:
    """Форматирует детали ошибки для показа пользователю"""
    if not error_details:
        return "Детали ошибки недоступны"
    
    result = []
    
    # Основная информация
    result.append(f"🔍 **Диагностика запроса**\n")
    result.append(f"**Операция:** {error_details.get('operation', 'неизвестно')}")
    result.append(f"**URL:** `{error_details.get('url', 'неизвестно')}`")
    result.append(f"**Метод:** {error_details.get('method', 'неизвестно')}")
    
    # Заголовки
    if 'headers' in error_details:
        result.append(f"\n**Заголовки запроса:**")
        for key, value in error_details['headers'].items():
            result.append(f"• `{key}: {value}`")
    
    # Данные запроса
    if 'data' in error_details:
        result.append(f"\n**Данные запроса:**")
        for key, value in error_details['data'].items():
            result.append(f"• `{key}: {value}`")
    
    # Информация о ответе
    if 'response_status' in error_details:
        result.append(f"\n**Ответ сервера:**")
        result.append(f"**Статус:** {error_details['response_status']}")
        
        if 'response_headers' in error_details:
            result.append(f"**Заголовки ответа:**")
            for key, value in list(error_details['response_headers'].items())[:5]:  # Показываем только первые 5
                result.append(f"• `{key}: {value}`")
        
        if 'response_text' in error_details:
            response_text = error_details['response_text']
            if len(response_text) > 500:
                response_text = response_text[:500] + "..."
            result.append(f"**Текст ответа:**\n```\n{response_text}\n```")
    
    # Curl команда
    if 'curl_command' in error_details:
        result.append(f"\n**Эквивалентная curl команда:**\n```bash\n{error_details['curl_command']}\n```")
    
    # Ошибка
    if 'error' in error_details:
        result.append(f"\n❌ **Ошибка:** {error_details['error']}")
    
    # Успех
    if error_details.get('success'):
        result.append(f"\n✅ **Запрос выполнен успешно**")
        if 'token_expires_in' in error_details:
            result.append(f"• Токен действует: {error_details['token_expires_in']} секунд")
    
    return "\n".join(result)


def get_provider_name(code):
    if code == "gigachat":
        return "GigaChat"
    elif code == "proxyapi":
        return "ProxyAPI (OpenAI)"
    else:
        return code


def get_default_model(provider):
    if provider == "gigachat":
        return "GigaChat-Pro"
    elif provider == "proxyapi":
        return "gpt-3.5-turbo"
    else:
        return "default"


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    provider = user_llm_provider.get(user_id, "gigachat")
    provider_name = get_provider_name(provider)
    welcome_text = f"""
🚀 **Добро пожаловать в Diagram Generator Bot!**

Этот бот поможет вам создавать диаграммы с помощью искусственного интеллекта {provider_name}.

**Что умеет бот:**
📊 Создает диаграммы на основе ваших текстовых описаний
🔧 Генерирует Python код с использованием библиотеки diagrams
🖼️ Отправляет готовые диаграммы в формате PNG

**Для начала работы:**
1. Установите ваш API ключ {provider_name}
2. Опишите какую диаграмму хотите создать
3. Получите готовое изображение!

Выберите действие из меню ниже:
    """
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "set_api_key")
async def set_api_key_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик установки API ключа"""
    user_id = callback.from_user.id
    provider = user_llm_provider.get(user_id, "gigachat")
    if provider == "proxyapi":
        provider_name = "ProxyAPI"
    else:
        provider_name = "Гигачата"
    await callback.message.edit_text(
        f"🔑 **Установка API ключа {provider_name}**\n\n"
        f"Отправьте ваш API ключ {provider_name}.\n"
        "Ключ будет сохранен безопасно и использован только для генерации диаграмм.\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_api_key)


@dp.callback_query(F.data == "create_diagram")
async def create_diagram_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик создания диаграммы"""
    user_id = callback.from_user.id
    
    if user_id not in user_api_keys:
        await callback.message.edit_text(
            "❌ **API ключ не установлен**\n\n"
            "Для создания диаграмм необходимо установить API ключ Гигачата.\n"
            "Нажмите кнопку ниже для установки ключа.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    await callback.message.edit_text(
        "📊 **Создание диаграммы**\n\n"
        "Опишите какую диаграмму вы хотите создать.\n\n"
        "**Примеры запросов:**\n"
        "• Веб-архитектура с базой данных\n"
        "• Микросервисная архитектура\n"
        "• CI/CD пайплайн\n"
        "• Сетевая топология\n"
        "• Процесс разработки ПО\n\n"
        "Для отмены введите /cancel",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_diagram_request)


@dp.callback_query(F.data == "select_model")
async def select_model_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора модели"""
    user_id = callback.from_user.id
    provider = user_llm_provider.get(user_id, "gigachat")
    if user_id not in user_api_keys:
        await callback.message.edit_text(
            "❌ **API ключ не установлен**\n\n"
            f"Для выбора модели необходимо установить API ключ выбранного провайдера ({provider}).\n"
            "Нажмите кнопку ниже для установки ключа.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    llm_client = llm_clients[provider]
    llm_client.set_credentials(user_api_keys[user_id])
    status_message = await callback.message.edit_text("🔄 Получаю список доступных моделей...")
    try:
        models = await llm_client.get_available_models()
        current_model = llm_client.get_current_model()
        if models:
            model_buttons = []
            for model in models:
                model_id = model["id"]
                model_desc = model["description"]
                button_text = f"✅ {model_desc}" if model_id == current_model else model_desc
                model_buttons.append([InlineKeyboardButton(
                    text=button_text, 
                    callback_data=f"model_{model_id}"
                )])
            model_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=model_buttons)
            await status_message.edit_text(
                f"🤖 **Выбор модели**\n\n"
                f"**Текущий провайдер:** {provider}\n"
                f"**Текущая модель:** {current_model}\n\n"
                f"Выберите модель для генерации диаграмм:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await status_message.edit_text(
                f"❌ **Не удалось получить список моделей у провайдера {provider}**\n\n"
                "Используется модель по умолчанию: GigaChat-Pro",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        error_details = llm_client.get_last_error_details()
        error_text = f"❌ **Ошибка получения моделей у провайдера {provider}**\n\n"
        error_text += f"**Ошибка:** {str(e)}\n\n"
        if error_details and not error_details.get('success', False):
            error_text += "**📋 Детали запроса к API:**\n"
            error_text += format_error_details(error_details)
        if len(error_text) > 4000:
            await status_message.edit_text(
                f"❌ **Ошибка получения моделей у провайдера {provider}**\n\n"
                f"**Ошибка:** {str(e)}\n\n"
                "Отправляю подробную диагностику...",
                parse_mode="Markdown"
            )
            if error_details and not error_details.get('success', False):
                await callback.message.answer(
                    "**📋 Детали запроса к API:**\n" + format_error_details(error_details),
                    parse_mode="Markdown"
                )
            await callback.message.answer(
                f"Используется модель по умолчанию: GigaChat-Pro",
                reply_markup=get_main_keyboard()
            )
        else:
            await status_message.edit_text(
                error_text + "\n\nИспользуется модель по умолчанию: GigaChat-Pro",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )


@dp.callback_query(F.data.startswith("model_"))
async def model_selected_callback(callback: types.CallbackQuery):
    """Обработчик выбора конкретной модели"""
    model_id = callback.data.replace("model_", "")
    user_id = callback.from_user.id
    
    if user_id in user_api_keys:
        llm_client = llm_clients[user_llm_provider.get(user_id, "gigachat")]
        llm_client.set_credentials(user_api_keys[user_id])
        llm_client.set_model(model_id)
        user_models[user_id] = model_id
        save_user_data()
        
        await callback.message.edit_text(
            f"✅ **Модель выбрана!**\n\n"
            f"**Активная модель:** {model_id}\n\n"
            f"Теперь диаграммы будут создаваться с использованием этой модели.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_text(
            "❌ API ключ не найден. Установите ключ заново.",
            reply_markup=get_main_keyboard()
        )


@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery):
    help_text = f"""
🆘 **Справка по использованию бота**

**Бот поддерживает несколько LLM-провайдеров:**
• GigaChat
• ProxyAPI (OpenAI)

**Основные команды:**
• /start - Главное меню
• /cancel - Отмена текущего действия

**Как работает бот:**
1. **Установка API ключа** — вы предоставляете ключ выбранного провайдера
2. **Описание диаграммы** — описываете, что хотите визуализировать
3. **Генерация** — выбранный провайдер создает Python-код для диаграммы
4. **Результат** — бот выполняет код и отправляет PNG изображение

**Примеры запросов:**
• "Создай диаграмму веб-приложения с фронтендом, бэкендом и базой данных"
• "Покажи архитектуру микросервисов с API Gateway"
• "Нарисуй схему CI/CD процесса"

**Поддерживаемые типы диаграмм:**
• Архитектурные диаграммы
• Сетевые топологии
• Диаграммы процессов
• Схемы развертывания
• И многое другое!

**Техническая информация:**
Бот использует библиотеку diagrams для Python, поддерживающую множество облачных и on-prem провайдеров.
"""
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(StateFilter(UserStates.waiting_api_key))
async def process_api_key(message: types.Message, state: FSMContext):
    """Обработчик ввода API ключа"""
    api_key = message.text.strip()
    user_id = message.from_user.id
    provider = user_llm_provider.get(user_id, "gigachat")
    # Удаляем сообщение с API ключом из соображений безопасности
    try:
        await message.delete()
    except:
        pass
    # Проверяем API ключ
    if provider == "proxyapi":
        provider_name = "ProxyAPI"
    else:
        provider_name = "Гигачата"
    status_message = await message.answer(f"🔄 Проверяю API ключ {provider_name}...")
    try:
        llm_client = llm_clients[provider]
        llm_client.set_credentials(api_key)
        is_valid, error_message = await llm_client.check_credentials()
        if is_valid:
            user_api_keys[user_id] = api_key
            save_user_data()
            await status_message.edit_text(
                f"✅ **API ключ {provider_name} успешно установлен!**\n\n"
                "Теперь вы можете создавать диаграммы.\n"
                "Выберите действие из меню:",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            error_details = llm_client.get_last_error_details()
            error_text = f"❌ **Неверный API ключ {provider_name}**\n\n"
            if error_message:
                error_text += f"**Ошибка:** {error_message}\n\n"
            if error_details:
                error_text += format_error_details(error_details)
                error_text += "\n\n**💡 Рекомендации:**\n"
                error_text += "• Проверьте правильность API ключа\n"
                error_text += "• Убедитесь, что ключ активен\n"
                error_text += "• Проверьте права доступа к API\n"
                error_text += "• Сравните с запросом в Postman"
            else:
                error_text += "Проверьте правильность ключа и попробуйте снова."
            if len(error_text) > 4000:
                await status_message.edit_text(
                    f"❌ **Неверный API ключ {provider_name}**\n\n"
                    f"**Ошибка:** {error_message}\n\n"
                    "Отправляю подробную диагностику...",
                    parse_mode="Markdown"
                )
                await message.answer(
                    format_error_details(error_details),
                    parse_mode="Markdown"
                )
                await message.answer(
                    "**💡 Рекомендации:**\n"
                    "• Проверьте правильность API ключа\n"
                    "• Убедитесь, что ключ активен\n"
                    "• Проверьте права доступа к API\n"
                    "• Сравните с запросом в Postman",
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await status_message.edit_text(
                    error_text,
                    reply_markup=get_main_keyboard(),
                    parse_mode="Markdown"
                )
    except Exception as e:
        logger.error(f"Ошибка проверки API ключа: {e}")
        error_details = llm_client.get_last_error_details()
        error_text = f"❌ **Ошибка проверки API ключа {provider_name}**\n\n"
        error_text += f"**Ошибка:** {str(e)}\n\n"
        if error_details:
            error_text += format_error_details(error_details)
        if len(error_text) > 4000:
            await status_message.edit_text(
                f"❌ **Ошибка проверки API ключа {provider_name}**\n\n"
                f"**Ошибка:** {str(e)}\n\n"
                "Отправляю подробную диагностику...",
                parse_mode="Markdown"
            )
            if error_details:
                await message.answer(
                    format_error_details(error_details),
                    parse_mode="Markdown"
                )
            await message.answer(
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_main_keyboard()
            )
        else:
            await status_message.edit_text(
                error_text,
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    await state.clear()


@dp.message(StateFilter(UserStates.waiting_diagram_request))
async def process_diagram_request(message: types.Message, state: FSMContext):
    """Обработчик запроса на создание диаграммы"""
    user_id = message.from_user.id
    request_text = message.text.strip()
    
    if user_id not in user_api_keys:
        await message.answer(
            "❌ API ключ не найден. Установите ключ заново.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        return
    
    # Устанавливаем API ключ для текущего запроса
    llm_client = llm_clients[user_llm_provider.get(user_id, "gigachat")]
    llm_client.set_credentials(user_api_keys[user_id])
    
    status_message = await message.answer("🤖 Генерирую код диаграммы...")
    
    try:
        # Генерируем код диаграммы
        diagram_code = await llm_client.generate_diagram_code(request_text)
        await status_message.edit_text("🔨 Создаю диаграмму...")
        
        # Генерируем диаграмму с повторными попытками
        result = await generate_diagram_with_retries(diagram_code, user_id, llm_client, max_attempts=3)
        if isinstance(result, str):
            diagram_path = result
        else:
            diagram_path, last_code, last_error = result if isinstance(result, tuple) and len(result) == 3 else (None, None, None)
        # Отправляем диаграмму пользователю
        if diagram_path and os.path.exists(diagram_path):
            await status_message.edit_text("📤 Отправляю диаграмму...")
            diagram_file = FSInputFile(diagram_path)
            await message.answer_photo(
                diagram_file,
                caption=f"📊 **Диаграмма готова!**\n\n**Запрос:** {request_text}",
                parse_mode="Markdown"
            )
            # Отправляем исходный скрипт отдельным сообщением
            await message.answer(
                f"**Исходный скрипт диаграммы:**\n```python\n{diagram_code}\n```",
                parse_mode="Markdown"
            )
            # Удаляем временный файл (если он в temp)
            try:
                if os.path.dirname(diagram_path) == os.path.abspath(DIAGRAMS_DIR):
                    pass  # не удаляем из diagrams
                else:
                    os.remove(diagram_path)
            except:
                pass
            await status_message.delete()
            # Предлагаем создать еще одну диаграмму
            await message.answer(
                "✨ **Диаграмма создана успешно!**\n\n"
                "Хотите создать еще одну диаграмму?",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        elif last_code and last_error:
            # Не удалось получить рабочий скрипт за 3 попытки
            # Отправляем пользователю итоговый скрипт и текст ошибки
            code_block = f'<pre language="python">{last_code}</pre>'
            error_block = f'<b>Ошибка:</b> {last_error}'
            await status_message.edit_text(
                "❌ <b>Не удалось создать рабочий скрипт для диаграммы за 3 попытки.</b>\n\n"
                "<b>Последний вариант скрипта:</b>\n" + code_block + "\n\n" + error_block,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        else:
            await status_message.edit_text(
                "❌ **Ошибка создания диаграммы**\n\n"
                "Не удалось создать диаграмму. Попробуйте изменить запрос.",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка создания диаграммы: {e}")
        
        # Получаем детали ошибки для диагностики
        error_details = llm_client.get_last_error_details()
        
        error_text = f"❌ **Ошибка создания диаграммы**\n\n"
        error_text += f"**Ошибка:** {str(e)}\n\n"
        
        if error_details:
            if not error_details.get('success', False):
                error_text += "**📋 Детали запроса к API:**\n"
                error_text += format_error_details(error_details)
        
        error_text += "\n**💡 Попробуйте:**\n"
        error_text += "• Изменить формулировку запроса\n"
        error_text += "• Использовать более простое описание\n"
        error_text += "• Повторить попытку позже"
        
        # Если сообщение слишком длинное, разбиваем на части
        if len(error_text) > 4000:
            await status_message.edit_text(
                f"❌ **Ошибка создания диаграммы**\n\n"
                f"**Ошибка:** {str(e)}\n\n"
                "Отправляю подробную диагностику...",
                parse_mode="Markdown"
            )
            
            if error_details and not error_details.get('success', False):
                await message.answer(
                    "**📋 Детали запроса к API:**\n" + format_error_details(error_details),
                    parse_mode="Markdown"
                )
            
            await message.answer(
                "**💡 Попробуйте:**\n"
                "• Изменить формулировку запроса\n"
                "• Использовать более простое описание\n"
                "• Повторить попытку позже",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await status_message.edit_text(
                error_text,
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    
    await state.clear()


@dp.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext):
    """Обработчик команды отмены"""
    await state.clear()
    await message.answer(
        "✅ Действие отменено.",
        reply_markup=get_main_keyboard()
    )


@dp.message()
async def unknown_message(message: types.Message):
    """Обработчик неизвестных сообщений"""
    await message.answer(
        "🤔 Я не понимаю эту команду.\n\n"
        "Используйте меню для взаимодействия с ботом:",
        reply_markup=get_main_keyboard()
    )


@dp.callback_query(F.data == "select_llm_provider")
async def select_llm_provider_callback(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    current_provider = user_llm_provider.get(user_id, "gigachat")
    buttons = [
        [InlineKeyboardButton(text=("✅ " if current_provider=="gigachat" else "")+"GigaChat", callback_data="llmprov_gigachat")],
        [InlineKeyboardButton(text=("✅ " if current_provider=="proxyapi" else "")+"ProxyAPI (OpenAI)", callback_data="llmprov_proxyapi")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(
        f"🌐 <b>Выбор LLM-провайдера</b>\n\nТекущий: <b>{current_provider}</b>\n\nВыберите провайдера для генерации кода диаграмм:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("llmprov_"))
async def llm_provider_selected_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    provider = callback.data.replace("llmprov_", "")
    user_llm_provider[user_id] = provider
    await callback.message.edit_text(
        f"✅ Провайдер LLM выбран: <b>{provider}</b>\n\nТеперь генерация диаграмм будет выполняться через выбранного провайдера.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Проверяем наличие токена
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен в переменных окружения")
        return
    
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())