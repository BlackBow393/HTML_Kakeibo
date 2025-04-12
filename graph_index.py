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

# 📌 グラフを作成する関数（ユーザーごとの月別支出額）
def create_expense_index_graph(year):
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

    for month, user, amount in data:
        month_index = months.index(month)
        # タクミはマイナスとして扱う
        if user == "タクミ":
            amount = -amount
        user_data[user][month_index] = amount
        
    # ユーザーごとの色を設定
    user_colors = {
        'タクミ': 'steelblue',
        'ミナヨ': 'coral',
        # 他のカテゴリーに色を追加
    }

    # 積み上げ棒グラフの描画
    plt.figure(figsize=(10, 6))
    plt.axhline(0, color='black', linewidth=2.0)  # Y=0に太めの線を引く


    for category, values in user_data.items():
        color = user_colors.get(category, 'gray')
        values_array = np.array(values)
        bars = plt.bar(months, values_array, label=category, color=color)
        
        # ラベル表示
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height != 0:  # 値がある場合のみラベルを表示
                label = f"{abs(int(height)):,}円"
                # ミナヨ（正）ならバーの上、タクミ（負）ならバーの下にラベルを置く
                y_pos = height + 500 if height > 0 else height - 3000
                plt.text(bar.get_x() + bar.get_width() / 2, y_pos, label,
                        ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=11, fontweight='bold')

    plt.xlabel("月")
    plt.ylabel("支出金額")
    plt.xticks(months)  # X軸を月に設定
    plt.legend()

    # 画像を保存
    graph_path = os.path.join(STATIC_FOLDER, "expense_index_chart.png")
    plt.savefig(graph_path, bbox_inches="tight")
    plt.close()
    return "/static/expense_index_chart.png"

# 📌 折れ線グラフを作成する関数（ユーザーごとの月別支出額）
def create_lifecost_graph(year):
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

    # 月ごとのカテゴリ合計を取得
    cursor.execute("""
        SELECT month,
               CAST(SUM(CASE WHEN category IN ('食費', '外食', '生活用品') THEN amount ELSE 0 END) AS INTEGER) AS category_total
        FROM expenses 
        WHERE year = ?
        GROUP BY month
        ORDER BY month ASC
    """, (year,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return None

    # データ整形
    months = [row[0] for row in data]
    totals = [row[1] for row in data]

    # 折れ線グラフを描画
    plt.figure(figsize=(10, 6))
    plt.plot(months, totals, marker='o', linestyle='-', color='mediumseagreen', label='生活費合計')

    # ラベルを表示
    for i, total in enumerate(totals):
        plt.text(months[i], total + 2000, f"{int(total):,}円", ha="center", fontsize=11)

    plt.xlabel("月")
    plt.ylabel("支出金額")
    plt.xticks(months)
    plt.grid(True)
    plt.legend()

    # 保存
    graph_path = os.path.join(STATIC_FOLDER, "lifecost_chart.png")
    plt.savefig(graph_path, bbox_inches="tight")
    plt.close()

    return "/static/lifecost_chart.png"

# ラベル表示の切り替え
def autopct_format(pct):
    return f'{pct:.1f}%' if pct >= 3 else ''  # 3% 未満なら空文字