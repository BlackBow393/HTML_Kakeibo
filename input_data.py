import sqlite3

# 🔥 データベースに接続
conn = sqlite3.connect("kakeibo.db")
cursor = conn.cursor()

# 🔥 挿入するデータ
data = (2025, 3, "食費", 5000, "タクミ")

# 🔥 データを挿入
cursor.execute("""
INSERT INTO expenses (year, month, category, amount, user)
VALUES (?, ?, ?, ?, ?)
""", data)

# 🔥 変更を保存して接続を閉じる
conn.commit()
conn.close()

print("✅ データ登録完了！")
