app_name = "general"
app_label = "General"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import General, GeneralDetail
from .views import bp
