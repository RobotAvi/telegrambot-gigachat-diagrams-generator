import os
import asyncio
from typing import List, Dict, Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv
import json

load_dotenv()

class TelegramService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.bot = None
        self.application = None
        
        if self.token:
            self.bot = Bot(token=self.token)
            self.application = Application.builder().token(self.token).build()
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup Telegram bot handlers."""
        if not self.application:
            return
            
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        
        # Callback query handler for job selections
        self.application.add_handler(CallbackQueryHandler(self._handle_job_selection))
    
    async def send_job_notifications(self, chat_id: str, jobs: List[Dict], user_id: int) -> bool:
        """Send job notifications to user with selection buttons."""
        if not self.bot:
            print("Telegram bot not configured")
            return False
        
        try:
            if not jobs:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="🔍 Сегодня новых подходящих вакансий не найдено."
                )
                return True
            
            message = f"🎯 Найдено {len(jobs)} подходящих вакансий:\n\n"
            
            for i, job in enumerate(jobs[:10], 1):  # Limit to 10 jobs
                salary_info = ""
                if job.get("salary_min") or job.get("salary_max"):
                    salary_parts = []
                    if job.get("salary_min"):
                        salary_parts.append(f"от {job['salary_min']:,}")
                    if job.get("salary_max"):
                        salary_parts.append(f"до {job['salary_max']:,}")
                    salary_info = f" ({' '.join(salary_parts)} {job.get('salary_currency', 'RUB')})"
                
                message += f"{i}. **{job['title']}**\n"
                message += f"🏢 {job['company']}\n"
                if job.get('location'):
                    message += f"📍 {job['location']}\n"
                message += f"💰 {salary_info}\n"
                message += f"🔗 [Ссылка]({job['external_url']})\n\n"
            
            # Create inline keyboard for job selection
            keyboard = []
            for i, job in enumerate(jobs[:10]):
                keyboard.append([
                    InlineKeyboardButton(
                        f"✅ Подать заявку на {i+1}",
                        callback_data=f"apply_{user_id}_{job['external_id']}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("❌ Пропустить все", callback_data=f"skip_all_{user_id}")
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False
    
    async def send_simple_notification(self, chat_id: str, message: str) -> bool:
        """Send a simple text notification."""
        if not self.bot:
            return False
        
        try:
            await self.bot.send_message(chat_id=chat_id, text=message)
            return True
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    async def send_application_status(self, chat_id: str, job_title: str, company: str, status: str) -> bool:
        """Send job application status update."""
        status_emoji = {
            "sent": "✅",
            "error": "❌",
            "hr_contacted": "📧"
        }
        
        emoji = status_emoji.get(status, "ℹ️")
        message = f"{emoji} **{job_title}** в {company}\n"
        
        if status == "sent":
            message += "Заявка отправлена успешно!"
        elif status == "error":
            message += "Ошибка при отправке заявки."
        elif status == "hr_contacted":
            message += "HR-менеджер получил сообщение."
        
        return await self.send_simple_notification(chat_id, message)
    
    async def _start_command(self, update, context):
        """Handle /start command."""
        welcome_message = """
🤖 Добро пожаловать в Job Assistant!

Я помогу вам найти работу и автоматически подавать заявки на подходящие вакансии.

Команды:
/help - Справка
/status - Статус поиска работы

Чтобы начать, настройте свой профиль в веб-интерфейсе и загрузите резюме.
        """
        
        await update.message.reply_text(welcome_message)
    
    async def _help_command(self, update, context):
        """Handle /help command."""
        help_message = """
🆘 **Справка по Job Assistant**

**Как это работает:**
1. Загрузите резюме в веб-интерфейсе
2. Настройте параметры поиска
3. Каждое утро бот ищет подходящие вакансии
4. Вы получаете уведомления с найденными вакансиями
5. Выбираете интересные и бот подает заявки автоматически

**Команды:**
/start - Начать работу
/status - Проверить статус
/help - Эта справка

**Поддержка:** support@jobassistant.com
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def _status_command(self, update, context):
        """Handle /status command."""
        # This would typically fetch user status from database
        status_message = """
📊 **Статус поиска работы:**

🎯 Активные поиски: Включены
📄 Резюме: Загружено
🔍 Последний поиск: Сегодня в 09:00
📝 Заявок отправлено: 5
📧 HR-менеджеров уведомлено: 3

Следующий поиск: Завтра в 09:00
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def _handle_job_selection(self, update, context):
        """Handle job selection callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data.startswith("apply_"):
            # Extract user_id and job_id from callback data
            parts = data.split("_")
            user_id = parts[1]
            job_id = parts[2]
            
            # Here you would trigger the job application process
            await query.edit_message_text(
                text=f"✅ Заявка на вакансию отправляется...\n\nВы получите уведомление о результате."
            )
            
            # TODO: Trigger actual application process
            
        elif data.startswith("skip_all_"):
            await query.edit_message_text(
                text="❌ Все вакансии пропущены. До встречи завтра!"
            )
    
    def start_bot(self):
        """Start the Telegram bot."""
        if self.application:
            self.application.run_polling()