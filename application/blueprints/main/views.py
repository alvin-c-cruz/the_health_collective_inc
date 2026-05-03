from flask import Blueprint, render_template, current_app, g, request
from datetime import date, datetime

from .. user import login_required

from .extensions import get_account_balance_summary


bp = Blueprint('main', __name__, template_folder="pages")


@bp.route("/", methods=["GET"])
@login_required
def home():
    report_date_str = request.args.get("report_date")
    
    if report_date_str:
        try:
            report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
        except ValueError:
            report_date = date.today()
    else:
        report_date = date.today()

    summary = get_account_balance_summary(report_date)

    context = {
        "summary": summary,
        "report_date": report_date.strftime("%Y-%m-%d"),
    }

    return render_template("main/home.html", **context)


@bp.before_app_request
def set_g():
    g.company_name = current_app.config["COMPANY_NAME"]
