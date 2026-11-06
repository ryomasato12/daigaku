"""仮データで動作するシフト閲覧アプリ。"""

from datetime import date, timedelta
import tkinter as tk
from tkinter import ttk


EMPLOYEES = ("佐藤 花子", "鈴木 健", "高橋 美咲", "田中 翔")
WEEKDAYS = ("月", "火", "水", "木", "金", "土", "日")

# (曜日, スタッフ番号, 開始, 終了, 担当)
SAMPLE_SHIFTS = (
    (0, 0, "09:00", "13:00", "受付"),
    (0, 1, "13:00", "18:00", "窓口"),
    (1, 2, "09:00", "14:00", "受付"),
    (1, 3, "14:00", "19:00", "窓口"),
    (2, 0, "10:00", "15:00", "窓口"),
    (2, 2, "15:00", "19:00", "受付"),
    (3, 1, "09:00", "13:00", "受付"),
    (3, 3, "13:00", "18:00", "窓口"),
    (4, 0, "09:00", "14:00", "受付"),
    (4, 2, "14:00", "19:00", "窓口"),
    (5, 1, "10:00", "15:00", "窓口"),
    (5, 3, "12:00", "17:00", "受付"),
    (6, 2, "10:00", "14:00", "受付"),
)


class ScheduleApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.today = date.today()
        self.week_start = self.today - timedelta(days=self.today.weekday())
        self.employee_filter = tk.StringVar(value="全員")

        root.title("シフト一覧")
        root.geometry("920x600")
        root.minsize(760, 480)
        root.configure(bg="#f3f5f7")

        self._configure_style()
        self._build_layout()
        self.refresh()

    def _configure_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=36, font=("TkDefaultFont", 10),
                        background="#ffffff", fieldbackground="#ffffff", foreground="#263238")
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"),
                        background="#e8edf0", foreground="#33434c", relief="flat")
        style.map("Treeview", background=[("selected", "#d8ece8")],
                  foreground=[("selected", "#173e38")])
        style.configure("TCombobox", padding=6)

    def _build_layout(self) -> None:
        header = tk.Frame(self.root, bg="#173e38", padx=28, pady=20)
        header.pack(fill="x")

        title_row = tk.Frame(header, bg="#173e38")
        title_row.pack(fill="x")
        tk.Label(title_row, text="シフト一覧", bg="#173e38", fg="white",
                 font=("TkDefaultFont", 20, "bold")).pack(side="left")

        navigation = tk.Frame(title_row, bg="#173e38")
        navigation.pack(side="right")
        self._button(navigation, "‹", self.previous_week, width=3).pack(side="left", padx=3)
        self.period_label = tk.Label(navigation, text="", width=27, bg="#173e38", fg="white",
                                     font=("TkDefaultFont", 11, "bold"))
        self.period_label.pack(side="left", padx=8)
        self._button(navigation, "›", self.next_week, width=3).pack(side="left", padx=3)
        self._button(navigation, "今週", self.current_week).pack(side="left", padx=(10, 0))

        content = tk.Frame(self.root, bg="#f3f5f7", padx=28, pady=20)
        content.pack(fill="both", expand=True)

        controls = tk.Frame(content, bg="#f3f5f7")
        controls.pack(fill="x", pady=(0, 16))
        tk.Label(controls, text="スタッフ", bg="#f3f5f7", fg="#53636a",
                 font=("TkDefaultFont", 10, "bold")).pack(side="left", padx=(0, 10))
        employee_picker = ttk.Combobox(
            controls,
            textvariable=self.employee_filter,
            values=("全員", *EMPLOYEES),
            state="readonly",
            width=18,
        )
        employee_picker.pack(side="left")
        employee_picker.bind("<<ComboboxSelected>>", lambda _event: self.refresh())

        stats = tk.Frame(content, bg="#f3f5f7")
        stats.pack(fill="x", pady=(0, 16))
        self.shift_count = self._stat(stats, "シフト件数")
        self.staff_count = self._stat(stats, "出勤スタッフ")
        self.week_count = self._stat(stats, "表示期間")

        table_frame = tk.Frame(content, bg="white", highlightthickness=1,
                               highlightbackground="#dce3e5")
        table_frame.pack(fill="both", expand=True)
        columns = ("date", "weekday", "employee", "time", "role")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "date": ("日付", 150),
            "weekday": ("曜日", 80),
            "employee": ("スタッフ", 200),
            "time": ("勤務時間", 180),
            "role": ("担当", 180),
        }
        for column, (label, width) in headings.items():
            self.table.heading(column, text=label)
            self.table.column(column, width=width, minwidth=70, anchor="w")
        self.table.tag_configure("odd", background="#f7f9fa")
        self.table.tag_configure("weekend", foreground="#a14335")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        scrollbar.pack(side="right", fill="y")

        self.status = tk.Label(content, text="", bg="#f3f5f7", fg="#718087",
                               anchor="w", font=("TkDefaultFont", 9))
        self.status.pack(fill="x", pady=(10, 0))

    @staticmethod
    def _button(parent: tk.Widget, text: str, command, width: int | None = None) -> tk.Button:
        return tk.Button(parent, text=text, command=command, width=width,
                         bg="#285c53", fg="white", activebackground="#367568",
                         activeforeground="white", relief="flat", cursor="hand2",
                         font=("TkDefaultFont", 10, "bold"), padx=10, pady=6)

    @staticmethod
    def _stat(parent: tk.Widget, label: str) -> tk.Label:
        block = tk.Frame(parent, bg="white", padx=14, pady=10,
                         highlightthickness=1, highlightbackground="#dce3e5")
        block.pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Label(block, text=label, bg="white", fg="#718087",
                 font=("TkDefaultFont", 9)).pack(anchor="w")
        value = tk.Label(block, text="-", bg="white", fg="#173e38",
                         font=("TkDefaultFont", 15, "bold"))
        value.pack(anchor="w", pady=(3, 0))
        return value

    def previous_week(self) -> None:
        self.week_start -= timedelta(days=7)
        self.refresh()

    def next_week(self) -> None:
        self.week_start += timedelta(days=7)
        self.refresh()

    def current_week(self) -> None:
        self.week_start = self.today - timedelta(days=self.today.weekday())
        self.refresh()

    def refresh(self) -> None:
        week_end = self.week_start + timedelta(days=6)
        self.period_label.config(
            text=f"{self.week_start:%Y年%m月%d日} - {week_end:%m月%d日}"
        )
        selected_employee = self.employee_filter.get()
        shifts = []
        for weekday, employee_index, start, end, role in SAMPLE_SHIFTS:
            if selected_employee != "全員" and EMPLOYEES[employee_index] != selected_employee:
                continue
            shift_date = self.week_start + timedelta(days=weekday)
            shifts.append((shift_date, employee_index, start, end, role))

        for item in self.table.get_children():
            self.table.delete(item)
        for index, (shift_date, employee_index, start, end, role) in enumerate(shifts):
            tags = ["odd"] if index % 2 else []
            if shift_date.weekday() >= 5:
                tags.append("weekend")
            self.table.insert("", "end", values=(
                f"{shift_date:%Y年%m月%d日}",
                WEEKDAYS[shift_date.weekday()],
                EMPLOYEES[employee_index],
                f"{start} - {end}",
                role,
            ), tags=tags)

        self.shift_count.config(text=f"{len(shifts)} 件")
        self.staff_count.config(text=f"{len({shift[1] for shift in shifts})} 人")
        self.week_count.config(text="1 週間")
        self.status.config(text=f"サンプルデータを表示中  |  {len(shifts)} 件のシフト")


def main() -> None:
    root = tk.Tk()
    ScheduleApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
