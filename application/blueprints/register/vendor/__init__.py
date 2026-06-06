app_name = "vendor"
app_label = "Vendor"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Vendor
from .views import bp
