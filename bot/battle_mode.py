import os
import random
import uuid
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import Database

class BattleMode:
    def __init__(self):
        self.active_battles = {}

    async def challenge_menu(self, update, context):
        keyboard = [
            [InlineKeyboardButton("Random Opponent", callback_data="battle_random")],
            [InlineKeyboardButton("Challenge Friend", callback_data="battle_friend")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "⚔️ Choose battle mode:",
            reply_markup=reply_markup
        )

    async def handle_battle_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        action = data[1]
        
        if action == 'random':
            await self.find_random_opponent(update, context)
        elif action == 'friend':
            await self.create_friend_challenge(update, context)
        elif action == 'accept':
            await self.accept_battle(update, context)
        elif action == 'decline':
            await self.decline_battle(update, context)
        elif action == 'answer':
            await self.handle_battle_answer(update, context)

    async def find_random_opponent(self, update, context):
        # Implementation for random matchmaking
        pass

    async def create_friend_challenge(self, update, context):
        battle_id = str(uuid.uuid4())
        creator_id = update.effective_user.id
        
        self.active_battles[battle_id] = {
            'creator': creator_id,
            'opponent': None,
            'status': 'waiting',
            'questions': self.get_battle_questions(),
            'scores': {creator_id: 0},
            'current_question': 0,
            'created_at': datetime.now()
        }
        
        share_link = f"https://t.me/{context.bot.username}?start=battle_{battle_id}"
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "⚔️ Challenge created!\n\n"
                f"Share this link with your friend:\n{share_link}\n\n"
                "They have 5 minutes to accept."
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Cancel Challenge", callback_data=f"battle_cancel_{battle_id}")]
            ])
        )

    async def accept_battle(self, update, context):
        query = update.callback_query
        battle_id = query.data.split('_')[2]
        
        if battle_id not in self.active_battles:
            await query.edit_message_text("This battle has expired or been canceled.")
            return
        
        battle = self.active_battles[battle_id]
        opponent_id = query.from_user.id
        
        if opponent_id == battle['creator']:
            await query.answer("You can't battle yourself!")
            return
        
        battle['opponent'] = opponent_id
        battle['status'] = 'active'
        battle['scores'][opponent_id] = 0
        
        # Notify both players
        await context.bot.send_message(
            chat_id=battle['creator'],
            text=f"@{query.from_user.username} has accepted your challenge! Battle starting..."
        )
        
        await query.edit_message_text("Battle accepted! Starting now...")
        
        # Start battle
        await self.send_battle_question(update, context, battle_id)

    async def send_battle_question(self, update, context, battle_id):
        battle = self.active_battles[battle_id]
        question = battle['questions'][battle['current_question']]
        
        options = [question[2], question[3], question[4], question[5]]
        correct_index = question[6]
        
        # Shuffle options
        shuffled = list(zip(options, [0, 1, 2, 3]))
        random.shuffle(shuffled)
        shuffled_options, original_indices = zip(*shuffled)
        new_correct_index = original_indices.index(correct_index)
        
        # Store correct answer
        battle['current_correct'] = new_correct_index
        
        keyboard = [
            [InlineKeyboardButton(option, callback_data=f"battle_answer_{battle_id}_{i}")]
            for i, option in enumerate(shuffled_options)
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send question to both players
        for player_id in [battle['creator'], battle['opponent']]:
            try:
                await context.bot.send_message(
                    chat_id=player_id,
                    text=f"⚔️ Battle Question {battle['current_question'] + 1}:\n{question[1]}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Failed to send to {player_id}: {e}")

    async def handle_battle_answer(self, update, context):
        query = update.callback_query
        await query.answer()
        
        data = query.data.split('_')
        battle_id = data[2]
        selected_index = int(data[3])
        
        if battle_id not in self.active_battles:
            await query.edit_message_text("This battle has ended.")
            return
        
        battle = self.active_battles[battle_id]
        user_id = query.from_user.id
        
        if user_id not in [battle['creator'], battle['opponent']]:
            await query.answer("You're not in this battle!")
            return
        
        is_correct = selected_index == battle['current_correct']
        
        if is_correct:
            battle['scores'][user_id] += 10
            feedback = "✅ Correct!"
        else:
            correct_option = battle['questions'][battle['current_question']][2 + battle['current_correct']]
            feedback = f"❌ Wrong! Correct answer was: {correct_option}"
        
        await query.edit_message_text(feedback)
        
        # Move to next question or end battle
        battle['current_question'] += 1
        if battle['current_question'] < len(battle['questions']):
            await asyncio.sleep(2)
            await self.send_battle_question(update, context, battle_id)
        else:
            await self.end_battle(update, context, battle_id)

    async def end_battle(self, update, context, battle_id):
        battle = self.active_battles[battle_id]
        creator_score = battle['scores'][battle['creator']]
        opponent_score = battle['scores'][battle['opponent']]
        
        if creator_score > opponent_score:
            winner_id = battle['creator']
            result = "You won! 🏆"
        elif opponent_score > creator_score:
            winner_id = battle['opponent']
            result = "You lost! 😢"
        else:
            winner_id = None
            result = "It's a tie! 🤝"
        
        # Save battle results to database
        self.save_battle_results(battle, winner_id)
        
        # Prepare result messages
        creator_msg = (
            f"⚔️ Battle Results:\n\n"
            f"Your score: {creator_score}\n"
            f"Opponent score: {opponent_score}\n\n"
            f"{result if winner_id == battle['creator'] else result.replace('You', 'Opponent')}"
        )
        
        opponent_msg = (
            f"⚔️ Battle Results:\n\n"
            f"Your score: {opponent_score}\n"
            f"Opponent score: {creator_score}\n\n"
            f"{result if winner_id == battle['opponent'] else result.replace('You', 'Opponent')}"
        )
        
        # Send results to both players
        await context.bot.send_message(chat_id=battle['creator'], text=creator_msg)
        await context.bot.send_message(chat_id=battle['opponent'], text=opponent_msg)
        
        # Clean up
        del self.active_battles[battle_id]

    def get_battle_questions(self):
        query = """
            SELECT question_id, question_text, option1, option2, option3, option4, correct_option
            FROM questions
            WHERE is_active = TRUE
            ORDER BY RANDOM()
            LIMIT 5
        """
        return Database.execute_query(query, fetch=True)

    def save_battle_results(self, battle, winner_id):
        # Save battle results to database
        pass  # Implementation omitted for brevity