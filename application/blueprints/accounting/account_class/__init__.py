app_name = "account_class"
app_label = "Account Class"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import AccountClass
from .views import bp
