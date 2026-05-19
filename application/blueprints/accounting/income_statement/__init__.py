app_name = "income_statement"
app_label = "Income Statement"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
