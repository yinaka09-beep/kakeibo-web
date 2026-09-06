import os

import psycopg
import pytest

import app  as app_module
from app import app

test_database_url = os.environ["TEST_DATABASE_URL"]

if test_database_url == os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "TEST_DATABASE_URLとDATABASE_URLが同じです。"
    )
    
    
@pytest.fixture
def test_db(monkeypatch):
    test_database_url = os.environ["TEST_DATABASE_URL"]
    
    monkeypatch.setenv(
        "DATABASE_URL",
        test_database_url
    )
    
    with open("schema.sql", "r", encoding="utf-8") as file:
        schema = file.read()
        
    with psycopg.connect(test_database_url) as conn:
        with conn.cursor() as cursor:
            for statement in schema.split(";"):
                statement = statement.strip()
                
                if statement:
                    cursor.execute(statement)
                    
            cursor.execute("""
                TRUNCATE records, budgets
                RESTART IDENTITY
            """)
        
    yield test_database_url    
        
    with psycopg.connect(test_database_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                truncate records, budgets
                RESTART IDENTITY
            """)
            
            
@pytest.fixture
def client(test_db):
    app.config["TESTING"] = True
    return app.test_client()


def test_index(client):    
    response = client.get("/")
    
    assert response.status_code == 200
    assert "家計簿" in response.get_data(as_text=True)

    
def test_records(client):
    response = client.get("/records")
    
    assert response.status_code == 200

    
def test_budgets(client):
    response = client.get("/budgets")
    
    assert response.status_code == 200

    
def test_create_database(test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
    assert "records" in tables
    assert "budgets" in tables

    
def test_add_record_invalid_amount(client):
    response = client.post(
        "/add",
        data = {
            "date": "2026-09-02",
            "kind": "支出",
            "category": "食費",
            "amount": "",
            "memo": "テスト"
        }
    )
    
    assert response.status_code == 200
    assert "金額を入力してください" in response.get_data(as_text=True)

    
def test_add_record(client, test_db):
    response = client.post(
        "/add",
        data = {
            "date": "2026-09-02",
            "kind": "支出",
            "category": "食費",
            "amount": "1200",
            "memo": "自動テスト"
        }
    )
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT date, kind, category, amount, memo
                FROM records
                WHERE memo = %s
            """,("自動テスト",))
            
            record = cursor.fetchone()
    
    assert record is not None
    assert record[0] == "2026-09-02"
    assert record[1] == "支出"
    assert record[2] == "食費"
    assert record[3] == 1200
    assert record[4] == "自動テスト"

    
def test_edit_record(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
            INSERT INTO records (date, kind, category, amount, memo)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,(
                "2026-09-01",
                "支出",
                "食費",
                1000,
                "編集前"
            ))
    
            record_id = cursor.fetchone()[0]
        
    response = client.post(
        f"/edit/{record_id}",
        data = {
            "date": "2026-09-02",
            "kind": "支出",
            "category": "食費",
            "amount": "1500",
            "memo": "編集後"
        }
    )
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT date, kind, category, amount, memo
                FROM records
                WHERE id = %s
            """,(record_id,))
    
            record = cursor.fetchone()
    
    assert record is not None
    assert record[0] == "2026-09-02"
    assert record[1] == "支出"
    assert record[2] == "食費"
    assert record[3] == 1500
    assert record[4] == "編集後"

    
def test_delete_record(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO records (date, kind, category, amount, memo)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,(
                    "2026-09-02",
                    "支出",
                    "交通費",
                    1000,
                    "削除前"
                )    
            )

            record_id = cursor.fetchone()[0]
    
    response = client.post(f"/delete/{record_id}")
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id
                FROM records
                WHERE id = %s
            """,(record_id,))
    
            record = cursor.fetchone()
    
    assert record is None
    
    
