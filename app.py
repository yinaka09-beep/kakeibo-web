import psycopg
from datetime import datetime
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for

plt.rcParams["font.family"] = "Meiryo"
plt.rcParams["axes.unicode_minus"] = False

GRAPH_FOLDER = os.path.join("static", "graphs")
CATEGORY_GRAPH_NAME = "category_summary.png"
MONTH_SUMMARY_GRAPH_NAME = "month_summary.png"
BUDGET_COMPARISON_GRAPH_NAME = "budget_comparison.png"

app = Flask(__name__)


def connect_db():
    """
    PostgreSQLデータベースに接続する。
    """
    database_url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(database_url)
    return conn


def get_records():
    """
    家計簿データの一覧を取得する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, kind, category, amount, memo
        FROM records
        ORDER BY date DESC, id DESC
    """)
    
    record_rows = cursor.fetchall()

    conn.close()
    
    return record_rows
    
    
def get_record_by_id(record_id):
    """
    指定されたIDの家計簿データを1件取得する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, kind, category, amount, memo
        FROM records
        WHERE id = %s
    """, (record_id,))
    
    record = cursor.fetchone()
    
    conn.close()
    
    return record


def insert_record(date, kind, category, amount, memo):
    """
    家計簿データを1件追加する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO records (date, kind, category, amount, memo)
        VALUES (%s, %s, %s, %s, %s)
    """, (date, kind, category, amount, memo))
    
    conn.commit()
    conn.close()
    

def update_record(record_id, date, kind, category, amount, memo):
    """
    指定されたIDの家計簿データを更新する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE records
        SET date = %s, kind = %s, category = %s, amount = %s, memo = %s
        WHERE id = %s
    """, (date, kind, category, amount, memo, record_id))
    
    conn.commit()
    conn.close()
 
   
def delete_record_by_id(record_id):
    """
    指定されたIDの家計簿データを1件削除する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM records
        WHERE id = %s
    """, (record_id,))
    
    conn.commit()
    conn.close()


def get_budgets():
    """
    予算データの一覧を取得する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, month, category, budget
        FROM budgets
        ORDER BY month DESC, category
    """)
    
    budget_rows = cursor.fetchall()
    
    conn.close()
    
    return budget_rows
    
    
def get_budget_by_id(budget_id):
    """
    指定されたIDの予算データを1件取得する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, month, category, budget
        FROM budgets
        WHERE id = %s
    """, (budget_id,))
    
    budget_row = cursor.fetchone()
    
    conn.close()
    
    return budget_row


def get_existing_budget(month, category, exclude_id=None):
    """
    同じ年月・カテゴリの予算データを取得する。
    編集時は指定されたIDを検索対象から除外する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    if exclude_id is None:
        cursor.execute("""
            SELECT id, month, category, budget
            FROM budgets
            WHERE month = %s AND category = %s
        """, (month, category))
    
    else:
        cursor.execute("""
            SELECT id, month, category, budget
            FROM budgets
            WHERE month = %s AND category = %s AND id != %s
        """, (month, category, exclude_id))
    
    existing_budget = cursor.fetchone()
    
    conn.close()
    
    return existing_budget


def insert_budget(month, category, budget):
    """
    予算データを1件追加する。
    """
    conn = connect_db()
    cursor = conn.cursor() 
    
    cursor.execute("""
        INSERT INTO budgets (month, category, budget)
        VALUES (%s, %s, %s)
    """, (month, category, budget))
    
    conn.commit()
    conn.close()


def update_budget_amount(month, category, budget):
    """
    指定された年月・カテゴリの予算金額を更新する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE budgets
        SET budget = %s
        WHERE month = %s AND category = %s
    """, (budget, month, category))
    
    conn.commit()
    conn.close()
    
    
def update_budget_by_id(budget_id, month, category, budget):
    """
    指定されたIDの予算データを更新する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE budgets
        SET month = %s, category = %s, budget = %s
        WHERE id = %s
    """, (month, category, budget, budget_id))
    
    conn.commit()
    conn.close()
    
    
def delete_budget_by_id(budget_id):
    """
    指定されたIDの予算データを1件削除する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM budgets
        WHERE id = %s
    """, (budget_id,))
    
    conn.commit()
    conn.close()


def get_month_summary(month):
    """
    指定された月の収入、支出、収支とデータの有無を取得する。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            SUM(CASE WHEN kind = '収入' THEN amount ELSE 0 END),
            SUM(CASE WHEN kind = '支出' THEN amount ELSE 0 END),
            COUNT(*)
        FROM records
        WHERE date LIKE %s
    """, (month + "-%",))
    
    result = cursor.fetchone()
    
    conn.close()
    
    income = result[0] or 0
    expense = result[1] or 0
    data_exists = result[2] > 0
    
    balance = income - expense
        
    return income, expense, balance, data_exists
 

def get_category_month(month):
    """
    指定された月のカテゴリ別支出合計を辞書で返す。
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT category, SUM(amount)
        FROM records
        WHERE date LIKE %s AND kind = %s
        GROUP BY category
        ORDER BY category
    """, (month + "-%", "支出"))
    
    category_actual_rows = cursor.fetchall()
    
    conn.close()
    
    category_totals = {}
    
    for category, total in category_actual_rows:
        category_totals[category] = total
        
    return category_totals
        
        
def get_budget_category_month(month):
    """
    指定された月のカテゴリ別予算を辞書で返す。
    """
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, budget
        FROM budgets
        WHERE month = %s
        ORDER BY category
    """, (month,))
    
    budget_rows = cursor.fetchall()
    
    conn.close()
        
    return dict(budget_rows)


