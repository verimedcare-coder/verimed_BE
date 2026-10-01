from django.db import models

# Create your models here.
class FieldsControlClassInfo(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    code = models.CharField(max_length=50,unique=True,null=True,blank=True)
    url_name=models.CharField(max_length=100,null=True,blank=True)
    app_name=models.CharField(max_length=50,null=True,blank=True)
    model_name=models.CharField(max_length=100,null=True,blank=True)
    view_class_name=models.CharField(max_length=100,null=True,blank=True)
    class Meta:
        db_table='fieldscontrol_class_info'
    def __str__(self):
        return f"{self.id}-{self.name}"

    
class FieldsControlFields(models.Model):
    class_info=models.ForeignKey("FieldsControlClassInfo",on_delete=models.SET_NULL,null=True,blank=True)
    field_name=models.CharField(max_length=100,null=True,blank=True)
    display_name=models.CharField(max_length=100,null=True,blank=True)
    fields_control=models.TextField(null=True,blank=True)
    view_class_name=models.CharField(max_length=100,null=True,blank=True)

    class Meta:
        db_table='fieldscontrol_fields'
    def __str__(self):
        return f"{self.id}-{self.class_info}-{self.field_name}-{self.display_name}"
    
    
class FieldsControlCode(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    code=models.CharField(max_length=70,null=True,blank=True)
    remarks=models.TextField(null=True,blank=True)
    class Meta:
        db_table='fieldscontrol_code'
    def __str__(self):
        return f"{self.id}-{self.name}-{self.code}"
    
class FieldsControlErrors(models.Model):
    error_code=models.CharField(max_length=20,unique=True,null=True,blank=True)
    error_name=models.CharField(max_length=100,null=True,blank=True)
    error_descriptions=models.TextField(null=True,blank=True)
    class Meta:
        db_table='fieldscontrol_errors'
    def __str__(self):
        return f"{self.id}-{self.error_code}-{self.error_name}"