app_name = "bank_account"
app_label = "Bank Account"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
from .models import BankAccount
