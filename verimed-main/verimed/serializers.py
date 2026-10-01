from rest_framework import serializers
from .models import VerimedCountryCode,VerimedDepartment,VerimedBookAppointment,User,DoctorProfile,CareTakerProfile,PatientProfile,SponsorProfile,DoctorReports,ContactUs,KetnyproductionCheck
from django.conf import settings

class VerimedCountryCodeViewSlr(serializers.ModelSerializer):
    class Meta:
        model = VerimedCountryCode
        fields = '__all__'
        

  
class UserViewSlr(serializers.ModelSerializer):
    country_code_id = serializers.SerializerMethodField()
    country_code = serializers.SerializerMethodField()
    photo_view_url = serializers.SerializerMethodField()
    photo_download_url = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = ["id","username","first_name","last_name","email","country_code_id","country_code","phone","user_role","is_active_state","photo_view_url","photo_download_url"]
        
    def get_country_code_id(self, obj):
        return obj.country_code.id if obj.country_code else None

    def get_country_code(self, obj):
        return obj.country_code.code if obj.country_code else None

    def get_photo_view_url(self, obj):
        request = self.context.get("request")
        if obj.photo:
            # photo_url = obj.photo.url
            # return request.build_absolute_uri(photo_url) if request else f"{settings.MEDIA_URL}{photo_url}"
            return f"{settings.FRONTEND_URL}{obj.photo.url}?download=true"
        return None

    def get_photo_download_url(self, obj):
        if obj.photo:
            return f"{settings.FRONTEND_URL}{obj.photo.url}?download=true"
        return None
    
    

class VerimedDepartmentViewSlr(serializers.ModelSerializer):
    country_code_id = serializers.SerializerMethodField()
    country_code = serializers.SerializerMethodField()
    class Meta:
        model = VerimedDepartment
        fields = ["id","dep_name","dep_type","contact_email","country_code_id","country_code","contact_phone","address","description","dep_ID","status","doctor","dep_city","dep_state","dep_country","dep_pincode"]
    
    def get_country_code_id(self, obj):
        return obj.country_code.id if obj.country_code else None

    def get_country_code(self, obj):
        return obj.country_code.code if obj.country_code else None


class DoctorProfileViewSlr(serializers.ModelSerializer):
    user = UserViewSlr(read_only=True)
    dep = VerimedDepartmentViewSlr(read_only=True)
    doc_country_code_id = serializers.SerializerMethodField()
    doc_country_code = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "doctor_verified", "doctor_id", "doc_exprience", "doc_gender",
            "speciality", "doc_phone", "joining_date", "doc_licence_no",
            "doc_address", "doc_city", "doc_state", "doc_country", "doc_pincode",
            "user", "dep", "doc_country_code_id", "doc_country_code"
        ]
        # fields = '__all__'
        
    def get_doc_country_code_id(self, obj):
        return obj.doc_country_code.id if obj.doc_country_code else None

    def get_doc_country_code(self, obj):
        return obj.doc_country_code.code if obj.doc_country_code else None


