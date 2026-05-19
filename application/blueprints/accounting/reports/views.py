from flask import Blueprint, render_template
from flask_login import login_required
from datetime import date


bp = Blueprint("reports", __name__, template_folder="pages", url_prefix="/reports")


@bp.route("/", methods=["GET"])
@login_required
def home():
    """
    Reports Hub - Central location for all financial reports
    """
    today = date.today()

    context = {
        "today": today,
    }

    return render_template("reports/home.html", **context)
