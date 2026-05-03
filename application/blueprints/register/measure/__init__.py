app_name = "measure"
app_label = "Measure"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import Measure
