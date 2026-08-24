import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import calculator
import charts
import db


LOAN_RATES = {
    "Gold Loan": {
        "Bank of Baroda": 7.35,
        "Union Bank": 7.50,
        "HDFC Bank": 8.85,
        "Axis Bank": 9.10
    },
    "Vehicle Loan": {
        "2-Wheeler": {
            "Bank of Baroda": 9.35,
            "Union Bank": 9.60,
            "HDFC Bank": 11.25,
            "Axis Bank": 11.50
        },
        "4-Wheeler": {
            "Bank of Baroda": 8.40,
            "Union Bank": 8.65,
            "HDFC Bank": 10.20,
            "Axis Bank": 10.45
        }
    }
}

PUBLIC_BANKS = ["Bank of Baroda", "Union Bank"]
PRIVATE_BANKS = ["HDFC Bank", "Axis Bank"]
CREDIT_SCORE_ADJUSTMENTS = {
    "Below 650": 0.5,
    "650-750": 0,
    "Above 750": -0.5
}

LOAN_AMOUNT_LIMITS = {
    "Gold Loan": (10000, 5000000),
    "Vehicle Loan": {
        "2-Wheeler": (20000, 300000),
        "4-Wheeler": (100000, 5000000)
    }
}

LOAN_TENURE_LIMITS = {
    "Gold Loan": (1, 3),
    "Vehicle Loan": {
        "2-Wheeler": (1, 5),
        "4-Wheeler": (1, 7)
    }
}

APP_BG = "#f3f6fb"
CARD_BG = "#ffffff"
TEXT = "#172033"
MUTED = "#64748b"
BORDER = "#d5dde8"
PRIMARY = "#0f766e"
PRIMARY_DARK = "#12315c"
SUCCESS = "#15803d"
DANGER = "#dc2626"
SECONDARY = "#475569"
WARNING = "#d97706"
PANEL_BG = "#e8eef7"
ENTRY_BG = "#f8fafc"


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.window = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.window is not None:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8

        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")

        tk.Label(
            self.window,
            text=self.text,
            bg="#172033",
            fg="#ffffff",
            padx=10,
            pady=6,
            font=("Arial", 9),
            relief="solid",
            bd=1
        ).pack()

    def hide(self, event=None):
        if self.window is not None:
            self.window.destroy()
            self.window = None


