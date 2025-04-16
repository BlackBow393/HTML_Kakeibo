from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
import matplotlib
matplotlib.use('Agg')  # ここでバックエンドをAggに設定
from graph_analysis1 import create_expense_graph , create_pie_chart
from graph_analysis2 import create_expense_user_graph , create_pie_user_chart
from graph_index import create_expense_index_graph , create_lifecost_graph

app = Flask(__name__)
DB_FILE = "kakeibo.db"
STATIC_FOLDER = "static"  # 画像を保存するフォルダ
app.secret_key = "your_secret_key_here"

def get_latest_year():
    """データベースからyear列の最大値を取得"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(year) FROM expenses")  # 最大のyearを取得
    latest_year = cursor.fetchone()[0]  # 結果を取得
    conn.close()
    return latest_year if latest_year else 2024  # データがない場合はデフォルト2024

@app.before_request
def set_default_year():
    """アプリ起動後に一度だけ実行し、初回アクセス時に最大yearを設定"""
    if "selected_year" not in session:
        session["selected_year"] = get_latest_year()  # 初期値をセット

    if "selected_category" not in session:
        session["selected_category"] = "すべて"  # カテゴリー初期値

    if "selected_user" not in session:
        session["selected_user"] = "すべて"  # ユーザー初期値

# 📌 データベースの初期化（テーブル作成）
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            category TEXT,
            amount INTEGER,
            user TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()  # アプリ起動時にDBを確認

# 📌 ホームページ（支出入力画面）
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["selected_year"] = int(request.form.get("year", session["selected_year"]))

    selected_year = session["selected_year"]

    graph_index_url = create_expense_index_graph(selected_year)
    graph_lifecost_url = create_lifecost_graph(selected_year)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, year, month, category, amount, user FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()
    
    # 年・月・分類ごとに、ユーザーAとユーザーBの合計金額を列で取得
    cursor.execute("""
        SELECT year, month, category,
           CAST(SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END) AS INTEGER) AS user_a_total,
           CAST(SUM(CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END) AS INTEGER) AS user_b_total,
            CAST((SUM(CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END) - 
                    SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END)) / 2 AS INTEGER) AS settlement_amount
        FROM expenses
        WHERE year = ?
        GROUP BY year, month, category
        ORDER BY year ASC, month ASC, category
    """, (selected_year,))
    categorized_totals = cursor.fetchall()
    
    # 年・月・分類ごとに、ユーザーAとユーザーBの合計金額を列で取得
    cursor.execute("""
        SELECT year, month, 
            CAST((SUM(CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END) - 
                    SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END)) / 2 AS INTEGER) AS settlement_amount
        FROM expenses
        WHERE year = ?
        GROUP BY year, month
        ORDER BY year ASC, month ASC
    """, (selected_year,))
    calcurate_totals = cursor.fetchall()
    
    # データベースからユニークな年のリストを取得
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM expenses ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template("index.html", expenses=expenses, categorized_totals=categorized_totals,calcurate_totals=calcurate_totals, graph_index_url=graph_index_url, graph_lifecost_url=graph_lifecost_url, years=years, selected_year=selected_year)

# 📌 支出入力ページ
@app.route("/input")
def input_page():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, year, month, category, amount, user 
        FROM expenses 
        ORDER BY year ASC, month ASC
        """)
    expenses = cursor.fetchall()
    conn.close()

    return render_template("input.html", expenses=expenses)

# 📌 支出分析ページ
@app.route("/analysis", methods=["GET", "POST"])
def analysis_page():
    if request.method == "POST":
        session["selected_year"] = int(request.form.get("year", session["selected_year"]))

        category = request.form.get("category", session["selected_category"])
        user = request.form.get("user", session["selected_user"])

        # 「すべて」のときは None に変換（→ SQL で絞り込みしない）
        session["selected_category"] = None if category == "all" else category
        session["selected_user"] = None if user == "all" else user

    # セッションから値を取得（初回アクセスにも備えてデフォルト値を設定）
    selected_year = session.get("selected_year", session["selected_year"])
    selected_category = session.get("selected_category", None) #all→None
    selected_user = session.get("selected_user", None) #all→None

    graph_url = create_expense_graph(selected_year, selected_category, selected_user)  # 棒グラフを生成
    pie_chart_url = create_pie_chart(selected_year, selected_category, selected_user)  # 円グラフを生成
    graph_user_url = create_expense_user_graph(selected_year, selected_category, selected_user)  # 棒グラフを生成
    pie_user_chart_url = create_pie_user_chart(selected_year, selected_category, selected_user)
    
    # データベースからユニークな年のリストを取得
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM expenses ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return render_template(
        "analysis.html",
        graph_url=graph_url,
        pie_chart_url=pie_chart_url,
        graph_user_url=graph_user_url,
        pie_user_chart_url=pie_user_chart_url,
        years=years,
        selected_year=selected_year,
        selected_category=selected_category,
        selected_user=selected_user
    )


# 📌 データを登録するAPI
@app.route("/submit", methods=["POST"])
def submit():
    year = request.form.get("year")
    month = request.form.get("month")
    category = request.form.get("category")
    amount = request.form.get("amount")
    user = request.form.get("user")

    # バリデーション（空欄チェック）
    if not (year and month and category and amount and user):
        return jsonify({"error": "入力項目が不足しています！"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 既存データを確認
    cursor.execute("""
        SELECT id FROM expenses 
        WHERE year = ? AND month = ? AND category = ? AND user = ?
    """, (year, month, category, user))
    
    existing_data = cursor.fetchone()

    if existing_data:
        # 既存データがあれば上書き更新
        cursor.execute("""
            UPDATE expenses 
            SET amount = ? 
            WHERE year = ? AND month = ? AND category = ? AND user = ?
        """, (amount, year, month, category, user))
    else:
        # データがなければ新規登録
        cursor.execute("""
            INSERT INTO expenses (year, month, category, amount, user) 
            VALUES (?, ?, ?, ?, ?)
        """, (year, month, category, amount, user))

    conn.commit()
    conn.close()

    return redirect("/input")  # 入力後にリダイレクト


# 📌 データを削除するAPI
@app.route("/delete", methods=["POST"])
def delete():
    data = request.json
    year = data.get("year")
    month = data.get("month")
    category = data.get("category")
    user = data.get("user")

    # 入力データのバリデーション
    if not (year and month and category and user):
        return jsonify({"error": "削除に必要な情報が不足しています！"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE year = ? AND month = ? AND category = ? AND user = ?",
                   (year, month, category, user))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# 📌 JSON APIを作成（データ取得用）
@app.route("/get_data", methods=["GET"])
def get_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, year, month, category, amount, user 
        FROM expenses
        ORDER BY year ASC, month ASC
        """)
    expenses = cursor.fetchall()
    conn.close()

    return jsonify(expenses)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
