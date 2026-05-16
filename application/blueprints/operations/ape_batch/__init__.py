app_name = "ape_batch"
app_label = "APE Batch"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
from .models import ApeBatch