def build_budget_comparison(month):
    """
    指定された月のカテゴリ・予算・支出・予算残額・達成状況を
    カテゴリ別にまとめる。
    """
    category_budget = get_budget_category_month(month)   
    category_totals = get_category_month(month)
    
    categories = set(category_budget.keys()) | set(category_totals.keys())
    
    comparison_data = []
    
    for category in sorted(categories):
        budget = category_budget.get(category)
        
        # 支出データがなければ0円として扱う。
        actual = category_totals.get(category, 0)
        
        if budget is None:
            balance = None
            status = "予算未設定"
            
        else:
            balance = budget - actual
            
            if balance >= 0:
                status = "予算内"
                
            else:
                status = "予算超過"
                
        comparison_data.append({
            "category": category,
            "budget": budget,
            "actual": actual,
            "balance": balance,
            "status": status
        })
                        
    return comparison_data

        
def create_month_summary_graph(month_summary_row, month):
    """
    指定された月の収入、支出、収支グラフを作成して、保存する。
    """
    income, expense, balance, _ = month_summary_row
    
    labels = ["収入", "支出", "差額"]
    values = [income, expense, balance]
    
    os.makedirs(GRAPH_FOLDER, exist_ok=True)
    
    graph_path = os.path.join(
        GRAPH_FOLDER,
        MONTH_SUMMARY_GRAPH_NAME
    )
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.bar(labels, values)
    
    ax.set_title(f"{month}の収支グラフ")
    ax.set_xlabel("項目")
    ax.set_ylabel("金額(円)")
    
    fig.tight_layout()
    fig.savefig(graph_path)
    
    plt.close(fig)
    
    return MONTH_SUMMARY_GRAPH_NAME


def create_category_summary_graph(category_totals, month):
    """
    指定された月のカテゴリ別支出グラフを作成して、保存する。
    """
    categories = list(category_totals.keys())
    totals = list(category_totals.values())
    
    os.makedirs(GRAPH_FOLDER, exist_ok=True)
    
    graph_path = os.path.join(
        GRAPH_FOLDER,
        CATEGORY_GRAPH_NAME
    )
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.bar(categories, totals)

    ax.set_title(f"{month}のカテゴリ別支出グラフ")
    ax.set_xlabel("カテゴリ")
    ax.set_ylabel("金額(円)")
    ax.tick_params(axis="x", labelrotation=45)
    
    fig.tight_layout()
    fig.savefig(graph_path)
    
    plt.close(fig)
    
    return CATEGORY_GRAPH_NAME

    
