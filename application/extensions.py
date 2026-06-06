from datetime import datetime, timedelta

from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from zoneinfo import ZoneInfo

db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
migrate = Migrate()
login_manager = LoginManager()

_PH = ZoneInfo("Asia/Manila")


def ph_today():
    """Return the current date in Philippine time (UTC+8)."""
    return datetime.now(_PH).date()


def year_first_day():
    date_today = ph_today()
    return str(datetime(date_today.year, 1, 1))[:10]


def month_first_day():
    date_today = ph_today()
    return str(datetime(date_today.year, date_today.month, 1))[:10]


def year_last_day():
    date_today = ph_today()
    return str(datetime(date_today.year, 12, 31))[:10]


def month_last_day():
    date_today = ph_today()
    year = date_today.year
    month = date_today.month
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1

    first_day_of_next_month = datetime(year, month, 1)
    last_day = first_day_of_next_month - timedelta(days=1)
    return str(last_day)[:10]


import re


def next_control_number(obj, control_number_field, record_date=None):
    record = obj.query.order_by(getattr(obj, control_number_field).desc()).first()

    if not record:
        return "00001"

    last_number = getattr(record, control_number_field)

    # Check if last character is a letter
    if last_number[-1].isalpha():
        return f"{last_number}-001"

    # Match and split by last numeric sequence
    match = re.search(r"(\d+)$", last_number)
    if match:
        num_str = match.group(1)
        prefix = last_number[: -len(num_str)]
        num_len = len(num_str)
        new_num = int(num_str) + 1
        return f"{prefix}{str(new_num).zfill(num_len)}"

    # Fallback: treat as pure number
    try:
        num_len = len(last_number)
        new_num = int(last_number) + 1
        return str(new_num).zfill(num_len)
    except ValueError:
        # If it’s not a number at all, start from -001
        return f"{last_number}-001"


def long_date(str_date):
    dte_date = datetime.strptime(str_date, "%Y-%m-%d")
    dte_date = datetime.strftime(dte_date, "%B %d, %Y")
    return dte_date


def short_date(str_date):
    dte_date = datetime.strptime(str_date, "%Y-%m-%d")
    dte_date = datetime.strftime(dte_date, "%d-%b-%Y")
    return dte_date
