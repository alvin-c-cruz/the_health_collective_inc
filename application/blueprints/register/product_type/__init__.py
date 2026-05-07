app_name = "product_type"
app_label = "Product Type"
menu_label = (app_name, f"/{app_name}", app_label)


from .views import bp
from .models import ProductType
