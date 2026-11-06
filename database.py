"""MySQL の worker / haken テーブルへ接続するデータ取得関数。

テーブル・列名は未確認のため、下記の値を仮定として設定している。
実際のスキーマが分かったら、この設定と各 SELECT 文を合わせて変更する。
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta
from typing import Any


# 接続設定。認証情報をソースコードに書かず、環境変数で指定する。
DATABASE_NAME = os.getenv("DB_NAME", "shift_management")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# 仮定しているテーブル名とカラム名。MySQL の識別子として安全な名前のみ許可する。
WORKER_TABLE = "worker"
HAKEN_TABLE = "haken"
WORKER_ID_COLUMN = "worker_id"
WORKER_NAME_COLUMN = "name"
SHIFT_EMPLOYEE_ID_COLUMN = "worker_id"
SHIFT_DATE_COLUMN = "shift_date"
SHIFT_START_COLUMN = "start_time"
SHIFT_END_COLUMN = "end_time"
SHIFT_ROLE_COLUMN = "role"

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_identifier(identifier: str) -> str:
    """SQL パラメーターにできないテーブル名・列名を検証して引用する。"""
    if not _IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValueError(f"不正なテーブル名またはカラム名です: {identifier!r}")
    return f"`{identifier}`"


@contextmanager
def _cursor() -> Iterator[Any]:
    """接続と辞書形式カーソルを作成し、処理後に両方を閉じる。"""
    try:
        import mysql.connector
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "MySQL ドライバーがありません。`pip install -r requirements.txt`を実行してください。"
        ) from error

    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DATABASE_NAME,
    )
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
    finally:
        cursor.close()
        connection.close()


def _as_text(value: Any) -> str | None:
    """MySQL の日付・時刻型を扱いやすい文字列にそろえる。"""
    if value is None:
        return None
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    return str(value)


def get_employees() -> list[dict[str, Any]]:
    """従業員 ID と名前を {"id": ..., "name": ...} の形式で返す。"""
    query = (
        f"SELECT {_quote_identifier(WORKER_ID_COLUMN)} AS `id`, "
        f"{_quote_identifier(WORKER_NAME_COLUMN)} AS `name` "
        f"FROM {_quote_identifier(WORKER_TABLE)} "
        f"ORDER BY {_quote_identifier(WORKER_NAME_COLUMN)}"
    )
    with _cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def get_schedules(start_date: str, end_date: str) -> list[dict[str, Any]]:
    """指定期間のシフトを返す。開始日と終了日の両方を含む。"""
    query = (
        f"SELECT h.{_quote_identifier(SHIFT_EMPLOYEE_ID_COLUMN)} AS `employee_id`, "
        f"h.{_quote_identifier(SHIFT_DATE_COLUMN)} AS `date`, "
        f"h.{_quote_identifier(SHIFT_START_COLUMN)} AS `start_time`, "
        f"h.{_quote_identifier(SHIFT_END_COLUMN)} AS `end_time`, "
        f"h.{_quote_identifier(SHIFT_ROLE_COLUMN)} AS `role`, "
        f"w.{_quote_identifier(WORKER_NAME_COLUMN)} AS `employee_name` "
        f"FROM {_quote_identifier(HAKEN_TABLE)} AS h "
        f"LEFT JOIN {_quote_identifier(WORKER_TABLE)} AS w "
        f"ON h.{_quote_identifier(SHIFT_EMPLOYEE_ID_COLUMN)} "
        f"= w.{_quote_identifier(WORKER_ID_COLUMN)} "
        f"WHERE h.{_quote_identifier(SHIFT_DATE_COLUMN)} BETWEEN %s AND %s "
        f"ORDER BY h.{_quote_identifier(SHIFT_DATE_COLUMN)}, "
        f"h.{_quote_identifier(SHIFT_START_COLUMN)}"
    )
    with _cursor() as cursor:
        cursor.execute(query, (start_date, end_date))
        rows = cursor.fetchall()

    return [
        {key: _as_text(value) if key != "employee_id" else value
         for key, value in row.items()}
        for row in rows
    ]


def get_employee(employee_id: int) -> dict[str, Any] | None:
    """従業員の ID と名前を返す。見つからなければ None を返す。

    パスワードなどの認証情報は返さない。追加の詳細列が必要な場合は、
    実際のスキーマを確認してこの SELECT に明示的に追加する。
    """
    query = (
        f"SELECT {_quote_identifier(WORKER_ID_COLUMN)} AS `id`, "
        f"{_quote_identifier(WORKER_NAME_COLUMN)} AS `name` "
        f"FROM {_quote_identifier(WORKER_TABLE)} "
        f"WHERE {_quote_identifier(WORKER_ID_COLUMN)} = %s LIMIT 1"
    )
    with _cursor() as cursor:
        cursor.execute(query, (employee_id,))
        return cursor.fetchone()