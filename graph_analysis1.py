from flask import request, jsonify, Blueprint
import sqlite3
import matplotlib
matplotlib.use('Agg')

api_analysis1 = Blueprint("api_analysis1", __name__)
DB_FILE = "kakeibo.db"
STATIC_FOLDER = "static"

# 📌 グラフを作成する関数（カテゴリーごとの月別支出額）
# 📌 グラフ用 API（カテゴリーごとの月別支出額）
@api_analysis1.route("/api/monthly_expense_by_category", methods=["GET"])
def api_monthly_expense_by_category():
    year = request.args.get("year", type=int)
    category = request.args.get("category")
    user = request.args.get("user")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = """
        SELECT month, category, SUM(amount)
        FROM expenses
        WHERE year = ?
    """
    params = [year]

    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)
    if user and user != 'all':
        query += " AND user = ?"
        params.append(user)

    query += " GROUP BY month, category ORDER BY month ASC"

    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    conn.close()

    # 🔁 グラフ用の形式に変換
    result = {}
    for month, cat, amt in data:
        if cat not in result:
            result[cat] = {"category": cat, "months": [], "amounts": []}
        result[cat]["months"].append(month)
        result[cat]["amounts"].append(amt)

    return jsonify(list(result.values()))

# 📌 カテゴリーごとの年間支出割合の円グラフを作成
@api_analysis1.route("/api/pie_data_by_category", methods=["GET"])
def api_pie_data_by_category():
    year = request.args.get("year", type=int)
    category = request.args.get("category")
    user = request.args.get("user")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    query = """
        SELECT category, SUM(amount)
        FROM expenses
        WHERE year = ?
    """
    params = [year]

    if category and category != 'all':
        query += " AND category = ?"
        params.append(category)
    if user and user != 'all':
        query += " AND user = ?"
        params.append(user)

    query += " GROUP BY category ORDER BY SUM(amount) DESC"

    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    conn.close()

    if not data:
        return jsonify([])

    total = sum([row[1] for row in data])
    result = [[cat, amt, round(amt / total * 100, 1)] for cat, amt in data]

    return jsonify(result)


# ラベル表示の切り替え
def autopct_format(pct):
    return f'{pct:.1f}%' if pct >= 3 else ''  # 3% 未満なら空文字