import os
import psycopg2
from psycopg2 import pool, sql

class Database:
    __connection_pool = None

    @classmethod
    def initialize(cls):
        cls.__connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20, os.getenv('DATABASE_URL')
        )

    @classmethod
    def get_connection(cls):
        return cls.__connection_pool.getconn()

    @classmethod
    def return_connection(cls, connection):
        cls.__connection_pool.putconn(connection)

    @classmethod
    def execute_query(cls, query, params=None, fetch=False):
        conn = cls.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            cls.return_connection(conn)

    @classmethod
    def create_tables(cls):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(32),
                first_name VARCHAR(64),
                last_name VARCHAR(64),
                join_date TIMESTAMP DEFAULT NOW(),
                last_active TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS questions (
                question_id SERIAL PRIMARY KEY,
                category VARCHAR(32),
                question_text TEXT,
                option1 TEXT,
                option2 TEXT,
                option3 TEXT,
                option4 TEXT,
                correct_option SMALLINT,
                difficulty SMALLINT,
                added_by BIGINT REFERENCES users(user_id),
                added_date TIMESTAMP DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
                total_quizzes INT DEFAULT 0,
                correct_answers INT DEFAULT 0,
                wrong_answers INT DEFAULT 0,
                highest_streak INT DEFAULT 0,
                current_streak INT DEFAULT 0,
                total_score BIGINT DEFAULT 0,
                last_quiz TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS battles (
                battle_id SERIAL PRIMARY KEY,
                player1_id BIGINT REFERENCES users(user_id),
                player2_id BIGINT REFERENCES users(user_id),
                winner_id BIGINT REFERENCES users(user_id),
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id SERIAL PRIMARY KEY,
                name VARCHAR(64),
                description TEXT,
                icon VARCHAR(32)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS user_achievements (
                user_id BIGINT REFERENCES users(user_id),
                achievement_id INT REFERENCES achievements(achievement_id),
                earned_date TIMESTAMP DEFAULT NOW(),
                PRIMARY KEY (user_id, achievement_id)
            )
            """
        ]
        
        for query in queries:
            cls.execute_query(query)