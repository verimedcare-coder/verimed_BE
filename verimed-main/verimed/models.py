from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone


class VerimedCountryCode(models.Model):
    name = models.CharField(max_length=100, unique=True,null=False,default="Unknown")
    flag = models.CharField(max_length=10,null=True,blank=True)  # Storing emojis as text
    code = models.CharField(max_length=10, unique=True,null=False)
    dial_code = models.CharField(max_length=10,null=False,default='+000')
    
    class Meta:
        db_table = 'verimed_countrycode'

    def __str__(self):
        return f"{self.id}-{self.name}"

class VerimedDepartment(models.Model):
    dep_name = models.CharField(max_length=100, null=True, blank=True)
    dep_type = models.CharField(max_length=100, null=True, blank=True)
    contact_email = models.EmailField(null=True, blank=True)
    country_code = models.ForeignKey("VerimedCountryCode", on_delete=models.SET_NULL, null=True, blank=True)
    contact_phone = models.CharField(max_length=25, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    dep_ID = models.CharField(max_length=100, null=True, blank=True)  # corrected
    status = models.CharField(max_length=100, null=True, blank=True)
    doctor = models.ForeignKey("DoctorProfile", on_delete=models.SET_NULL, null=True, blank=True)
    dep_city = models.CharField(max_length=100, null=True, blank=True)
    dep_state = models.CharField(max_length=100, null=True, blank=True)
    dep_country = models.CharField(max_length=100, null=True, blank=True)
    dep_pincode = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "verimed_department"

    def __str__(self):
        return f"{self.id}-{self.dep_name}"


APPOINTMENT_STATUS = (
    ('Pending', 'Pending'),
    ('Confirmed', 'Confirmed'),
    ('InProgress', 'In Progress'),
    ('Completed', 'Completed'),
    ('Expired', 'Expired'),
)
class VerimedBookAppointmentLabReports(models.Model):
    appointment = models.ForeignKey(
        "VerimedBookAppointment",
        on_delete=models.SET_NULL,
        related_name="verimed_bookappointment_lab_reports_appointment",
        null=True, blank=True
    )
    file = models.FileField(upload_to="lab_reports/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    patient = models.ForeignKey("PatientProfile", on_delete=models.SET_NULL, null=True, blank=True)
    referid = models.CharField(max_length=150,null=True,blank=True)


    class Meta:
        db_table = "verimed_book_appoinments_labreports"

    def __str__(self):
        return f"{self.id}-{self.appointment}-{self.uploaded_at}"

    

class VerimedBookAppointment(models.Model):
    sponsor = models.ForeignKey("SponsorProfile", on_delete=models.SET_NULL, null=True, blank=True)
    dep = models.ForeignKey("VerimedDepartment", on_delete=models.SET_NULL, null=True, blank=True)
    doc = models.ForeignKey("DoctorProfile", on_delete=models.SET_NULL, null=True, blank=True)
    patient = models.ForeignKey("PatientProfile", on_delete=models.SET_NULL, null=True, blank=True)
    caretaker = models.ForeignKey("CareTakerProfile", on_delete=models.SET_NULL, null=True, blank=True)
    
    appointment_date = models.DateField(null=True, blank=True)
    appointment_time = models.TimeField(null=True, blank=True)
    appointment_type = models.CharField(max_length=150, null=True, blank=True)
    treatment_performed = models.CharField(max_length=150, null=True, blank=True)
    
    lab_reports = models.CharField(max_length=150, null=True, blank=True)
    care_taker_notes = models.TextField(null=True, blank=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subscription_plan = models.CharField(max_length=150, null=True, blank=True)
    
    height = models.CharField(max_length=150, null=True, blank=True)
    weight = models.CharField(max_length=150, null=True, blank=True)
    blood_pressure = models.CharField(max_length=150, null=True, blank=True)
    blood_sugar = models.CharField(max_length=150, null=True, blank=True)
    
    medical_history = models.TextField(null=True, blank=True)
    appointment_history = models.TextField(null=True, blank=True)
    time_line = models.TextField(null=True, blank=True)
    
    appointment_reason = models.TextField(null=True, blank=True)
    appointment_status = models.CharField(
        max_length=20,
        choices=APPOINTMENT_STATUS,
        default='Pending',
        null=True,
        blank=True
    )
    
    preferred_dates = models.JSONField(blank=True, null=True, default=list)
    preferred_times = models.JSONField(blank=True, null=True, default=list)
    service_purchased = models.BooleanField(default=False)

    class Meta:
        db_table = "verimed_book_appoinments"

    def __str__(self):
        return f"{self.id}-{self.patient}-{self.appointment_status}"


ROLE_CHOICES = [
        ("admin", "Admin"),
        ("sponsor", "Sponsor"),
        ("doctor", "Doctor"),
        ("care_taker", "Care Taker"),
        # ("patient", "Patient"),
    ]

class User(AbstractUser):
    country_code = models.ForeignKey("VerimedCountryCode",on_delete=models.SET_NULL,null=True,blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    photo = models.ImageField(upload_to="user_photos/", null=True, blank=True)
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)  # ✅ New field
    service_purchased = models.CharField(max_length=150,null=True, blank=True)
    is_active_state = models.BooleanField(default=True)


    groups = models.ManyToManyField(
        Group,
        related_name="verimed_user_groups",  # avoid clash
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="verimed_user_user_permissions",
        blank=True
    )


    class Meta:
        db_table = "verimed_user"

    def __str__(self):
        return f"{self.id}-{self.phone}"
    

class SponsorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="sponsor_profile"
    )
    sponsor_verified = models.BooleanField(default=False)
    sponsor_id = models.CharField(max_length=150, unique=True, null=True, blank=True)
    sponsor_address = models.TextField(null=True, blank=True)
    sponsor_gender = models.CharField(max_length=50, null=True, blank=True)
    work_employment = models.CharField(max_length=300,null=True,blank=True)
    how_found_us = models.CharField(max_length=150,null=True,blank=True)
    
    

    class Meta:
        db_table = "verimed_sponsorprofile"

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.sponsor_id}"


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    dep = models.ForeignKey("VerimedDepartment", on_delete=models.SET_NULL, null=True, blank=True)
    doctor_verified = models.BooleanField(default=False)
    doctor_id = models.CharField(max_length=150, unique=True, null=True, blank=True)
    doc_address = models.TextField(null=True, blank=True)
    doc_exprience = models.IntegerField(null=True, blank=True)  # fixed
    doc_gender = models.CharField(max_length=50, null=True, blank=True)
    speciality = models.CharField(max_length=50, null=True, blank=True)
    doc_country_code = models.ForeignKey("VerimedCountryCode",on_delete=models.SET_NULL,null=True,blank=True)
    doc_phone = models.CharField(max_length=25, null=True, blank=True)
    joining_date = models.DateField(null=True,blank=True)
    doc_licence_no = models.CharField(max_length=100,null=True,blank=True)
    doc_city = models.CharField(max_length=100, null=True, blank=True)
    doc_state = models.CharField(max_length=100, null=True, blank=True)
    doc_country = models.CharField(max_length=100, null=True, blank=True)
    doc_pincode = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = "verimed_doctorprofile"

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.doctor_id}"


class CareTakerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="caretaker_profile"
    )
    caretaker_verified = models.BooleanField(default=False)
    caretaker_id = models.CharField(max_length=150, unique=True, null=True, blank=True)
    caretaker_address = models.TextField(null=True, blank=True)
    caretaker_exprience = models.IntegerField(null=True, blank=True)  # fixed
    care_gender = models.CharField(max_length=50, null=True, blank=True)
    credentials = models.CharField(max_length=300,null=True,blank=True)
    yr_of_graduation = models.CharField(max_length=150,null=True,blank=True)
    skillset = models.TextField(null=True,blank=True)
    title = models.CharField(max_length=150,null=True,blank=True)


    class Meta:
        db_table = "verimed_caretakerprofile"

    def __str__(self):
        return f"{self.id} - {self.user.username} - {self.caretaker_id}"


class PatientUploadDocuments(models.Model):
    patient_profile = models.ForeignKey(
        "PatientProfile",
        on_delete=models.SET_NULL,
        related_name="patient_profile_upload_doc",
        null=True, blank=True
    )
    file = models.FileField(upload_to="patient_upload_doc/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    referid = models.CharField(max_length=150,null=True,blank=True)
    filename = models.CharField(max_length=150,null=True,blank=True)
    
    class Meta:
        db_table = "patient_upload_documents"

    def __str__(self):
        return f"{self.id} - {self.filename} - {self.referid}"


class PatientProfile(models.Model):
    # user = models.OneToOneField(
    #     User, on_delete=models.CASCADE, related_name="patient_profile"
    # )
    sponsor = models.ForeignKey(
        "SponsorProfile", on_delete=models.SET_NULL, null=True, blank=True
    )
    # doctor = models.ForeignKey(
    #     "DoctorProfile", on_delete=models.SET_NULL, null=True, blank=True
    # )
    caretaker = models.ForeignKey(
        "CareTakerProfile", on_delete=models.SET_NULL, null=True, blank=True
    )
    patient_name = models.CharField(max_length=200,null=True,blank=True)
    country_code = models.ForeignKey("VerimedCountryCode",on_delete=models.SET_NULL,related_name="patientprofile_countrycode",null=True,blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    photo = models.ImageField(upload_to="patientphotos/", null=True, blank=True)
    email = models.EmailField(null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)
    
    # add
    height = models.CharField(max_length=150, null=True, blank=True)
    weight = models.CharField(max_length=150, null=True, blank=True)
    blood_pressure = models.CharField(max_length=150, null=True, blank=True)
    blood_sugar = models.CharField(max_length=150, null=True, blank=True)
    heart_rate = models.CharField(max_length=100, blank=True, null=True)
    oxygen = models.CharField(max_length=100, blank=True, null=True)
    temperature = models.CharField(max_length=100, blank=True, null=True)
    respiratory_rate = models.CharField(max_length=100, blank=True, null=True)
    
    patient_verified = models.BooleanField(default=False)
    patient_dob = models.DateField(null=True, blank=True)
    patient_gender = models.CharField(max_length=50, null=True, blank=True)
    blood_group = models.CharField(max_length=10, null=True, blank=True)
    patient_home_address = models.TextField(null=True, blank=True)
    primary_language = models.CharField(max_length=100, null=True, blank=True)
    religion = models.CharField(max_length=100, null=True, blank=True)
    escalate_to_physician = models.CharField(max_length=100, null=True, blank=True)

    # Emergency Contact
    emer_con_name = models.CharField(max_length=150, null=True, blank=True)
    emer_con_relation = models.CharField(max_length=100, null=True, blank=True)
    emer_con_coun_of_residen = models.CharField(max_length=100, null=True, blank=True)
    emer_con_country_code = models.ForeignKey(
        "VerimedCountryCode", on_delete=models.SET_NULL, null=True, blank=True
    )
    emer_con_phone = models.CharField(max_length=25, null=True, blank=True)
    emer_con_email = models.EmailField(null=True, blank=True)

    # Local Contact
    local_con_name = models.CharField(max_length=150, null=True, blank=True)
    local_con_relation = models.CharField(max_length=100, null=True, blank=True)
    local_con_country_code = models.ForeignKey(
        "VerimedCountryCode", on_delete=models.SET_NULL, null=True, blank=True, related_name="local_country_code"
    )
    local_con_phone = models.CharField(max_length=25, null=True, blank=True)

    # Reason for Enrollment
    reason_enrollment = models.TextField(null=True, blank=True)
    reason_other = models.TextField(null=True, blank=True)

    # Medical History
    medical_his_diagnosis = models.TextField(null=True, blank=True)
    medical_his_cancer = models.TextField(null=True, blank=True)
    medical_his_other = models.TextField(null=True, blank=True)
    medical_his_provided_medi_care = models.TextField(null=True, blank=True)
    medical_his_major_surgeries = models.TextField(null=True, blank=True)
    medical_his_curr_symp = models.TextField(null=True, blank=True)

    # Medication
    medication = models.JSONField(null=True, blank=True)    
    # medication_name = models.CharField(max_length=150, null=True, blank=True)
    # medication_dose = models.CharField(max_length=150, null=True, blank=True)
    # medication_frequency = models.CharField(max_length=150, null=True, blank=True)
    # medication_reason = models.TextField(null=True, blank=True)
    # medication_issues = models.BooleanField(default=False)
    # medication_issues_explain = models.TextField(null=True, blank=True)

    # Allergies
    allergies_issues = models.BooleanField(default=False)
    allergies_drug = models.TextField(null=True, blank=True)
    allergies_food = models.TextField(null=True, blank=True)

    # Functional Abilities
    functional_bathe = models.CharField(max_length=150, null=True, blank=True)
    functional_dress = models.CharField(max_length=150, null=True, blank=True)
    functional_eat = models.CharField(max_length=150, null=True, blank=True)
    functional_walk = models.CharField(max_length=150, null=True, blank=True)
    functional_use_bathroom = models.CharField(max_length=150, null=True, blank=True)
    functional_daily_activity = models.CharField(max_length=150, null=True, blank=True)
    functional_manage_finance = models.CharField(max_length=150, null=True, blank=True)
    functional_any_falls = models.BooleanField(default=False)
    functional_how_many = models.CharField(max_length=150, null=True, blank=True)
    functional_memory_pbms = models.BooleanField(default=False)

    # Lifestyle
    lifestyle_daily_routine = models.TextField(null=True, blank=True)
    lifestyle_dietary_habits = models.TextField(null=True, blank=True)
    lifestyle_sleep_quality = models.CharField(max_length=100, null=True, blank=True)
    lifestyle_physical_activity = models.CharField(max_length=100, null=True, blank=True)
    lifestyle_alcohol_use = models.CharField(max_length=100, null=True, blank=True)
    lifestyle_pain_complaints = models.CharField(max_length=100, null=True, blank=True)
    lifestyle_pain_where = models.TextField(null=True, blank=True)

    # Social and Emotional
    social_emotion_health = models.CharField(max_length=100, null=True, blank=True)
    social_spiritual_needs = models.CharField(max_length=100, null=True, blank=True)
    social_trusted_person = models.BooleanField(default=False)
    social_name = models.CharField(max_length=150, null=True, blank=True)

    # Goals
    goals_family_hope = models.TextField(null=True, blank=True)
    goals_special_instructions = models.TextField(null=True, blank=True)
    goals_term_membership = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "verimed_patientprofile"

    def __str__(self):
        return f"{self.id} - {self.patient_name}"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="admin_profile"
    )
    admin_verified = models.BooleanField(default=False)
    admin_id = models.CharField(max_length=150, unique=True, null=True, blank=True)
    admin_address = models.TextField(null=True, blank=True)
    admin_gender = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        db_table = "verimed_adminprofile"

    def __str__(self):
        return f"{self.id}-{self.admin_id}"
    

class SponsorID(models.Model):
    sponsor_id = models.CharField(max_length=150, null=True, blank=True)

    class Meta:
        db_table = "verimed_sponsorid"

    def __str__(self):
        return f"{self.id}-{self.sponsor_id}"
    
class PatientID(models.Model):
    patient_id = models.CharField(max_length=150, null=True, blank=True)
    
    class Meta:
        db_table = "verimed_patientid"

    def __str__(self):
        return f"{self.id}-{self.patient_id}"
    
class CaretakerID(models.Model):
    caretaker_id = models.CharField(max_length=150, null=True, blank=True)
    
    class Meta:
        db_table = "verimed_caretakerid"

    def __str__(self):
        return f"{self.id}-{self.caretaker_id}"
    
class DoctorID(models.Model):
    doctor_id = models.CharField(max_length=150, null=True, blank=True)
    
    class Meta:
        db_table = "verimed_doctorid"

    def __str__(self):
        return f"{self.id}-{self.doctor_id}"
    
class AdminID(models.Model):
    admin_id = models.CharField(max_length=150, null=True, blank=True)
    
    class Meta:
        db_table = "verimed_adminid"

    def __str__(self):
        return f"{self.id}-{self.admin_id}"
    
    
ROLE_CHOICES = [
        ("admin", "Admin"),
        ("sponsor", "Sponsor"),
        ("doctor", "Doctor"),
        ("care_taker", "Care Taker"),
        ("patient", "Patient"),
    ]
class EmailVerificationToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    payload = models.TextField()  # stores JSON of signup data
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,null=True,blank=True)
    
    # ✅ Soft delete support
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)

    def mark_as_used(self):
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    class Meta:
        db_table = "verimed_emailverificationtoken"

    def __str__(self):
        return f"{self.id}-{self.email}-{self.token}-"
    
    
    
