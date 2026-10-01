from django.urls import path
from .views import FieldsControlClassInfoCreate,FieldsControlCodeView,FieldsControlClassInfoDelete,FieldsControlFieldsDelete

urlpatterns = [
    path('validate_field_validation/', FieldsControlClassInfoCreate.as_view()),
    path('validations_code/', FieldsControlCodeView.as_view(), name='validations_code'),
    path('page_info_delete/<int:id>/', FieldsControlClassInfoDelete.as_view()),
    path('field_validation_delete/', FieldsControlFieldsDelete.as_view()),
    # path('validatefieldfalidation_pageinfoview/',ValidateFieldValidationPageInfoView.as_view()),
]