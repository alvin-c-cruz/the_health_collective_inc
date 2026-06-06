app_name = "company"
app_label = "Company"
menu_label = (app_name, f"/{app_name}", app_label)

from .models import Company
from .views import bp
