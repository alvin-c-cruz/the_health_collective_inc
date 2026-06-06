app_name = "disbursement"
app_label = "Disbursement"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Disbursement, DisbursementDetail
from .views import bp
