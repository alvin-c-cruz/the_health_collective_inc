app_name = "general"
app_label = "General"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import General, GeneralDetail
