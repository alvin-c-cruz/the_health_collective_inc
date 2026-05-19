app_name = "reports"
app_label = "Reports"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
