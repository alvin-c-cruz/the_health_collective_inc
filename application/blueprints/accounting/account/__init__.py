app_name = "account"
app_label = "Account"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Account
from .views import bp
