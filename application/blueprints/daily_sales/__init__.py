app_name = "daily_sales"
app_label = "Daily Sales"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
