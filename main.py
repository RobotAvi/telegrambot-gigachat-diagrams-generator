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


# Хранилище API ключей пользователей (в реальном приложении лучше использовать базу данных)
user_api_keys = {}

# Хранилище выбранных моделей пользователей
user_models = {}


def get_main_keyboard():
    """Возвращает основную клавиатуру бота"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Установить API ключ", callback_data="set_api_key")],
        [InlineKeyboardButton(text="🤖 Выбрать модель", callback_data="select_model")],
        [InlineKeyboardButton(text="📊 Создать диаграмму", callback_data="create_diagram")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])
    return keyboard


@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    current_model = user_models.get(user_id, "GigaChat-Pro")
    
    welcome_text = f"""
🚀 **Добро пожаловать в Diagram Generator Bot!**

Этот бот поможет вам создавать диаграммы с помощью искусственного интеллекта Гигачат.

**Что умеет бот:**
📊 Создает диаграммы на основе ваших текстовых описаний
🔧 Генерирует Python код с использованием библиотеки diagrams
🖼️ Отправляет готовые диаграммы в формате PNG

**Текущие настройки:**
🤖 Активная модель: **{current_model}**
{'🔑 API ключ: ✅ Установлен' if user_id in user_api_keys else '🔑 API ключ: ❌ Не установлен'}

**Для начала работы:**
1. Установите ваш API ключ Гигачата
2. Выберите подходящую модель GigaChat
3. Опишите какую диаграмму хотите создать
4. Получите готовое изображение!

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
            "Для выбора модели необходимо сначала установить API ключ Гигачата.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    await callback.message.edit_text(
        "🔄 **Загружаю доступные модели...**",
        parse_mode="Markdown"
    )
    
    try:
        # Устанавливаем API ключ для запроса
        gigachat_client.set_credentials(user_api_keys[user_id])
        
        # Получаем список моделей
        models = await gigachat_client.get_available_models()
        
        # Текущая модель
        current_model = user_models.get(user_id, "GigaChat-Pro")
        
        # Создаем клавиатуру с моделями
        keyboard_buttons = []
        for model in models:
            model_id = model["id"]
            description = model["description"]
            
            # Отмечаем текущую модель
            text = f"{'✅ ' if model_id == current_model else ''}🤖 {description}"
            keyboard_buttons.append([
                InlineKeyboardButton(text=text, callback_data=f"model_{model_id}")
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"🤖 **Выбор модели GigaChat**\n\n"
            f"**Текущая модель:** {current_model}\n\n"
            f"Выберите модель для генерации диаграмм:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки моделей: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка загрузки моделей**\n\n"
            "Не удалось получить список доступных моделей. "
            "Проверьте API ключ и попробуйте позже.",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )


@dp.callback_query(F.data.startswith("model_"))
async def model_selected_callback(callback: types.CallbackQuery):
    """Обработчик выбора конкретной модели"""
    user_id = callback.from_user.id
    model_id = callback.data.replace("model_", "")
    
    # Сохраняем выбранную модель
    user_models[user_id] = model_id
    gigachat_client.set_model(model_id)
    
    await callback.message.edit_text(
        f"✅ **Модель выбрана!**\n\n"
        f"**Активная модель:** {model_id}\n\n"
        f"Теперь все диаграммы будут генерироваться с использованием этой модели.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery):
    """Возврат в главное меню"""
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
2. **Выбор модели** - выбираете подходящую модель GigaChat
3. **Описание диаграммы** - описываете что хотите визуализировать
4. **Генерация** - Гигачат создает Python код для диаграммы
5. **Результат** - бот выполняет код и отправляет PNG изображение

**Доступные модели:**
• **GigaChat** - базовая модель (быстрая)
• **GigaChat-Pro** - продвинутая модель (рекомендуется)
• **GigaChat-Max** - максимальная модель (самая умная)

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
        is_valid = await gigachat_client.check_credentials()
        
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
            await status_message.edit_text(
                "❌ **Неверный API ключ**\n\n"
                "Проверьте правильность ключа и попробуйте снова.",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка проверки API ключа: {e}")
        await status_message.edit_text(
            "❌ **Ошибка проверки API ключа**\n\n"
            "Произошла ошибка при проверке ключа. Попробуйте позже.",
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
    
    # Устанавливаем API ключ и выбранную модель для текущего запроса
    gigachat_client.set_credentials(user_api_keys[user_id])
    
    # Устанавливаем выбранную пользователем модель
    selected_model = user_models.get(user_id, "GigaChat-Pro")
    gigachat_client.set_model(selected_model)
    
    status_message = await message.answer(f"🤖 Генерирую код диаграммы с помощью {selected_model}...")
    
    try:
        # Генерируем код диаграммы
        diagram_code = await gigachat_client.generate_diagram_code(request_text)
        
        await status_message.edit_text("🔨 Создаю диаграмму...")
        
        # Генерируем диаграмму
        diagram_path = await diagram_generator.generate_diagram(diagram_code, user_id)
        
        # Отправляем диаграмму пользователю
        if diagram_path and os.path.exists(diagram_path):
            await status_message.edit_text("📤 Отправляю диаграмму...")
            
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
                
            await status_message.delete()
            
            # Предлагаем создать еще одну диаграмму
            await message.answer(
                "✨ **Диаграмма создана успешно!**\n\n"
                "Хотите создать еще одну диаграмму?",
                reply_markup=get_main_keyboard(),
                parse_mode="Markdown"
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
        await status_message.edit_text(
            f"❌ **Ошибка создания диаграммы**\n\n"
            f"Произошла ошибка: {str(e)}\n\n"
            f"Попробуйте изменить запрос или попробовать позже.",
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