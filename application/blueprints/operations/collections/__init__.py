app_name = "collections"
app_label = "Collections"
menu_label = (app_name, f"/{app_name}", app_label)

from .views import bp
from .models import Collection, CollectionDetail
