import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile

from config import BOT_TOKEN
from gigachat_client import gigachat_client
from diagram_generator import diagram_generator


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния для FSM
class UserStates(StatesGroup):
    waiting_api_key = State()
    waiting_diagram_request = State()
    selecting_model = State()
    waiting_error_fix_confirmation = State()


# Хранилище API ключей пользователей (в реальном приложении лучше использовать базу данных)
user_api_keys = {}

# Хранилище выбранных моделей пользователей
user_models = {}

# Хранилище контекста ошибок для исправления
user_error_context = {}


def get_main_keyboard():
    """Возвращает основную клавиатуру бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
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
        # Экранируем специальные символы для Telegram markdown
        curl_command = error_details['curl_command'].replace('_', '\\_').replace('*', '\\*').replace('`', '\\`')
        result.append(f"\n**Эквивалентная curl команда:**\n```\n{curl_command}\n```")
    
    # Ошибка
    if 'error' in error_details:
        result.append(f"\n❌ **Ошибка:** {error_details['error']}")
    
    # Успех
    if error_details.get('success'):
        result.append(f"\n✅ **Запрос выполнен успешно**")
        if 'token_expires_in' in error_details:
            result.append(f"• Токен действует: {error_details['token_expires_in']} секунд")
    
    return "\n".join(result)


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = """
🚀 **Добро пожаловать в Diagram Generator Bot!**

Этот бот поможет вам создавать диаграммы с помощью искусственного интеллекта Гигачат.

**Что умеет бот:**
📊 Создает диаграммы на основе ваших текстовых описаний
🔧 Генерирует Python код с использованием библиотеки diagrams
🖼️ Отправляет готовые диаграммы в формате PNG

