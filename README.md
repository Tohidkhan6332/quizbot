# Ultimate Telegram Quiz Bot

## Features
- Multiple quiz modes (Timed, Survival, Categories)
- Real-time multiplayer battles
- Achievements and leaderboards
- Admin panel for question management
- PostgreSQL database
- Heroku-ready deployment

## Deployment

1. Clone this repository
2. Create a new Heroku app
3. Add PostgreSQL database
4. Set environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `DATABASE_URL`
   - `ADMIN_IDS` (comma-separated)
5. Deploy to Heroku

## Commands
- `/start` - Main menu
- `/quiz` - Start a new quiz
- `/battle` - Challenge a friend
- `/leaderboard` - View top players
- `/stats` - Your personal stats
- `/admin` - Admin panel (admin only)