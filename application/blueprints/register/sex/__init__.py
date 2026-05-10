app_name = "sex"
app_label = "Sex"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import Sex
