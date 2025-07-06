from flask import request, jsonify, Blueprint
import sqlite3
import matplotlib
matplotlib.use('Agg')  # ここでバックエンドをAggに設定
from config import DB_FILE


api_index = Blueprint("api_index", __name__)
STATIC_FOLDER = "static"  # 画像を保存するフォルダ

# 📌 グラフを作成する関数（ユーザーごとの月別支出額）
@api_index.route("/api/monthly_expense_by_user", methods=["GET"])
def api_monthly_expense_by_user():
    year = request.args.get("year", type=int)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT month, user, SUM(amount)
        FROM expenses
        WHERE year = ?
        GROUP BY month, user
        ORDER BY month ASC
    """, (year,))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return jsonify([])

    # 整形：{ user: { 'months': [...], 'amounts': [...] } }
    result = {}
    months_set = set()

    for month, user, amount in data:
        if user not in result:
            result[user] = {'user': user, 'months': [], 'amounts': []}
        result[user]['months'].append(month)
        # タクミはマイナスとして扱う
        result[user]['amounts'].append(-amount if user == "タクミ" else amount)
        months_set.add(month)

    return jsonify({
        "users": list(result.values()),
        "months": sorted(months_set)
    })

# 📌 折れ線グラフを作成する関数（ユーザーごとの月別支出額）
@api_index.route("/api/monthly_lifecost_by_user", methods=["GET"])
def api_monthly_lifecost_by_user():
    year = request.args.get("year", type=int)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

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
        return jsonify({"months": [], "totals": []})

    months = [row[0] for row in data]
    totals = [row[1] for row in data]

    return jsonify({"months": months, "totals": totals})


# ラベル表示の切り替え
def autopct_format(pct):
    return f'{pct:.1f}%' if pct >= 3 else ''  # 3% 未満なら空文字