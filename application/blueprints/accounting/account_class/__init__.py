app_name = "account_class"
app_label = "Account Class"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import AccountClass
