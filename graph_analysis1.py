from flask import Flask
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

# 📌 グラフを作成する関数（カテゴリーごとの月別支出額）
def create_expense_graph(year, category=None, user=None):
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

    # 🔹 SQLクエリ作成（動的にフィルターを追加）
    base_query = """
        SELECT month, category, SUM(amount)
        FROM expenses
        WHERE year = ?
    """
    params = [year]

    if category:
        base_query += " AND category = ?"
        params.append(category)

    if user:
        base_query += " AND user = ?"
        params.append(user)

    base_query += """
        GROUP BY month, category
        ORDER BY month ASC
    """

    cursor.execute(base_query, tuple(params))
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
def create_pie_chart(year, category=None, user=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 🔹 SQLクエリ作成（動的にフィルターを追加）
    base_query = """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE year = ?
    """
    params = [year]

    if category:
        base_query += " AND category = ?"
        params.append(category)

    if user:
        base_query += " AND user = ?"
        params.append(user)

    base_query += """
        GROUP BY  category
        ORDER BY SUM(amount) DESC
    """

    cursor.execute(base_query, tuple(params))
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

# ラベル表示の切り替え
def autopct_format(pct):
    return f'{pct:.1f}%' if pct >= 3 else ''  # 3% 未満なら空文字