"""情報閲覧機能"""

from datetime import date, datetime, timedelta

import database


def _parse_date(value: date | str, parameter_name: str) -> date:
    # date型とYYYY-MM-DD形式の文字列を、計算に使えるdate型へそろえる。
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as error:
            raise ValueError(f"{parameter_name}はYYYY-MM-DD形式で指定してください") from error
    raise ValueError(f"{parameter_name}はdateまたはYYYY-MM-DD形式で指定してください")


def check_schedule_permission(
    is_admin: bool = False,
) -> None:
    # 従業員の詳細情報など、管理者限定の機能だけを確認する。
    if not is_admin:
        raise PermissionError("この情報の表示には管理者権限が必要です")


def get_employee_list() -> list[dict[str, int | str]]:
    # 全ユーザーが従業員を選べるよう、IDと名前の一覧を返す。
    return [
        {"id": employee["id"], "name": employee["name"]}
        for employee in database.get_employees()
    ]


def get_schedule_by_date(
    start_date: date | str, end_date: date | str
) -> list[dict[str, int | str]]:
    # 指定した開始日から終了日までのシフトを取得する。両端の日付も含む。
    parsed_start = _parse_date(start_date, "開始日")
    parsed_end = _parse_date(end_date, "終了日")
    if parsed_start > parsed_end:
        raise ValueError("開始日は終了日以前の日付を指定してください")

    return database.get_schedules(parsed_start.isoformat(), parsed_end.isoformat())


def filter_shift(
    schedules: list[dict[str, int | str]], employee_id: int | None = None
) -> list[dict[str, int | str]]:
    # employee_idがNoneなら全員分、それ以外なら指定従業員分だけに絞る。
    if employee_id is None:
        return list(schedules)
    return [schedule for schedule in schedules if schedule["employee_id"] == employee_id]


def filter_by_period(
    target_date: date | str, period: str = "week"
) -> tuple[date, date]:
    # 基準日を含む週（月曜始まり）または月の開始日・終了日を求める。
    parsed_date = _parse_date(target_date, "基準日")

    if period == "week":
        start_date = parsed_date - timedelta(days=parsed_date.weekday())
        return start_date, start_date + timedelta(days=6)
    if period == "month":
        start_date = parsed_date.replace(day=1)
        if parsed_date.month == 12:
            next_month = parsed_date.replace(year=parsed_date.year + 1, month=1, day=1)
        else:
            next_month = parsed_date.replace(month=parsed_date.month + 1, day=1)
        return start_date, next_month - timedelta(days=1)

    raise ValueError("periodは'week'または'month'を指定してください")


def filter_by_user(
    schedules: list[dict[str, int | str]],
    user_id: int | None,
    show_all: bool = False,
) -> list[dict[str, int | str]]:
    # 初期表示は本人分。全体表示を選んだ場合は全従業員分を返す。
    if show_all:
        return list(schedules)
    if user_id is None:
        raise ValueError("本人のシフト表示にはuser_idが必要です")
    return filter_shift(schedules, user_id)


def get_schedule_view(
    target_date: date | str,
    user_id: int | None,
    period: str = "week",
    show_all: bool = False,
    employee_id: int | None = None,
) -> list[dict[str, int | str]]:
    # 期間内のシフトを取得し、選択従業員・全体・本人のいずれかに絞る。
    start_date, end_date = filter_by_period(target_date, period)
    schedules = get_schedule_by_date(start_date, end_date)
    if employee_id is not None:
        return filter_shift(schedules, employee_id)
    return filter_by_user(schedules, user_id, show_all)


def get_employee_info(
    employee_id: int, is_admin: bool = False
) -> dict[str, int | str] | None:
    # 管理者が従業員の詳細を取得する。存在しないIDならNoneを返す。
    check_schedule_permission(is_admin)
    return database.get_employee(employee_id)