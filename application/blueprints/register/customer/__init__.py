app_name = "customer"
app_label = "Customer"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Customer
from .views import bp
