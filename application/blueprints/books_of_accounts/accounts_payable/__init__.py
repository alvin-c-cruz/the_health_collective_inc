app_name = "accounts_payable"
app_label = "Accounts Payable"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import AccountsPayable, AccountsPayableDetail
