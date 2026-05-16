app_name = "sales_extra"
app_label = "Sales Extra"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import SalesExtra, SalesExtraDetail
