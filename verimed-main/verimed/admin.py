from django.contrib import admin

# Register your models here.
from .models import VerimedCountryCode,VerimedDepartment,VerimedBookAppointmentLabReports,VerimedBookAppointment,User,SponsorProfile,DoctorProfile,CareTakerProfile,PatientProfile,SponsorID,CaretakerID,DoctorID,PatientID,AdminID,EmailVerificationToken,DoctorReports,PatientUploadDocuments,Order
from rest_framework.authtoken.models import Token
from django.contrib.sessions.models import Session

admin.site.register(Token)
admin.site.register(Session)


admin.site.register(VerimedCountryCode)
admin.site.register(VerimedDepartment)
admin.site.register(VerimedBookAppointmentLabReports)
admin.site.register(VerimedBookAppointment)
admin.site.register(User)
admin.site.register(SponsorProfile)
admin.site.register(DoctorProfile)
admin.site.register(CareTakerProfile)
admin.site.register(PatientProfile)
admin.site.register(SponsorID)
admin.site.register(CaretakerID)
admin.site.register(DoctorID)
admin.site.register(PatientID)
admin.site.register(AdminID)
admin.site.register(EmailVerificationToken)
admin.site.register(DoctorReports)  
admin.site.register(PatientUploadDocuments)
admin.site.register(Order)  



