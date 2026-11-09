"""第 3 课：SQLite 数据库基础（Python 自带，零配置）。

你要掌握的 4 个动作：
- 增：INSERT
- 删：DELETE
- 改：UPDATE
- 查：SELECT

外加两个重要概念：
- 主键 PRIMARY KEY：每一行的唯一身份证，不允许重复
- 索引 INDEX：像书的目录，查得更快

运行：python scripts/03_sqlite_basics.py
"""

from __future__ import annotations

import sqlite3

from common import PROCESSED_DIR, print_step, print_title

DB_PATH = PROCESSED_DIR / "practice.db"


def create_table(conn: sqlite3.Connection) -> None:
    print_step("1. 建表：CREATE TABLE（id 是主键）")

    sql = """
    CREATE TABLE IF NOT EXISTS weather_notes (
        id      INTEGER PRIMARY KEY,   -- 唯一身份证，不能重复
        city    TEXT    NOT NULL,
        date    TEXT    NOT NULL,
        temp    REAL,
        note    TEXT
    )
    """
    conn.execute(sql)
    conn.commit()
    print("表 weather_notes 已创建。")
    print("字段：id（主键）, city, date, temp, note")


def insert_rows(conn: sqlite3.Connection) -> None:
    print_step("2. 增：INSERT 插入数据")

    rows = [
        (1, "Nanjing", "2026-10-01", 28.0, "sunny"),
        (2, "Nanjing", "2026-10-02", 31.5, "hot"),
        (3, "Beijing", "2026-10-01", 22.0, "cloudy"),
        (4, "Shanghai", "2026-10-03", 26.0, "rainy"),
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO weather_notes (id, city, date, temp, note) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    print(f"插入了 {len(rows)} 行。注意 SQL 里的 ? 是占位符，防止拼字符串出错。")


def select_rows(conn: sqlite3.Connection) -> None:
    print_step("3. 查：SELECT 查询数据")

    print("查询全部（按 id 排序）：")
    for row in conn.execute("SELECT id, city, date, temp, note FROM weather_notes ORDER BY id"):
        print("  ", row)

    print("\n只查南京的记录：")
    for row in conn.execute("SELECT * FROM weather_notes WHERE city = ?", ("Nanjing",)):#必须为元组
        print("  ", row)

    print("\n每个城市有几条记录（GROUP BY）：")
    for row in conn.execute(
        "SELECT city, COUNT(*) AS n FROM weather_notes GROUP BY city ORDER BY n DESC"
    ):
        print("  ", row)


def update_row(conn: sqlite3.Connection) -> None:
    print_step("4. 改：UPDATE 修改数据")

    conn.execute("UPDATE weather_notes SET temp = ?, note = ? WHERE id = ?", (29.5, "updated", 1))
    conn.commit()
    print("把 id=1 的温度改成 29.5：")
    print("  ", conn.execute("SELECT * FROM weather_notes WHERE id = 1").fetchone())


def delete_row(conn: sqlite3.Connection) -> None:
    print_step("5. 删：DELETE 删除数据（只删 id=4）")

    conn.execute("DELETE FROM weather_notes WHERE id = ?", (4,))
    conn.commit()
    remaining = conn.execute("SELECT COUNT(*) FROM weather_notes").fetchone()[0]
    print(f"删除后还剩 {remaining} 行。")


def show_primary_key_rule(conn: sqlite3.Connection) -> None:
    print_step("6. 主键为什么重要：插入重复 id 会直接报错")

    try:
        conn.execute(
            "INSERT INTO weather_notes (id, city, date, temp, note) VALUES (?, ?, ?, ?, ?)",
            (2, "Suzhou", "2026-10-05", 25.0, "duplicate test"),
        )
        conn.commit()
        print("居然插入成功了？说明主键设置有问题。")
    except sqlite3.IntegrityError as exc:
        print("插入失败，这其实是好事：", exc)
        print("数据库帮我们挡住了重复 id=2，保证每一行都有唯一身份。")


def create_index(conn: sqlite3.Connection) -> None:
    print_step("7. 索引：给常用查询列建目录")

    conn.execute("CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_notes (city)")
    conn.commit()
    print("已创建索引 idx_weather_city（按 city 查询会更快）。")

    print("\n当前数据库里的表和索引：")
    for row in conn.execute(
        "SELECT type, name FROM sqlite_master WHERE type IN ('table', 'index') ORDER BY type, name"
    ):
        print("  ", row)


def main() -> None:
    print_title("第 3 课：SQLite 数据库基础")

    # 每次运行先删掉旧数据库，保证结果可重复。
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        create_table(conn)
        insert_rows(conn)
        select_rows(conn)
        update_row(conn)
        delete_row(conn)
        show_primary_key_rule(conn)
        create_index(conn)
    finally:
        conn.close()

    print(f"\n数据库文件：{DB_PATH}")
    print("可以用 DB Browser for SQLite 这个免费软件打开它，点点看表里的数据。")
    print("下一步：python scripts/04_load_clean.py")


if __name__ == "__main__":
    main()
