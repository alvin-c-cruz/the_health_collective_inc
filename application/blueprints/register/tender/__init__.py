app_name = "tender"
app_label = "Tender"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Tender
from .views import bp
