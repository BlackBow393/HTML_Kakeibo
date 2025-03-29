from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.font_manager as fm

app = Flask(__name__)
DB_FILE = "kakeibo.db"
STATIC_FOLDER = "static"  # 画像を保存するフォルダ

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

    return render_template("index.html", expenses=expenses)

# 📌 支出入力ページ
@app.route("/input")
def input_page():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, year, month, category, amount, user FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()
    conn.close()

    return render_template("input.html", expenses=expenses)

# 📌 支出分析ページ
@app.route("/analysis")
def analysis_page():
    graph_url = create_expense_graph()  # グラフ画像を生成
    return render_template("analysis.html", graph_url=graph_url)

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
    cursor.execute("SELECT id, year, month, category, amount, user FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()
    conn.close()

    return jsonify(expenses)

# 📌 グラフを作成する関数（カテゴリーごとの月別支出額）
def create_expense_graph():
    
    # 🔹 日本語フォントを設定（システム内のフォントを自動検索）
    font_path = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"  # Linuxの場合
    if not os.path.exists(font_path):  # フォントがない場合は検索
        font_candidates = fm.findSystemFonts(fontpaths=['/usr/share/fonts', '/Library/Fonts', 'C:/Windows/Fonts'])
        font_path = next((f for f in font_candidates if 'ipag' in f.lower() or 'msmincho' in f.lower()), None)

    if font_path:
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        print("⚠ 日本語フォントが見つかりません！英語のまま表示します。")
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 各月ごとのカテゴリー別支出額を取得
    cursor.execute("""
        SELECT month, category, SUM(amount) 
        FROM expenses 
        GROUP BY month, category
        ORDER BY month ASC
    """)
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None  # データがなければグラフを作成しない

    # データの整形
    months = sorted(set(row[0] for row in data))  # 月のリスト
    categories = sorted(set(row[1] for row in data))  # カテゴリーのリスト

    category_data = {cat: [0] * len(months) for cat in categories}

    for month, category, amount in data:
        month_index = months.index(month)
        category_data[category][month_index] = amount

    # 積み上げ棒グラフの描画
    plt.figure(figsize=(10, 6))
    bottom_values = np.zeros(len(months))  # 積み上げ用の初期値

    for category, values in category_data.items():
        plt.bar(months, values, bottom=bottom_values, label=category)
        bottom_values += np.array(values)
    
    plt.xlabel("月")
    plt.ylabel("支出金額")
    plt.title("月ごとのカテゴリー別支出")
    plt.xticks(months)  # X軸を月に設定
    plt.legend()

    # 画像を保存
    graph_path = os.path.join(STATIC_FOLDER, "expense_chart.png")
    plt.savefig(graph_path, bbox_inches="tight")
    plt.close()
    return "/static/expense_chart.png"

if __name__ == "__main__":
    app.run(debug=True)
