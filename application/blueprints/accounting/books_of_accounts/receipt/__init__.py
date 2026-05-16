app_name = "receipt"
app_label = "Receipt"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import Receipt, ReceiptDetail