def create_budget_comparison_graph(comparison_data, month):
    """
    指定された月の予算と支出の比較グラフを作成して、保存する。
    """
    categories = []
    budget_values = []
    actual_values = []
    
    for row in comparison_data:
        categories.append(row["category"])
        
        if row["budget"] is None:
            budget_values.append(0)
        else:
            budget_values.append(row["budget"])
                
        actual_values.append(row["actual"])
        
           
    os.makedirs(GRAPH_FOLDER, exist_ok=True)
    
    graph_path = os.path.join(
        GRAPH_FOLDER,
        BUDGET_COMPARISON_GRAPH_NAME
    )
    
    x_positions = range(len(categories))
    
    bar_width = 0.35
    bar_gap = 0.05
    offset = (bar_width + bar_gap) / 2
    
    budget_values_positions = [
        x - offset for x in x_positions
        ]
    actual_values_positions = [
        x + offset for x in x_positions
        ]
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    ax.bar(
        budget_values_positions,
        budget_values,
        width=bar_width,
        label="予算"
    )
    
    ax.bar(
        actual_values_positions,
        actual_values,
        width=bar_width,
        label="支出"
    )
    
    ax.set_title(f"{month}の予算比較グラフ")
    ax.set_xlabel("カテゴリ")
    ax.set_ylabel("金額(円)")
    
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        categories,
        rotation=45,
        ha="right"
    )
    
    ax.legend()
    
    fig.tight_layout()
    fig.savefig(graph_path)
    
    plt.close(fig)
    
    return BUDGET_COMPARISON_GRAPH_NAME
           
    
def validate_record_form(date, kind, category, amount):
    """
    家計簿フォームの入力値を検証し、
    エラーメッセージのリストを返す。
    """
    errors = []
    
    if not date:
        errors.append("日付を入力してください。")
    
    else:    
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append("日付の形式が正しくありません。")
            
    if kind not in ["収入", "支出"]:
        errors.append("種類は収入か支出を選択してください。")
        
    if not category:
        errors.append("カテゴリを入力してください。")
        
    if not amount:
        errors.append("金額を入力してください。")
        
    else:
        try:
            amount_int = int(amount)
            
            if amount_int <= 0:
                errors.append("金額は1円以上を入力してください。")
        except ValueError:
            errors.append("金額は数字を入力してください。")
            
    return errors


def validate_budget_form(month, category, budget):
    """
    予算フォームの入力値を検証し、
    エラーメッセージのリストを返す。
    """
    errors = []
    
    if month == "":
        errors.append("年月を入力してください。")
    
    else:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            errors.append("年月の形式がただしくありません。")
            
    if category == "":
        errors.append("カテゴリを入力してください。")
        
    if budget == "":
        errors.append("予算を入力してください。")
        
    else:
        try:
            budget_int = int(budget)
            
            if budget_int <= 0:
                errors.append("予算は１円以上の数字を入力してください。")
                
        except ValueError:
            errors.append("予算には数字を入力してください。")
            
    return errors
    
    
def validate_month(month):
    """
    入力された年月を検証し、
    エラーメッセージのリストを返す。
    """
    errors = []
    if not month:
        errors.append("年月を入力してください。")
        
    else:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            errors.append("年月はYYYY-MMで入力してください。")
            
    return errors
    
    
def get_month_search_request():
    """
    リクエストから年月を取得し、
    検索が要求されたかどうかとともに返す。
    """
    if request.method == "POST":
        month = request.form.get("month", "").strip()
        search_requested = True
        
    else:
        month = request.args.get("month", "").strip()
        search_requested = bool(month)
        
    return month, search_requested
    
    
def get_graph_version(graph_filename):
    """
    グラフ画像の更新時刻を、
    ブラウザのキャッシュ対策用の値として返す。
    """
    graph_path = os.path.join(
        GRAPH_FOLDER,
        graph_filename
    )
    
    return os.stat(graph_path).st_mtime_ns


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/records")
def records():
    record_rows = get_records()
    return render_template("records.html", records=record_rows)


