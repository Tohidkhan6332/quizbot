from bot.database import Database

def run_migrations():
    print("Running initial database migrations...")
    Database.initialize()
    Database.create_tables()
    print("Migrations completed successfully.")

if __name__ == '__main__':
    run_migrations()
