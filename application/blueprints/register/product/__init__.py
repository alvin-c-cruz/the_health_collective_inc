app_name = "product"
app_label = "Product"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import Product