def test_add_budget(client, test_db):
    response = client.post(
        "/add-budget",
        data = {
            "month": "2026-09",
            "category": "食費",
            "budget": "5000"
        }
    )
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT month, category, budget
                FROM budgets
                WHERE month = %s AND category = %s AND budget = %s
            """,("2026-09", "食費", 5000)
            )
    
            budget_row = cursor.fetchone()
            
    assert budget_row is not None
    assert budget_row[0] == "2026-09"
    assert budget_row[1] == "食費"
    assert budget_row[2] == 5000

    
def test_edit_budget(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO BUDGETS (month, category, budget)
                VALUES (%s, %s, %s)
                RETURNING id
                """,(
                    "2026-08",
                    "食費",
                    4000
                ))
    
            budget_id = cursor.fetchone()[0]
    
    response = client.post(
        f"/edit-budget/{budget_id}",
        data = {
            "month": "2026-09",
            "category": "食費",
            "budget": "5000"
        }
    )
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT month, category, budget
                FROM budgets
                WHERE id = %s
            """,(budget_id,))
    
            budget_row = cursor.fetchone()
    
    assert budget_row is not None
    assert budget_row[0] == "2026-09"
    assert budget_row[1] == "食費"
    assert budget_row[2] == 5000

    
def test_delete_budget(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
                RETURNING id
                """,(
                    "2026-09",
                    "交通費",
                    4000
                ))
    
            budget_id = cursor.fetchone()[0]
    
    response = client.post(
        f"/delete-budget/{budget_id}"
    )
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id
                FROM budgets
                WHERE id = %s
            """,(budget_id,))
    
            budget_row = cursor.fetchone()
    
    assert budget_row is None
    
    
def test_add_budget_updates_existing(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
                """,(
                    "2026-09",
                    "食費",
                    5000
                ))
    
    response = client.post(
        "/add-budget",
        data = {
            "month": "2026-09",
            "category": "食費",
            "budget": "8000"
        }
    )
    
    assert response.status_code == 302
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT budget
                FROM budgets
                WHERE month = %s AND category = %s
            """,("2026-09", "食費"))
    
            budget_rows = cursor.fetchall()
    
    assert len(budget_rows) == 1
    assert budget_rows[0][0] == 8000

    
def test_edit_budget_duplicate(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
            """,(
                "2026-09",
                "食費",
                5000
                ))
            
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
                RETURNING id
            """,(
                "2026-09",
                "娯楽費",
                3000
                ))
    
            budget_id = cursor.fetchone()[0]
    
    response = client.post(
        f"/edit-budget/{budget_id}",
        data = {
            "month": "2026-09",
            "category": "食費",
            "budget": "3000"
        }
    )
    
    assert response.status_code == 200
    
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
    
            cursor.execute("""
                SELECT month, category, budget
                FROM budgets
                WHERE id = %s
            """,(budget_id,))
    
            budget_row = cursor.fetchone()
       
    assert budget_row is not None
    assert budget_row[0] == "2026-09"
    assert budget_row[1] == "娯楽費"
    assert budget_row[2] == 3000

    
def test_budget_comparison_calculation(test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
                """,(
                    "2026-09",
                    "食費",
                    5000
                ))
    
            cursor.execute("""
                INSERT INTO records(date, kind, category, amount, memo)
                VALUES (%s, %s, %s, %s, %s)
                """,(
                    "2026-09-02",
                    "支出",
                    "食費",
                    3000,
                    "テスト"
                ))
    
    comparison_data = app_module.build_budget_comparison("2026-09")
    
    assert len(comparison_data) == 1
    
    comparison_row = comparison_data[0]
    
    assert comparison_row["category"] == "食費"
    assert comparison_row["budget"] == 5000
    assert comparison_row["actual"] == 3000
    assert comparison_row["balance"] == 2000
    assert comparison_row["status"] == "予算内"

    
def test_budget_comparison_page(client, test_db):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
    
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
            """,(
                "2026-09",
                "食費",
                5000
                ))
                
            cursor.execute("""
                INSERT INTO records(date, kind, category, amount, memo)
                VALUES (%s, %s, %s, %s, %s)
            """,(
                "2026-09-02",
                "支出",
                "食費",
                3000,
                "テスト"
                ))
    
    response = client.post(
        "/budget-comparison",
        data = {
            "month": "2026-09"
        }
    )
    
    assert response.status_code == 200

    
def test_budget_comparison_graph_page(
    client,
    test_db,
    tmp_path,
    monkeypatch
):
    with psycopg.connect(test_db) as conn:
        with conn.cursor() as cursor:
    
            cursor.execute("""
                INSERT INTO budgets (month, category, budget)
                VALUES (%s, %s, %s)
                """,(
                    "2026-09",
                    "食費",
                    5000
                ))
            
            cursor.execute("""
                INSERT INTO records (date, kind, category, amount, memo)
                VALUES (%s, %s, %s, %s, %s)
                """,(
                    "2026-09-02",
                    "支出",
                    "食費",
                    5000,
                    "テスト"
                ))
    
    graph_folder = tmp_path / "graphs"
    
    monkeypatch.setattr(
        app_module,
        "GRAPH_FOLDER",
        str(graph_folder)
    )
    
    response = client.post(
        "/budget-comparison-graph",
        data = {
            "month":"2026-09"
        }
    )
    
    assert response.status_code == 200
    
    graph_path = (
        graph_folder
        / app_module.BUDGET_COMPARISON_GRAPH_NAME
    )
    
    assert graph_path.exists()