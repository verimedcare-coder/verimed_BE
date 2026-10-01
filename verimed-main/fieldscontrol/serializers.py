from rest_framework import serializers
from .models import FieldsControlCode,FieldsControlFields

class ValidationsCodeSlr(serializers.ModelSerializer):
    class Meta:
        model = FieldsControlCode
        fields = '__all__'
        

class ValidateFieldValidationPageInfoSlr(serializers.ModelSerializer):
    pageinfo_id = serializers.SerializerMethodField()
    pageinfo_name = serializers.SerializerMethodField()
    pageinfo_code = serializers.SerializerMethodField()
    pageinfo_url_name = serializers.SerializerMethodField()
    pageinfo_app_name = serializers.SerializerMethodField()
    pageinfo_model_name = serializers.SerializerMethodField()
    pageinfo_view_class_name = serializers.SerializerMethodField()
    pageinfo_lock = serializers.SerializerMethodField()
    pageinfo_flag = serializers.SerializerMethodField()
    pageinfo_createvia = serializers.SerializerMethodField()
    pageinfo_create_User = serializers.SerializerMethodField()
    pageinfo_update_User = serializers.SerializerMethodField()

    class Meta:
        model = FieldsControlFields
        fields = [
            "id",
            "pageinfo_id", "pageinfo_name", "pageinfo_code", "pageinfo_url_name",
            "pageinfo_app_name", "pageinfo_model_name", "pageinfo_view_class_name",
            "pageinfo_lock", "pageinfo_flag", "pageinfo_createvia",
            "pageinfo_create_User", "pageinfo_update_User",
            "field_name", "display_name", "validation", "verify_order",
            "lock", "flag", "createvia", "create_User", "update_User"
        ]

    def get_pageinfo_id(self, obj):
        return getattr(obj.page_info, "id", None)

    def get_pageinfo_name(self, obj):
        return getattr(obj.page_info, "name", None)

    def get_pageinfo_code(self, obj):
        return getattr(obj.page_info, "code", None)

    def get_pageinfo_url_name(self, obj):
        return getattr(obj.page_info, "url_name", None)

    def get_pageinfo_app_name(self, obj):
        return getattr(obj.page_info, "app_name", None)

    def get_pageinfo_model_name(self, obj):
        return getattr(obj.page_info, "model_name", None)

    def get_pageinfo_view_class_name(self, obj):
        return getattr(obj.page_info, "view_class_name", None)

    def get_pageinfo_lock(self, obj):
        return getattr(obj.page_info, "lock", None)

    def get_pageinfo_flag(self, obj):
        return getattr(obj.page_info, "flag", None)

    def get_pageinfo_createvia(self, obj):
        return getattr(obj.page_info, "createvia", None)

    def get_pageinfo_create_User(self, obj):
        return getattr(obj.page_info, "create_User", None)

    def get_pageinfo_update_User(self, obj):
        return getattr(obj.page_info, "update_User", None)