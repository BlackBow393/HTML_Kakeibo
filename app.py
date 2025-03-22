from flask import Flask, render_template, request, redirect, jsonify
import sqlite3

app = Flask(__name__)
DB_FILE = "kakeibo.db"

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
@app.route("/")
def index():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, year, month, category, amount, user FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()
    conn.close()

    return render_template("input.html", expenses=expenses)

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

    # DBにデータを保存
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (year, month, category, amount, user) VALUES (?, ?, ?, ?, ?)",
                   (year, month, category, amount, user))
    conn.commit()
    conn.close()

    return redirect("/")  # 入力後にトップページへリダイレクト

# 📌 JSON APIを作成（データ取得用）
@app.route("/get_data", methods=["GET"])
def get_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, year, month, category, amount, user FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()
    conn.close()

    return jsonify(expenses)

if __name__ == "__main__":
    app.run(debug=True)
