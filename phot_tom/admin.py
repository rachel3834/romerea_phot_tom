from django.contrib import admin
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import TargetExtra

admin.site.register(ReducedDatum)
admin.site.register(TargetExtra)
