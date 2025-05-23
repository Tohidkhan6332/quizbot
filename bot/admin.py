from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database

class AdminPanel:
    def __init__(self):
        self.admin_commands = {
            'add_question': self.add_question,
            'edit_question': self.edit_question,
            'toggle_question': self.toggle_question,
            'view_stats': self.view_stats,
            'broadcast': self.broadcast
        }

    async def admin_menu(self, update, context):
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("🚫 You don't have admin privileges.")
            return
        
        keyboard = [
            [InlineKeyboardButton("➕ Add Question", callback_data="admin_add_question")],
            [InlineKeyboardButton("✏️ Edit Question", callback_data="admin_edit_question")],
            [InlineKeyboardButton("🔧 Toggle Question", callback_data="admin_toggle_question")],
            [InlineKeyboardButton("📊 View Stats", callback_data="admin_view_stats")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🛠 Admin Panel:",
            reply_markup=reply_markup
        )

    async def handle_admin_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("🚫 You don't have admin privileges.")
            return
        
        action = query.data.split('_')[1]
        if action in self.admin_commands:
            await self.admin_commands[action](update, context)

    async def add_question(self, update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please send the question in this format:\n\n"
                 "Category|Question Text|Option1|Option2|Option3|Option4|CorrectOption\n\n"
                 "Example: science|What is H2O?|Gold|Water|Salt|Oxygen|2"
        )
        context.user_data['awaiting_question'] = True

    async def edit_question(self, update, context):
        # Implementation for editing questions
        pass

    async def toggle_question(self, update, context):
        # Implementation for toggling question status
        pass

    async def view_stats(self, update, context):
        query = """
            SELECT COUNT(*) as total_users,
                   (SELECT COUNT(*) FROM questions) as total_questions,
                   (SELECT COUNT(*) FROM questions WHERE is_active = TRUE) as active_questions,
                   (SELECT SUM(total_score) FROM user_stats) as total_points
            FROM users
        """
        stats = Database.execute_query(query, fetch=True)
        
        if stats:
            stats_msg = (
                "📊 Bot Statistics:\n\n"
                f"👥 Total users: {stats[0][0]}\n"
                f"📝 Total questions: {stats[0][1]}\n"
                f"✅ Active questions: {stats[0][2]}\n"
                f"🏆 Total points earned: {stats[0][3]}"
            )
            await update.callback_query.edit_message_text(stats_msg)

    async def broadcast(self, update, context):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please send the message you want to broadcast to all users:"
        )
        context.user_data['awaiting_broadcast'] = True

    def is_admin(self, user_id):
        admin_ids = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',') if id]
        return user_id in admin_ids