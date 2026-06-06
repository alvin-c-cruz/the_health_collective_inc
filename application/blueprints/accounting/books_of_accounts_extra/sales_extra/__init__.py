app_name = "sales_extra"
app_label = "Sales Extra"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import SalesExtra, SalesExtraDetail
from .views import bp
