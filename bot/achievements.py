from database import Database

class AchievementSystem:
    def __init__(self):
        self.achievements = {
            'quiz_starter': {
                'name': 'Quiz Starter',
                'description': 'Complete your first quiz',
                'icon': '🎯'
            },
            'streak_3': {
                'name': 'Hot Streak',
                'description': 'Get a 3-question streak',
                'icon': '🔥'
            },
            'streak_10': {
                'name': 'Quiz Master',
                'description': 'Get a 10-question streak',
                'icon': '🏆'
            },
            'battle_winner': {
                'name': 'Battle Champion',
                'description': 'Win your first battle',
                'icon': '⚔️'
            }
        }

    def check_achievements(self, user_id, action, value=None):
        earned = []
        
        if action == 'quiz_complete':
            if value == 1:  # First quiz
                earned.append(self.grant_achievement(user_id, 'quiz_starter'))
                
        elif action == 'streak':
            if value >= 3:
                earned.append(self.grant_achievement(user_id, 'streak_3'))
            if value >= 10:
                earned.append(self.grant_achievement(user_id, 'streak_10'))
                
        elif action == 'battle_win':
            earned.append(self.grant_achievement(user_id, 'battle_winner'))
        
        return [f"{a['icon']} {a['name']}" for a in earned if a]

    def grant_achievement(self, user_id, achievement_id):
        # Check if already earned
        query = """
            SELECT 1 FROM user_achievements
            WHERE user_id = %s AND achievement_id = %s
        """
        exists = Database.execute_query(query, (user_id, achievement_id), fetch=True)
        
        if not exists:
            # Insert new achievement
            query = """
                INSERT INTO user_achievements (user_id, achievement_id)
                VALUES (%s, %s)
            """
            Database.execute_query(query, (user_id, achievement_id))
            return self.achievements.get(achievement_id)
        return None