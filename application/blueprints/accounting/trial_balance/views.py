from flask import Blueprint, render_template
from flask_login import login_required, current_user

from .extensions import trial_balance_dataframe
from .. account import Account


bp = Blueprint("trial_balance", __name__, template_folder="pages", url_prefix="/trial_balance")


@bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    accounts = [i for _, i in trial_balance_dataframe(2025).iterrows()]
    
    context = {
        "accounts": accounts,
        "report_year": 2025
    }
    
    return render_template("trial_balance/home.html", **context)