@app.route("/add", methods=["GET", "POST"])
def add_record():
    if request.method == "POST":
        date = request.form.get("date", "").strip()
        kind = request.form.get("kind", "").strip()
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()
        memo = request.form.get("memo", "").strip()
        
        errors = validate_record_form(date, kind, category, amount)
        
        if errors:
            return render_template(
                "add_record.html",
                errors=errors,
                date=date,
                kind=kind,
                category=category,
                amount=amount,
                memo=memo
            )
        
        insert_record(date, kind, category, int(amount), memo)
        
        return redirect(url_for('records'))
    
    return render_template(
        "add_record.html",
        errors=[],
        date="",
        kind="支出",
        category="",
        amount="",
        memo=""
        )
        
        
@app.route("/edit/<int:record_id>", methods=["GET", "POST"])
def edit_record(record_id):
    record = get_record_by_id(record_id)
    
    if record is None:
        return "指定された家計簿データは存在しません。", 404
    
    if request.method == "POST":
        date = request.form.get("date", "").strip()
        kind = request.form.get("kind", "").strip()
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()
        memo = request.form.get("memo", "").strip()
        
        errors = validate_record_form(date, kind, category, amount)
        
        if errors:
            return render_template(
                "edit_record.html",
                errors=errors,
                record_id=record_id,
                date=date,
                kind=kind,
                category=category,
                amount=amount,
                memo=memo
            )
            
        update_record(record_id, date, kind, category, int(amount), memo)
        
        return redirect(url_for("records"))
        
    return render_template(
        "edit_record.html",
        errors=[],
        record_id=record[0],
        date=record[1],
        kind=record[2],
        category=record[3],
        amount=record[4],
        memo=record[5]
    )
        
        
@app.route("/delete/<int:record_id>", methods=["GET", "POST"])
def delete_record(record_id):
    record = get_record_by_id(record_id)
    
    if record is None:
        return "指定された家計簿データが見つかりません。", 404
    
    if request.method == "POST":
        delete_record_by_id(record_id)
        return redirect(url_for("records"))

    return render_template("delete_record.html", record=record)


@app.route("/budgets")
def budgets():
    budget_rows = get_budgets()
    return render_template("budgets.html", budgets=budget_rows)


@app.route("/add-budget", methods=["GET", "POST"])
def add_budget():
    month = ""
    category = ""
    budget = ""
    errors = []
    
    if request.method == "POST":
        month = request.form["month"].strip()
        category = request.form["category"].strip()
        budget = request.form["budget"].strip()
        
        errors = validate_budget_form(month, category, budget)
        
        if errors:
            return render_template(
                "add_budget.html",
                month=month,
                category=category,
                budget=budget,
                errors=errors
            )
            
        existing_budget = get_existing_budget(month, category)
        
        if existing_budget is None:
            insert_budget(month, category, int(budget))
        
        else:
            update_budget_amount(month, category, int(budget))
        
        return redirect(url_for("budgets"))
        
    return render_template(
        "add_budget.html",
        month=month,
        category=category,
        budget=budget,
        errors=errors,
    )


@app.route("/edit-budget/<int:budget_id>", methods=["GET", "POST"])
def edit_budget(budget_id):
    budget_row = get_budget_by_id(budget_id)
    
    if budget_row is None:
        return "指定されたidの予算データはありません。", 404
    
    if request.method == "POST":
        new_month = request.form.get("month", "").strip()
        new_category = request.form.get("category", "").strip()
        new_budget = request.form.get("budget", "").strip()
    
        errors = validate_budget_form(new_month, new_category, new_budget)

        if not errors:
            existing_budget = get_existing_budget(new_month, new_category, budget_id)
            
            if existing_budget is not None:
                errors.append("同じ年月、同じカテゴリのデータがすでに登録されています。")    
        
        if errors:
            return render_template(
                "edit_budget.html",
                budget_id=budget_id,
                month=new_month,
                category=new_category,
                budget=new_budget,
                errors=errors
            )
        
        update_budget_by_id(budget_id, new_month, new_category, int(new_budget))
        return redirect(url_for("budgets"))
    
    return render_template(
        "edit_budget.html",
        budget_id=budget_row[0],
        month=budget_row[1],
        category=budget_row[2],
        budget=budget_row[3],
        errors=[] 
    )
    
    
