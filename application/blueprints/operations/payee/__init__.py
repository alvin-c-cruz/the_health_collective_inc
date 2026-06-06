app_name = "payee"
app_label = "Payee"
menu_label = (app_name, f"/{app_name}", app_label)

from application.blueprints.operations.daily_sales.models import Payee

from .views import bp
