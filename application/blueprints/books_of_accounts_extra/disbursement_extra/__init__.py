app_name = "disbursement_extra"
app_label = "Disbursement Extra"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import DisbursementExtra, DisbursementExtraDetail
