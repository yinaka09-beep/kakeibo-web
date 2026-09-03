import sqlite3

DB_NAME = "kakeibo_practice.db"
SCHEMA_FILE = "schema.sql"

def init_db():
    """
    shema.sqlを読み込み、データベースのテーブルを作成する。
    """
    conn = sqlite3.connect(DB_NAME)
    
    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema = file.read()
        
    conn.executescript(schema)
    
    conn.close()
    
    print("データベースを初期化しました。")
    
if __name__ == "__main__":
    init_db()
    
