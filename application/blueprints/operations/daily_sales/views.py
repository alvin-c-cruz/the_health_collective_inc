from flask import Blueprint, render_template, request
from datetime import date
from dataclasses import dataclass

from ...user import login_required, roles_accepted

from . import app_label, app_name

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    summary = Summary()
    
    context = {
        "app_label": app_label,
        "today": date.today(),
        "summary": summary,
    }
    return render_template("daily_sales/home.html", **context)


@bp.route('/transaction/new', methods=['GET'])
def new_transaction():
    transaction_type = request.args.get('type')  # gets 'walk_in' from ?type=walk_in
    return render_template('daily_sales/new_transaction.html', transaction_type=transaction_type)


@bp.route('/deposit/new', methods=['GET'])
def record_deposit():
    return render_template('record_deposit.html')


@bp.route("/daily_report", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def daily_report():
    prev_report = Report()
    prev_report.report_date = date(2026, 4, 24)
    prev_report.hmo_sales = {
        "Hive Health": 0.00,
        "Gcash / Bank Transfer": 200.00,
        }
    prev_report.home_service_sales = {
        "Gcash / Bank Transfer": 1200.00
        }
    
    
    curr_report = Report()
    curr_report.report_date = date(2026, 4, 25)
    curr_report.hmo_sales = {
        "Asian Care": 1000.00,
    }
    curr_report.home_service_sales = {
        "Gcash / Bank Transfer": 300.00
    }
    curr_report.walk_in_sales = {
        "Gcash / Bank Transfer": 0.00,
        "Credit Card": 0.00,
        "Cash": 1540.00
    }

    hmos = [
        {"hmo_name": "Hive Health", "receivable": "0.00"},
        {"hmo_name": "Dynamic Care", "receivable": "0.00"},
        {"hmo_name": "Forticare", "receivable": "0.00"},
        {"hmo_name": "Asian Care", "receivable": "0.00"},
        {"hmo_name": "Philhealth", "receivable": "0.00"},
        {"hmo_name": "Gcash / Bank Transfer", "receivable": "0.00"},
        {"hmo_name": "Cash", "receivable": "0.00"}
    ]

    context = {
        "prev_report": prev_report,
        "curr_report": curr_report,
        "hmos": hmos,
        "app_label": app_label,
    }
    return render_template("daily_sales/daily_sales_report.html", **context)


class Report:
    report_date: date
    hmo_sales: dict[str, float] = {}
    home_service_sales: dict[str, float] = {}
    walk_in_sales: dict[str, float] = {}
    total_diagnostic_sales: float = 0.00
    
    dialysis_sales: dict[str, float] = {}
    total_dialysis_sales: float = 0.00
    
    @property
    def total_sales(self):
        total = self.dialysis_sales + self.total_diagnostic_sales
        return total
    

class Summary:
    total_sales: float = 0.00
    cash_on_hand: float = 0.00