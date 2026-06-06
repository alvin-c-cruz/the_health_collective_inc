app_name = "measure"
app_label = "Measure"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Measure
from .views import bp
