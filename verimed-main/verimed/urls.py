from django.urls import path
# from .views import*
from . import views
from .views import VerimedCountrycode,VerimedDepartmentCreateUpdate,VerimedBookAppoinmentCreateUpdate,AppoinmentStatusChoices,VB_PatientAppoinment_List,VB_DoctorAppoinment_List,UserCreate,UserUpdate,UserDelete,UserLogin,UserLogout,SponsorProfileList,PatientProfileList,DoctorProfileList,CareTakerProfileList,UserChoices,UserSignup,UserEmailVerify,UserView,DoctorProfileUpdate,PatientProfileCreateUpdate,SponsorProfileUpdate,CaretakerProfileUpdate,DoctorReportsCRUD,SponsoridPatientProfileList,ContactUsC,ContactUsRD,SponsoridPatientProfileDelete,KetnyproductionCheckC,KetnyproductionCheckRD,UserUpdateUser

urlpatterns = [
    path('verimed_countrycode/', VerimedCountrycode.as_view(), name='verimed_department_create'),


    path('verimed_department_create_update/', VerimedDepartmentCreateUpdate.as_view(), name='verimed_department_create'),
    
    path('appoinmentstatus_choices/',AppoinmentStatusChoices.as_view()),
    path('verimed_bookappoinment_create_update/',VerimedBookAppoinmentCreateUpdate.as_view(),name='VerimedBookAppoinment'),
    path('vb_patientappoinment_list/',VB_PatientAppoinment_List.as_view()),
    path('vb_doctorappoinment_list/',VB_DoctorAppoinment_List.as_view()),

    
    
    # login
    path("user_create/",UserCreate.as_view(),name="user_create"),
    path("user_update/",UserUpdate.as_view(),name="user_update"),
    path("user_delete/",UserDelete.as_view(),name="user_delete"),
    path("user_login/",UserLogin.as_view(),name="user_login"),
    path("user_logout/",UserLogout.as_view(),name="user_logout"),
    path("user_update_user/",UserUpdateUser.as_view(),name="user_update"),

    
    path("sponsorprofile_list/",SponsorProfileList.as_view(),name="sponsorprofile_list"),
    path("sponsorprofile_update/",SponsorProfileUpdate.as_view(),name="patientprofile_list"),
    # path("sponsor_patients_view/",SponsorPatientsView.as_view(),name="SponsorProfile"),

    
    path("patientprofile_list/",PatientProfileList.as_view(),name="patientprofile_list"),
    path("patientprofile_create_update/",PatientProfileCreateUpdate.as_view(),name="patientprofile_create_update"),
    path("sponsorid_patientprofile_list/",SponsoridPatientProfileList.as_view(),name="sponsorid_patientprofile_list"),
    path("sponsorid_patientprofile_delete/",SponsoridPatientProfileDelete.as_view(),name="sponsorid_patientprofile_list"),



    path("doctorprofile_list/",DoctorProfileList.as_view(),name="doctorprofile_list"),
    path("doctorprofile_update/",DoctorProfileUpdate.as_view(),name="doctorprofile_update"),
    
    path("caretakerprofile_list/",CareTakerProfileList.as_view(),name="caretakerprofile_list"),
    path("caretakerprofile_update/",CaretakerProfileUpdate.as_view(),name="caretakerprofile_update"),

    # doctor reports
    path("doctor_reports_curd/",DoctorReportsCRUD.as_view(),name="doctor_reports_curd"),
    
    # contactus
    path("contactus_c/",ContactUsC.as_view(),name="contactus_c"),
    path("contactus_rd/",ContactUsRD.as_view(),name="contactus_rd"),

    # ketnycheckform
    
    path("ketnyproductioncheck_c/",KetnyproductionCheckC.as_view(),name="contactus_rd"),
    path("ketnyproductioncheck_rd/",KetnyproductionCheckRD.as_view(),name="contactus_rd"),

    
    # payment urls
    path("payment/", views.payment_page, name="payment"),
    path("create-checkout-session/", views.create_checkout_session, name="create_checkout"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    # choices
    path("user_choices/",UserChoices.as_view()),

    # Endpoint to submit signup data and send verification email
    path('user-signup/', UserSignup.as_view(), name='sponsor-signup'),

    # Endpoint to verify email and create the user
    path('verify-email/', UserEmailVerify.as_view(), name='verify-email'),

    #    
   path('user_view/',UserView.as_view())
] 