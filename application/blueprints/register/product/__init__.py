app_name = "product"
app_label = "Product"
menu_label = (app_name, f"/{app_name}", app_label)


from .models import Product
from .views import bp
