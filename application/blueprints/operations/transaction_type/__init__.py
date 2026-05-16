app_name = "transaction_type"
app_label = "Transaction Type"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
from .models import TransactionType
