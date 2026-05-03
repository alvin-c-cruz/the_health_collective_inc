app_name = "receipt_extra"
app_label = "Receipt Extra"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import ReceiptExtra, ReceiptExtraDetail