class LoanComparisonApp:
    def __init__(self):
        db.create_table()

        self.root = tk.Tk()
        self.root.title("Loan Comparison System")
        self.root.geometry("1360x820")
        self.root.minsize(1180, 720)
        self.root.configure(bg=APP_BG)
        self.setup_styles()

        self.build_input_page()
        self.build_result_page()

    def run(self):
        self.root.mainloop()

    def format_currency(self, value):
        sign = "-" if value < 0 else ""
        amount = abs(value)
        integer_part, decimal_part = f"{amount:.2f}".split(".")

        if len(integer_part) > 3:
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            groups = []

            while len(remaining) > 2:
                groups.insert(0, remaining[-2:])
                remaining = remaining[:-2]

            if remaining:
                groups.insert(0, remaining)

            integer_part = ",".join(groups + [last_three])

        return f"{sign}₹{integer_part}.{decimal_part}"

    def setup_styles(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TCombobox",
            padding=6,
            fieldbackground=ENTRY_BG,
            background=ENTRY_BG,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", ENTRY_BG)],
            foreground=[("readonly", TEXT)],
            selectbackground=[("readonly", ENTRY_BG)],
            selectforeground=[("readonly", TEXT)]
        )
        style.configure(
            "Treeview",
            rowheight=42,
            background=ENTRY_BG,
            fieldbackground=ENTRY_BG,
            foreground=TEXT,
            bordercolor=BORDER,
            font=("Arial", 12)
        )
        style.map(
            "Treeview",
            background=[("selected", PRIMARY)],
            foreground=[("selected", PRIMARY_DARK)]
        )
        style.configure(
            "Treeview.Heading",
            font=("Arial", 12, "bold"),
            background=PANEL_BG,
            foreground=TEXT
        )
        style.configure(
            "TNotebook",
            background=APP_BG,
            borderwidth=0,
            tabmargins=(0, 0, 0, 0)
        )
        style.configure(
            "TNotebook.Tab",
            background=PANEL_BG,
            foreground=MUTED,
            padding=(38, 16),
            font=("Arial", 13, "bold")
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", CARD_BG)],
            foreground=[("selected", TEXT)]
        )

    def clear_roi(self):
        self.public_roi.config(state="normal")
        self.private_roi.config(state="normal")
        self.public_roi.delete(0, tk.END)
        self.private_roi.delete(0, tk.END)
        self.public_roi.config(state="readonly")
        self.private_roi.config(state="readonly")

    def set_roi_values(self, public_rate, private_rate):
        self.public_roi.config(state="normal")
        self.private_roi.config(state="normal")
        self.public_roi.delete(0, tk.END)
        self.public_roi.insert(0, f"{public_rate:.2f}")
        self.private_roi.delete(0, tk.END)
        self.private_roi.insert(0, f"{private_rate:.2f}")
        self.public_roi.config(state="readonly")
        self.private_roi.config(state="readonly")

    def get_base_rates(self):
        selected_loan = self.loan_type.get()
        selected_public_bank = self.public_bank.get()
        selected_private_bank = self.private_bank.get()

        if selected_public_bank not in PUBLIC_BANKS:
            return None

        if selected_private_bank not in PRIVATE_BANKS:
            return None

        if selected_loan == "Gold Loan":
            rates = LOAN_RATES[selected_loan]
            return rates[selected_public_bank], rates[selected_private_bank]

        if selected_loan == "Vehicle Loan":
            selected_vehicle = self.vehicle_type.get()

            if selected_vehicle in LOAN_RATES[selected_loan]:
                rates = LOAN_RATES[selected_loan][selected_vehicle]
                return rates[selected_public_bank], rates[selected_private_bank]

        return None

    def get_amount_limits(self):
        selected_loan = self.loan_type.get()

        if selected_loan == "Gold Loan":
            return LOAN_AMOUNT_LIMITS["Gold Loan"]

        if selected_loan == "Vehicle Loan":
            selected_vehicle = self.vehicle_type.get()
            return LOAN_AMOUNT_LIMITS["Vehicle Loan"].get(selected_vehicle)

        return None

    def get_tenure_limits(self):
        selected_loan = self.loan_type.get()

        if selected_loan == "Gold Loan":
            return LOAN_TENURE_LIMITS["Gold Loan"]

        if selected_loan == "Vehicle Loan":
            selected_vehicle = self.vehicle_type.get()
            return LOAN_TENURE_LIMITS["Vehicle Loan"].get(selected_vehicle)

        return None

    def get_amount_limit_text(self):
        limits = self.get_amount_limits()

        if limits is None:
            return "Select loan type to view allowed amount range."

        minimum, maximum = limits
        return (
            f"Allowed range: {self.format_currency(minimum)} to "
            f"{self.format_currency(maximum)}."
        )

    def get_tenure_limit_text(self):
        limits = self.get_tenure_limits()

        if limits is None:
            return "Select loan type to view allowed tenure range."

        minimum, maximum = limits
        return f"Allowed tenure: {minimum} to {maximum} years."

    def update_amount_hint(self):
        if hasattr(self, "amount_hint"):
            self.amount_hint.config(text=self.get_amount_limit_text())

    def update_tenure_hint(self):
        if hasattr(self, "tenure_hint"):
            self.tenure_hint.config(text=self.get_tenure_limit_text())

    def validate_loan_amount_limit(self, amount):
        limits = self.get_amount_limits()

        if limits is None:
            messagebox.showwarning(
                "Invalid Loan Amount",
                "Please select valid loan details before entering amount."
            )
            return False

        minimum, maximum = limits

        if amount < minimum or amount > maximum:
            messagebox.showwarning(
                "Invalid Loan Amount",
                (
                    "Loan amount must be between "
                    f"{self.format_currency(minimum)} and "
                    f"{self.format_currency(maximum)} for the selected loan."
                )
            )
            return False

        return True

    def validate_loan_tenure_limit(self, years):
        limits = self.get_tenure_limits()

        if limits is None:
            messagebox.showwarning(
                "Invalid Loan Tenure",
                "Please select valid loan details before entering tenure."
            )
            return False

        minimum, maximum = limits

        if years < minimum or years > maximum:
            messagebox.showwarning(
                "Invalid Loan Tenure",
                (
                    "Loan tenure must be between "
                    f"{minimum} and {maximum} years for the selected loan."
                )
            )
            return False

        return True

    def apply_credit_score_adjustment(self, public_rate, private_rate):
        adjustment = CREDIT_SCORE_ADJUSTMENTS.get(self.credit_score.get(), 0)
        return public_rate + adjustment, private_rate + adjustment

    def parse_positive_float(self, value, field_name):
        try:
            amount = float(value)
        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                f"Please enter a valid number for {field_name}."
            )
            return None

        if amount <= 0:
            messagebox.showwarning(
                "Invalid Input",
                f"{field_name} must be greater than zero."
            )
            return None

        return amount

    def parse_positive_int(self, value, field_name):
        try:
            number = int(value)
        except ValueError:
            messagebox.showwarning(
                "Invalid Input",
                f"Please enter a valid whole number for {field_name}."
            )
            return None

        if number <= 0:
            messagebox.showwarning(
                "Invalid Input",
                f"{field_name} must be greater than zero."
            )
            return None

        return number

    def update_vehicle_option(self, event=None):
        if self.loan_type.get() == "Vehicle Loan":
            self.vehicle_frame.pack_forget()
            self.vehicle_frame.pack(fill="x", pady=(10, 0), after=self.loan_type)
        else:
            self.vehicle_frame.pack_forget()
            self.vehicle_type.set("Select Vehicle Type")

        self.clear_roi()
        self.update_amount_hint()
        self.update_tenure_hint()
        self.update_roi()

    def update_roi(self, event=None):
        self.update_amount_hint()
        self.update_tenure_hint()
        rates = self.get_base_rates()

        if rates is None:
            self.clear_roi()
            return

        public_rate, private_rate = self.apply_credit_score_adjustment(*rates)
        self.set_roi_values(public_rate, private_rate)

    def reset_fields(self):
        self.loan_type.set("Select Loan Type")
        self.vehicle_frame.pack_forget()
        self.vehicle_type.set("Select Vehicle Type")
        self.amount_entry.delete(0, tk.END)
        self.year_entry.delete(0, tk.END)
        self.credit_score.set("650-750")
        self.public_bank.set("Select Public Bank")
        self.private_bank.set("Select Private Bank")
        self.clear_roi()
        self.update_amount_hint()
        self.update_tenure_hint()
        self.fig.clear()
        self.canvas.draw()
        self.show_input_page()

    def show_input_page(self):
        self.result_frame.pack_forget()
        self.input_frame.pack(fill="both", expand=True)

    def show_result_page(self):
        self.input_frame.pack_forget()
        self.result_frame.pack(fill="both", expand=True)

    def validate_required_fields(self):
        if self.loan_type.get() == "Select Loan Type":
            messagebox.showwarning("Warning", "Please Select Loan Type")
            return False

        if (
            self.loan_type.get() == "Vehicle Loan"
            and self.vehicle_type.get() == "Select Vehicle Type"
        ):
            messagebox.showwarning("Warning", "Please Select Vehicle Type")
            return False

        if self.amount_entry.get().strip() == "":
            messagebox.showwarning("Warning", "Please Enter Loan Amount")
            return False

        if self.year_entry.get().strip() == "":
            messagebox.showwarning("Warning", "Please Enter Loan Tenure")
            return False

        if self.public_bank.get() == "Select Public Bank":
            messagebox.showwarning("Warning", "Please Select Public Bank")
            return False

        if self.private_bank.get() == "Select Private Bank":
            messagebox.showwarning("Warning", "Please Select Private Bank")
            return False

        return True

    def compare_sector(self):
        if not self.validate_required_fields():
            return

        amount = self.parse_positive_float(
            self.amount_entry.get().strip(),
            "Loan Amount"
        )

        if amount is None:
            return

        if not self.validate_loan_amount_limit(amount):
            return

        years = self.parse_positive_int(
            self.year_entry.get().strip(),
            "Loan Tenure"
        )

        if years is None:
            return

        if not self.validate_loan_tenure_limit(years):
            return

        rates = self.get_base_rates()

        if rates is None:
            messagebox.showwarning("Warning", "Please select valid loan details.")
            return

        public_rate, private_rate = self.apply_credit_score_adjustment(*rates)
        self.set_roi_values(public_rate, private_rate)

        try:
            emi1, int1, tot1 = calculator.calculate_emi(
                amount,
                public_rate,
                years
            )
            emi2, int2, tot2 = calculator.calculate_emi(
                amount,
                private_rate,
                years
            )
        except ValueError as error:
            messagebox.showwarning("Invalid Input", str(error))
            return

        vehicle_value = (
            self.vehicle_type.get()
            if self.loan_type.get() == "Vehicle Loan"
            else "Not Applicable"
        )

        db.insert_data((
            self.loan_type.get(),
            vehicle_value,
            amount,
            years,
            self.public_bank.get(),
            self.private_bank.get(),
            public_rate,
            private_rate,
            emi1,
            emi2,
            tot1,
            tot2
        ))

        self.header_title.config(text=f"{self.loan_type.get()} Comparison")
        self.header_subtitle.config(
            text=f"{self.public_bank.get()} vs {self.private_bank.get()}"
        )
        self.public_bank_title.config(
            text=f"PUBLIC BANK ({self.public_bank.get()})"
        )
        self.private_bank_title.config(
            text=f"PRIVATE BANK ({self.private_bank.get()})"
        )

        if tot1 < tot2:
            difference = round(tot2 - tot1, 2)
            cheaper_bank = self.public_bank.get()
            cheaper_side = "public"
            result_text = (
                f"{cheaper_bank} is cheaper by {self.format_currency(difference)}"
            )
        elif tot2 < tot1:
            difference = round(tot1 - tot2, 2)
            cheaper_bank = self.private_bank.get()
            cheaper_side = "private"
            result_text = (
                f"{cheaper_bank} is cheaper by {self.format_currency(difference)}"
            )
        else:
            difference = 0
            cheaper_bank = "Tie"
            cheaper_side = "tie"
            result_text = "Both banks have the same total repayment"

        self.summary_cheaper_value.config(text=cheaper_bank)
        self.summary_savings_value.config(text=self.format_currency(difference))
        self.summary_amount_value.config(text=self.format_currency(amount))

        generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")
        self.generated_label.config(text=f"Generated on: {generated_at}")

        self.public_badge.config(
            text="Recommended" if cheaper_side == "public" else "Compared",
            bg=SUCCESS if cheaper_side == "public" else PANEL_BG,
            fg="white" if cheaper_side == "public" else MUTED
        )
        self.private_badge.config(
            text="Recommended" if cheaper_side == "private" else "Compared",
            bg=SUCCESS if cheaper_side == "private" else PANEL_BG,
            fg="white" if cheaper_side == "private" else MUTED
        )

        self.public_emi_value.config(text=self.format_currency(emi1))
        self.private_emi_value.config(text=self.format_currency(emi2))

        self.public_detail_label.config(
            text=
            f"Interest Rate      {public_rate:.2f}%\n"
            f"Total Interest     {self.format_currency(int1)}\n"
            f"Total Repayment    {self.format_currency(tot1)}"
        )
        self.private_detail_label.config(
            text=
            f"Interest Rate      {private_rate:.2f}%\n"
            f"Total Interest     {self.format_currency(int2)}\n"
            f"Total Repayment    {self.format_currency(tot2)}"
        )

        if cheaper_side == "tie":
            reason = (
                "Both banks have the same total repayment for the selected "
                "loan amount, tenure, and credit score category."
            )
            recommendation_title = "Both banks are equally suitable"
            recommendation_detail = (
                "No repayment saving is available because both options have "
                "the same total repayment."
            )
        else:
            reason = (
                f"{cheaper_bank} is recommended because its total repayment is "
                f"{self.format_currency(difference)} lower over {years} years."
            )
            recommendation_title = f"Choose {cheaper_bank}"
            recommendation_detail = (
                f"{cheaper_bank} offers the lower total repayment and saves "
                f"{self.format_currency(difference)} compared with the other option."
            )

        self.reason_label.config(text=reason)
        self.final_recommendation_title.config(text=recommendation_title)
        self.final_recommendation_detail.config(text=recommendation_detail)
        self.result_label.config(text=result_text, fg=SUCCESS)
        self.update_metric_table(
            public_rate,
            private_rate,
            emi1,
            emi2,
            int1,
            int2,
            tot1,
            tot2
        )
        self.chart_insights_label.config(
            text=(
                f"ROI Gap: {abs(public_rate - private_rate):.2f}%\n"
                f"EMI Gap: {self.format_currency(abs(emi1 - emi2))} per month\n"
                f"Repayment Gap: {self.format_currency(abs(tot1 - tot2))}"
            )
        )

        charts.update_graph(
            self.fig,
            self.canvas,
            public_rate,
            private_rate,
            emi1,
            emi2,
            int1,
            int2,
            tot1,
            tot2,
            amount
        )

        self.result_tabs.select(0)
        self.show_result_page()

    def show_history(self):
        rows = db.fetch_all()

        if not rows:
            messagebox.showinfo(
                "History",
                "No loan comparisons have been saved yet."
            )
            return

        history_window = tk.Toplevel(self.root)
        history_window.title("Comparison History")
        history_window.geometry("1150x460")
        history_window.configure(bg=APP_BG)

        tk.Label(
            history_window,
            text="Saved Loan Comparisons",
            font=("Arial", 18, "bold"),
            bg=APP_BG,
            fg=TEXT
        ).pack(pady=(16, 10))

        table_frame = tk.Frame(
            history_window,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        columns = (
            "timestamp",
            "loan_type",
            "vehicle_type",
            "amount",
            "years",
            "public_bank",
            "private_bank",
            "public_rate",
            "private_rate",
            "public_total",
            "private_total"
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=12
        )

        headings = {
            "timestamp": "Date",
            "loan_type": "Loan Type",
            "vehicle_type": "Vehicle",
            "amount": "Amount",
            "years": "Years",
            "public_bank": "Public Bank",
            "private_bank": "Private Bank",
            "public_rate": "Public ROI",
            "private_rate": "Private ROI",
            "public_total": "Public Total",
            "private_total": "Private Total"
        }

        widths = {
            "timestamp": 150,
            "loan_type": 110,
            "vehicle_type": 100,
            "amount": 120,
            "years": 70,
            "public_bank": 130,
            "private_bank": 130,
            "public_rate": 90,
            "private_rate": 90,
            "public_total": 120,
            "private_total": 120
        }

        for column in columns:
            tree.heading(column, text=headings[column])
            tree.column(column, width=widths[column], anchor="center")

        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set
        )

        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        for row in rows:
            (
                record_id,
                saved_loan_type,
                saved_vehicle_type,
                amount,
                years,
                saved_public_bank,
                saved_private_bank,
                public_rate,
                private_rate,
                public_emi,
                private_emi,
                public_total,
                private_total,
                timestamp
            ) = row

            tree.insert(
                "",
                tk.END,
                iid=record_id,
                values=(
                    timestamp,
                    saved_loan_type,
                    saved_vehicle_type,
                    f"₹{amount:,.2f}",
                    years,
                    saved_public_bank,
                    saved_private_bank,
                    f"{public_rate:.2f}%",
                    f"{private_rate:.2f}%",
                    f"₹{public_total:,.2f}",
                    f"₹{private_total:,.2f}"
                )
            )

        action_frame = tk.Frame(history_window, bg=APP_BG)
        action_frame.pack(pady=(0, 14))

        clear_button = self.create_button(
            action_frame,
            "Clear History",
            DANGER,
            lambda: self.clear_history(history_window),
            width=14
        )
        clear_button.pack()
        Tooltip(clear_button, "Delete all saved comparison records.")

    def clear_history(self, history_window):
        confirmed = messagebox.askyesno(
            "Clear History",
            "Are you sure you want to delete all saved comparisons?"
        )

        if not confirmed:
            return

        db.clear_history()
        history_window.destroy()
        messagebox.showinfo("History", "Comparison history has been cleared.")

    def add_field_label(self, parent, text):
        tk.Label(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w", pady=(12, 0))

    def add_hint(self, parent, text):
        label = tk.Label(
            parent,
            text=text,
            font=("Arial", 8),
            bg=CARD_BG,
            fg=MUTED
        )
        label.pack(anchor="w", pady=(0, 4))
        return label

    def create_button(self, parent, text, bg, command, width=14):
        button = tk.Button(
            parent,
            text=text,
            bg=bg,
            fg="white",
            width=width,
            font=("Arial", 11, "bold"),
            activebackground=bg,
            activeforeground="white",
            bd=0,
            padx=12,
            pady=9,
            cursor="hand2",
            command=command
        )
        return button

    def style_text_entry(self, entry, readonly=False):
        entry.config(
            bg=ENTRY_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=PRIMARY,
            readonlybackground=ENTRY_BG
        )

        if readonly:
            entry.config(fg=PRIMARY)

    def create_summary_card(self, parent, title):
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=14
        )
        card.pack(side="left", fill="x", expand=True, padx=8)

        tk.Label(
            card,
            text=title,
            font=("Arial", 11, "bold"),
            bg=CARD_BG,
            fg=MUTED
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text="-",
            font=("Arial", 20, "bold"),
            bg=CARD_BG,
            fg=TEXT
        )
        value_label.pack(anchor="w", pady=(6, 0))
        return value_label

    def add_divider(self, parent, pady=(14, 14)):
        divider = tk.Frame(parent, bg=BORDER, height=1)
        divider.pack(fill="x", pady=pady)
        return divider

    def update_metric_table(
        self,
        public_rate,
        private_rate,
        emi1,
        emi2,
        int1,
        int2,
        tot1,
        tot2
    ):
        for widget in self.metric_table_frame.winfo_children():
            widget.destroy()

        rows = [
            ("Metric", self.public_bank.get(), self.private_bank.get()),
            ("ROI", f"{public_rate:.2f}%", f"{private_rate:.2f}%"),
            ("Monthly EMI", self.format_currency(emi1), self.format_currency(emi2)),
            ("Total Interest", self.format_currency(int1), self.format_currency(int2)),
            ("Total Repayment", self.format_currency(tot1), self.format_currency(tot2))
        ]

        for row_index, row in enumerate(rows):
            for column_index, value in enumerate(row):
                is_header = row_index == 0
                cell = tk.Label(
                    self.metric_table_frame,
                    text=value,
                    bg=PANEL_BG if is_header else ENTRY_BG,
                    fg=TEXT,
                    font=("Arial", 13, "bold") if is_header else ("Arial", 13),
                    padx=16,
                    pady=14,
                    anchor="w" if column_index == 0 else "center",
                    highlightbackground=BORDER,
                    highlightthickness=1
                )
                cell.grid(
                    row=row_index,
                    column=column_index,
                    sticky="nsew"
                )

        for column in range(3):
            self.metric_table_frame.columnconfigure(column, weight=1)

    def build_input_page(self):
        self.input_frame = tk.Frame(self.root, bg=APP_BG)
        self.input_frame.pack(fill="both", expand=True)

        container = tk.Frame(self.input_frame, bg=APP_BG)
        container.pack(fill="both", expand=True, padx=46, pady=34)

        side_panel = tk.Frame(
            container,
            bg=PRIMARY_DARK,
            width=360,
            padx=30,
            pady=32
        )
        side_panel.pack(side="left", fill="y", padx=(0, 28))
        side_panel.pack_propagate(False)

        tk.Label(
            side_panel,
            text="Loan Comparison\nSystem",
            font=("Arial", 27, "bold"),
            bg=PRIMARY_DARK,
            fg="white",
            justify="left"
        ).pack(anchor="w", pady=(12, 18))

        tk.Label(
            side_panel,
            text="Evaluate loan offers with clear EMI, interest, repayment, and affordability insights.",
            font=("Arial", 12),
            bg=PRIMARY_DARK,
            fg="#cbd5e1",
            justify="left",
            wraplength=285
        ).pack(anchor="w")

        divider = tk.Frame(side_panel, bg=PRIMARY, height=2)
        divider.pack(fill="x", pady=28)

        for title, detail in (
            ("Rate Analysis", "Compare ROI across selected banking options."),
            ("Credit Profile", "Factor credit score impact into repayment estimates."),
            ("Financial Insights", "Review EMI, interest, and repayment breakdowns.")
        ):
            tk.Label(
                side_panel,
                text=title,
                font=("Arial", 12, "bold"),
                bg=PRIMARY_DARK,
                fg="white"
            ).pack(anchor="w", pady=(0, 4))
            tk.Label(
                side_panel,
                text=detail,
                font=("Arial", 10),
                bg=PRIMARY_DARK,
                fg="#cbd5e1",
                justify="left",
                wraplength=285
            ).pack(anchor="w", pady=(0, 16))

        form_area = tk.Frame(container, bg=APP_BG)
        form_area.pack(side="left", fill="both", expand=True)

        tk.Label(
            form_area,
            text="Compare Loan Options",
            font=("Arial", 24, "bold"),
            bg=APP_BG,
            fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            form_area,
            text="Enter loan details and choose one public bank and one private bank.",
            font=("Arial", 11),
            bg=APP_BG,
            fg=MUTED
        ).pack(anchor="w", pady=(4, 18))

        form_card = tk.Frame(
            form_area,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=34,
            pady=24
        )
        form_card.pack(anchor="w", fill="x")

        left_fields = tk.Frame(form_card, bg=CARD_BG)
        left_fields.pack(side="left", fill="both", expand=True, padx=(0, 22))

        right_fields = tk.Frame(form_card, bg=CARD_BG)
        right_fields.pack(side="left", fill="both", expand=True, padx=(22, 0))

        self.add_field_label(left_fields, "Loan Type")
        self.loan_type = ttk.Combobox(
            left_fields,
            values=["Gold Loan", "Vehicle Loan"],
            state="readonly",
            width=38
        )
        self.loan_type.pack(fill="x", pady=8)
        self.loan_type.set("Select Loan Type")
        self.loan_type.bind("<<ComboboxSelected>>", self.update_vehicle_option)
        Tooltip(self.loan_type, "Choose the loan category to compare.")

        self.vehicle_frame = tk.Frame(left_fields, bg=CARD_BG)
        tk.Label(
            self.vehicle_frame,
            text="Vehicle Type",
            font=("Arial", 11, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w")
        self.vehicle_type = ttk.Combobox(
            self.vehicle_frame,
            values=["2-Wheeler", "4-Wheeler"],
            state="readonly",
            width=38
        )
        self.vehicle_type.pack(fill="x", pady=8)
        self.vehicle_type.set("Select Vehicle Type")
        self.vehicle_type.bind("<<ComboboxSelected>>", self.update_roi)
        Tooltip(self.vehicle_type, "Required only for vehicle loans.")

        self.amount_label = tk.Label(
            left_fields,
            text="Loan Amount",
            font=("Arial", 11, "bold"),
            bg=CARD_BG,
            fg=TEXT
        )
        self.amount_label.pack(anchor="w", pady=(12, 0))
        self.amount_entry = tk.Entry(
            left_fields,
            width=40,
            font=("Arial", 11),
        )
        self.style_text_entry(self.amount_entry)
        self.amount_entry.pack(fill="x", pady=(8, 2))
        self.amount_hint = self.add_hint(
            left_fields,
            "Select loan type to view allowed amount range."
        )
        Tooltip(
            self.amount_entry,
            "Amount must be within the selected loan range."
        )

        self.add_field_label(left_fields, "Loan Tenure (Years)")
        self.year_entry = tk.Entry(
            left_fields,
            width=40,
            font=("Arial", 11),
        )
        self.style_text_entry(self.year_entry)
        self.year_entry.pack(fill="x", pady=(8, 2))
        self.tenure_hint = self.add_hint(
            left_fields,
            "Select loan type to view allowed tenure range."
        )
        Tooltip(self.year_entry, "Tenure must be greater than zero.")

        self.add_field_label(right_fields, "Credit Score")
        self.credit_score = ttk.Combobox(
            right_fields,
            values=["Below 650", "650-750", "Above 750"],
            state="readonly",
            width=38
        )
        self.credit_score.pack(fill="x", pady=(8, 2))
        self.credit_score.set("650-750")
        self.credit_score.bind("<<ComboboxSelected>>", self.update_roi)
        self.add_hint(right_fields, "Higher score reduces ROI; lower score adds ROI.")
        Tooltip(self.credit_score, "Applies a small adjustment to bank rates.")

        self.add_field_label(right_fields, "Public Bank")
        self.public_bank = ttk.Combobox(
            right_fields,
            values=PUBLIC_BANKS,
            state="readonly",
            width=38
        )
        self.public_bank.pack(fill="x", pady=8)
        self.public_bank.set("Select Public Bank")
        self.public_bank.bind("<<ComboboxSelected>>", self.update_roi)
        Tooltip(self.public_bank, "Select a public sector bank.")

        self.add_field_label(right_fields, "Public ROI (%)")
        self.public_roi = tk.Entry(
            right_fields,
            state="readonly",
            font=("Arial", 10),
        )
        self.style_text_entry(self.public_roi, readonly=True)
        self.public_roi.pack(fill="x", pady=8)
        Tooltip(self.public_roi, "Auto-calculated public bank ROI.")

        self.add_field_label(right_fields, "Private Bank")
        self.private_bank = ttk.Combobox(
            right_fields,
            values=PRIVATE_BANKS,
            state="readonly",
            width=38
        )
        self.private_bank.pack(fill="x", pady=8)
        self.private_bank.set("Select Private Bank")
        self.private_bank.bind("<<ComboboxSelected>>", self.update_roi)
        Tooltip(self.private_bank, "Select a private sector bank.")

        self.add_field_label(right_fields, "Private ROI (%)")
        self.private_roi = tk.Entry(
            right_fields,
            state="readonly",
            font=("Arial", 10),
        )
        self.style_text_entry(self.private_roi, readonly=True)
        self.private_roi.pack(fill="x", pady=8)
        Tooltip(self.private_roi, "Auto-calculated private bank ROI.")

        btn_frame = tk.Frame(form_area, bg=APP_BG)
        btn_frame.pack(pady=20)

        compare_button = self.create_button(
            btn_frame,
            "Compare Sector",
            SUCCESS,
            self.compare_sector,
            width=18
        )
        compare_button.grid(row=0, column=0, padx=12)
        Tooltip(compare_button, "Calculate and compare both bank options.")

        reset_button = self.create_button(
            btn_frame,
            "Reset",
            DANGER,
            self.reset_fields,
            width=12
        )
        reset_button.grid(row=0, column=1, padx=12)
        Tooltip(reset_button, "Clear current form values.")

        history_button = self.create_button(
            btn_frame,
            "View History",
            PRIMARY,
            self.show_history,
            width=14
        )
        history_button.grid(row=0, column=2, padx=12)
        Tooltip(history_button, "Open saved loan comparison records.")

    def build_result_page(self):
        self.result_frame = tk.Frame(self.root, bg=APP_BG)

        header_bar = tk.Frame(self.result_frame, bg=APP_BG)
        header_bar.pack(fill="x", padx=32, pady=(22, 12))

        title_block = tk.Frame(header_bar, bg=APP_BG)
        title_block.pack(side="left", fill="x", expand=True)

        self.header_title = tk.Label(
            title_block,
            text="Comparison",
            font=("Arial", 30, "bold"),
            bg=APP_BG,
            fg=TEXT
        )
        self.header_title.pack(anchor="w")

        self.header_subtitle = tk.Label(
            title_block,
            text="",
            font=("Arial", 14),
            bg=APP_BG,
            fg=MUTED
        )
        self.header_subtitle.pack(anchor="w", pady=(4, 0))

        self.generated_label = tk.Label(
            header_bar,
            text="Generated on: -",
            font=("Arial", 12),
            bg=APP_BG,
            fg=MUTED
        )
        self.generated_label.pack(side="right", anchor="n", pady=(8, 0))

        self.result_tabs = ttk.Notebook(self.result_frame)
        self.result_tabs.pack(fill="both", expand=True, padx=24, pady=(0, 18))

        summary_tab = tk.Frame(self.result_tabs, bg=APP_BG)
        charts_tab = tk.Frame(self.result_tabs, bg=APP_BG)
        details_tab = tk.Frame(self.result_tabs, bg=APP_BG)

        self.result_tabs.add(summary_tab, text="Summary")
        self.result_tabs.add(charts_tab, text="Charts")
        self.result_tabs.add(details_tab, text="Details")

        summary_strip = tk.Frame(summary_tab, bg=APP_BG)
        summary_strip.pack(fill="x", pady=(18, 18))

        self.summary_cheaper_value = self.create_summary_card(
            summary_strip,
            "RECOMMENDED BANK"
        )
        self.summary_savings_value = self.create_summary_card(
            summary_strip,
            "REPAYMENT SAVINGS"
        )
        self.summary_amount_value = self.create_summary_card(
            summary_strip,
            "LOAN AMOUNT"
        )

        summary_body = tk.Frame(summary_tab, bg=APP_BG)
        summary_body.pack(fill="both", expand=True)

        bank_grid = tk.Frame(summary_body, bg=APP_BG)
        bank_grid.pack(side="left", fill="both", expand=True, padx=(0, 18))

        public_card = tk.Frame(
            bank_grid,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=24,
            pady=22
        )
        public_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        private_card = tk.Frame(
            bank_grid,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=24,
            pady=22
        )
        private_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

        public_header = tk.Frame(public_card, bg=CARD_BG)
        public_header.pack(fill="x")

        self.public_bank_title = tk.Label(
            public_header,
            text="PUBLIC BANK",
            font=("Arial", 12, "bold"),
            bg=CARD_BG,
            fg=SUCCESS,
            anchor="w"
        )
        self.public_bank_title.pack(side="left", anchor="w")

        self.public_badge = tk.Label(
            public_header,
            text="Compared",
            font=("Arial", 8, "bold"),
            bg=PANEL_BG,
            fg=MUTED,
            padx=10,
            pady=4
        )
        self.public_badge.pack(side="right")

        tk.Label(
            public_card,
            text="Monthly EMI",
            font=("Arial", 10, "bold"),
            bg=CARD_BG,
            fg=MUTED
        ).pack(anchor="w", pady=(28, 0))

        self.public_emi_value = tk.Label(
            public_card,
            text="-",
            font=("Arial", 30, "bold"),
            bg=CARD_BG,
            fg=SUCCESS
        )
        self.public_emi_value.pack(anchor="w", pady=(4, 22))

        self.public_detail_label = tk.Label(
            public_card,
            text="",
            justify="left",
            bg=CARD_BG,
            fg=TEXT,
            font=("Consolas", 11),
            anchor="nw"
        )
        self.public_detail_label.pack(anchor="w")

        private_header = tk.Frame(private_card, bg=CARD_BG)
        private_header.pack(fill="x")

        self.private_bank_title = tk.Label(
            private_header,
            text="PRIVATE BANK",
            font=("Arial", 12, "bold"),
            bg=CARD_BG,
            fg=PRIMARY,
            anchor="w"
        )
        self.private_bank_title.pack(side="left", anchor="w")

        self.private_badge = tk.Label(
            private_header,
            text="Compared",
            font=("Arial", 8, "bold"),
            bg=PANEL_BG,
            fg=MUTED,
            padx=10,
            pady=4
        )
        self.private_badge.pack(side="right")

        tk.Label(
            private_card,
            text="Monthly EMI",
            font=("Arial", 10, "bold"),
            bg=CARD_BG,
            fg=MUTED
        ).pack(anchor="w", pady=(28, 0))

        self.private_emi_value = tk.Label(
            private_card,
            text="-",
            font=("Arial", 30, "bold"),
            bg=CARD_BG,
            fg=PRIMARY
        )
        self.private_emi_value.pack(anchor="w", pady=(4, 22))

        self.private_detail_label = tk.Label(
            private_card,
            text="",
            justify="left",
            bg=CARD_BG,
            fg=TEXT,
            font=("Consolas", 11),
            anchor="nw"
        )
        self.private_detail_label.pack(anchor="w")

        decision_panel = tk.Frame(
            summary_body,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=24,
            pady=22,
            width=360
        )
        decision_panel.pack(side="right", fill="y")
        decision_panel.pack_propagate(False)

        tk.Label(
            decision_panel,
            text="Decision Summary",
            font=("Arial", 13, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w")

        self.result_label = tk.Label(
            decision_panel,
            text="",
            font=("Arial", 18, "bold"),
            bg=CARD_BG,
            fg=SUCCESS,
            wraplength=300,
            justify="left"
        )
        self.result_label.pack(anchor="w", pady=(18, 8))

        self.reason_label = tk.Label(
            decision_panel,
            text="",
            font=("Arial", 10),
            bg=CARD_BG,
            fg=MUTED,
            wraplength=300,
            justify="left"
        )
        self.reason_label.pack(anchor="w")

        action_frame = tk.Frame(decision_panel, bg=CARD_BG)
        action_frame.pack(side="bottom", fill="x", pady=(24, 0))

        back_button = self.create_button(
            action_frame,
            "Back to Edit",
            SECONDARY,
            self.show_input_page,
            width=14
        )
        back_button.pack(fill="x", pady=(0, 10))
        Tooltip(back_button, "Return to the form without clearing values.")

        new_button = self.create_button(
            action_frame,
            "New Comparison",
            PRIMARY,
            self.reset_fields,
            width=14
        )
        new_button.pack(fill="x")
        Tooltip(new_button, "Clear all fields and start again.")

        graph_card = tk.Frame(
            charts_tab,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=22,
            pady=20,
            width=980,
            height=360
        )
        graph_card.pack(pady=(24, 0))
        graph_card.pack_propagate(False)

        self.fig = Figure(figsize=(8.8, 3.0), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        chart_insights_card = tk.Frame(
            charts_tab,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=22,
            pady=16,
            width=980,
            height=135
        )
        chart_insights_card.pack(pady=(16, 0))
        chart_insights_card.pack_propagate(False)

        tk.Label(
            chart_insights_card,
            text="Comparison Insights",
            font=("Arial", 13, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w")

        self.chart_insights_label = tk.Label(
            chart_insights_card,
            text="",
            font=("Arial", 12),
            bg=CARD_BG,
            fg=MUTED,
            justify="left"
        )
        self.chart_insights_label.pack(anchor="w", pady=(8, 0))

        details_shell = tk.Frame(details_tab, bg=APP_BG)
        details_shell.pack(fill="both", expand=True, pady=(18, 0))

        table_card = tk.Frame(
            details_shell,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=22,
            pady=20
        )
        table_card.pack(fill="both", expand=True)

        tk.Label(
            table_card,
            text="Metric Comparison",
            font=("Arial", 20, "bold"),
            bg=CARD_BG,
            fg=TEXT
        ).pack(anchor="w")

        tk.Label(
            table_card,
            text="Review the cost metrics and final recommendation for the selected banks.",
            font=("Arial", 12),
            bg=CARD_BG,
            fg=MUTED
        ).pack(anchor="w", pady=(6, 0))

        self.add_divider(table_card, pady=(18, 18))

        self.metric_table_frame = tk.Frame(
            table_card,
            bg=BORDER,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        self.metric_table_frame.pack(fill="x")

        self.add_divider(table_card, pady=(24, 18))

        recommendation_card = tk.Frame(
            table_card,
            bg=PANEL_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=16
        )
        recommendation_card.pack(fill="x")

        tk.Label(
            recommendation_card,
            text="Final Recommendation",
            font=("Arial", 13, "bold"),
            bg=PANEL_BG,
            fg=MUTED
        ).pack(anchor="w")

        self.final_recommendation_title = tk.Label(
            recommendation_card,
            text="-",
            font=("Arial", 20, "bold"),
            bg=PANEL_BG,
            fg=SUCCESS
        )
        self.final_recommendation_title.pack(anchor="w", pady=(8, 4))

        self.final_recommendation_detail = tk.Label(
            recommendation_card,
            text="",
            font=("Arial", 12),
            bg=PANEL_BG,
            fg=TEXT,
            justify="left",
            wraplength=950
        )
        self.final_recommendation_detail.pack(anchor="w")


if __name__ == "__main__":
    app = LoanComparisonApp()
    app.run()
