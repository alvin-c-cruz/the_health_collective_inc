app_name = "balance_sheet"
app_label = "Balance Sheet"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