class PatientProfileViewSlr(serializers.ModelSerializer):
    # user = UserViewSlr(read_only=True)
    
    photo_view_url = serializers.SerializerMethodField()
    photo_download_url = serializers.SerializerMethodField()

    
    country_code_id = serializers.SerializerMethodField()
    country_code = serializers.SerializerMethodField()
    
    
    emer_country_code_id = serializers.SerializerMethodField()
    emer_country_code = serializers.SerializerMethodField()
    
    local_con_country_code_id = serializers.SerializerMethodField()
    local_con_country_code = serializers.SerializerMethodField()

    
    class Meta:
        model = PatientProfile
        fields = [
            "id",
            "sponsor",
            "caretaker",
            "patient_name",
            "country_code_id",
            "country_code",
            "phone",
            "email",
            "age",
            "height",
            "weight",
            "blood_pressure",
            "blood_sugar",
            "heart_rate",
            "oxygen",
            "temperature",
            "respiratory_rate",
            "photo_view_url",
            "photo_download_url",
            "patient_verified",
            "patient_dob",
            "patient_gender",
            "blood_group",
            "patient_home_address",
            "primary_language",
            "religion",
            "escalate_to_physician",
            # Emergency Contact
            "emer_con_name",
            "emer_con_relation",
            "emer_con_coun_of_residen",
            "emer_country_code_id",
            "emer_country_code",
            "emer_con_phone",
            "emer_con_email",
            # Local Contact
            "local_con_name",
            "local_con_relation",
            "local_con_country_code_id",
            "local_con_country_code",
            "local_con_phone",
            # Reason for Enrollment
            "reason_enrollment",
            "reason_other",
            # Medical History
            "medical_his_diagnosis",
            "medical_his_cancer",
            "medical_his_other",
            "medical_his_provided_medi_care",
            "medical_his_major_surgeries",
            "medical_his_curr_symp",
            # Medication
            "medication",
            # "medication_name",
            # "medication_dose",
            # "medication_frequency",
            # "medication_reason",
            # "medication_issues",
            # "medication_issues_explain",
            # Allergies
            "allergies_issues",
            "allergies_drug",
            "allergies_food",
            # Functional Abilities
            "functional_bathe",
            "functional_dress",
            "functional_eat",
            "functional_walk",
            "functional_use_bathroom",
            "functional_daily_activity",
            "functional_manage_finance",
            "functional_any_falls",
            "functional_how_many",
            "functional_memory_pbms",
            # Lifestyle
            "lifestyle_daily_routine",
            "lifestyle_dietary_habits",
            "lifestyle_sleep_quality",
            "lifestyle_physical_activity",
            "lifestyle_alcohol_use",
            "lifestyle_pain_complaints",
            "lifestyle_pain_where",
            # Social and Emotional
            "social_emotion_health",
            "social_spiritual_needs",
            "social_trusted_person",
            "social_name",
            # Goals
            "goals_family_hope",
            "goals_special_instructions",
            "goals_term_membership",
        ]
    
    def get_country_code_id(self, obj):
        return obj.country_code.id if obj.country_code else None

    def get_country_code(self, obj):
        return obj.country_code.code if obj.country_code else None
    
        
    def get_emer_country_code_id(self, obj):
        return obj.emer_con_country_code.id if obj.emer_con_country_code else None

    def get_emer_country_code(self, obj):
        return obj.emer_con_country_code.code if obj.emer_con_country_code else None
    
    def get_local_con_country_code_id(self, obj):
        return obj.local_con_country_code.id if obj.local_con_country_code else None

    def get_local_con_country_code(self, obj):
        return obj.local_con_country_code.code if obj.local_con_country_code else None

   
    
    def get_photo_view_url(self, obj):
        request = self.context.get("request")

        if not obj.photo:
            return None

        if request:
            return request.build_absolute_uri(obj.photo.url)

        return f"{settings.FRONTEND_URL}{obj.photo.url}"


    def get_photo_download_url(self, obj):
        request = self.context.get("request")

        if not obj.photo:
            return None

        download_url = f"{obj.photo.url}?download=true"

        if request:
            return request.build_absolute_uri(download_url)

        return f"{settings.FRONTEND_URL}{download_url}"
        # fields = "__all__"



class VerimedDepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerimedDepartment
        fields = '__all__'


class SponsorProfileViewSlr(serializers.ModelSerializer):
    user = UserViewSlr(read_only=True)
    
    class Meta:
        model = SponsorProfile
        fields = '__all__'


# class DoctorProfileViewSlr(serializers.ModelSerializer):
#     class Meta:
#         model = DoctorProfile
#         fields = '__all__'


class CareTakerProfileViewSlr(serializers.ModelSerializer):
    # class Meta:
    #     model = CareTakerProfile
    #     fields = '__all__'
    user = UserViewSlr(read_only=True)
    
    class Meta:
        model = CareTakerProfile
        fields = [
            "id", "caretaker_verified", "caretaker_id", "caretaker_address",
            "caretaker_exprience", "care_gender", "credentials", "yr_of_graduation",
            "skillset", "title",
            "user"
        ]
        # fields = '__all__'
        
    


# class PatientProfileViewSlr(serializers.ModelSerializer):
#     class Meta:
#         model = PatientProfile
#         fields = '__all__'





class VerimedBookAppointmentViewSlr(serializers.ModelSerializer):
    # Expand related foreign key data
    sponsor = SponsorProfileViewSlr(read_only=True)
    dep = VerimedDepartmentSerializer(read_only=True)
    doc = DoctorProfileViewSlr(read_only=True)
    patient = PatientProfileViewSlr(read_only=True)
    caretaker = CareTakerProfileViewSlr(read_only=True)

    class Meta:
        model = VerimedBookAppointment
        fields = '__all__'



class DoctorReportsViewSlr(serializers.ModelSerializer):

    class Meta:
        model = DoctorReports
        fields = '__all__'
        
class ContactUsViewSlr(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = '__all__'
        
class KetnyproductionCheckViewSlr(serializers.ModelSerializer):
    class Meta:
        model = KetnyproductionCheck
        fields = '__all__'
        