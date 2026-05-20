from flask import Blueprint, render_template, current_app, g

from .. user import login_required
from .extensions import get_dashboard_stats
from application.extensions import ph_today


bp = Blueprint('dashboard', __name__, template_folder="pages")


@bp.route("/", methods=["GET"])
@login_required
def home():
    today = ph_today()
    context = get_dashboard_stats(today)
    return render_template("dashboard/home.html", **context)


@bp.route("/about")
@login_required
def about():
    return render_template("dashboard/about.html")


@bp.before_app_request
def set_g():
    g.company_name = current_app.config["COMPANY_NAME"]
