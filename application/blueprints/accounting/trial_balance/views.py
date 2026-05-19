from flask import Blueprint, render_template, request, send_file
from flask_login import login_required, current_user
from datetime import datetime
import pandas as pd
import io

from .extensions import trial_balance_dataframe
from .. account import Account


bp = Blueprint("trial_balance", __name__, template_folder="pages", url_prefix="/trial_balance")


@bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    # Get date parameter (default to current year)
    date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        report_date = datetime.strptime(date_param, '%Y-%m-%d')
        report_year = report_date.year
    except:
        report_year = datetime.now().year

    accounts = [i for _, i in trial_balance_dataframe(report_year).iterrows()]

    context = {
        "accounts": accounts,
        "report_year": report_year,
        "report_date": report_date if 'report_date' in locals() else datetime.now()
    }

    # Check if AJAX request
    if request.args.get('ajax') == '1':
        return render_template("trial_balance/view.html", **context)

    return render_template("trial_balance/home.html", **context)


@bp.route("/download_excel", methods=["GET"])
@login_required
def download_excel():
    # Get date parameter
    date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        report_date = datetime.strptime(date_param, '%Y-%m-%d')
        report_year = report_date.year
    except:
        report_year = datetime.now().year

    # Get the dataframe
    df = trial_balance_dataframe(report_year)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Trial Balance', index=False)
    output.seek(0)

    # Send file
    filename = f"trial_balance_{date_param}.xlsx"
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
