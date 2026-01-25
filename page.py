from flask import Blueprint, render_template, request, session,redirect,url_for
import sqlite3
from config import DB_FILE

page_view = Blueprint("page_view", __name__)

# 📌 ホームページ（支出入力画面）
@page_view.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["selected_year"] = int(request.form.get("year", session["selected_year"]))

    selected_year = session["selected_year"]

    graph_index_url = None
    graph_lifecost_url = None
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, year, month, category, amount, user FROM expenses ORDER BY id DESC")
    expenses = cursor.fetchall()
    
    # 年・月・分類ごとに、ユーザーAとユーザーBの合計金額を列で取得
    cursor.execute("""
        SELECT year, month, category,
            CAST(SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END) AS INTEGER) AS user_a_total,
            CAST(SUM(CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END) AS INTEGER) AS user_b_total,
            CAST(
                CASE
                
                    WHEN year <= 2025 THEN
                        (SUM( CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END ) -
                        SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END )) / 2
                        
                    WHEN year >= 2026 AND category IN ('食費','外食') THEN
                        -1 * SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END)
                    
                    ELSE
                        (SUM( CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END ) -
                        SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END )) / 2
                END
            ) AS settlement_amount
        FROM expenses
        WHERE year = ?
        GROUP BY year, month, category
        ORDER BY year ASC, month ASC, category
    """, (selected_year,))
    categorized_totals = cursor.fetchall()
    
    # 年・月・分類ごとに、ユーザーAとユーザーBの合計金額を列で取得
    cursor.execute("""
        SELECT year, month, 
            CAST(
                CASE
                    WHEN year <= 2025 THEN
                        (SUM(CASE WHEN user = 'ミナヨ' THEN amount ELSE 0 END) - 
                        SUM(CASE WHEN user = 'タクミ' THEN amount ELSE 0 END)) / 2 AS INTEGER
                        
                    ELSE
                        (SUM( CASE WHEN user = 'ミナヨ' AND category IN ('生活用品','コインランドリー','レジャー') THEN amount ELSE 0 END ) -
                        SUM(CASE WHEN user = 'タクミ' AND category IN ('食費','外食','生活用品','コインランドリー','レジャー') THEN amount ELSE 0 END)) / 2 AS INTEGER
            ) AS settlement_amount
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

    return render_template(
        "index.html", 
        expenses=expenses, 
        categorized_totals=categorized_totals,
        calcurate_totals=calcurate_totals, 
        graph_index_url=graph_index_url, 
        graph_lifecost_url=graph_lifecost_url, 
        years=years, 
        selected_year=selected_year
    )

# 📌 支出入力ページ
@page_view.route("/input")
def input_page():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, year, month, category, amount, user 
        FROM expenses 
        ORDER BY year ASC, month ASC
        """)
    expenses = cursor.fetchall()
    
    # カテゴリーマスタの取得
    cursor.execute("SELECT category FROM category_master ORDER BY id ASC")
    categories = [row[0] for row in cursor.fetchall()]
    
    # ユーザーマスタの取得
    cursor.execute("SELECT user FROM user_master ORDER BY id ASC")
    users = [row[0] for row in cursor.fetchall()]
    
    conn.close()

    return render_template("input.html", expenses=expenses, categories=categories, users=users)

# 📌 支出分析ページ
@page_view.route("/analysis", methods=["GET", "POST"])
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
    selected_category = session.get("selected_category", None)  # all→None
    selected_user = session.get("selected_user", None)  # all→None

    # 🔄 Plotly表示用：画像URLは不要なので None にする
    graph_url = None
    pie_chart_url = None
    graph_user_url = None
    pie_user_chart_url = None

    # データベースからユニークな年のリストを取得
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT year FROM expenses ORDER BY year DESC")
    years = [row[0] for row in cursor.fetchall()]
    
    # 🔹 カテゴリー一覧を category_master テーブルから取得
    cursor.execute("SELECT category FROM category_master ORDER BY id ASC")
    categories = [row[0] for row in cursor.fetchall()]
    
    # 🔹 ユーザー一覧を user_master テーブルから取得
    cursor.execute("SELECT user FROM user_master ORDER BY id ASC")
    users = [row[0] for row in cursor.fetchall()]
    
    conn.close()

    return render_template(
        "analysis.html",
        graph_url=graph_url,
        pie_chart_url=pie_chart_url,
        graph_user_url=graph_user_url,
        pie_user_chart_url=pie_user_chart_url,
        years=years,
        categories=categories,
        users=users,
        selected_year=selected_year,
        selected_category=selected_category,
        selected_user=selected_user
    )

# 📌 マスタ編集ページ
@page_view.route("/setting", methods=["GET", "POST"])
def settings_page():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        user = request.form.get("user", "").strip()
        if "form_add" in request.form:
            if category:
                cursor.execute("INSERT INTO category_master (category) VALUES (?)", (category,))
            if user:
                cursor.execute("INSERT INTO user_master (user) VALUES (?)", (user,))
        elif "form_delete" in request.form:
            if category:
                cursor.execute("DELETE FROM category_master WHERE category = ?", (category,))
            if user:
                cursor.execute("DELETE FROM user_master WHERE user = ?", (user,))
        conn.commit()
        conn.close()
        # 🔁 POST処理後にリダイレクトして再送信防止
        return redirect(url_for("page_view.settings_page"))

    cursor.execute("SELECT id , category FROM category_master ORDER BY id ASC")
    category_master = cursor.fetchall()
    
    cursor.execute("SELECT id , user FROM user_master ORDER BY id ASC")
    user_master = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        "settings.html",
        category_master=category_master,
        user_master=user_master
    )