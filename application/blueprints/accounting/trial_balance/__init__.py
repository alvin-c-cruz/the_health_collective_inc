app_name = "trial_balance"
app_label = "Trial Balance"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
