import os
import psycopg2
from psycopg2 import pool

class Database:
    __connection_pool = None

    @classmethod
    def initialize(cls):
        # Get database URL from environment variable
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Parse the URL (Heroku provides it in postgres:// format, psycopg2 needs postgresql://)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        # Initialize connection pool
        cls.__connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url
        )