@app.route("/delete-budget/<int:budget_id>", methods=["GET", "POST"])
def delete_budget(budget_id):
    budget_row = get_budget_by_id(budget_id)
    
    if budget_row is None:
        return "指定されたidの予算データはまだありません。 ", 404
    
    if request.method == "POST":
        delete_budget_by_id(budget_id)
        return redirect(url_for('budgets'))

    return render_template(
        "delete_budget.html",
        budget_id=budget_row[0],
        month=budget_row[1],
        category=budget_row[2],
        budget=budget_row[3]
    )    
        

@app.route("/month-summary", methods=["GET", "POST"])
def month_summary():
    errors = []
    income = 0
    expense = 0
    balance = 0
    data_exists = None
    
    month, search_requested = get_month_search_request()
        
    if search_requested:
        errors = validate_month(month)
        
        if not errors:
            income, expense, balance, data_exists = get_month_summary(month)
            
    return render_template(
        "month_summary.html",
        month=month,
        errors=errors,
        income=income,
        expense=expense,
        balance=balance,
        data_exists=data_exists,
    )


@app.route("/month-summary-graph", methods=["GET", "POST"])
def month_summary_graph():
    errors = []
    graph_filename = None
    graph_version = None
    data_exists = None
    
    month, search_requested = get_month_search_request()
        
    if search_requested:
        errors = validate_month(month)
        
        if not errors:
            month_summary_row = get_month_summary(month)
            _, _, _, data_exists = month_summary_row
            
            if data_exists:
                graph_filename = create_month_summary_graph(
                    month_summary_row,
                    month
                    )
                
                graph_version = get_graph_version(graph_filename)
                                
    return render_template(
        "month_summary_graph.html",
        month=month,
        errors=errors,
        graph_filename=graph_filename,
        graph_version=graph_version,
        data_exists=data_exists
    )


@app.route("/category-summary", methods=["GET", "POST"])
def category_summary():
    errors = []
    category_totals = None
    
    month, search_requested = get_month_search_request()
        
    if search_requested:
        errors = validate_month(month)
        
        if not errors:
            category_totals = get_category_month(month)
            
    return render_template(
        "category_summary.html",
        month=month,
        errors=errors,
        category_totals=category_totals
    )
        
        
@app.route("/category-summary-graph", methods=["GET", "POST"])
def category_summary_graph():
    errors = []
    graph_filename = None
    graph_version = None
    data_exists = None
    
    month, search_requested = get_month_search_request()
        
    if search_requested:
        errors = validate_month(month)
        
        if not errors:
            category_totals = get_category_month(month)
            
            if category_totals:
                graph_filename = create_category_summary_graph(
                    category_totals,
                    month
                )
                
                graph_version = get_graph_version(graph_filename)
                
                data_exists = True

            else:
                data_exists = False
    
    return render_template(
        "category_summary_graph.html",
        graph_filename=graph_filename,
        graph_version=graph_version,
        month=month,
        errors=errors,
        data_exists=data_exists
    )

    
@app.route("/budget-comparison", methods=["GET", "POST"])
def budget_comparison():
    errors = []
    comparison_data = None
    
    month, search_requested = get_month_search_request()
    
    if search_requested:
        errors = validate_month(month)
        
        if not errors:
            comparison_data = build_budget_comparison(month)
                
    return render_template(
        "budget_comparison.html",
        month=month,
        errors=errors,
        comparison_data=comparison_data
    )
            

@app.route("/budget-comparison-graph", methods=["GET", "POST"])
def budget_comparison_graph():
    errors = []
    graph_filename = None
    graph_version = None
    data_exists = None
        
    month, search_requested = get_month_search_request() 

    if search_requested:
        errors = validate_month(month)
        
        if not errors:
            comparison_data = build_budget_comparison(month)
            data_exists = bool(comparison_data)
            
            if data_exists:
                graph_filename = create_budget_comparison_graph(
                    comparison_data,
                    month)
                
                graph_version = get_graph_version(graph_filename)
                
    return render_template(
        "budget_comparison_graph.html",
        month=month,
        errors=errors,
        graph_filename=graph_filename,
        graph_version=graph_version,
        data_exists=data_exists
        )
                

if __name__ == "__main__":
    app.run(debug=True)

