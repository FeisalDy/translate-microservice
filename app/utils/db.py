import psycopg2
from psycopg2.extensions import connection as Connection


def create_connection() -> Connection:
    return psycopg2.connect(
        database="novel-postgres",
        user="postgres",
        password="admin",
        host="localhost",
        port="5432"
    )