class VerimedDoctorReportsFiles(models.Model):
    doc_report_files = models.ForeignKey(
        "DoctorReports",
        on_delete=models.SET_NULL,
        related_name="verimed_doctor_file_reports",
        null=True, blank=True
    )
    file = models.FileField(upload_to="doctorfilereports/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    referid = models.CharField(max_length=150,null=True,blank=True)
    

class DoctorReports(models.Model):
    # Foreign Keys
    patient = models.ForeignKey('PatientProfile', on_delete=models.CASCADE, related_name='doctor_reports')
    doctor = models.ForeignKey('DoctorProfile', on_delete=models.CASCADE, related_name='doctor_reports')
    sponsor = models.ForeignKey('SponsorProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_reports')
    caretaker = models.ForeignKey('CareTakerProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_reports')

    # Patient Info
    patient_name = models.CharField(max_length=255,null=True,blank=True)
    # patient_age = models.IntegerField(null=True,blank=True)
    # patient_gender = models.CharField(max_length=50,null=True,blank=True)
    # nationality = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=50, blank=True, null=True)

    # Vitals
    bp = models.CharField(max_length=50, blank=True, null=True)
    heart_rate = models.CharField(max_length=100, blank=True, null=True)
    sugar = models.CharField(max_length=100, blank=True, null=True)
    oxygen = models.CharField(max_length=100, blank=True, null=True)
    temperature = models.CharField(max_length=100, blank=True, null=True)
    respiratory_rate = models.CharField(max_length=100, blank=True, null=True)
    weight = models.CharField(max_length=100, blank=True, null=True)
    # status = models.CharField(max_length=255, blank=True, null=True)

    # Address
    # address_1 = models.CharField(max_length=255, blank=True, null=True)
    # address_2 = models.CharField(max_length=255, blank=True, null=True)
    # city = models.CharField(max_length=100, blank=True, null=True)
    # state = models.CharField(max_length=100, blank=True, null=True)
    # country = models.CharField(max_length=100, blank=True, null=True)
    # pincode = models.IntegerField(blank=True, null=True)

    # Notes
    doctor_notes = models.TextField(blank=True, null=True)
    initial_visit = models.CharField(max_length=150,null=True,blank=True) 

    class Meta:
        db_table = "verimed_doctor_reports"

    def __str__(self):
        return f"{self.id}-{self.patient}-{self.doctor}-"
    
    
class ContactUs(models.Model):
    department = models.CharField(max_length=200,null=True,blank=True)
    doctor = models.CharField(max_length=200,null=True,blank=True)
    full_name = models.CharField(max_length=200,null=True,blank=True)
    email = models.EmailField(null=True,blank=True)
    country_code = models.ForeignKey("VerimedCountryCode",on_delete=models.SET_NULL,null=True,blank=True)
    phone = models.CharField(max_length=25,null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    time = models.TimeField(null=True,blank=True)
    
    class Meta:
        db_table = "verimed_contactus"

    def __str__(self):
        return f"{self.id}-{self.departmentc}"
    



class KetnyproductionCheck(models.Model):
    name = models.CharField(max_length=255)

    country_code = models.ForeignKey(
        "VerimedCountryCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    phone = models.CharField(max_length=25, null=True, blank=True)

    email = models.EmailField(max_length=255, null=True, blank=True)

    city = models.CharField(max_length=100, null=True, blank=True)
    neighborhood = models.CharField(max_length=100,null=True,blank=True)
    age_range = models.CharField(max_length=100, null=True, blank=True)

    gender = models.CharField(max_length=50,null=True,blank=True)
    allergies = models.CharField(max_length=255, null=True, blank=True)

    sugar_kidneytest = models.TextField(null=True, blank=True)

    medication_sugar_pressure = models.CharField(max_length=255, null=True, blank=True)

    emergency_con_name = models.CharField(max_length=255, null=True, blank=True)

    emergency_country_code = models.ForeignKey(
        "VerimedCountryCode",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="emergency_country_code"
    )

    emergency_phone = models.CharField(max_length=25, null=True, blank=True)

    health_check = models.TextField(null=True, blank=True)

    comm_preference = models.CharField(max_length=100, null=True, blank=True)

    health_concern = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    screening_date = models.CharField(max_length=100, null=True, blank=True)


    class Meta:
        db_table = "verimed_ketnyproductioncheck"

    def __str__(self):
        return f"{self.id}-{self.name}"
    
# payment
from django.db import models

class Order(models.Model):
    email = models.EmailField()
    amount = models.IntegerField()   # cents
    payment_intent = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="pending")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verimed_order"

    def __str__(self):
        return f"{self.id}-{self.email}"