**Для начала работы:**
1. Установите ваш API ключ Гигачата
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
    await callback.message.edit_text(
        "🔑 **Установка API ключа Гигачата**\n\n"
        "Отправьте ваш API ключ Гигачата.\n"
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
    
    if user_id not in user_api_keys:
        await callback.message.edit_text(
            "❌ **API ключ не установлен**\n\n"
            "Для выбора модели необходимо установить API ключ Гигачата.\n"
            "Нажмите кнопку ниже для установки ключа.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Устанавливаем API ключ для текущего запроса
    gigachat_client.set_credentials(user_api_keys[user_id])
    
    status_message = await callback.message.edit_text("🔄 Получаю список доступных моделей...")
    
    try:
        models = await gigachat_client.get_available_models()
        current_model = gigachat_client.get_current_model()
        
        if models:
            model_buttons = []
            for model in models:
                model_id = model["id"]
                model_desc = model["description"]
                
                # Добавляем галочку для текущей модели
                button_text = f"✅ {model_desc}" if model_id == current_model else model_desc
                model_buttons.append([InlineKeyboardButton(
                    text=button_text, 
                    callback_data=f"model_{model_id}"
                )])
            
            # Добавляем кнопку возврата
            model_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=model_buttons)
            
            await status_message.edit_text(
                f"🤖 **Выбор модели**\n\n"
                f"**Текущая модель:** {current_model}\n\n"
                f"Выберите модель для генерации диаграмм:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await status_message.edit_text(
                "❌ **Не удалось получить список моделей**\n\n"
                "Используется модель по умолчанию: GigaChat-Pro",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка получения моделей: {e}")
        
        # Получаем детали ошибки для диагностики
        error_details = gigachat_client.get_last_error_details()
        
        error_text = "❌ **Ошибка получения моделей**\n\n"
        error_text += f"**Ошибка:** {str(e)}\n\n"
        
        if error_details and not error_details.get('success', False):
            error_text += "**📋 Детали запроса к API:**\n"
            error_text += format_error_details(error_details)
        
        # Если сообщение слишком длинное, разбиваем на части
        if len(error_text) > 4000:
            await status_message.edit_text(
                "❌ **Ошибка получения моделей**\n\n"
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
                "Используется модель по умолчанию: GigaChat-Pro",
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
        gigachat_client.set_credentials(user_api_keys[user_id])
        gigachat_client.set_model(model_id)
        user_models[user_id] = model_id
        
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


@dp.callback_query(F.data == "fix_error")
async def fix_error_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик исправления ошибки через Gigachat"""
    user_id = callback.from_user.id
    
    if user_id not in user_error_context:
        await callback.message.edit_text(
            "❌ Контекст ошибки не найден. Попробуйте создать диаграмму заново.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    if user_id not in user_api_keys:
        await callback.message.edit_text(
            "❌ API ключ не найден. Установите ключ заново.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Устанавливаем API ключ
    gigachat_client.set_credentials(user_api_keys[user_id])
    
    # Получаем контекст ошибки
    error_context = user_error_context[user_id]
    
    status_message = await callback.message.edit_text("🔧 Прошу Gigachat исправить код...")
    
    try:
        # Просим Gigachat исправить код
        fixed_code = await gigachat_client.fix_diagram_code(
            error_context['original_code'],
            error_context['error_message'],
            error_context['user_request']
        )
        
        await status_message.edit_text("🔨 Пытаюсь выполнить исправленный код...")
        
        # Пытаемся выполнить исправленный код
        diagram_path = await diagram_generator.generate_diagram(fixed_code, user_id)
        
        # Очищаем контекст ошибки
        del user_error_context[user_id]
        
        # Отправляем диаграмму пользователю
        if diagram_path and os.path.exists(diagram_path):
            await status_message.edit_text("📤 Отправляю исправленную диаграмму...")
            
            diagram_file = FSInputFile(diagram_path)
            await callback.message.answer_photo(
                diagram_file,
                caption=f"📊 **Диаграмма исправлена и готова!**\n\n**Запрос:** {error_context['user_request']}",
                parse_mode="Markdown"
            )
            
            # Удаляем временный файл
            try:
                os.remove(diagram_path)
            except:
                pass
                
            await status_message.delete()
            
            # Предлагаем создать еще одну диаграмму
            await callback.message.answer(
                "✨ **Диаграмма успешно исправлена!**\n\n"
                "Gigachat смог исправить ошибку в коде. Хотите создать еще одну диаграмму?",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await status_message.edit_text(
                "❌ **Не удалось создать диаграмму даже после исправления**\n\n"
                "Попробуйте изменить формулировку запроса.",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка исправления кода: {e}")
        
        await status_message.edit_text(
            f"❌ **Ошибка при исправлении кода**\n\n"
            f"**Ошибка:** {str(e)}\n\n"
            f"Gigachat не смог исправить код. Попробуйте изменить запрос или создать диаграмму заново.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    await state.clear()


@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик возврата в главное меню"""
    # Очищаем состояние и контекст ошибки
    await state.clear()
    user_id = callback.from_user.id
    if user_id in user_error_context:
        del user_error_context[user_id]
    
    await callback.message.edit_text(
        "🏠 **Главное меню**\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery):
    """Обработчик помощи"""
    help_text = """
🆘 **Справка по использованию бота**

**Основные команды:**
• /start - Главное меню
• /cancel - Отмена текущего действия

**Как работает бот:**
1. **Установка API ключа** - вы предоставляете ключ от Гигачата
2. **Описание диаграммы** - описываете что хотите визуализировать
3. **Генерация** - Гигачат создает Python код для диаграммы
4. **Результат** - бот выполняет код и отправляет PNG изображение

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
Бот использует библиотеку diagrams для Python, которая поддерживает множество провайдеров облачных сервисов (AWS, Azure, GCP) и других компонентов.
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
    
    # Удаляем сообщение с API ключом из соображений безопасности
    try:
        await message.delete()
    except:
        pass
    
    # Проверяем API ключ
    status_message = await message.answer("🔄 Проверяю API ключ...")
    
    try:
        gigachat_client.set_credentials(api_key)
        is_valid, error_message = await gigachat_client.check_credentials()
        
        if is_valid:
            user_api_keys[user_id] = api_key
            await status_message.edit_text(
                "✅ **API ключ успешно установлен!**\n\n"
                "Теперь вы можете создавать диаграммы.\n"
                "Выберите действие из меню:",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            # Получаем детали ошибки
            error_details = gigachat_client.get_last_error_details()
            
            error_text = "❌ **Неверный API ключ**\n\n"
            
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
            
            # Если сообщение слишком длинное, разбиваем на части
            if len(error_text) > 4000:
                await status_message.edit_text(
                    "❌ **Неверный API ключ**\n\n"
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
        
        # Получаем детали ошибки для диагностики
        error_details = gigachat_client.get_last_error_details()
        
        error_text = "❌ **Ошибка проверки API ключа**\n\n"
        error_text += f"**Ошибка:** {str(e)}\n\n"
        
        if error_details:
            error_text += format_error_details(error_details)
        
        # Если сообщение слишком длинное, разбиваем на части
        if len(error_text) > 4000:
            await status_message.edit_text(
                "❌ **Ошибка проверки API ключа**\n\n"
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
    gigachat_client.set_credentials(user_api_keys[user_id])
    
    status_message = await message.answer("🤖 Генерирую код диаграммы...")
    
    try:
        # Генерируем код диаграммы
        diagram_code = await gigachat_client.generate_diagram_code(request_text)
        
        # Показываем сгенерированный код пользователю
        code_text = f"📝 **Сгенерированный код диаграммы:**\n\n```python\n{diagram_code}\n```"
        
        # Если код слишком длинный, обрезаем для показа
        if len(code_text) > 4000:
            truncated_code = diagram_code[:3000] + "\n... (код обрезан)"
            code_text = f"📝 **Сгенерированный код диаграммы:**\n\n```python\n{truncated_code}\n```"
        
        await status_message.edit_text(code_text, parse_mode="Markdown")
        
        # Отправляем статус выполнения
        execution_message = await message.answer("🔨 **Пытаюсь выполнить код и создать диаграмму...**", parse_mode="Markdown")
        
        # Генерируем диаграмму
        diagram_path = await diagram_generator.generate_diagram(diagram_code, user_id)
        
        # Отправляем диаграмму пользователю
        if diagram_path and os.path.exists(diagram_path):
            await execution_message.edit_text("📤 **Отправляю диаграмму...**", parse_mode="Markdown")
            
            diagram_file = FSInputFile(diagram_path)
            await message.answer_photo(
                diagram_file,
                caption=f"📊 **Диаграмма готова!**\n\n**Запрос:** {request_text}",
                parse_mode="Markdown"
            )
            
            # Удаляем временный файл
            try:
                os.remove(diagram_path)
            except:
                pass
                
            await execution_message.delete()
            
            # Предлагаем создать еще одну диаграмму
            await message.answer(
                "✨ **Диаграмма создана успешно!**\n\n"
                "Хотите создать еще одну диаграмму?",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
        else:
            # Удаляем сообщение о выполнении
            if 'execution_message' in locals():
                try:
                    await execution_message.delete()
                except:
                    pass
            
            await status_message.edit_text(
                "❌ **Ошибка создания диаграммы**\n\n"
                "Не удалось создать диаграмму. Попробуйте изменить запрос.",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка создания диаграммы: {e}")
        
        # Сохраняем контекст ошибки для возможного исправления
        if 'diagram_code' in locals():
            user_error_context[user_id] = {
                'original_code': diagram_code,
                'error_message': str(e),
                'user_request': request_text
            }
            
            # Показываем ошибку и предлагаем исправление
            error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="� Попросить Gigachat исправить", callback_data="fix_error")],
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
            ])
            
            await status_message.edit_text(
                f"❌ **Ошибка создания диаграммы**\n\n"
                f"**Ошибка:** {str(e)}\n\n"
                f"💡 Я могу попросить Gigachat проанализировать ошибку и исправить код. "
                f"Хотите попробовать?",
                reply_markup=error_keyboard,
                parse_mode="Markdown"
            )
        else:
            # Если нет сгенерированного кода (ошибка на этапе генерации)
            error_text = f"❌ **Ошибка создания диаграммы**\n\n"
            error_text += f"**Ошибка:** {str(e)}\n\n"
            
            # Получаем детали ошибки для диагностики API
            error_details = gigachat_client.get_last_error_details()
            if error_details and not error_details.get('success', False):
                error_text += "**📋 Детали запроса к API:**\n"
                error_text += format_error_details(error_details)
            
            error_text += "\n**💡 Попробуйте:**\n"
            error_text += "• Изменить формулировку запроса\n"
            error_text += "• Использовать более простое описание\n"
            error_text += "• Повторить попытку позже"
            
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