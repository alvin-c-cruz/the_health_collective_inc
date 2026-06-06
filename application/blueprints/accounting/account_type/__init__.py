app_name = "account_type"
app_label = "Account Type"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import AccountType
from .views import bp
