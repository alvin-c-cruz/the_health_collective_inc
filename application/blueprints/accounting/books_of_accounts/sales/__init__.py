app_name = "sales"
app_label = "Sales"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Sales, SalesDetail
from .views import bp
