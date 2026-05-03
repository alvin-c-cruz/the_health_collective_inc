app_name = "accounts_payable_extra"
app_label = "Accounts Payable Extra"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import AccountsPayableExtra, AccountsPayableExtraDetail
