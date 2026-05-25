from flask import Blueprint, render_template, current_app, g, request
from datetime import datetime

from .. user import login_required
from .extensions import get_dashboard_stats
from application.extensions import ph_today


bp = Blueprint('dashboard', __name__, template_folder="pages")


@bp.route("/", methods=["GET"])
@login_required
def home():
    # Get date from query parameter or default to today
    as_of_date_str = request.args.get('as_of_date')

    if as_of_date_str:
        try:
            as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
        except ValueError:
            as_of_date = ph_today()
    else:
        as_of_date = ph_today()

    context = get_dashboard_stats(as_of_date)
    return render_template("dashboard/home.html", **context)


@bp.route("/about")
@login_required
def about():
    return render_template("dashboard/about.html")


@bp.before_app_request
def set_g():
    g.company_name = current_app.config["COMPANY_NAME"]
