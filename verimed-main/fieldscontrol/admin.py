from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(FieldsControlClassInfo)
admin.site.register(FieldsControlFields)
admin.site.register(FieldsControlCode)
admin.site.register(FieldsControlErrors)



