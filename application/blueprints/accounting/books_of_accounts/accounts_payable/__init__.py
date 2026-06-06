app_name = "accounts_payable"
app_label = "Accounts Payable"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import AccountsPayable, AccountsPayableDetail
from .views import bp
