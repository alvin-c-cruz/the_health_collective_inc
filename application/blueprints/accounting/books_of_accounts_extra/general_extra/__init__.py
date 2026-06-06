app_name = "general_extra"
app_label = "General Extra"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import GeneralExtra, GeneralExtraDetail
from .views import bp
