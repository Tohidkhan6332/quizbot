import os
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database

class QuizEngine:
    def __init__(self):
        self.categories = self.load_categories()

    def load_categories(self):
        return {
            'general': 'General Knowledge',
            'science': 'Science',
            'history': 'History',
            'movies': 'Movies',
            'music': 'Music'
        }

    async def start_quiz_menu(self, update, context):
        keyboard = [
            [InlineKeyboardButton(category, callback_data=f"quiz_category_{cat_id}")]
            for cat_id, category in self.categories.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📚 Choose a quiz category:",
            reply_markup=reply_markup
        )

    async def handle_quiz_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        action = data[1]
        
        if action == 'category':
            await self.start_quiz(update, context, data[2])
        elif action == 'answer':
            await self.check_answer(update, context)
        elif action == 'next':
            await self.send_question(update, context)

    async def start_quiz(self, update, context, category):
        query = update.callback_query
        user_id = query.from_user.id
        
        # Initialize quiz session
        context.user_data['quiz'] = {
            'category': category,
            'score': 0,
            'streak': 0,
            'question_index': 0,
            'start_time': datetime.now(),
            'questions': self.get_questions(category, 10)
        }
        
        await self.send_question(update, context)

    def get_questions(self, category, limit):
        query = """
            SELECT question_id, question_text, option1, option2, option3, option4, correct_option
            FROM questions
            WHERE category = %s AND is_active = TRUE
            ORDER BY RANDOM()
            LIMIT %s
        """
        return Database.execute_query(query, (category, limit), fetch=True)

    async def send_question(self, update, context):
        quiz = context.user_data['quiz']
        question_data = quiz['questions'][quiz['question_index']]
        
        options = [
            question_data[2],  # option1
            question_data[3],  # option2
            question_data[4],  # option3
            question_data[5]   # option4
        ]
        
        # Shuffle options but remember correct index
        correct_index = question_data[6]
        shuffled = list(zip(options, [0, 1, 2, 3]))
        random.shuffle(shuffled)
        shuffled_options, original_indices = zip(*shuffled)
        new_correct_index = original_indices.index(correct_index)
        
        # Store correct index in user data
        context.user_data['quiz']['current_correct'] = new_correct_index
        
        keyboard = [
            [InlineKeyboardButton(option, callback_data=f"quiz_answer_{i}")]
            for i, option in enumerate(shuffled_options)
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❓ Question {quiz['question_index'] + 1}:\n{question_data[1]}",
            reply_markup=reply_markup
        )

    async def check_answer(self, update, context):
        query = update.callback_query
        await query.answer()
        
        quiz = context.user_data['quiz']
        selected_index = int(query.data.split('_')[2])
        is_correct = selected_index == quiz['current_correct']
        
        if is_correct:
            quiz['score'] += 10
            quiz['streak'] += 1
            feedback = "✅ Correct!"
        else:
            quiz['streak'] = 0
            correct_option = quiz['questions'][quiz['question_index']][2 + quiz['current_correct']]
            feedback = f"❌ Wrong! Correct answer was: {correct_option}"
        
        # Update message with feedback
        await query.edit_message_text(feedback)
        
        # Update database stats
        self.update_stats(
            query.from_user.id,
            is_correct,
            quiz['streak'],
            quiz['category']
        )
        
        # Move to next question or end quiz
        quiz['question_index'] += 1
        if quiz['question_index'] < len(quiz['questions']):
            await asyncio.sleep(1.5)
            await self.send_question(update, context)
        else:
            await self.end_quiz(update, context)

    def update_stats(self, user_id, is_correct, streak, category):
        # Update user stats in database
        pass  # Implementation omitted for brevity

    async def end_quiz(self, update, context):
        quiz = context.user_data['quiz']
        user_id = update.effective_user.id
        
        # Calculate time taken
        time_taken = (datetime.now() - quiz['start_time']).seconds
        
        # Save quiz results
        self.save_quiz_results(user_id, quiz)
        
        # Check achievements
        new_achievements = self.check_achievements(user_id)
        
        # Prepare result message
        message = (
            f"🏁 Quiz Complete!\n\n"
            f"📊 Your score: {quiz['score']} points\n"
            f"⏱ Time taken: {time_taken} seconds\n"
            f"🔥 Highest streak: {max(quiz.get('highest_streak', 0), quiz['streak'])}\n\n"
        )
        
        if new_achievements:
            message += "🎉 New achievements unlocked!\n" + "\n".join(new_achievements) + "\n\n"
        
        message += "Type /quiz to play again!"
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=message
        )
        
        # Clear quiz data
        del context.user_data['quiz']

    async def show_leaderboard(self, update, context):
        query = """
            SELECT u.user_id, u.username, us.total_score
            FROM user_stats us
            JOIN users u ON us.user_id = u.user_id
            ORDER BY us.total_score DESC
            LIMIT 10
        """
        top_players = Database.execute_query(query, fetch=True)
        
        leaderboard = "🏆 Top Players:\n\n"
        for i, (user_id, username, score) in enumerate(top_players, 1):
            leaderboard += f"{i}. @{username if username else user_id}: {score} pts\n"
        
        await update.message.reply_text(leaderboard)

    async def show_stats(self, update, context):
        user_id = update.effective_user.id
        query = """
            SELECT total_quizzes, correct_answers, wrong_answers, 
                   highest_streak, total_score
            FROM user_stats
            WHERE user_id = %s
        """
        stats = Database.execute_query(query, (user_id,), fetch=True)
        
        if stats:
            stats_msg = (
                f"📊 Your Stats:\n\n"
                f"📝 Quizzes taken: {stats[0][0]}\n"
                f"✅ Correct answers: {stats[0][1]}\n"
                f"❌ Wrong answers: {stats[0][2]}\n"
                f"🔥 Highest streak: {stats[0][3]}\n"
                f"🏆 Total score: {stats[0][4]}"
            )
            await update.message.reply_text(stats_msg)