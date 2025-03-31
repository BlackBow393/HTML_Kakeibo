from flask import Flask, render_template, request, redirect, jsonify, session
import sqlite3
import matplotlib
matplotlib.use('Agg')  # ここでバックエンドをAggに設定
import matplotlib.pyplot as plt
import os
import numpy as np
import matplotlib.font_manager as fm  # これを追加

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
    
    # 年・月・分類ごとに、ユーザーAとユーザーBの合計金額を列で取得
    cursor.execute("""
        SELECT year, month, category,
               SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END) AS user_a_total,
               SUM(CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END) AS user_b_total
        FROM expenses
        GROUP BY year, month, category
        ORDER BY year DESC, month DESC, category
    """)
    categorized_totals = cursor.fetchall()
    
    conn.close()

    return render_template("index.html", expenses=expenses, categorized_totals=categorized_totals)

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
@app.route("/analysis", methods=["GET", "POST"])
def analysis_page():
    if request.method == "POST":
        session["selected_year"] = int(request.form.get("year", session["selected_year"]))

    selected_year = session["selected_year"]

    graph_url = create_expense_graph(selected_year)  # 棒グラフを生成
    pie_chart_url = create_pie_chart(selected_year)  # 円グラフを生成
    graph_user_url = create_expense_user_graph(selected_year)  # 棒グラフを生成
    pie_user_chart_url = create_pie_user_chart(selected_year)
    
    # データベースからユニークな年のリストを取得
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM expenses ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return render_template("analysis.html", graph_url=graph_url, pie_chart_url=pie_chart_url, graph_user_url=graph_user_url, pie_user_chart_url=pie_user_chart_url, years=years, selected_year=selected_year)


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
def create_expense_graph(year):
    # 🔹 日本語フォントの設定
    font_path = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
    if not os.path.exists(font_path):
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
        WHERE year = ?
        GROUP BY month, category
        ORDER BY month ASC
    """,(year,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None  # データがなければグラフを作成しない

    # データの整形
    months = sorted(set(row[0] for row in data))  # 月のリスト
    categories = sorted(set(row[1] for row in data))  # カテゴリーのリスト

    category_data = {cat: [0] * len(months) for cat in categories}
    total_by_month = [0] * len(months)  # 月ごとの合計額を格納

    for month, category, amount in data:
        month_index = months.index(month)
        category_data[category][month_index] = amount
        total_by_month[month_index] += amount  # 各月の合計を計算

    # カテゴリーごとの色を設定
    category_colors = {
        '食費': 'green',
        '外食': 'lightgreen',
        '生活用品': 'purple',
        '住宅費': 'steelblue',
        'お土産': 'orange',
        'コインランドリー': 'skyblue',
        'レジャー': 'pink',
        # 他のカテゴリーに色を追加
    }

    # 積み上げ棒グラフの描画
    plt.figure(figsize=(10, 6))
    bottom_values = np.zeros(len(months))  # 積み上げ用の初期値

    for category, values in category_data.items():
        color = category_colors.get(category, 'gray')  # 指定がない場合は灰色
        plt.bar(months, values, bottom=bottom_values, label=category, color=color)
        bottom_values += np.array(values)

    # 月ごとの合計金額を棒の上にラベル表示
    for i, total in enumerate(total_by_month):
        plt.text(months[i], total + 3000, f"{int(total):,}円", ha="center", fontsize=12, fontweight="bold")

    plt.xlabel("月")
    plt.ylabel("支出金額")
    plt.xticks(months)  # X軸を月に設定
    plt.legend()

    # 画像を保存
    graph_path = os.path.join(STATIC_FOLDER, "expense_chart.png")
    plt.savefig(graph_path, bbox_inches="tight")
    plt.close()
    return "/static/expense_chart.png"


# 📌 カテゴリーごとの年間支出割合の円グラフを作成
def create_pie_chart(year):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 年間のカテゴリー別支出合計を取得
    cursor.execute("""
        SELECT category, SUM(amount) 
        FROM expenses 
        WHERE year = ?
        GROUP BY category
    """,(year,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None  # データがない場合はグラフを作成しない

    categories = [row[0] for row in data]
    amounts = [row[1] for row in data]

    # 🔹 日本語フォントの設定
    font_path = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
    if not os.path.exists(font_path):
        font_candidates = fm.findSystemFonts(fontpaths=['/usr/share/fonts', '/Library/Fonts', 'C:/Windows/Fonts'])
        font_path = next((f for f in font_candidates if 'ipag' in f.lower() or 'msmincho' in f.lower()), None)

    if font_path:
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        print("⚠ 日本語フォントが見つかりません！英語のまま表示します。")

    # カテゴリーごとの色を設定
    category_colors = {
        '食費': 'green',
        '外食': 'lightgreen',
        '生活用品': 'purple',
        '住宅費': 'steelblue',
        'お土産': 'orange',
        'コインランドリー': 'skyblue',
        'レジャー': 'pink',
        # 他のカテゴリーに色を追加
    }

    # 🔹 円グラフを描画（ラベルの位置を調整）
    plt.figure(figsize=(8, 8))
    
    # 色をカテゴリーに対応させてリストに変換
    colors = [category_colors.get(category, 'gray') for category in categories]
    
    wedges, texts, autotexts = plt.pie(
        amounts, labels=None, autopct=autopct_format, startangle=90, counterclock=False,
        pctdistance=0.9,  # 数値（％）の表示位置を調整（円の中心からの距離）
        labeldistance=1.15,  # ラベルの距離を調整
        colors=colors  # カテゴリーごとに色を指定
    )

    # 🔹 ラベルのサイズを調整
    for text in texts:
        text.set_fontsize(12)  # カテゴリー名のフォントサイズ
        text.set_fontproperties(font_prop)  # 日本語フォントを適用
    for autotext in autotexts:
        autotext.set_fontsize(10)  # 割合（％）のフォントサイズ
        autotext.set_color("black")  # ％の色を変更
        autotext.set_fontweight("bold")  # 太字にする

    # 🔹 凡例を追加（ラベルの重なりを避ける）
    plt.legend(wedges, categories, loc="upper left", bbox_to_anchor=(1, 1), fontsize=10)

    # 画像を保存
    pie_chart_path = os.path.join(STATIC_FOLDER, "expense_pie_chart.png")
    plt.savefig(pie_chart_path, bbox_inches="tight")
    plt.close()
    return "/static/expense_pie_chart.png"

# 📌 グラフを作成する関数（ユーザーごとの月別支出額）
def create_expense_user_graph(year):
    # 🔹 日本語フォントの設定
    font_path = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
    if not os.path.exists(font_path):
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
        SELECT month, user, SUM(amount) 
        FROM expenses 
        WHERE year = ?
        GROUP BY month, user
        ORDER BY month ASC
    """,(year,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None  # データがなければグラフを作成しない

    # データの整形
    months = sorted(set(row[0] for row in data))  # 月のリスト
    users = sorted(set(row[1] for row in data))  # ユーザーのリスト

    user_data = {cat: [0] * len(months) for cat in users}
    total_by_month = [0] * len(months)  # 月ごとの合計額を格納

    for month, user, amount in data:
        month_index = months.index(month)
        user_data[user][month_index] = amount
        total_by_month[month_index] += amount  # 各月の合計を計算

    # ユーザーごとの色を設定
    user_colors = {
        'タクミ': 'steelblue',
        'ミナヨ': 'coral',
        # 他のカテゴリーに色を追加
    }

    # 積み上げ棒グラフの描画
    plt.figure(figsize=(10, 6))
    bottom_values = np.zeros(len(months))  # 積み上げ用の初期値

    for category, values in user_data.items():
        color = user_colors.get(category, 'gray')  # 指定がない場合は灰色
        plt.bar(months, values, bottom=bottom_values, label=category, color=color)
        bottom_values += np.array(values)

    # 月ごとの合計金額を棒の上にラベル表示
    for i, total in enumerate(total_by_month):
        plt.text(months[i], total + 3000, f"{int(total):,}円", ha="center", fontsize=12, fontweight="bold")

    plt.xlabel("月")
    plt.ylabel("支出金額")
    plt.xticks(months)  # X軸を月に設定
    plt.legend()

    # 画像を保存
    graph_path = os.path.join(STATIC_FOLDER, "expense_user_chart.png")
    plt.savefig(graph_path, bbox_inches="tight")
    plt.close()
    return "/static/expense_user_chart.png"


# 📌 カテゴリーごとの年間支出割合の円グラフを作成
def create_pie_user_chart(year):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 年間のカテゴリー別支出合計を取得
    cursor.execute("""
        SELECT user, SUM(amount) 
        FROM expenses 
        WHERE year = ?
        GROUP BY user
    """,(year,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None  # データがない場合はグラフを作成しない

    users = [row[0] for row in data]
    amounts = [row[1] for row in data]

    # 🔹 日本語フォントの設定
    font_path = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
    if not os.path.exists(font_path):
        font_candidates = fm.findSystemFonts(fontpaths=['/usr/share/fonts', '/Library/Fonts', 'C:/Windows/Fonts'])
        font_path = next((f for f in font_candidates if 'ipag' in f.lower() or 'msmincho' in f.lower()), None)

    if font_path:
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
    else:
        print("⚠ 日本語フォントが見つかりません！英語のまま表示します。")

    # ユーザーごとの色を設定
    user_colors = {
        'タクミ': 'steelblue',
        'ミナヨ': 'coral',
        # 他のカテゴリーに色を追加
    }

    # 🔹 円グラフを描画（ラベルの位置を調整）
    plt.figure(figsize=(8, 8))
    
    # 色をカテゴリーに対応させてリストに変換
    colors = [user_colors.get(category, 'gray') for category in users]
    
    wedges, texts, autotexts = plt.pie(
        amounts, labels=None, autopct=autopct_format, startangle=90, counterclock=False,
        pctdistance=0.9,  # 数値（％）の表示位置を調整（円の中心からの距離）
        labeldistance=1.15,  # ラベルの距離を調整
        colors=colors  # カテゴリーごとに色を指定
    )

    # 🔹 ラベルのサイズを調整
    for text in texts:
        text.set_fontsize(12)  # カテゴリー名のフォントサイズ
        text.set_fontproperties(font_prop)  # 日本語フォントを適用
    for autotext in autotexts:
        autotext.set_fontsize(10)  # 割合（％）のフォントサイズ
        autotext.set_color("black")  # ％の色を変更
        autotext.set_fontweight("bold")  # 太字にする

    # 🔹 凡例を追加（ラベルの重なりを避ける）
    plt.legend(wedges, users, loc="upper left", bbox_to_anchor=(1, 1), fontsize=10)

    # 画像を保存
    pie_chart_path = os.path.join(STATIC_FOLDER, "expense_user_pie_chart.png")
    plt.savefig(pie_chart_path, bbox_inches="tight")
    plt.close()
    return "/static/expense_user_pie_chart.png"

# ラベル表示の切り替え
def autopct_format(pct):
    return f'{pct:.1f}%' if pct >= 3 else ''  # 3% 未満なら空文字

if __name__ == "__main__":
    app.run(debug=True)
