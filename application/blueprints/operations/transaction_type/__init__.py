app_name = "transaction_type"
app_label = "Service Types"
menu_label = (app_name, f"/{app_name}", app_label)

from .models import TransactionType
from .views import bp
