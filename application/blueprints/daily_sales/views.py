from flask import Blueprint, render_template
from datetime import date
from dataclasses import dataclass

from .. user import login_required, roles_accepted

from . import app_label, app_name

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    return render_template("daily_sales/home.html", app_label=app_label)


@bp.route("/daily_report", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def daily_report():
    prev_report = Report()
    prev_report.report_date = date(2026, 4, 24)
    prev_report.total_sales = 2482.00
    prev_report.hmo_sales = {
        "Hive Health": 0.00,
        "Gcash / Bank Transfer": 200.00,
        }
    
    
    curr_report = Report()
    curr_report.report_date = date(2026, 4, 25)
    curr_report.total_sales = 1540.00
    curr_report.hmo_sales = {
        "Asian Care": 1000.00,

    }

    hmos = [
        {"hmo_name": "Hive Health", "receivable": "0.00"},
        {"hmo_name": "Dynamic Care", "receivable": "0.00"},
        {"hmo_name": "Forticare", "receivable": "0.00"},
        {"hmo_name": "Asian Care", "receivable": "0.00"},
        {"hmo_name": "Philhealth", "receivable": "431,800.00"},
        {"hmo_name": "Gcash / Bank Transfer", "receivable": "0.00"},
        {"hmo_name": "Cash", "receivable": "0.00"}
    ]

    context = {
        "prev_report": prev_report,
        "curr_report": curr_report,
        "hmos": hmos,
        "app_label": app_label
    }
    return render_template("daily_sales/daily_sales_report.html", **context)


class Report:
    report_date: date
    total_sales: float
    hmo_sales: dict[str, float] = {}
