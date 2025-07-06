from flask import Flask, request, redirect, jsonify, session
import sqlite3
import matplotlib
matplotlib.use('Agg')  # ここでバックエンドをAggに設定

from page import page_view

from graph_analysis1 import api_analysis1
from graph_analysis2 import api_analysis2
from graph_index import api_index

import webbrowser
from threading import Timer
import os
from config import DB_FILE,BASE_DIR

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
    )
STATIC_FOLDER = "static"  # 画像を保存するフォルダ
app.secret_key = "your_secret_key_here"

app.register_blueprint(page_view)

app.register_blueprint(api_analysis1)
app.register_blueprint(api_analysis2)
app.register_blueprint(api_index)

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
        session["selected_category"] = None  # カテゴリー初期値 すべて→None

    if "selected_user" not in session:
        session["selected_user"] = None  # ユーザー初期値 すべて→None

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

@app.route("/get_latest_date", methods=["GET"])
def get_latest_date():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT year, month 
        FROM expenses 
        ORDER BY year DESC, month DESC 
        LIMIT 1
    """)
    latest = cursor.fetchone()
    conn.close()

    if latest:
        latest_date = f"{latest[0]}年{latest[1]}月"
    else:
        latest_date = "データなし"

    return jsonify({"latest_date": latest_date})

if __name__ == "__main__":
    # 1秒後にブラウザを開く（Flaskサーバの起動と並行で）
    Timer(1, lambda: webbrowser.open_new("http://127.0.0.1:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
