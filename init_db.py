import os

import psycopg

SCHEMA_FILE = "schema.sql"

def init_db():
    """
    schema.sq;を読み込み、
    PostgreSQLに必要なテーブルを作成する。
    """
    database_url = os.environ["DATABASE_URL"]
    
    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema_sql = file.read()
        
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cursor:
            for statement in schema_sql.split(";"):
                statement = statement.strip()
                
                if statement:
                    cursor.execute(statement)
    
    print("データベースを初期化しました。")
    
if __name__ == "__main__":
    init_db()
    
