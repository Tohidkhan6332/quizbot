import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from database import Database
from quiz_engine import QuizEngine
from battle_mode import BattleMode
from admin import AdminPanel
from achievements import AchievementSystem

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class QuizBot:
    def __init__(self):
        Database.initialize()
        self.quiz_engine = QuizEngine()
        self.battle_mode = BattleMode()
        self.admin_panel = AdminPanel()
        self.achievements = AchievementSystem()

    async def start(self, update, context):
        user = update.effective_user
        welcome_msg = (
            f"👋 Welcome {user.first_name} to QuizMaster Pro!\n\n"
            "🎮 Available Commands:\n"
            "/quiz - Start a new quiz\n"
            "/battle - Challenge a friend\n"
            "/leaderboard - View top players\n"
            "/stats - Your personal stats\n"
        )
        await update.message.reply_text(welcome_msg)

    async def error_handler(self, update, context):
        logger.error(f"Update {update} caused error: {context.error}")

    def setup_handlers(self, application):
        # Command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("quiz", self.quiz_engine.start_quiz_menu))
        application.add_handler(CommandHandler("battle", self.battle_mode.challenge_menu))
        application.add_handler(CommandHandler("leaderboard", self.quiz_engine.show_leaderboard))
        application.add_handler(CommandHandler("stats", self.quiz_engine.show_stats))
        application.add_handler(CommandHandler("admin", self.admin_panel.admin_menu))

        # Callback handlers
        application.add_handler(CallbackQueryHandler(self.quiz_engine.handle_quiz_callback, pattern="^quiz_"))
        application.add_handler(CallbackQueryHandler(self.battle_mode.handle_battle_callback, pattern="^battle_"))
        application.add_handler(CallbackQueryHandler(self.admin_panel.handle_admin_callback, pattern="^admin_"))

        # Error handler
        application.add_error_handler(self.error_handler)

def main():
    bot = QuizBot()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    application = Application.builder().token(token).build()
    
    bot.setup_handlers(application)

    if 'DYNO' in os.environ:  # Running on Heroku
        webhook_url = os.getenv('WEBHOOK_URL') + '/telegram'
        port = int(os.environ.get('PORT', 5000))
        
        async def post_init(app):
            await app.bot.set_webhook(webhook_url)
        
        application.post_init = post_init
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )
    else:  # Running locally
        application.run_polling()

if __name__ == '__main__':
    main()