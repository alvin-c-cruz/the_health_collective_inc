app_name = "receipt"
app_label = "Receipt"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Receipt, ReceiptDetail
from .views import bp
