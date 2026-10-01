from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from fieldscontrol.models import FieldsControlErrors
import json
from django.db import transaction
from verimed.models import VerimedCountryCode,VerimedDepartment,VerimedBookAppointment,APPOINTMENT_STATUS,SponsorID,PatientID,DoctorID,CaretakerID,AdminID,SponsorProfile,DoctorProfile,CareTakerProfile,PatientProfile,AdminProfile,ROLE_CHOICES,VerimedBookAppointmentLabReports,PatientUploadDocuments,DoctorReports,VerimedDoctorReportsFiles,ContactUs,KetnyproductionCheck
from fieldscontrol.views import field_validate_not_iterate
from .serializers import VerimedCountryCodeViewSlr,VerimedDepartmentViewSlr,VerimedBookAppointmentViewSlr,UserViewSlr,SponsorProfileViewSlr,PatientProfileViewSlr,DoctorProfileViewSlr,CareTakerProfileViewSlr,PatientProfileViewSlr,DoctorReportsViewSlr,ContactUsViewSlr,KetnyproductionCheckViewSlr
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny

# Create your views here.

class VerimedCountrycode(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        data = VerimedCountryCode.objects.all()
        serializer = VerimedCountryCodeViewSlr(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

 

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password
from .models import User, SponsorProfile, PatientProfile
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authentication import TokenAuthentication


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.urls import reverse
import json
from .models import User, SponsorProfile, EmailVerificationToken, SponsorID
from django.db import transaction
from django.contrib.auth.hashers import make_password

class UserChoices(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        appoinment_status = [{"key": key, "value": value} for key, value in ROLE_CHOICES]
        return Response(appoinment_status, status=status.HTTP_200_OK)
                    

class UserSignup(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        
        update_data = request.data.get("user_signup")
        if not update_data:
            return Response({"error": "doctorprofile_update_data is required"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(update_data, str):
            try:
                usersignup_data = json.loads(update_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(update_data, dict):
            usersignup_data = update_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )

        email = usersignup_data.get("email")
        role = usersignup_data.get("role")
        
        
        # --- CREATE VERIFICATION TOKEN ---
        token = get_random_string(length=48)
        EmailVerificationToken.objects.create(
            email=email,
            token=token,
            # role="sponsor", 
            role=role,
            payload=json.dumps(usersignup_data)  # store all signup data
        )

        # --- SEND EMAIL ---
        verification_link = f"{settings.FRONTEND_URL}/verimed/verify-email/?token={token}"
        send_mail(
            subject="Verify Your Email",
            message=f"Click the link to verify your email and complete signup: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "Verification email sent"}, status=status.HTTP_200_OK)


class UserEmailVerify(APIView):
    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return Response({"error": "Token missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # ✅ Already used token check
            verification = EmailVerificationToken.objects.get(token=token)
                        
            if verification.is_used:
                return Response({"error": "This verification link has already been used"}, status=status.HTTP_400_BAD_REQUEST)

        except EmailVerificationToken.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

        payload = json.loads(verification.payload)
        role = verification.role
        email = verification.email
        
        country_code_obj=None
        phonewithcountrycode = None
        country_code = payload.get("country_code")
        if country_code:
            phone = payload.get("phone")
            if phone: 
                try:
                    countrycode_obj = VerimedCountryCode.objects.get(code=country_code)
                    dialcode = countrycode_obj.dial_code
                    phonewithcountrycode = f"{dialcode}-{phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid Country Code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                 

        try:
            with transaction.atomic():
                # --- ROLE BASED LOGIC ---
                if role == "sponsor":
                    last_data = SponsorID.objects.last()
                    sponsor_id = f"S{int(last_data.sponsor_id)}" if last_data else "S1"
                    if last_data:
                        last_data.sponsor_id = int(last_data.sponsor_id) + 1
                        last_data.save()

                    user = User.objects.create(
                        username=sponsor_id,
                        first_name=payload.get("first_name"),
                        last_name=payload.get("last_name"),
                        email=email,
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=verification.role,
                        password=make_password(payload.get("password"))
                    )

                    SponsorProfile.objects.create(
                        user=user,
                        sponsor_verified=True,
                        sponsor_id=sponsor_id
                    )

                    # ✅ Soft delete (mark token as used)
                    verification.mark_as_used()

                    response_msg = {"message": "Sponsor created successfully", "sponsor_id": sponsor_id}
                
                elif role == "doctor":
                    last_data = DoctorID.objects.last()
                    doctor_id = f"D{int(last_data.doctor_id)}" if last_data else "D1"
                    if last_data:
                        last_data.doctor_id = int(last_data.doctor_id) + 1
                        last_data.save()
                    user = User.objects.create(
                        username=doctor_id,
                        first_name=payload.get("first_name"),
                        last_name=payload.get("last_name"),
                        email=email,
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=verification.role,
                        password=make_password(payload.get("password"))
                    )

                    DoctorProfile.objects.create(
                        user=user,
                        doctor_verified=True,
                        doctor_id=doctor_id
                    )
                    # ✅ Soft delete (mark token as used)
                    verification.mark_as_used()

                    response_msg = {"message": "Doctor created successfully", "doctor_id": doctor_id}

                elif role == "care_taker":
                    last_data = CaretakerID.objects.last()
                    caretaker_id = f"C{int(last_data.caretaker_id)}" if last_data else "C1"
                    if last_data:
                        last_data.caretaker_id = int(last_data.caretaker_id) + 1
                        last_data.save()
                    user = User.objects.create(
                        username=caretaker_id,
                        first_name=payload.get("first_name"),
                        last_name=payload.get("last_name"),
                        email=email,
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=verification.role,
                        password=make_password(payload.get("password"))
                    )

                    CareTakerProfile.objects.create(
                        user=user,
                        caretaker_verified=True,
                        caretaker_id=caretaker_id
                    )
                    # ✅ Soft delete (mark token as used)
                    verification.mark_as_used()

                    response_msg = {"message": "CareTaker created successfully", "caretaker_id": caretaker_id}

                
                elif role == "patient":
                    sponsor_id = payload.get("sponser_id")
                    sponsor_obj = None  

                    if sponsor_id:
                        try:
                            sponsor_id = int(sponsor_id)
                            try:
                                sponsor_obj = SponsorProfile.objects.get(id=sponsor_id)
                            except SponsorProfile.DoesNotExist:
                                raise ValueError("Invalid sponsor ID")
                        except (ValueError, TypeError):
                            raise ValueError("Sponsor ID must be an integer")
                    else:
                        sponsor_obj = None
                        
                    # doctor
                    doctor_id = payload.get("doctor_id") 
                    doctor_obj = None  

                    if doctor_id:
                        try:
                            doctor_id = int(doctor_id)
                            try:
                                doctor_obj = DoctorProfile.objects.get(id=doctor_id)
                            except DoctorProfile.DoesNotExist:
                                raise ValueError("Invalid doctor ID")
                        except (ValueError, TypeError):
                            raise ValueError("Doctor ID must be an integer")
                    else:
                        doctor_obj = None
                        
                    # caretaker
                    caretaker_id = payload.get("caretaker_id") 
                    caretaker_obj = None  

                    if sponsor_id:
                        try:
                            caretaker_id = int(caretaker_id)
                            try:
                                caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
                            except CareTakerProfile.DoesNotExist:
                                raise ValueError("Invalid caretaker ID")
                        except (ValueError, TypeError):
                            raise ValueError("Caretaker ID must be an integer")
                    else:
                        caretaker_obj = None
                      
                    last_data = PatientID.objects.last()
                    patient_id = f"P{int(last_data.patient_id)}" if last_data else "P1"
                    if last_data:
                        last_data.patient_id = int(last_data.patient_id) + 1
                        last_data.save()
                        
                    user = User.objects.create(
                        username=patient_id,
                        first_name=payload.get("first_name"),
                        last_name=payload.get("last_name"),
                        email=email,
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=verification.role,
                        password=make_password(payload.get("password"))
                    )

                    PatientProfile.objects.create(
                        user=user,
                        sponsor=sponsor_obj,
                        doctor=doctor_obj,
                        caretaker=caretaker_obj,
                        patient_verified=True,
                        patient_id=patient_id,
                        
                    )

                    response_msg = {"message": "Patient created successfully", "patient_id": patient_id}

                
                elif role == "admin":
                    last_data = AdminID.objects.last()
                    admin_id = f"A{int(last_data.admin_id)}" if last_data else "A"
                    if last_data:
                        last_data.admin_id = int(last_data.admin_id) + 1
                        last_data.save()
                    user = User.objects.create(
                        username=admin_id,
                        first_name=payload.get("first_name"),
                        last_name=payload.get("last_name"),
                        email=payload.get("email"),
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=role,
                        password=make_password(payload.get("password"))
                    )

                    AdminProfile.objects.create(
                        user=user,
                        admin_verified=True,
                        admin_id=admin_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()

                    response_msg = {"message": "Admin created successfully", "admin_id": admin_id}

                
                
                else:
                    return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

                # ✅ Mark token as used (soft delete)
                verification.mark_as_used()

                return Response(response_msg, status=status.HTTP_200_OK)


        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
 
 
class UserLogin(APIView):
    permission_classes = [AllowAny]  # Allow anyone to log in
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {"error": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        elif not user.is_active_state:
            return Response(
                {"error": "Activate your status. Please contact your admin."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        
        # Create session
        login(request, user)  

        # Create or get token
        token, created = Token.objects.get_or_create(user=user)

        # Get sessionid from cookie storage
        session_id = request.session.session_key
        if not session_id:  # ensure session exists
            request.session.save()
            session_id = request.session.session_key

        return Response(
            {
                "message": "Login successful",
                "sessionid": session_id,
                "token": token.key,
                "username": user.username
            },
            status=status.HTTP_200_OK
        )   

class UserLogout(APIView):
    authentication_classes = [TokenAuthentication]   # ✅ Requires Token auth
    permission_classes = [IsAuthenticated]           # ✅ Only logged-in users

    def post(self, request):
        user = request.user

        # Delete current token
        Token.objects.filter(user=user).delete()

        # Delete current session
        if request.session.session_key:
            request.session.flush()   # removes the session completely

        # Django logout (extra safety)
        logout(request)

        return Response(
            {"message": "Logout successful"},
            status=status.HTTP_200_OK
        )

class UserView(APIView):
    authentication_classes = [TokenAuthentication]   # ✅ Requires Token auth
    permission_classes = [IsAuthenticated]           # ✅ Only logged-in users

    # authentication_classes = []        # No authentication required
    # permission_classes = [AllowAny]    # Anyone can access

    def get(self, request):
        users = User.objects.all()
        serializer = UserViewSlr(users, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserCreate(APIView):
    
    def post(self, request):
        
        user_signup_data_raw = request.data.get("user_signup")
        if not user_signup_data_raw:
            return Response({"error": "user_signup is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(user_signup_data_raw, str):
            import json
            try:
                user_signup_data = json.loads(user_signup_data_raw)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
            
         # Update photo if provided
        photo = request.data.get("photo",None)
        if photo:
            photo=photo
            
        countrycode = user_signup_data.get("countrycode")
        if countrycode:

            try:
                countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            countrycode_obj=None
            dialcode=None
        
        mobile = user_signup_data.get("phone")
        if mobile:
            phonewithcountrycode = f"{dialcode}-{mobile}"
        else:
            phonewithcountrycode=None
        
        role =user_signup_data.get("role")
        if not role:
            return Response(
                    {"error": "Role is important"},  
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            with transaction.atomic():
                url = "https://verimed-dashboard.vercel.app/"
                # files sending
                from django.core.mail import EmailMessage
                from django.conf import settings

                def send_api_verticalcontact_mail(firstname,name, password, email):
                    # subject = "Welcome to VeriMED — Thank You for Registering Your Loved One"
                    # # message = (
                    #     f"Hello {firstname},\n\n"
                    #     f"Username:{name}\n"
                    #     f"Password: {password}\n"
                    #     f"Login Url:{url}\n\n"
                        
                    #     f"Thank you for registering with VeriMED, the physician-led, nurse-powered home "
                    #     f"health and geriatric wellness service trusted by Cameroon's global families. "
                    #     f"Your account is now active, and we are honored to support you as you take this "
                    #     f"important step in caring for someone you love.\n\n"
                        
                    #     f"We understand the responsibility you carry as a sponsor — balancing distance, "
                    #     f"concern, and the desire for reliable, compassionate medical support. Our mission "
                    #     f"is to provide you with exactly that: premium in-home and virtual care, transparent "
                    #     f"updates, dependable communication, and global-standard clinical oversight for your "
                    #     f"loved one in Cameroon.\n\n"
                        
                    #     f"You can now log into your portal at any time to:\n"
                    #     f"    • View care updates and medical reports\n"
                    #     f"    • Communicate with your nurse or physician and our care team\n"
                    #     f"    • Schedule appointments\n"
                    #     f"    • Track wellness progress and changes\n"
                    #     f"    • Request additional services\n\n"
                        
                    #     f"At VeriMED, we believe every family deserves peace of mind, and every elder "
                    #     f"deserves care delivered with dignity, precision, and kindness.\n\n"
                        
                    #     f"Thank you for trusting us with your loved one’s health and safety.\n\n"
                        
                    #     f"With gratitude,\n"
                    #     f"The VeriMED Clinical & Care Coordination Team\n"
                    #     f"Physician-Led. Nurse-Powered. Cameroon’s Trusted Home Health Service.\n"
                    #     f"Global-Standard Medical Care for Loved Ones Back Home.\n\n"
                        
                    #     f"www.Verimed.care ~~~ Serving Families Worldwide"
                    #     )
                      
                        
                    subject = "Welcome to VeriMED — Thank You for Registering Your Loved One"

                    message = f"""
                    <p>Hello <strong>{firstname}</strong>,</p>

                    <p>
                        <strong>Username:</strong> {name}<br>
                        <strong>Password:</strong> {password}<br>
                        <strong>Login URL:</strong> <a href="{url}">{url}</a>
                    </p>

                    <p>
                        Thank you for registering with VeriMED, the physician-led, nurse-powered home
                        health and geriatric wellness service trusted by Cameroon's global families.
                        Your account is now active, and we are honored to support you as you take this
                        important step in caring for someone you love.
                    </p>

                    <p>
                        We understand the responsibility you carry as a sponsor — balancing distance,
                        concern, and the desire for reliable, compassionate medical support. Our mission
                        is to provide you with exactly that: premium in-home and virtual care, transparent
                        updates, dependable communication, and global-standard clinical oversight for your
                        loved one in Cameroon.
                    </p>

                    <p>You can now log into your portal at any time to:</p>
                    <ul>
                        <li>View care updates and medical reports</li>
                        <li>Communicate with your nurse or physician and our care team</li>
                        <li>Schedule appointments</li>
                        <li>Track wellness progress and changes</li>
                        <li>Request additional services</li>
                    </ul>

                    <p>
                        At VeriMED, we believe every family deserves peace of mind, and every elder
                        deserves care delivered with dignity, precision, and kindness.
                    </p>

                    <p>
                        Thank you for trusting us with your loved one’s health and safety.
                    </p>

                    <p>
                        With gratitude,<br>
                        <strong>The VeriMED Clinical & Care Coordination Team</strong><br>
                        Physician-Led. Nurse-Powered. Cameroon’s Trusted Home Health Service.<br>
                        Global-Standard Medical Care for Loved Ones Back Home.
                    </p>

                    <p>www.Verimed.care ~~~ Serving Families Worldwide</p>
                    """
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [email]

                    try:
                        # email_msg = EmailMessage(subject, message, from_email, recipient_list)
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                        email_msg.content_subtype = "html"  # VERY IMPORTANT
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Error sending vertical contact email: {e}")
                        return False
                
                

                def send_api_caretaker_mail(firstname,name, password, email):
                    subject = "Welcome to VeriMED"

                    message = f"""
                    <p>Dear <strong>{firstname}</strong>,</p>

                    <p><strong>Welcome to VeriMED!</strong></p>

                    <p>
                        <strong>Username:</strong> {name}<br>
                        <strong>Password:</strong> {password}<br>
                        <strong>Login URL:</strong> <a href="{url}">{url}</a>
                    </p>

                    <p>
                        We are delighted that you have chosen to become part of our growing team. On behalf of
                        our physicians, nurses, and healthcare professionals, welcome to an organization that is
                        committed to bringing world-class healthcare closer to the people and communities we serve.
                    </p>

                    <p>
                        At VeriMED, we believe that exceptional healthcare begins with exceptional people. Every
                        interaction with a client, family member, colleague, or community partner is an opportunity
                        to demonstrate professionalism, compassion, integrity, and excellence. Whether you provide
                        direct patient care or support our operations behind the scenes, your work contributes to
                        improving lives and strengthening our mission.
                    </p>

                    <p>As a member of the VeriMED team, we ask you to uphold the professional standards that define our organization:</p>
                    <ul>
                        <li>Place the patient and family at the center of every decision.</li>
                        <li>Treat every person with dignity, respect, kindness, and compassion.</li>
                        <li>Demonstrate honesty, integrity, confidentiality, and accountability in everything you do.</li>
                        <li>Pursue excellence through continuous learning and attention to detail.</li>
                        <li>Communicate professionally and collaborate respectfully with colleagues and community partners.</li>
                        <li>Represent VeriMED with pride, professionalism, and the highest ethical standards at all times.</li>
                    </ul>

                    <p>
                        Our vision is to build healthier communities through preventive care, innovative healthcare
                        services, patient education, and compassionate home-based medical care. We strive to become
                        the trusted healthcare partner that families think of first when they need guidance, support,
                        or exceptional clinical care.
                    </p>

                    <p>Over the coming days, you will receive information about your work with us.</p>
                    <ul>
                        <li>If you are on our screening team, you will receive a welcome phone call from our Director of Operations.</li>
                        <li>If you are also on our clinical team, you will also be welcomed by our Chief Medical Officer.</li>
                    </ul>

                    <p>
                        Please take the time to review any orientation materials, training resources, and
                        organizational policies as they will help prepare you for success at VeriMED.
                    </p>

                    <p>
                        Thank you for joining our mission of bringing world-class healthcare to Cameroon. We are
                        excited to have you on our team and look forward to the knowledge, compassion, and
                        professionalism you will bring to the lives of those we serve.
                    </p>

                    <hr>

                    <p>
                        <strong>The VeriMED Promise</strong><br>
                        We serve with compassion. We lead with integrity. We pursue excellence. We work as one team.
                        We never stop learning. And we always place our patients and their families first.
                    </p>

                    <hr>

                    <p>
                        Welcome to the VeriMED family!<br><br>
                        Warm regards,<br>
                        <strong>Human Resources &amp; People Development Department</strong><br>
                        VeriMED<br>
                        <a href="https://www.verimed.care">www.verimed.care</a>
                    </p>
                    """
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [email]

                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                        email_msg.content_subtype = "html"  # VERY IMPORTANT
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Employee welcome email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Error sending employee welcome email: {e}")
                        return False

                # --- ROLE BASED LOGIC ---
                if role == "sponsor":
                    last_data = SponsorID.objects.last()
                    sponsor_id = f"S{int(last_data.sponsor_id)}" if last_data else "S1"
                    if last_data:
                        last_data.sponsor_id = int(last_data.sponsor_id) + 1
                        last_data.save()

                    user = User.objects.create(
                        username=sponsor_id,
                        first_name=user_signup_data.get("first_name"),
                        last_name=user_signup_data.get("last_name"),
                        email=user_signup_data.get("email"),
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=role,
                        photo=photo,
                        service_purchased=user_signup_data.get("service_purchased"),
                        password=make_password(user_signup_data.get("password")),
                        is_active_state = user_signup_data.get("is_active_state")
                    )

                    SponsorProfile.objects.create(
                        user=user,
                        sponsor_verified=True,
                        sponsor_id=sponsor_id
                    )

                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()
                    send_api_verticalcontact_mail(user.first_name,user.username, user_signup_data.get("password"), user.email)

                    response_msg = {"message": "Sponsor created successfully Check the Email", "sponsor_id": sponsor_id}
                
                elif role == "doctor":
                    last_data = DoctorID.objects.last()
                    doctor_id = f"D{int(last_data.doctor_id)}" if last_data else "D1"
                    if last_data:
                        last_data.doctor_id = int(last_data.doctor_id) + 1
                        last_data.save()
                    user = User.objects.create(
                        username=doctor_id,
                        first_name=user_signup_data.get("first_name"),
                        last_name=user_signup_data.get("last_name"),
                        email=user_signup_data.get("email"),
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=role,
                        photo=photo,
                        service_purchased=user_signup_data.get("service_purchased"),
                        password=make_password(user_signup_data.get("password")),
                        is_active_state = user_signup_data.get("is_active_state")

                    )

                    DoctorProfile.objects.create(
                        user=user,
                        doctor_verified=True,
                        doctor_id=doctor_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()
                    
                    
                    send_api_verticalcontact_mail(user.first_name,user.username, user_signup_data.get("password"), user.email)
                    response_msg = {"message": "Doctor created successfully Check the Email", "doctor_id": doctor_id}

                elif role == "care_taker":
                    last_data = CaretakerID.objects.last()
                    caretaker_id = f"C{int(last_data.caretaker_id)}" if last_data else "C1"
                    if last_data:
                        last_data.caretaker_id = int(last_data.caretaker_id) + 1
                        last_data.save()
                    user = User.objects.create(
                        username=caretaker_id,
                        first_name=user_signup_data.get("first_name"),
                        last_name=user_signup_data.get("last_name"),
                        email=user_signup_data.get("email"),
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=role,
                        photo=photo,
                        service_purchased=user_signup_data.get("service_purchased"),
                        password=make_password(user_signup_data.get("password")),
                        is_active_state = user_signup_data.get("is_active_state")

                    )

                    CareTakerProfile.objects.create(
                        user=user,
                        caretaker_verified=True,
                        caretaker_id=caretaker_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()

                    send_api_caretaker_mail(user.first_name,user.username, user_signup_data.get("password"), user.email)
                    response_msg = {"message": "CareTaker created successfully Check the Email", "caretaker_id": caretaker_id}

                
                # elif role == "patient":
                #     sponsor_id = user_signup_data.get("sponser_id")
                #     sponsor_obj = None  

                #     if sponsor_id:
                #         try:
                #             sponsor_id = int(sponsor_id)
                #             try:
                #                 sponsor_obj = SponsorProfile.objects.get(id=sponsor_id)
                #             except SponsorProfile.DoesNotExist:
                #                 raise ValueError("Invalid sponsor ID")
                #         except (ValueError, TypeError):
                #             raise ValueError("Sponsor ID must be an integer")
                #     else:
                #         sponsor_obj = None
                        
                #     # doctor
                #     doctor_id = user_signup_data.get("doctor_id") 
                #     doctor_obj = None  

                #     if doctor_id:
                #         try:
                #             doctor_id = int(doctor_id)
                #             try:
                #                 doctor_obj = DoctorProfile.objects.get(id=doctor_id)
                #             except DoctorProfile.DoesNotExist:
                #                 raise ValueError("Invalid doctor ID")
                #         except (ValueError, TypeError):
                #             raise ValueError("Doctor ID must be an integer")
                #     else:
                #         doctor_obj = None
                        
                #     # caretaker
                #     caretaker_id = user_signup_data.get("caretaker_id") 
                #     caretaker_obj = None  

                #     if sponsor_id:
                #         try:
                #             caretaker_id = int(caretaker_id)
                #             try:
                #                 caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
                #             except CareTakerProfile.DoesNotExist:
                #                 raise ValueError("Invalid caretaker ID")
                #         except (ValueError, TypeError):
                #             raise ValueError("Caretaker ID must be an integer")
                #     else:
                #         caretaker_obj = None
                      
                #     last_data = PatientID.objects.last()
                #     patient_id = f"P{int(last_data.patient_id)}" if last_data else "P1"
                #     if last_data:
                #         last_data.patient_id = int(last_data.patient_id) + 1
                #         last_data.save()
                        
                #     user = User.objects.create(
                #         username=patient_id,
                #         first_name=user_signup_data.get("first_name"),
                #         last_name=user_signup_data.get("last_name"),
                #         email=user_signup_data.get("email"),
                #         country_code=countrycode_obj,
                #         phone=phonewithcountrycode,
                #         user_role=role,
                #         password=make_password(user_signup_data.get("password"))
                #     )

                #     PatientProfile.objects.create(
                #         user=user,
                #         sponsor=sponsor_obj,
                #         doctor=doctor_obj,
                #         caretaker=caretaker_obj,
                #         patient_verified=True,
                #         patient_id=patient_id,
                        
                #     )

                #     send_api_verticalcontact_mail(user.username, user_signup_data.get("password"), user.email)
                #     response_msg = {"message": "Patient created successfully Check the Email", "patient_id": patient_id}

                
                elif role == "admin":
                    last_data = AdminID.objects.last()
                    admin_id = f"A{int(last_data.admin_id)}" if last_data else "A"
                    if last_data:
                        last_data.admin_id = int(last_data.admin_id) + 1
                        last_data.save()
                    user = User.objects.create(
                        username=admin_id,
                        first_name=user_signup_data.get("first_name"),
                        last_name=user_signup_data.get("last_name"),
                        email=user_signup_data.get("email"),
                        country_code=countrycode_obj,
                        phone=phonewithcountrycode,
                        user_role=role,
                        photo=photo,
                        service_purchased=user_signup_data.get("service_purchased"),
                        password=make_password(user_signup_data.get("password")),
                        is_active_state = user_signup_data.get("is_active_state")

                    )

                    AdminProfile.objects.create(
                        user=user,
                        admin_verified=True,
                        admin_id=admin_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()
                    
                    send_api_verticalcontact_mail(user.first_name,user.username, user_signup_data.get("password"), user.email)
                    response_msg = {"message": "Admin created successfullyCheck the Email ", "admin_id": admin_id}

                
                else:
                    return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

                # ✅ Mark token as used (soft delete)
                # verification.mark_as_used()

                return Response(response_msg, status=status.HTTP_200_OK)


        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
 

class UserUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        # Ensure 'user_update_data' exists
        user_update_data = request.data.get("user_update_data")
        if not user_update_data:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(user_update_data, str):
            import json
            try:
                user_update_data = json.loads(user_update_data)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        # Get user object
        try:
            user = User.objects.get(id=user_update_data.get("updateid"))
        except User.DoesNotExist:
            return Response({"error": "Give me a valid user"}, status=status.HTTP_404_NOT_FOUND)
        
        countrycode = user_update_data.get("countrycode")
        if countrycode:

            try:
                countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            countrycode_obj=None
            dialcode=None
        
        mobile = user_update_data.get("phone")
        if mobile:
            phonewithcountrycode = f"{dialcode}-{mobile}"
        else:
            phonewithcountrycode=None
        
      
        try:
            with transaction.atomic():
        
                # Update user fields
                user.first_name = user_update_data.get("first_name", user.first_name)
                user.last_name = user_update_data.get("last_name", user.last_name)
                user.email = user_update_data.get("email", user.email)
                user.service_purchased = user_update_data.get("service_purchased", user.service_purchased)
                user.country_code = countrycode_obj
                user.phone = phonewithcountrycode
                user.is_active_state = user_update_data.get("is_active_state",user.is_active_state)

                # user.role = user_update_data.get("role", user.role)

                # Update photo if provided
                photo = request.data.get("photo")   
                if photo:
                    user.photo = photo

                # Update password if provided
                password = user_update_data.get("password")
                if password:
                    user.password = make_password(password)

                user.save()
                print("userid",user.id)
                codes = user.country_code.id if user and user.country_code else None
                print("codes",codes)
                # print(type(codes))
                if codes:
                    codee = VerimedCountryCode.objects.get(id=codes)
                    code =codee.code
                else:
                    code=None
                
                return Response({
                    "message": "User updated successfully",
                    "user": {
                        # "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "countrycode":code,
                        "phone": user.phone,
                        "role": user.user_role,
                        "service_purchased":user.service_purchased
                    }
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
                

class UserUpdateUser(APIView):

    def patch(self, request):
        # Ensure 'user_update_data' exists
        user_update_data = request.data.get("user_update_data")
        if not user_update_data:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(user_update_data, str):
            import json
            try:
                user_update_data = json.loads(user_update_data)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)


        username=user_update_data.get("username")
        # Get user object
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": f"no user name found {username}"}, status=status.HTTP_404_NOT_FOUND)        
        
        
        
        countrycode = user_update_data.get("countrycode")
        if countrycode:

            try:
                countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            countrycode_obj=None
            dialcode=None
        
        mobile = user_update_data.get("phone")
        if mobile:
            phonewithcountrycode = f"{dialcode}-{mobile}"
        else:
            phonewithcountrycode=None
        
      
        try:
            with transaction.atomic():
                
                # Update user fields
                user.first_name = user_update_data.get("first_name", user.first_name)
                user.last_name = user_update_data.get("last_name", user.last_name)
                user.email = user_update_data.get("email", user.email)
                user.service_purchased = user_update_data.get("service_purchased", user.service_purchased)
                if countrycode:
                    user.country_code = countrycode_obj
                if phonewithcountrycode:
                    user.phone = phonewithcountrycode
                user.is_active_state = user_update_data.get("is_active_state",user.is_active_state)

                # user.role = user_update_data.get("role", user.role)

                # Update photo if provided
                photo = request.data.get("photo")   
                if photo:
                    user.photo = photo

                # Update password if provided
                password = user_update_data.get("password")
                if password:
                    print("password",password)
                    user.password = make_password(password)
                    

                user.save()
                
                url = "https://verimed-dashboard.vercel.app/"

                from django.core.mail import EmailMessage
                from django.conf import settings
                
                if password:
                    def send_api_verticalcontact_mail():
                    
                        subject = "Welcome to VeriMED — User Updated Sucessfully"

                        message = f"""
                        <p>
                            <strong>Username:</strong> {username}<br>
                            <strong>Password:</strong> {password}<br>
                            <strong>Login URL:</strong> <a href="{url}">{url}</a>
                        </p>"""
                        from_email = settings.DEFAULT_FROM_EMAIL
                        recipient_list = [user.email]
                        
                        try:
                            # email_msg = EmailMessage(subject, message, from_email, recipient_list)
                            email_msg = EmailMessage(subject, "", from_email, recipient_list)
                            email_msg.content_subtype = "html"  # VERY IMPORTANT
                            email_msg.body = message
                            email_msg.send(fail_silently=False)
                            print("Email sent successfully")
                            return True
                        except Exception as e:
                            print(f"Error sending vertical contact email: {e}")
                            return False
                    send_api_verticalcontact_mail()

                codes = user.country_code.id if user and user.country_code else None
                # print("codes",codes)
                # print(type(codes))
                if codes:
                    codee = VerimedCountryCode.objects.get(id=codes)
                    code =codee.code
                else:
                    code=None
                    
                return Response({
                    "message": "User updated successfully",
                    "user": {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "countrycode":code,
                        "phone": user.phone,
                        "role": user.user_role,
                        "service_purchased":user.service_purchased
                    }
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
                

    

class UserDelete(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # authentication_classes = []        # No authentication required
    # permission_classes = [AllowAny]    # Anyone can access
    

    def delete(self, request):
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            delete_ids = request.data.getlist("deleteids")  # form-data
        else:
            delete_ids = request.data.get("deleteids", [])  # JSON list

        if not delete_ids:
            return Response(
                {"error": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        notvalidids = []

        for i in delete_ids:
            try:
                user = User.objects.get(id=i)
            except User.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid user IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        
        try:
            with transaction.atomic():
                for user_id in delete_ids:
                    try:
                        user = User.objects.get(id=user_id)
                        user.delete()
                       
                    except User.DoesNotExist:
                        return Response({"error":"Give me  a valid User ID"})
               
                return Response(
                    {   "message": "User Deleted successfully",
                       
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )        
        
        

class VerimedDepartmentCreateUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    
    def post(self, request):

        raw_data = request.data.get("verimed_department")
        print("raw_data", raw_data)
        
        if isinstance(raw_data, str):
            try:
                dep_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_data, dict):
            dep_data = raw_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )
        doc_id = dep_data.get("docid") 
        doc_obj =None
        if doc_id:
            try:
                doc_obj = DoctorProfile.objects.get(id=doc_id)
            except DoctorProfile.DoesNotExist:
                return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        countrycode = dep_data.get("country_code")
        if countrycode:

            try:
                countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            countrycode_obj=None
            dialcode=None
        
        mobile = dep_data.get("contact_phone")
        if mobile:
            phonewithcountrycode = f"{dialcode}-{mobile}"
        else:
            phonewithcountrycode=None
        
       
        # --- MAIN TRANSACTION ---
        try:
            with transaction.atomic():
                # Create main asset_cleaned_data.get("department")
                verimeddepartment = VerimedDepartment.objects.create(
                    dep_name=dep_data.get("dep_name"),
                    dep_type=dep_data.get("dep_type"),
                    contact_email=dep_data.get("contact_email"),                    
                    country_code=countrycode_obj,
                    contact_phone=phonewithcountrycode,
                    address=dep_data.get("address"),
                    description=dep_data.get("description"),
                    dep_ID=dep_data.get("dep_ID"),
                    status=dep_data.get("status"),
                    doctor=doc_obj,
                    dep_city=dep_data.get("dep_city"),
                    dep_state=dep_data.get("dep_state"),
                    dep_country=dep_data.get("dep_country"),
                    dep_pincode=dep_data.get("dep_pincode"),
                )
                return Response(
                    {"message": "Department Created successfully"},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
    def patch(self, request):

            raw_data = request.data.get("verimed_department")
            print("raw_data", raw_data)
            
            if isinstance(raw_data, str):
                try:
                    dep_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
            elif isinstance(raw_data, dict):
                dep_data = raw_data
            else:
                return Response(
                    {"error": "Invalid data type. Expected JSON string or dict."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            depupdateid =dep_data.get("depupdateid") 
            if depupdateid:
                try:
                    dep_obj = VerimedDepartment.objects.get(id=depupdateid)
                except VerimedDepartment.DoesNotExist:
            
                    return Response({"error": "Invalid DepartmentUpdateid ID"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response  ({"error": "depupdateid is Mandatory."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            doc_id = dep_data.get("docid") 
            print("doc_id",doc_id)
            doc_obj =None
            if doc_id:
                try:
                    doc_obj = DoctorProfile.objects.get(id=doc_id)
                except DoctorProfile.DoesNotExist:
                    return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

            countrycode = dep_data.get("country_code")
            if countrycode:

                try:
                    countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                    dialcode = countrycode_obj.dial_code
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid Country Code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                countrycode_obj=None
                dialcode=None
            
            mobile = dep_data.get("contact_phone")
            if mobile:
                phonewithcountrycode = f"{dialcode}-{mobile}"
            else:
                phonewithcountrycode=None
            
        
            # --- MAIN TRANSACTION ---
            try:
                with transaction.atomic():
                    
                    dep_obj.dep_name=dep_data.get("dep_name")
                    dep_obj.dep_type=dep_data.get("dep_type")
                    dep_obj.contact_email=dep_data.get("contact_email")                  
                    dep_obj.country_code=countrycode_obj
                    dep_obj.contact_phone=phonewithcountrycode
                    dep_obj.address=dep_data.get("address")
                    dep_obj.description=dep_data.get("description")
                    dep_obj.dep_ID=dep_data.get("dep_ID")
                    dep_obj.status=dep_data.get("status")
                    dep_obj.doctor=doc_obj
                    dep_obj.dep_city=dep_data.get("dep_city")
                    dep_obj.dep_state=dep_data.get("dep_state")
                    dep_obj.dep_country=dep_data.get("dep_country")
                    dep_obj.dep_pincode=dep_data.get("dep_pincode")
                    dep_obj.save()
                    
                    return Response(
                        {"message": "Department Updated successfully"},
                        status=status.HTTP_200_OK
                    )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def get(self, request):
        try:
            verimed_doctor_qs = VerimedDepartment.objects.all()
            serializer = VerimedDepartmentViewSlr(verimed_doctor_qs, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
        
    def delete(self, request):
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            departmentdeleteids = request.data.get("departmentdeleteids")  # form-data
        else:
            departmentdeleteids = request.data.get("departmentdeleteids", [])  # JSON list

        if not departmentdeleteids:
            return Response(
                {"error": "No Department Delete IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        notvalidids = []

        for i in departmentdeleteids:
            try:
                department = VerimedDepartment.objects.get(id=i)
            except VerimedDepartment.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Department Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        
        try:
            with transaction.atomic():
                for dep_id in departmentdeleteids:
                    try:
                        dep = VerimedDepartment.objects.get(id=dep_id)
                        dep.delete()
                
                    except VerimedDepartment.DoesNotExist:
                        return Response({"error":"Give me  a valid Department ID"})
               
                return Response(
                    {   "message": "Department Deleted successfully",
                        
                    },
                            status=status.HTTP_200_OK
                        )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )        
        
      
            
class AppoinmentStatusChoices(APIView):
    
    def get(self, request):
        appoinment_status = [{"key": key, "value": value} for key, value in APPOINTMENT_STATUS]
        return Response(appoinment_status, status=status.HTTP_200_OK)
                    

class VerimedBookAppoinmentCreateUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Step 1: Parse JSON data
        raw_data = request.data.get("bookappoinment_data")
        if not raw_data:
            return Response({"error": "bookappoinment_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(raw_data, str):
            try:
                report_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_data, dict):
            report_data = raw_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 2: Validate Foreign Keys
        sponid=report_data.get("sponsor")
        spon_obj=None
        if sponid:
            try:
                spon_obj = SponsorProfile.objects.get(id=sponid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)

        
        dep_id = report_data.get("dep")
        dep_obj = None
        if dep_id:
            try:
                dep_obj = VerimedDepartment.objects.get(id=dep_id)
            except VerimedDepartment.DoesNotExist:
                return Response({"error": "Invalid department ID"}, status=status.HTTP_404_NOT_FOUND)

        doc_id = report_data.get("doc")
        doc_obj = None
        if doc_id:
            try:
                doc_obj = DoctorProfile.objects.get(id=doc_id)
            except DoctorProfile.DoesNotExist:
                return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        caretaker_id = report_data.get("caretaker")
        caretaker_obj = None
        if caretaker_id:
            try:
                caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)

        patient_id = report_data.get("patient")
        patient_obj = None
        if patient_id:
            try:
                patient_obj = PatientProfile.objects.get(id=patient_id)
            except PatientProfile.DoesNotExist:
                return Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)

        # Step 3: Get uploaded files (multiple)
        lab_report_files = request.FILES.getlist("lab_reports")

        # Step 4: Transaction block to ensure atomic save
        try:
            with transaction.atomic():
                appointment = VerimedBookAppointment.objects.create(
                    sponsor=spon_obj,
                    dep=dep_obj,
                    doc=doc_obj,
                    patient=patient_obj,
                    caretaker=caretaker_obj,
                    appointment_date=report_data.get("appointment_date"),
                    appointment_time=report_data.get("appointment_time"),
                    appointment_type=report_data.get("appointment_type"),
                    treatment_performed=report_data.get("treatment_performed"),
                    care_taker_notes=report_data.get("care_taker_notes"),
                    amount=report_data.get("amount"),
                    subscription_plan=report_data.get("subscription_plan"),
                    height=report_data.get("height"),
                    weight=report_data.get("weight"),
                    blood_pressure=report_data.get("blood_pressure"),
                    blood_sugar=report_data.get("blood_sugar"),
                    medical_history=report_data.get("medical_history"),
                    appointment_history=report_data.get("appointment_history"),
                    time_line=report_data.get("time_line"),
                    appointment_reason=report_data.get("appointment_reason"),
                    appointment_status=report_data.get("appointment_status", "Pending"),
                    preferred_dates=report_data.get("preferred_dates"),
                    preferred_times=report_data.get("preferred_times"),
                    service_purchased=report_data.get("service_purchased")
                    
                )

                # Step 5: Save multiple lab reports
                if lab_report_files:
                    for file_obj in lab_report_files:
                        VerimedBookAppointmentLabReports.objects.create(
                            appointment=appointment,
                            file=file_obj,
                            patient=patient_obj,
                            referid=appointment.id
                        )
                from django.core.mail import EmailMessage
                from django.conf import settings
                 # ✅ Add three recipient emails
                sponsoremail = spon_obj.user.email
                sponsorname = spon_obj.user.first_name
                    
                def send_api_verticalcontact_mail(sponsorname,sponsoremail):
                    subject = "Thank You — Your Appointment Request Is Being Processed"                    
                    message = f"""
                    <p>Hello <strong>{sponsorname}</strong>,</p>

                    <p>
                        Thank you for scheduling with VeriMED, the trusted in-home and virtual care
                        program for Cameroon’s global families.
                    </p>

                    <p>
                        Your appointment request has been received. Our care coordination team is
                        reviewing your preferred date and time. You will receive a formal
                        confirmation shortly.
                    </p>

                    <p>
                        Thank you for choosing a service designed to give aging parents premium care —
                        and families abroad peace of mind.
                    </p>

                    <p>
                        With gratitude,<br>
                        <strong>The VeriMED Clinical & Care Coordination Team</strong><br>
                        Physician-Led. Nurse-Powered. Cameroon’s Trusted Home Health Service.<br>
                        Global-Standard Medical Care for Loved Ones Back Home.
                    </p>

                    <p>www.Verimed.care ~~~ Serving Families Worldwide</p>
                    """   
                    
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [sponsoremail]

                    
                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                        email_msg.content_subtype = "html"  # VERY IMPORTANT
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Vertical contact email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Appoinment Booking Post sending vertical contact email: {e}")
                        return False
                    
                send_api_verticalcontact_mail(sponsorname,sponsoremail)
                

                return Response(
                    {"message": "Patient appointment booked successfully"},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def patch(self, request):
       
       # Step 1: Parse JSON data
        raw_data = request.data.get("bookappoinment_data")
        if not raw_data:
            return Response({"error": "bookappoinment_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(raw_data, str):
            try:
                report_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_data, dict):
            report_data = raw_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
         # Step 2: Get existing appointment
        appointment_id = report_data.get("update_appoinmentid")
        if not appointment_id:
            return Response({"error": "update_appoinmentid is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            appointmentobj = VerimedBookAppointment.objects.get(id=appointment_id)
        except VerimedBookAppointment.DoesNotExist:
            return Response({"error": "Invalid update_appoinmentid"}, status=status.HTTP_404_NOT_FOUND)


        # Step 2: Validate Foreign Keys
        sponid=report_data.get("sponsor")
        spon_obj=None
        if sponid:
            try:
                spon_obj = SponsorProfile.objects.get(id=sponid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)

        
        dep_id = report_data.get("dep")
        dep_obj = None
        if dep_id:
            try:
                dep_obj = VerimedDepartment.objects.get(id=dep_id)
            except VerimedDepartment.DoesNotExist:
                return Response({"error": "Invalid department ID"}, status=status.HTTP_404_NOT_FOUND)

        doc_id = report_data.get("doc")
        doc_obj = None
        if doc_id:
            try:
                doc_obj = DoctorProfile.objects.get(id=doc_id)
            except DoctorProfile.DoesNotExist:
                return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        caretaker_id = report_data.get("caretaker")
        caretaker_obj = None
        if caretaker_id:
            try:
                caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)

        patient_id = report_data.get("patient")
        patient_obj = None
        if patient_id:
            try:
                patient_obj = PatientProfile.objects.get(id=patient_id)
            except PatientProfile.DoesNotExist:
                return Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)


        # Step 4: Handle uploaded files
        lab_report_files = list(request.FILES.getlist("lab_reports"))
        lab_report_ids = list(request.data.getlist("lab_report_ids"))
        print("lab_report_files",lab_report_files)
        print("lab_report_ids",lab_report_ids)
        print(len(lab_report_files))
        print(len(lab_report_ids))
        
        if lab_report_files or lab_report_ids:
            # --- Normalize lab_report_ids ---
            # Handle case where input is like ['1,2,null']
            if len(lab_report_ids) == 1 and "," in lab_report_ids[0]:
                lab_report_ids = lab_report_ids[0].split(",")

            # Clean up invalid or placeholder values
            cleaned_ids = []
            for val in lab_report_ids:
                if val and val.lower() not in ["null", "none", ""]:
                    try:
                        cleaned_ids.append(int(val))
                    except ValueError:
                        cleaned_ids.append(None)
                else:
                    cleaned_ids.append(None)

            if len(lab_report_files) != len(cleaned_ids):
                return Response(
                    {
                        "error": f"The number of lab_reports ({len(lab_report_files)}) "
                                f"does not match the number of lab_report_ids ({len(lab_report_ids)})"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        # print(dddd)
        # Step 5: Transaction block
        try:
            with transaction.atomic():
                # FK assignments
                mapping = {
                    "sponsor": spon_obj,
                    "dep": dep_obj,
                    "doc": doc_obj,
                    "patient": patient_obj,
                    "caretaker": caretaker_obj,
                }

                for field, obj in mapping.items():
                    if obj:
                        setattr(appointmentobj, field, obj)

                
                # Update all scalar fields (keep defaults if missing)
                for field in [
                    "appointment_date", "appointment_time", "appointment_type",
                    "treatment_performed", "care_taker_notes", "amount",
                    "subscription_plan", "height", "weight", "blood_pressure",
                    "blood_sugar", "medical_history", "appointment_history",
                    "time_line", "appointment_reason", "appointment_status",
                    "preferred_dates", "preferred_times", "service_purchased"
                ]:
                    if field in report_data:
                        setattr(appointmentobj, field, report_data.get(field))

                appointmentobj.save()

                
                # appointmentobj.appointment_date=report_data.get("appointment_date",appointmentobj.appointment_date)
                # appointmentobj.appointment_time=report_data.get("appointment_time",appointmentobj.appointment_time)
                # appointmentobj.appointment_type=report_data.get("appointment_type",appointmentobj.appointment_type)
                # appointmentobj.treatment_performed=report_data.get("treatment_performed",appointmentobj.treatment_performed)
                # appointmentobj.care_taker_notes=report_data.get("care_taker_notes")
                # appointmentobj.amount=report_data.get("amount")
                # appointmentobj.subscription_plan=report_data.get("subscription_plan")
                # appointmentobj.height=report_data.get("height")
                # appointmentobj.weight=report_data.get("weight")
                # appointmentobj.blood_pressure=report_data.get("blood_pressure")
                # appointmentobj.blood_sugar=report_data.get("blood_sugar")
                # appointmentobj.medical_history=report_data.get("medical_history")
                # appointmentobj.appointment_history=report_data.get("appointment_history")
                # appointmentobj.time_line=report_data.get("time_line")
                # appointmentobj.appointment_reason=report_data.get("appointment_reason")
                # appointmentobj.appointment_status=report_data.get("appointment_status")
                # appointmentobj.preferred_dates=report_data.get("preferred_dates")
                # appointmentobj.preferred_times=report_data.get("preferred_times")
                # appointmentobj.service_purchased=report_data.get("service_purchased")

                # appointmentobj.save()
               
                if lab_report_files or lab_report_ids:
                    # Handle lab reports (update or create)
                    for index, file_obj in enumerate(lab_report_files):
                        report_id = cleaned_ids[index]

                        if report_id:
                            try:
                                report = VerimedBookAppointmentLabReports.objects.get(id=report_id)
                                report.file = file_obj
                                report.save()
                            except VerimedBookAppointmentLabReports.DoesNotExist:
                                raise NotFound(detail=f"Invalid lab report ID: {report_id}")
                        else:
                            VerimedBookAppointmentLabReports.objects.create(
                                appointment=appointmentobj,
                                file=file_obj,
                                patient=appointmentobj.patient,
                                referid=appointmentobj.id
                            )
                
                # Fetch all lab reports for this appointment & patient
                lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                    appointment_id=appointmentobj.id,
                    patient_id=patient_obj.id
                )
                print("lab_reports_qs",lab_reports_qs)
                
                # Build document list
                documents = []
                if lab_reports_qs:
                    for report in lab_reports_qs: 
                        documents.append({
                            # "id": report.id,
                            # "name": report.file.name if report.file else None,
                            # "uploaded_at": report.uploaded_at,
                            # "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                            "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                        })      
                       
                sponsorname=spon_obj.user.first_name if spon_obj and spon_obj.user else None
                departmentname=dep_obj.dep_name if dep_obj and dep_obj else None
                doctorname=doc_obj.user.first_name if doc_obj and doc_obj.user else None
                patientname=patient_obj.patient_name if patient_obj and patient_obj else None
                caretakername = caretaker_obj.user.first_name if caretaker_obj and caretaker_obj.user else None
                date=appointmentobj.appointment_date
                time=appointmentobj.appointment_time
                print("sponsorname",sponsorname)
                
                print("jjjjj")
                
                from django.core.mail import EmailMessage
                from django.conf import settings

                # def send_api_verticalcontact_mail(sponsorname,date,time,patientname):
                #     subject = "Your VeriMED Appointment Is Confirmed"
                #     message = f"""
                #         <p>Hello <strong>{sponsorname}</strong>,</p>

                #         <p>
                #             Your appointment with VeriMED’s physician-led, nurse-powered care team
                #             has been <strong>confirmed</strong>.
                #         </p>

                #         <p>
                #             <strong>Date:</strong> {date}<br>
                #             <strong>Time:</strong> {time}<br>
                #             <strong>Provider:</strong> {patientname}
                #         </p>

                #         <p>
                #             Our mission is simple: deliver global-standard medical care to your loved one,
                #             and provide you with complete clarity every step of the way.
                #         </p>

                #         <p>
                #             If you need adjustments, please reach out through your portal.
                #         </p>

                #         <p>
                #             With gratitude,<br>
                #             <strong>The VeriMED Clinical & Care Coordination Team</strong><br>
                #             Physician-Led. Nurse-Powered. Cameroon’s Trusted Home Health Service.<br>
                #             Global-Standard Medical Care for Loved Ones Back Home.
                #         </p>

                #         <p>www.Verimed.care ~~~ Serving Families Worldwide</p>
                #         """
                    
                #     from_email = settings.DEFAULT_FROM_EMAIL
                    
                #     # ✅ Add three recipient emails
                #     sponsoremail = spon_obj.user.email
                #     doctoremail = doc_obj.user.email
                #     caretakeremail = getattr(getattr(caretaker_obj, "user", None), "email", None)
                #     print("dddddddddd")

                #     recipient_list = [sponsoremail, doctoremail]

                    
                #     try:
                #         email_msg = EmailMessage(subject, "", from_email, recipient_list)
                #         email_msg.content_subtype = "html"  # VERY IMPORTANT
                #         email_msg.body = message
                #         email_msg.send(fail_silently=False)
                #         print("Appoinment Booking email sent successfully")
                #         return True
                #     except Exception as e:
                #         print(f"Error sending vertical contact email: {e}")
                #         return False
                    
                # send_api_verticalcontact_mail(sponsorname,date,time,patientname)
                
                def send_api_care_update_mail(sponsorname, patientname):
                    subject = "Your appointment is confirmed a New Care Update is Available in Your VeriMED Portal"
                    message = f"""
                        <p>Dear <strong>{sponsorname}</strong>,</p>

                        <p>Your appointment is confirmed a new care update has been added to your VeriMED Family Portal.</p>

                        <p>
                            Our healthcare team has completed today's visit with <strong>{patientname}</strong>,
                            and the clinical documentation has now been securely uploaded for your review.
                        </p>

                        <p>Depending on today's visit, your update may include:</p>
                        <ul>
                            <li>Clinical observations and nursing or physician notes</li>
                            <li>Changes in health status</li>
                            <li>Vital signs and assessment findings</li>
                            <li>Medications or treatment updates</li>
                            <li>Recommendations and follow-up plans</li>
                            <li>Photos or supporting documents (when appropriate)</li>
                        </ul>

                        <p>To review the latest information, simply log in to your VeriMED Portal at your convenience.</p>

                        <p>
                            Your family's peace of mind is important to us. We remain committed to providing
                            timely communication, compassionate care, and professional oversight so you can
                            stay informed, wherever you are.
                        </p>

                        <p>Thank you for trusting VeriMED with your care and the care of your loved one.</p>

                        <p>
                            Warm regards,<br>
                            <strong>The VeriMED Care Team</strong><br>
                            Bringing World-Class Healthcare to Cameroon<br>
                            <a href="https://www.verimed.care">www.verimed.care</a>
                        </p>
                        """

                    from_email = settings.DEFAULT_FROM_EMAIL

                    sponsoremail = spon_obj.user.email

                    recipient_list = [sponsoremail]

                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                        email_msg.content_subtype = "html"  # VERY IMPORTANT
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Care update email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Error sending care update email: {e}")
                        return False

                send_api_care_update_mail(sponsorname, patientname)
                        
                return Response({"message": "Appointment updated successfully Check the Email"}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        try:
            # Fetch all appointments
            appointments_qs = VerimedBookAppointment.objects.all().order_by('-id')
            serializer = VerimedBookAppointmentViewSlr(appointments_qs, many=True,context={'request': request})

            response_data = []

            for item in serializer.data:
                appointment_id = item["id"]
                patient_id = item["patient"]["id"] if item.get("patient") else None

                # Fetch all lab reports for this appointment & patient
                lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                    appointment_id=appointment_id,
                    patient_id=patient_id
                )

                # Build document list
                documents = []
                for report in lab_reports_qs:
                    documents.append({
                        "id": report.id,
                        "filename": report.file.name if report.file else None,
                        "uploaded_at": report.uploaded_at,
                        "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                        "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                    })

                # Merge documents into appointment data
                item_with_docs = dict(item)  # Convert OrderedDict to dict
                item_with_docs["documents"] = documents
                response_data.append(item_with_docs)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self,request):
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            appoinmentdeleteids = request.data.get("appoinmentdeleteids")  # form-data
        else:
            appoinmentdeleteids = request.data.get("appoinmentdeleteids", [])  # JSON list

        if not appoinmentdeleteids:
            return Response(
                {"error": "No Appoinment Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = []
        
        for i in appoinmentdeleteids:
            try:
                appointmentdeleteobj=VerimedBookAppointment.objects.get(id=i)
            except VerimedBookAppointment.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Appoinment Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                for i in appoinmentdeleteids:
                    try:
                        appointmentdeleteobj = VerimedBookAppointment.objects.get(id=i)

                        # Delete related documents
                        VerimedBookAppointmentLabReports.objects.filter(
                            referid=appointmentdeleteobj.id,
                        ).delete()

                        # Delete the award
                        appointmentdeleteobj.delete()
                             
                    except VerimedBookAppointment.DoesNotExist:
                        return Response({"error": "Invalid Appoinment Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)

                return Response({"message": "Appoinment  Deleted sucessfully"}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VB_PatientAppoinment_List(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        patientprofileid=request.data.get("patientprofileid")
        try:
                # Fetch all appointments
                appointments_qs = VerimedBookAppointment.objects.filter(patient_id=patientprofileid).order_by('-id')                
                serializer = VerimedBookAppointmentViewSlr(appointments_qs, many=True,context={'request': request})

                response_data = []

                for item in serializer.data:
                    appointment_id = item["id"]
                    patient_id = item["patient"]["id"] if item.get("patient") else None

                    # Fetch all lab reports for this appointment & patient
                    lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                        appointment_id=appointment_id,
                        patient_id=patient_id
                    )

                    # Build document list
                    documents = []
                    for report in lab_reports_qs:
                        documents.append({
                            "id": report.id,
                            "filename": report.file.name if report.file else None,
                            "uploaded_at": report.uploaded_at,
                            "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                            "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                        })

                    # Merge documents into appointment data
                    item_with_docs = dict(item)  # Convert OrderedDict to dict
                    item_with_docs["documents"] = documents
                    response_data.append(item_with_docs)

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VB_DoctorAppoinment_List(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        doctorprofileid=request.data.get("doctorprofileid")
        try:
                # Fetch all appointments
                appointments_qs = VerimedBookAppointment.objects.filter(doc_id=doctorprofileid).order_by('-id')                
                serializer = VerimedBookAppointmentViewSlr(appointments_qs, many=True,context={'request': request})

                response_data = []

                for item in serializer.data:
                    appointment_id = item["id"]
                    patient_id = item["patient"]["id"] if item.get("patient") else None

                    # Fetch all lab reports for this appointment & patient
                    lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                        appointment_id=appointment_id,
                        patient_id=patient_id
                    )

                    # Build document list
                    documents = []
                    for report in lab_reports_qs:
                        documents.append({
                            "id": report.id,
                            "filename": report.file.name if report.file else None,
                            "uploaded_at": report.uploaded_at,
                            "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                            "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                        })

                    # Merge documents into appointment data
                    item_with_docs = dict(item)  # Convert OrderedDict to dict
                    item_with_docs["documents"] = documents
                    response_data.append(item_with_docs)

                return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DoctorProfileUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def patch(self,request):
        update_data = request.data.get("doctorprofile_update_data")
        if not update_data:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(update_data, str):
            import json
            try:
                data = json.loads(update_data)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        
        try:
            doc_updateobj= DoctorProfile.objects.get(id=data.get("doc_profile_updateid"))
        except DoctorProfile.DoesNotExist:
            return Response({"error": "Give me a valid DoctorProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        dep_obj=None
        dep = data.get("dep")
        if dep:
            try:
                dep_obj= VerimedDepartment.objects.get(id=dep)
            except VerimedDepartment.DoesNotExist:
                return Response({"error": "Give me a valid DoctorProfile"}, status=status.HTTP_404_NOT_FOUND)
    
        
        countrycode_obj=None
        countrycode = data.get("doc_country_code")
        if countrycode:
            mobile = data.get("doc_phone")
            if mobile: 
                try:
                    countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                    dialcode = countrycode_obj.dial_code
                    phonewithcountrycode = f"{dialcode}-{mobile}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid Country Code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        try:
            with transaction.atomic():
                if dep_obj:
                    doc_updateobj.dep = dep_obj
                if countrycode_obj:
                    doc_updateobj.doc_country_code = countrycode_obj
                    doc_updateobj.doc_phone = phonewithcountrycode
                else:
                    doc_updateobj.doc_phone = data.get("doc_phone", doc_updateobj.doc_phone)

                doc_updateobj.doc_address=data.get("doc_address",doc_updateobj.doc_address)
                doc_updateobj.doc_exprience=data.get("doc_exprience",doc_updateobj.doc_exprience)
                doc_updateobj.doc_gender=data.get("doc_gender",doc_updateobj.doc_gender)
                doc_updateobj.speciality=data.get("speciality",doc_updateobj.speciality)
                doc_updateobj.joining_date=data.get("joining_date",doc_updateobj.joining_date)
                doc_updateobj.doc_licence_no=data.get("doc_licence_no",doc_updateobj.doc_licence_no)
                doc_updateobj.doc_city=data.get("doc_city",doc_updateobj.doc_city)
                doc_updateobj.doc_state=data.get("doc_state",doc_updateobj.doc_state)
                doc_updateobj.doc_country=data.get("doc_country",doc_updateobj.doc_country)
                doc_updateobj.doc_pincode=data.get("doc_pincode",doc_updateobj.doc_pincode)
                doc_updateobj.save()
                return Response(
                    {"message": "Doctor Profile Updated successfully"},
                    status=status.HTTP_200_OK
                )
                
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

class DoctorProfileList(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # authentication_classes = []        # No authentication required
    # permission_classes = [AllowAny]    # Anyone can access

    def get(self, request):
        doctor_profiles = DoctorProfile.objects.all()
        print("dddd")
        serializer = DoctorProfileViewSlr(doctor_profiles, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientProfileCreateUpdate(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def post(self,request):
        update_data = request.data.get("patientprofile_data")
        if not update_data:
            return Response({"error": "patientprofile_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(update_data, str):
            import json
            try:
                data = json.loads(update_data)
            except Exception:
                return Response({"error": "Invalid JSON format patientprofile_data"}, status=status.HTTP_400_BAD_REQUEST)

        medication_data = request.data.get("medication")
        if medication_data:
        
            # If user_update_data is a JSON string, parse it
            if isinstance(medication_data, str):
                import json
                try:
                    medication = json.loads(medication_data)
                except Exception:
                    return Response({"error": "Invalid JSON format medication"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            medication=None
        
        sponsorobj=None
        sponsorid = data.get("sponsorid")
        if sponsorid:
            try:
                sponsorobj= SponsorProfile.objects.get(id=sponsorid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Give me a valid SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({"error": "Give me a SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)

    
        # doctorobj=None
        # doctorid = data.get("doctorid")
        # if doctorid:
        #     try:
        #         doctorobj= DoctorProfile.objects.get(id=doctorid)
        #     except DoctorProfile.DoesNotExist:
        #         return Response({"error": "Give me a valid DoctoProfile"}, status=status.HTTP_404_NOT_FOUND)
    
        caretakerobj=None
        caretakerid = data.get("caretakerid")
        if caretakerid:
            try:
                caretakerobj= CareTakerProfile.objects.get(id=caretakerid)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Give me a valid CareTakerProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        country_code_obj=None
        phonewithcountrycode=None
        country_code = data.get("country_code")
        if country_code:
            phone = data.get("phone")
            if phone: 
                try:
                    country_code_obj = VerimedCountryCode.objects.get(code=country_code)
                    dialcode = country_code_obj.dial_code
                    phonewithcountrycode = f"{dialcode}-{phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
               
    
        print("phonewithcountrycode",phonewithcountrycode)
        emer_con_country_code_obj=None
        emer_con_phonewithcountrycode=None
        emer_con_country_code = data.get("emer_con_country_code")
        if emer_con_country_code:
            emer_con_phone = data.get("emer_con_phone")
            if emer_con_phone: 
                try:
                    emer_con_country_code_obj = VerimedCountryCode.objects.get(code=emer_con_country_code)
                    dialcode = emer_con_country_code_obj.dial_code
                    emer_con_phonewithcountrycode = f"{dialcode}-{emer_con_phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid emer_con_country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        print("emer_con_phonewithcountrycode",emer_con_phonewithcountrycode)
        local_con_country_code_obj=None
        local_con_phonewithcountrycode=None
        local_con_country_code = data.get("local_con_country_code")
        if local_con_country_code:
            local_con_phone = data.get("local_con_phone")
            if local_con_phone: 
                try:
                    local_con_country_code_obj = VerimedCountryCode.objects.get(code=emer_con_country_code)
                    dialcode = local_con_country_code_obj.dial_code
                    local_con_phonewithcountrycode = f"{dialcode}-{local_con_phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid local_con_country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        # Step 4: Handle uploaded files
        upload_files = list(request.FILES.getlist("patient_upload_files"))
        # upload_files_ids = list(request.data.getlist("patient_files_ids"))
        upload_files_name = list(request.data.getlist("patient_files_name"))
        print("upload_files_name")
        
        if upload_files or upload_files_name:
            print("upload_files",upload_files)
            # print("upload_files_ids",upload_files_ids)
            print("upload_files_name",upload_files_name)
            print(len(upload_files))
            # print(len(upload_files_ids))
            
        # --- Normalize upload_files_ids ---
            # Handle case where input is like ['1,2,null']
            # if len(upload_files_ids) == 1 and "," in upload_files_ids[0]:
            #     upload_files_ids = upload_files_ids[0].split(",")

            # # Clean up invalid or placeholder values
            # cleaned_upload_files_ids = []
            # for val in upload_files_ids:
            #     if val and val.lower() not in ["null", "none", ""]:
            #         try:
            #             cleaned_upload_files_ids.append(int(val))
            #         except ValueError:
            #             cleaned_upload_files_ids.append(None)
            #     else:
            #         cleaned_upload_files_ids.append(None)
                    
            # print("cleaned_upload_files_ids",cleaned_upload_files_ids)

            # --- Normalize upload_files_name ---
            # Handle case where input is like ['1,2,null']
            if len(upload_files_name) == 1 and "," in upload_files_name[0]:
                upload_files_name = upload_files_name[0].split(",")

            # Clean up invalid or placeholder values
            cleaned_upload_files_name = []
            
            for val in upload_files_name:
                    
                    cleaned_upload_files_name.append(val)
                    
            print("cleaned_upload_failes_name",cleaned_upload_files_name)
            
            if not (len(upload_files) == len(cleaned_upload_files_name)):
                return Response(
                    
                     {
            "error": (
                f"Mismatch in counts: upload_files ({len(upload_files)}), "
                # f"patient_files_ids ({len(cleaned_upload_files_ids)}), "
                f"patient_files_name ({len(cleaned_upload_files_name)})"
            )
        },
        status=status.HTTP_400_BAD_REQUEST
                )
        
        
        photo = request.data.get("patient_photo",None)
        if photo:
            photo=photo
        print("hii")    

    
        try:
            with transaction.atomic():
                patient_profile=PatientProfile.objects.create(
                    
                    sponsor=sponsorobj,
                    caretaker=caretakerobj,
                    country_code=country_code_obj,
                    phone=phonewithcountrycode,
                    photo=photo,
                    
                        
                    emer_con_country_code = emer_con_country_code_obj,
                    emer_con_phone = emer_con_phonewithcountrycode,
                    
                    local_con_country_code = local_con_country_code_obj,
                    local_con_phone = local_con_phonewithcountrycode,

                    email=data.get("email") or None,
                    age=data.get("age"),
                    # 
                    height=data.get("height") or None,
                    weight=data.get("weight") or None,
                    blood_pressure=data.get("blood_pressure") or None,
                    blood_sugar=data.get("blood_sugar") or None,
                    heart_rate=data.get("heart_rate") or None,
                    oxygen=data.get("oxygen") or None,
                    temperature=data.get("temperature") or None,
                    respiratory_rate=data.get("respiratory_rate") or None,
                    
                    patient_name=data.get("patient_name") or None,
                    patient_dob=data.get("patient_dob") or None,
                    patient_gender=data.get("patient_gender") or None,
                    blood_group=data.get("blood_group") or None,
                    patient_home_address=data.get("patient_home_address") or None,
                    primary_language=data.get("primary_language") or None,
                    religion=data.get("religion") or None,
                    escalate_to_physician=data.get("escalate_to_physician") or None,
                    
                    # Emergency Contact
                    emer_con_name=data.get("emer_con_name")or None,
                    emer_con_relation=data.get("emer_con_relation") or None,
                    emer_con_coun_of_residen=data.get("emer_con_coun_of_residen") or None,
                    emer_con_email=data.get("emer_con_email") or None,
                    
                    local_con_name=data.get("local_con_name") or None,
                    local_con_relation=data.get("local_con_relation") or None,

                    
                    # Reason for Enrollment
                    reason_enrollment=data.get("reason_enrollment") or None,
                    reason_other=data.get("reason_other") or None,
                    
                    # Medical History
                    medical_his_diagnosis=data.get("medical_his_diagnosis") or None,
                    medical_his_cancer=data.get("medical_his_cancer") or None,
                    medical_his_other=data.get("medical_his_other") or None,
                    medical_his_provided_medi_care=data.get("medical_his_provided_medi_care") or None,
                    medical_his_major_surgeries=data.get("medical_his_major_surgeries") or None,
                    medical_his_curr_symp=data.get("medical_his_curr_symp") or None,
                    
                    # Medication
                    medication=medication,
                    # medication_name=data.get("medication_name"),
                    # medication_dose=data.get("medication_dose"),
                    # medication_frequency=data.get("medication_frequency"),
                    # medication_reason=data.get("medication_reason"),
                    # medication_issues=data.get("medication_issues"),
                    # medication_issues_explain=data.get("reasomedication_issues_explainn_other"),
                    
                    # Allergies
                    allergies_issues=data.get("allergies_issues") or False,
                    allergies_drug=data.get("allergies_drug") or None,
                    allergies_food=data.get("allergies_food") or None,
                    
                    # Functional Abilities
                    functional_bathe=data.get("functional_bathe") or None,
                    functional_dress=data.get("functional_dress") or None,
                    functional_eat=data.get("functional_eat") or None,
                    functional_walk=data.get("functional_walk") or None,
                    functional_use_bathroom=data.get("functional_use_bathroom") or None,
                    functional_daily_activity=data.get("functional_daily_activity") or None,
                    functional_manage_finance=data.get("functional_manage_finance") or None,
                    functional_any_falls=data.get("functional_any_falls") or False,
                    functional_how_many=data.get("functional_how_many") or None,
                    functional_memory_pbms=data.get("functional_memory_pbms") or False,
                    
                    # Lifestyle
                    lifestyle_daily_routine=data.get("lifestyle_daily_routine") or None,
                    lifestyle_dietary_habits=data.get("lifestyle_dietary_habits") or None,
                    lifestyle_sleep_quality=data.get("lifestyle_sleep_quality") or None,
                    lifestyle_physical_activity=data.get("lifestyle_physical_activity") or None,
                    lifestyle_alcohol_use=data.get("lifestyle_alcohol_use") or None,
                    lifestyle_pain_complaints=data.get("lifestyle_pain_complaints") or None,
                    lifestyle_pain_where=data.get("lifestyle_pain_where") or None,
                    
                    # Social and Emotional
                    social_emotion_health=data.get("social_emotion_health") or None,
                    social_spiritual_needs=data.get("social_spiritual_needs") or None,
                    social_trusted_person=data.get("social_trusted_person") or False,
                    social_name=data.get("social_name") or None,
                    
                    # Goals
                    goals_family_hope=data.get("goals_family_hope") or None,
                    goals_special_instructions=data.get("goals_special_instructions") or None,
                    goals_term_membership=data.get("goals_term_membership") or None
                    )
                
                patient_profile.save()
                
                if upload_files:
                    # --- Handle lab reports (update or create) ---
                    for index, file_obj in enumerate(upload_files):
                        # report_id = cleaned_upload_files_ids[index]
                        file_name = cleaned_upload_files_name[index]

                        PatientUploadDocuments.objects.create(
                            patient_profile=patient_profile,
                            file=file_obj,
                            filename=file_name,  # optional if model supports this field
                            referid=patient_profile.id
                        )
                        
                sponsorname=sponsorobj.user.first_name
                from django.core.mail import EmailMessage
                from django.conf import settings

                
                def send_api_verticalcontact_mail(sponsorname):
                    subject = "Welcome to VeriMED — Your Premium Care Journey Begins Here"

                    message = f"""
                    <p>Hello <strong>{sponsorname}</strong>,</p>

                    <p>
                        Welcome to VeriMED, Cameroon’s physician-led, nurse-powered home health and
                        geriatric wellness service. We are honored that you have chosen us for your own care.
                    </p>

                    <p>
                        Whether you live in Cameroon or abroad, you deserve medical support that is exceptional,
                        transparent, and dependable. Our team is here to provide you with premium in-home and
                        virtual care designed to help you stay healthy, supported, and confident in every
                        stage of life.
                    </p>

                    <p>Your VeriMED portal is now active. You can log in at any time to:</p>

                    <ul>
                        <li>Schedule your own appointments</li>
                        <li>Receive updates and medical reports</li>
                        <li>Communicate with your care team</li>
                        <li>Request additional services</li>
                        <li>Track your health and wellness progress</li>
                    </ul>

                    

                    <p>
                        At VeriMED, you are not just a patient — you are a valued partner in your own care.
                        Our mission is to provide you with global-standard medical oversight, compassion, and
                        the peace of mind that comes from having a dedicated team by your side.
                    </p>

                    <p>
                        Thank you for trusting VeriMED with your health.
                    </p>

                    <p>
                        With gratitude,<br>
                        <strong>The VeriMED Clinical & Care Coordination Team</strong><br>
                        Physician-Led. Nurse-Powered. Cameroon’s Trusted Home Health Service.<br>
                        Global-Standard Medical Care for Loved Ones Back Home.
                    </p>

                    <p>www.Verimed.care ~~~ Serving Families Worldwide</p>
                    """

                    from_email = settings.DEFAULT_FROM_EMAIL
                    
                    # ✅ Add three recipient emails
                    sponsoremail = sponsorobj.user.email

                    recipient_list = [sponsoremail]

                    
                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                        email_msg.content_subtype = "html"  # VERY IMPORTANT
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Appoinment Booking email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Error sending vertical contact email: {e}")
                        return False
                    
                send_api_verticalcontact_mail(sponsorname)
                

                return Response(
                    {"message": "Patient Profile Created successfully"},
                    status=status.HTTP_200_OK
                )
                
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
             
    def patch(self,request):
        update_data = request.data.get("patientprofile_update_data")
        if not update_data:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(update_data, str):
            import json
            try:
                data = json.loads(update_data)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        medication_data = request.data.get("medication")
        if medication_data:
        
            # If user_update_data is a JSON string, parse it
            if isinstance(medication_data, str):
                import json
                try:
                    medication = json.loads(medication_data)
                except Exception:
                    return Response({"error": "Invalid JSON format medication"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            medication=None
        
        try:
            patient_updateobj= PatientProfile.objects.get(id=data.get("patient_profile_updateid"))
        except PatientProfile.DoesNotExist:
            return Response({"error": "Give me a valid PatientProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        sponsorobj=None
        sponsorid = data.get("sponsorid")
        if sponsorid:
            try:
                sponsorobj= SponsorProfile.objects.get(id=sponsorid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Give me a valid SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)
            
        else:
            return Response({"error": "Give me a SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)

    
    
        # doctorobj=None
        # doctorid = data.get("doctorid")
        # if doctorid:
        #     try:
        #         doctorobj= DoctorProfile.objects.get(id=doctorid)
        #     except DoctorProfile.DoesNotExist:
        #         return Response({"error": "Give me a valid DoctoProfile"}, status=status.HTTP_404_NOT_FOUND)
    
        caretakerobj=None
        phonewithcountrycode=None
        caretakerid = data.get("caretakerid")
        if caretakerid:
            try:
                caretakerobj= CareTakerProfile.objects.get(id=caretakerid)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Give me a valid CareTakerProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        country_code_obj=None
        country_code = data.get("country_code")
        if country_code:
            phone = data.get("phone")
            if phone: 
                try:
                    country_code_obj = VerimedCountryCode.objects.get(code=country_code)
                    dialcode = country_code_obj.dial_code
                    phonewithcountrycode = f"{dialcode}-{phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        
        emer_con_country_code_obj=None
        emer_con_phonewithcountrycode=None
        emer_con_country_code = data.get("emer_con_country_code")
        if emer_con_country_code:
            emer_con_phone = data.get("emer_con_phone")
            if emer_con_phone: 
                try:
                    emer_con_country_code_obj = VerimedCountryCode.objects.get(code=emer_con_country_code)
                    dialcode = emer_con_country_code_obj.dial_code
                    emer_con_phonewithcountrycode = f"{dialcode}-{emer_con_phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid emer_con_country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        local_con_country_code_obj=None
        local_con_phonewithcountrycode=None
        local_con_country_code = data.get("local_con_country_code")
        if local_con_country_code:
            local_con_phone = data.get("local_con_phone")
            if local_con_phone: 
                try:
                    local_con_country_code_obj = VerimedCountryCode.objects.get(code=emer_con_country_code)
                    dialcode = local_con_country_code_obj.dial_code
                    local_con_phonewithcountrycode = f"{dialcode}-{local_con_phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid local_con_country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        # Step 4: Handle uploaded files
        upload_files = list(request.FILES.getlist("patient_upload_files"))
        upload_files_ids = list(request.data.getlist("patient_files_ids"))
        upload_files_name = list(request.data.getlist("patient_files_name"))
        
        if upload_files or upload_files_name or upload_files_name:
            print("upload_files",upload_files)
            print("upload_files_ids",upload_files_ids)
            print("upload_files_name",upload_files_name)
            print(len(upload_files))
            print(len(upload_files_ids))
            
        # --- Normalize upload_files_ids ---
            # Handle case where input is like ['1,2,null']
            if len(upload_files_ids) == 1 and "," in upload_files_ids[0]:
                upload_files_ids = upload_files_ids[0].split(",")

            # Clean up invalid or placeholder values
            cleaned_upload_files_ids = []
            for val in upload_files_ids:
                if val and val.lower() not in ["null", "none", ""]:
                    try:
                        cleaned_upload_files_ids.append(int(val))
                    except ValueError:
                        cleaned_upload_files_ids.append(None)
                else:
                    cleaned_upload_files_ids.append(None)
                    
            print("cleaned_upload_files_ids",cleaned_upload_files_ids)

            # --- Normalize upload_files_name ---
            # Handle case where input is like ['1,2,null']
            if len(upload_files_name) == 1 and "," in upload_files_name[0]:
                upload_files_name = upload_files_name[0].split(",")

            # Clean up invalid or placeholder values
            cleaned_upload_files_name = []
            
            for val in upload_files_name:
                    
                    cleaned_upload_files_name.append(val)
                    
            print("cleaned_upload_files_name",cleaned_upload_files_name)
            
            if not (len(upload_files) == len(cleaned_upload_files_ids) == len(cleaned_upload_files_name)):
                return Response(
                    
                     {
            "error": (
                f"Mismatch in counts: upload_files ({len(upload_files)}), "
                f"patient_files_ids ({len(cleaned_upload_files_ids)}), "
                f"patient_files_name ({len(cleaned_upload_files_name)})"
            )
        },
        status=status.HTTP_400_BAD_REQUEST
                )
        
        photo = request.data.get("patient_photo",None)

        # print(ddddddddddd)
        try:
            with transaction.atomic():
                if sponsorobj:
                    patient_updateobj.sponsor = sponsorobj
                    
                # if doctorobj:
                #     patient_updateobj.doctor = doctorobj
                    
                if caretakerobj:
                    patient_updateobj.caretaker = caretakerobj
                
                if country_code_obj:
                    patient_updateobj.country_code = country_code_obj
                    patient_updateobj.phone = phonewithcountrycode
                # else:
                #     patient_updateobj.emer_con_phone = data.get("emer_con_phone", patient_updateobj.emer_con_phone)
                
                
                if emer_con_country_code_obj:
                    patient_updateobj.emer_con_country_code = emer_con_country_code_obj
                    patient_updateobj.emer_con_phone = emer_con_phonewithcountrycode
                # else:
                #     patient_updateobj.emer_con_phone = data.get("emer_con_phone", patient_updateobj.emer_con_phone)
                
                
                if local_con_country_code_obj:
                    patient_updateobj.local_con_country_code = local_con_country_code_obj
                    patient_updateobj.local_con_phone = local_con_phonewithcountrycode
                # else:
                #     patient_updateobj.local_con_phone = data.get("local_con_phone", patient_updateobj.local_con_phone)
                if photo:
                    patient_updateobj.photo=photo  
                    
                patient_updateobj.email=data.get("email",patient_updateobj.email)
                patient_updateobj.age=data.get("age",patient_updateobj.age)
                # 
                patient_updateobj.height=data.get("height",patient_updateobj.height)
                patient_updateobj.weight=data.get("weight",patient_updateobj.weight)
                patient_updateobj.blood_pressure=data.get("blood_pressure",patient_updateobj.blood_pressure)
                patient_updateobj.blood_sugar=data.get("blood_sugar",patient_updateobj.blood_sugar)
                patient_updateobj.heart_rate=data.get("heart_rate",patient_updateobj.heart_rate)
                patient_updateobj.oxygen=data.get("oxygen",patient_updateobj.oxygen)
                patient_updateobj.temperature=data.get("temperature",patient_updateobj.temperature)
                patient_updateobj.respiratory_rate=data.get("respiratory_rate",patient_updateobj.respiratory_rate)
                       
                     
                patient_updateobj.patient_name=data.get("patient_name",patient_updateobj.patient_name)
                patient_updateobj.patient_dob=data.get("patient_dob",patient_updateobj.patient_dob)
                patient_updateobj.patient_gender=data.get("patient_gender",patient_updateobj.patient_gender)
                patient_updateobj.blood_group=data.get("blood_group",patient_updateobj.blood_group)
                patient_updateobj.patient_home_address=data.get("patient_home_address",patient_updateobj.patient_home_address)
                patient_updateobj.primary_language=data.get("primary_language",patient_updateobj.primary_language)
                patient_updateobj.religion=data.get("religion",patient_updateobj.religion)
                patient_updateobj.escalate_to_physician=data.get("escalate_to_physician",patient_updateobj.escalate_to_physician)
                
                # Emergency Contact
                patient_updateobj.emer_con_name=data.get("emer_con_name",patient_updateobj.emer_con_name)
                patient_updateobj.emer_con_relation=data.get("emer_con_relation",patient_updateobj.emer_con_relation)
                patient_updateobj.emer_con_coun_of_residen=data.get("emer_con_coun_of_residen",patient_updateobj.emer_con_coun_of_residen)
                patient_updateobj.emer_con_email=data.get("emer_con_email",patient_updateobj.emer_con_email)
                
                patient_updateobj.local_con_name=data.get("local_con_name",patient_updateobj.local_con_name)
                patient_updateobj.local_con_relation=data.get("local_con_relation",patient_updateobj.local_con_relation)

                
                # Reason for Enrollment
                patient_updateobj.reason_enrollment=data.get("reason_enrollment",patient_updateobj.reason_enrollment)
                patient_updateobj.reason_other=data.get("reason_other",patient_updateobj.reason_other)
                
                # Medical History
                patient_updateobj.medical_his_diagnosis=data.get("medical_his_diagnosis",patient_updateobj.medical_his_diagnosis)
                patient_updateobj.medical_his_cancer=data.get("medical_his_cancer",patient_updateobj.medical_his_cancer)
                patient_updateobj.medical_his_other=data.get("medical_his_other",patient_updateobj.medical_his_other)
                patient_updateobj.medical_his_provided_medi_care=data.get("medical_his_provided_medi_care",patient_updateobj.medical_his_provided_medi_care)
                patient_updateobj.medical_his_major_surgeries=data.get("medical_his_major_surgeries",patient_updateobj.medical_his_major_surgeries)
                patient_updateobj.medical_his_curr_symp=data.get("medical_his_curr_symp",patient_updateobj.medical_his_curr_symp)
                
                # Medication
                
                patient_updateobj.medication=medication or patient_updateobj.medication
                # patient_updateobj.medication_name=data.get("medication_name",patient_updateobj.medication_name)
                # patient_updateobj.medication_dose=data.get("medication_dose",patient_updateobj.medication_dose)
                # patient_updateobj.medication_frequency=data.get("medication_frequency",patient_updateobj.medication_frequency)
                # patient_updateobj.medication_reason=data.get("medication_reason",patient_updateobj.medication_reason)
                # patient_updateobj.medication_issues=data.get("medication_issues",patient_updateobj.medication_issues)
                # patient_updateobj.medication_issues_explain=data.get("reasomedication_issues_explainn_other",patient_updateobj.medication_issues_explain)
                
                # Allergies
                patient_updateobj.allergies_issues=data.get("allergies_issues",patient_updateobj.allergies_issues)
                patient_updateobj.allergies_drug=data.get("allergies_drug",patient_updateobj.allergies_drug)
                patient_updateobj.allergies_food=data.get("allergies_food",patient_updateobj.allergies_food)
                
                # Functional Abilities
                patient_updateobj.functional_bathe=data.get("functional_bathe",patient_updateobj.functional_bathe)
                patient_updateobj.functional_dress=data.get("functional_dress",patient_updateobj.functional_dress)
                patient_updateobj.functional_eat=data.get("functional_eat",patient_updateobj.functional_eat)
                patient_updateobj.functional_walk=data.get("functional_walk",patient_updateobj.functional_walk)
                patient_updateobj.functional_use_bathroom=data.get("functional_use_bathroom",patient_updateobj.functional_use_bathroom)
                patient_updateobj.functional_daily_activity=data.get("functional_daily_activity",patient_updateobj.functional_daily_activity)
                patient_updateobj.functional_manage_finance=data.get("functional_manage_finance",patient_updateobj.functional_manage_finance)
                patient_updateobj.functional_any_falls=data.get("functional_any_falls",patient_updateobj.functional_any_falls)
                patient_updateobj.functional_how_many=data.get("functional_how_many",patient_updateobj.functional_how_many)
                patient_updateobj.functional_memory_pbms=data.get("functional_memory_pbms",patient_updateobj.functional_memory_pbms)
                
                # Lifestyle
                patient_updateobj.lifestyle_daily_routine=data.get("lifestyle_daily_routine",patient_updateobj.lifestyle_daily_routine)
                patient_updateobj.lifestyle_dietary_habits=data.get("lifestyle_dietary_habits",patient_updateobj.lifestyle_dietary_habits)
                patient_updateobj.lifestyle_sleep_quality=data.get("lifestyle_sleep_quality",patient_updateobj.lifestyle_sleep_quality)
                patient_updateobj.lifestyle_physical_activity=data.get("lifestyle_physical_activity",patient_updateobj.lifestyle_physical_activity)
                patient_updateobj.lifestyle_alcohol_use=data.get("lifestyle_alcohol_use",patient_updateobj.lifestyle_alcohol_use)
                patient_updateobj.lifestyle_pain_complaints=data.get("lifestyle_pain_complaints",patient_updateobj.lifestyle_pain_complaints)
                patient_updateobj.lifestyle_pain_where=data.get("lifestyle_pain_where",patient_updateobj.lifestyle_pain_where)
                
                # Social and Emotional
                patient_updateobj.social_emotion_health=data.get("social_emotion_health",patient_updateobj.social_emotion_health)
                patient_updateobj.social_spiritual_needs=data.get("social_spiritual_needs",patient_updateobj.social_spiritual_needs)
                patient_updateobj.social_trusted_person=data.get("social_trusted_person",patient_updateobj.social_trusted_person)
                patient_updateobj.social_name=data.get("social_name",patient_updateobj.social_name)
                
                # Goals
                patient_updateobj.goals_family_hope=data.get("goals_family_hope",patient_updateobj.goals_family_hope)
                patient_updateobj.goals_special_instructions=data.get("goals_special_instructions",patient_updateobj.goals_special_instructions)
                patient_updateobj.goals_term_membership=data.get("goals_term_membership",patient_updateobj.goals_term_membership)
                
                patient_updateobj.save()
                
                if upload_files:
                    # --- Handle lab reports (update or create) ---
                    for index, file_obj in enumerate(upload_files):
                        report_id = cleaned_upload_files_ids[index]
                        file_name = cleaned_upload_files_name[index]

                        if report_id:
                            try:
                                report = PatientUploadDocuments.objects.get(id=report_id)
                                report.file = file_obj
                                report.filename = file_name or report.filename  # optional: store filename if model has field
                                report.save()
                            except PatientUploadDocuments.DoesNotExist:
                                raise NotFound(detail=f"Invalid patient upload document ID: {report_id}")
                        else:
                            PatientUploadDocuments.objects.create(
                                patient_profile=patient_updateobj,
                                file=file_obj,
                                filename=file_name,  # optional if model supports this field
                                referid=patient_updateobj.id
                            )

                return Response(
                    {"message": "Patient Profile Updated successfully"},
                    status=status.HTTP_200_OK
                )
                
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

class PatientProfileList(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # authentication_classes = []        # No authentication required
    # permission_classes = [AllowAny]    # Anyone can access

    def get(self,request):
        try:
            verimed_doctor_qs = PatientProfile.objects.all()
            serializer = PatientProfileViewSlr(verimed_doctor_qs, many=True)
            
            response_data = []
            
            for item in serializer.data:
                refer_id = item["id"]
                
                all_documents = PatientUploadDocuments.objects.filter(
                    referid=refer_id,
                    
                )
                documents = []
                for report in all_documents:
                    documents.append({
                        "id": report.id,
                        "reson_file":report.filename if report.filename else None,
                        "filename": report.file.name if report.file else None,
                        "uploaded_at": report.uploaded_at,
                        "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                        "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                    })

                # Merge documents into appointment data
                item_with_docs = dict(item)  # Convert OrderedDict to dict
                item_with_docs["documents"] = documents
                response_data.append(item_with_docs)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
     
    def delete(self,request):
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            patientprofiledeleteids = request.data.get("patientprofiledeleteids")  # form-data
        else:
            patientprofiledeleteids = request.data.get("patientprofiledeleteids", [])  # JSON list

        if not patientprofiledeleteids:
            return Response(
                {"error": "No Patient Profile Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = []
        
        for i in patientprofiledeleteids:
            try:
                patiend_deleteobj=PatientProfile.objects.get(id=i)
            except PatientProfile.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Patient Profile Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                deleted_count, _ = PatientProfile.objects.filter(
                    id__in=patientprofiledeleteids
                ).delete()

                if deleted_count == 0:
                    return Response(
                        {"error": "No Patient Profile found for the given IDs."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                return Response(
                    {
                        "message": f"Patient Profile deleted successfully."
                    },
                    status=status.HTTP_200_OK,
)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
        

class SponsoridPatientProfileList(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        sponsorid = request.data.get("sponsorid")
        try:
            sponsor = SponsorProfile.objects.get(id=sponsorid)
        except SponsorProfile.DoesNotExist:
            return Response(
                {"error": "Please provide a valid sponsor ID."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            
            verimed_doctor_qs = PatientProfile.objects.filter(sponsor=sponsor.id)
            serializer = PatientProfileViewSlr(verimed_doctor_qs, many=True)
            
            response_data = []
            
            for item in serializer.data:
                refer_id = item["id"]
                
                all_documents = PatientUploadDocuments.objects.filter(
                    referid=refer_id,
                    
                )
                documents = []
                for report in all_documents:
                    documents.append({
                        "id": report.id,
                        "reson_file":report.filename if report.filename else None,
                        "filename": report.file.name if report.file else None,
                        "uploaded_at": report.uploaded_at,
                        "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                        "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                    })

                # Merge documents into appointment data
                item_with_docs = dict(item)  # Convert OrderedDict to dict
                item_with_docs["documents"] = documents
                response_data.append(item_with_docs)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SponsoridPatientProfileDelete(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def delete(self,request):
        sponsorid = request.data.get("sponsorid")
        try:
            sponsor = SponsorProfile.objects.get(id=sponsorid)
        except SponsorProfile.DoesNotExist:
            return Response(
                {"error": "Please provide a valid sponsor ID."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            patientprofiledeleteids = request.data.get("patientprofiledeleteids")  # form-data
        else:
            patientprofiledeleteids = request.data.get("patientprofiledeleteids", [])  # JSON list

        if not patientprofiledeleteids:
            return Response(
                {"error": "No Patient Deleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = []
        
        for i in patientprofiledeleteids:
            try:
                patientprofiledeleteobj=PatientProfile.objects.get(id=i,sponsor=sponsor)
            except PatientProfile.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Patient Profile Deleteids Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
 
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                for i in patientprofiledeleteids:
                    try:
                        patientprofiledeleteobj = PatientProfile.objects.get(id=i,sponsor=sponsor)
                        
                        
                        # Delete related documents
                        PatientUploadDocuments.objects.filter(
                            referid=patientprofiledeleteobj.id,
                        ).delete()

                        # Delete the award
                        patientprofiledeleteobj.delete()
                             
                    except PatientProfile.DoesNotExist:
                        return Response({"error": "Invalid Patient Profile  Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)

                return Response({"message": "Patient Deleted sucessfully"}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
       

class SponsorProfileUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
       
    def patch(self,request):
        update_data = request.data.get("sponsorprofile_update_data")
        if not update_data:
            return Response({"error": "sponsorprofile_update_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(update_data, str):
            import json
            try:
                data = json.loads(update_data)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        
        try:
            spon_updateobj= SponsorProfile.objects.get(id=data.get("spon_profile_updateid"))
        except SponsorProfile.DoesNotExist:
            return Response({"error": "Give me a valid SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with transaction.atomic():
        
                spon_updateobj.sponsor_address=data.get("sponsor_address",spon_updateobj.sponsor_address)
                spon_updateobj.sponsor_gender=data.get("sponsor_gender",spon_updateobj.sponsor_gender)
                spon_updateobj.work_employment=data.get("work_employment",spon_updateobj.work_employment)
                spon_updateobj.how_found_us=data.get("how_found_us",spon_updateobj.how_found_us)
                spon_updateobj.save()
                return Response(
                    {"message": "Sponsor Profile Updated successfully"},
                    status=status.HTTP_200_OK
                )
                
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def delete(self,request):
            # Get list of IDs from request data
            if hasattr(request.data, "getlist"):
                sponsorprofiledeleteids = request.data.get("sponsorprofiledeleteids")  # form-data
            else:
                sponsorprofiledeleteids = request.data.get("sponsorprofiledeleteids", [])  # JSON list
    
            if not sponsorprofiledeleteids:
                return Response(
                    {"error": "No SponsorProfile Deleted IDs provided."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            notvalidids = []
            
            for i in sponsorprofiledeleteids:
                try:
                    spon_deleteobj=SponsorProfile.objects.get(id=i)
                except SponsorProfile.DoesNotExist:
                    notvalidids.append(i)
    
            if notvalidids:
                return Response(
                    {
                        "error": "Invalid Sponser Profile Deleted IDs.",
                        "invalid_ids": notvalidids
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
     
            
            # --- DATABASE DE choose LETE ---
            try:
                with transaction.atomic():
                    deleted_count, _ = SponsorProfile.objects.filter(
                        id__in=sponsorprofiledeleteids
                    ).delete()

                    if deleted_count == 0:
                        return Response(
                            {"error": "No Sponsor Profile found for the given IDs."},
                            status=status.HTTP_404_NOT_FOUND,
                        )

                    return Response(
                        {
                            "message": f"Sponsor Profile deleted successfully."
                        },
                        status=status.HTTP_200_OK,
)
                        
            except Exception as e:
                return Response(
                    {"error": f"Unexpected error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        

class SponsorProfileList(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    

    def get(self,request):
        try:
            verimed_doctor_qs = SponsorProfile.objects.all()
            serializer = SponsorProfileViewSlr(verimed_doctor_qs, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class SponsorPatientsView(APIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]
#     def post(self, request):
#         sponsorprofileid = request.data.get("sponsorprofileid")

#         if not sponsorprofileid:
#             return Response(
#                 {"error": "sponsorprofileid is required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         try:
#             # Get the sponsor
#             sponsor = SponsorProfile.objects.get(id=sponsorprofileid)

#             # Get all patients linked to that sponsor
#             patients = PatientProfile.objects.filter(sponsor=sponsor.id)

#             # Serialize the patients
#             serializer = PatientProfileViewSlr(patients, many=True)

#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except SponsorProfile.DoesNotExist:
#             return Response(
#                 {"error": "Sponsor not found"},
#                 status=status.HTTP_404_NOT_FOUND,
#             )
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class CaretakerProfileUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
       
    def patch(self,request):
        update_data = request.data.get("caretakerprofile_update_data")
        if not update_data:
            return Response({"error": "caretakerprofile_update_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user_update_data is a JSON string, parse it
        if isinstance(update_data, str):
            import json
            try:
                data = json.loads(update_data)
            except Exception:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        
        try:
            caretake_updateobj= CareTakerProfile.objects.get(id=data.get("caretaker_profile_updateid"))
        except CareTakerProfile.DoesNotExist:
            return Response({"error": "Give me a valid CaretakerrProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with transaction.atomic():
        
                caretake_updateobj.caretaker_address=data.get("caretaker_address",caretake_updateobj.caretaker_address)
                caretake_updateobj.caretaker_exprience=data.get("caretaker_exprience",caretake_updateobj.caretaker_exprience)
                caretake_updateobj.care_gender=data.get("care_gender",caretake_updateobj.care_gender)
                caretake_updateobj.credentials=data.get("credentials",caretake_updateobj.credentials)              
                caretake_updateobj.yr_of_graduation=data.get("yr_of_graduation",caretake_updateobj.yr_of_graduation)
                caretake_updateobj.skillset=data.get("skillset",caretake_updateobj.skillset)
                caretake_updateobj.title=data.get("title",caretake_updateobj.title)

                caretake_updateobj.save()
                return Response(
                    {"message": "Caretaker Profile Updated successfully"},
                    status=status.HTTP_200_OK
                )
                
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            


class CareTakerProfileList(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def get(self,request):
        try:
            verimed_doctor_qs = CareTakerProfile.objects.all()
            serializer = CareTakerProfileViewSlr(verimed_doctor_qs, many=True,context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class DoctorReportsCRUD(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Step 1: Parse JSON data
        raw_data = request.data.get("doc_reports_data")
        if not raw_data:
            return Response({"error": "doc_reports_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(raw_data, str):
            try:
                report_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_data, dict):
            report_data = raw_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 2: Validate Foreign Keys
        sponid=report_data.get("sponsor")
        spon_obj=None
        if sponid:
            try:
                spon_obj = SponsorProfile.objects.get(id=sponid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)

        
        doc_id = report_data.get("doctor")
        doc_obj = None
        if doc_id:
            try:
                doc_obj = DoctorProfile.objects.get(id=doc_id)
            except DoctorProfile.DoesNotExist:
                return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        caretaker_id = report_data.get("caretaker")
        caretaker_obj = None
        if caretaker_id:
            try:
                caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)

        patient_id = report_data.get("patient")
        patient_obj = None
        if patient_id:
            try:
                patient_obj = PatientProfile.objects.get(id=patient_id)
            except PatientProfile.DoesNotExist:
                return Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)
            
        # Step 3: Get uploaded files (multiple)
        doctor_report_files = request.FILES.getlist("doc_reports")


        # Step 4: Transaction block to ensure atomic save
        try:
            with transaction.atomic():
                doc_reports = DoctorReports.objects.create(
                    # Foreign Keys
                    sponsor=spon_obj,
                    doctor=doc_obj,
                    patient=patient_obj,
                    caretaker=caretaker_obj,
                    # Patient Info
                    patient_name=report_data.get("patient_name"),
                    # patient_age=report_data.get("patient_age"),
                    # patient_gender=report_data.get("patient_gender"),
                    # nationality=report_data.get("nationality"),
                    blood_group=report_data.get("blood_group"),
                    # Vitals
                    bp=report_data.get("bp"),
                    heart_rate=report_data.get("heart_rate"),
                    sugar=report_data.get("sugar"),
                    oxygen=report_data.get("oxygen"),
                    temperature=report_data.get("temperature"),
                    respiratory_rate=report_data.get("respiratory_rate"),
                    weight=report_data.get("weight"),
                    # status=report_data.get("status"),
                    # Address
                    # address_1=report_data.get("address_1"),
                    # address_2=report_data.get("address_2"),
                    # city=report_data.get("city"),
                    # state=report_data.get("state"),
                    # country=report_data.get("country"),
                    # pincode=report_data.get("pincode"),
                    doctor_notes=report_data.get("doctor_notes"),
                    initial_visit=report_data.get("initial_visit"),
                    
                )
                doc_reports.save()
                if doctor_report_files:
                    for file_obj in doctor_report_files:
                        VerimedDoctorReportsFiles.objects.create(
                            doc_report_files=doc_reports,
                            file=file_obj,
                            referid=doc_reports.id
                        )
                
                sponsorname=spon_obj.user.first_name
                doctorname=doc_obj.user.first_name
                patientname=patient_obj.patient_name
                caretakername=caretaker_obj.user.first_name
                
                
                from django.core.mail import EmailMessage
                from django.conf import settings

                def send_api_verticalcontact_mail(sponsorname):
                    subject = "Your VeriMED Service Report Will Be Available Soon"

                    message = f"""
                    <p>Hello <strong>{sponsorname}</strong>,</p>

                    <p>
                        Your recent VeriMED service or consultation has been completed.
                        A detailed report will be uploaded to your portal shortly for your review.
                    </p>

                    <p>
                        Thank you for trusting VeriMED — the physician-led, nurse-powered, premium
                        in-home and virtual care solution designed for families abroad who want
                        exceptional, transparent, and dependable care for their aging parents in Cameroon.
                    </p>

                    <p>
                        We are honored to support your family’s health, dignity, and peace of mind.
                    </p>

                    <p>
                        If our team has served you well, we would be grateful if you shared your experience
                        with others. Your kind words help more families find reliable care for their loved ones.
                    </p>

                    <p>
                        You may leave a review here:<br>
                        <a href="https://www.facebook.com/VeriMEDglobal/reviews">
                            https://www.facebook.com/VeriMEDglobal/reviews
                        </a>
                    </p>

                    <p>
                        Thank you again for allowing us to care for you and someone precious to you.
                    </p>

                    <p>
                        With gratitude,<br>
                        <strong>The VeriMED Clinical & Care Coordination Team</strong>
                    </p>

                    <p>www.Verimed.care ~~~ Serving Families Worldwide</p>
                    """
                    
                    from_email = settings.DEFAULT_FROM_EMAIL
                    
                    # ✅ Add three recipient emails
                    sponsoremail = spon_obj.user.email
                    caretakeremail = caretaker_obj.user.email
                    doctoremail = doc_obj.user.email

                    recipient_list = [sponsoremail, doctoremail]

                    
                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                       

                        # ✅ Attach each uploaded file to the email
                        for f in doctor_report_files:
                            email_msg.attach(f.name, f.read(), f.content_type)

                        # ✅ Send the email
                        email_msg.content_subtype = "html"  # VERY IMPORTANT
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Vertical contact email sent successfully with attachments")
                        return True

                    except Exception as e:
                        
                        print(f"Error sending email: {e}")
                        return False

                send_api_verticalcontact_mail(sponsorname)
               
                return Response(
                    {"message": "Doctor Reports Successfully Check the email"},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        # Step 1: Parse JSON data
        raw_data = request.data.get("doc_reports_data")
        if not raw_data:
            return Response({"error": "doc_reports_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(raw_data, str):
            try:
                report_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_data, dict):
            report_data = raw_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )

        doc_report_updateid=report_data.get("doc_report_updateid")
        
        if doc_report_updateid:
            try:
                updateobj = DoctorReports.objects.get(id=doc_report_updateid)
            except DoctorReports.DoesNotExist:
                return Response({"error": "Invalid doc_report_updateid ID"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "doc_report_updateid ID is mandatory"}, status=status.HTTP_404_NOT_FOUND)
            

        # Step 2: Validate Foreign Keys
        sponid=report_data.get("sponsor")
        spon_obj=None
        if sponid:
            try:
                spon_obj = SponsorProfile.objects.get(id=sponid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)

        
        doc_id = report_data.get("doc")
        doc_obj = None
        if doc_id:
            try:
                doc_obj = DoctorProfile.objects.get(id=doc_id)
            except DoctorProfile.DoesNotExist:
                return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        caretaker_id = report_data.get("caretaker")
        caretaker_obj = None
        if caretaker_id:
            try:
                caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)

        patient_id = report_data.get("patient")
        patient_obj = None
        if patient_id:
            try:
                patient_obj = PatientProfile.objects.get(id=patient_id)
            except PatientProfile.DoesNotExist:
                return Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)
            
        # Step 4: Handle uploaded files
        doc_report_files = list(request.FILES.getlist("doc_reports"))
        doc_report_ids = list(request.data.getlist("doc_report_ids"))
        print("lab_report_files",doc_report_files)
        print("lab_report_ids",doc_report_ids)
        print(len(doc_report_ids))
        print(len(doc_report_ids))
        
       # --- Normalize lab_report_ids ---
        # Handle case where input is like ['1,2,null']
        if len(doc_report_ids) == 1 and "," in doc_report_ids[0]:
            doc_report_ids = doc_report_ids[0].split(",")

        # Clean up invalid or placeholder values
        cleaned_ids = []
        for val in doc_report_ids:
            if val and val.lower() not in ["null", "none", ""]:
                try:
                    cleaned_ids.append(int(val))
                except ValueError:
                    cleaned_ids.append(None)
            else:
                cleaned_ids.append(None)

        if len(doc_report_files) != len(cleaned_ids):
            return Response(
                {
                    "error": f"The number of lab_reports ({len(doc_report_files)}) "
                            f"does not match the number of lab_report_ids ({len(doc_report_ids)})"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        

        # Step 4: Transaction block to ensure atomic save
        try:
            with transaction.atomic():
                # Foreign Keys
                updateobj.sponsor=spon_obj
                updateobj.doctor=doc_obj
                updateobj.patient=patient_obj
                updateobj.caretaker=caretaker_obj
                # Patient Info
                updateobj.patient_name=report_data.get("patient_name")
                # updateobj.patient_age=report_data.get("patient_age")
                # updateobj.patient_gender=report_data.get("patient_gender")
                # updateobj.nationality=report_data.get("nationality")
                updateobj.blood_group=report_data.get("blood_group")
                # Vitals
                updateobj.bp=report_data.get("bp")
                updateobj.heart_rate=report_data.get("heart_rate")
                updateobj.sugar=report_data.get("sugar")
                updateobj.oxygen=report_data.get("oxygen")
                updateobj.temperature=report_data.get("temperature")
                updateobj.respiratory_rate=report_data.get("respiratory_rate")
                updateobj.weight=report_data.get("weight")
                # updateobj.status=report_data.get("status")
                # Address
                # updateobj.address_1=report_data.get("address_1")
                # updateobj.address_2=report_data.get("address_2")
                # updateobj.city=report_data.get("city")
                # updateobj.state=report_data.get("state")
                # updateobj.country=report_data.get("country")
                # updateobj.pincode=report_data.get("pincode")
                updateobj.doctor_notes=report_data.get("doctor_notes")
                updateobj.initial_visit=report_data.get("initial_visit",updateobj.initial_visit)
                
                updateobj.save()
                
                # Handle lab reports (update or create)
                for index, file_obj in enumerate(doc_report_files):
                    report_id = cleaned_ids[index]

                    if report_id:
                        try:
                            report = VerimedDoctorReportsFiles.objects.get(id=report_id)
                            report.file = file_obj
                            report.save()
                        except VerimedDoctorReportsFiles.DoesNotExist:
                            raise NotFound(detail=f"Invalid lab report ID: {report_id}")
                    else:
                        VerimedDoctorReportsFiles.objects.create(
                            doc_report_files=updateobj,
                            file=file_obj,
                            referid=updateobj.id
                        )
                     
                return Response(
                    {"message": "Doctor Reports Updated successfully"},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self,request):
        try:
            verimed_doctor_qs = DoctorReports.objects.all()
            serializer = DoctorReportsViewSlr(verimed_doctor_qs, many=True,context={"request": request})
            
            response_data = []

            for item in serializer.data:
                docreport_id = item["id"]
                # patient_id = item["patient"]["id"] if item.get("patient") else None

                # Fetch all lab reports for this appointment & patient
                lab_reports_qs = VerimedDoctorReportsFiles.objects.filter(
                    referid=docreport_id,
                    
                )

                # Build document list
                documents = []
                for report in lab_reports_qs:
                    documents.append({
                        "id": report.id,
                        "filename": report.file.name if report.file else None,
                        "uploaded_at": report.uploaded_at,
                        "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                        "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                    })

                # Merge documents into appointment data
                item_with_docs = dict(item)  # Convert OrderedDict to dict
                item_with_docs["documents"] = documents
                response_data.append(item_with_docs)

            return Response(response_data, status=status.HTTP_200_OK)

            
            
            
        except Exception as e:
            # return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
              
    def delete(self,request):
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            doctorreportsdeleteids = request.data.get("doctorreportsdeleteids")  # form-data
        else:
            doctorreportsdeleteids = request.data.get("doctorreportsdeleteids", [])  # JSON list

        if not doctorreportsdeleteids:
            return Response(
                {"error": "No Doctor Reports Deleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = []
        
        for i in doctorreportsdeleteids:
            try:
                doctorreportsdeleteobj=DoctorReports.objects.get(id=i)
            except DoctorReports.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Doctor Reports Deleteids Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
 
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                for i in doctorreportsdeleteids:
                    try:
                        doctorreportsdeleteobj = DoctorReports.objects.get(id=i)
                        
                        # Delete related documents
                        VerimedDoctorReportsFiles.objects.filter(
                            referid=doctorreportsdeleteobj.id,
                        ).delete()

                        # Delete the award
                        doctorreportsdeleteobj.delete()
                             
                    except DoctorReports.DoesNotExist:
                        return Response({"error": "Invalid Doctor Report  Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)

                return Response({"message": "Doctor Report   Deleted sucessfully"}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContactUsC(APIView):
    def post(self,request):
        data=request.data
        country_code_obj=None
        phonewithcountrycode=None
        country_code = data.get("country_code")
        if country_code:
            phone = data.get("phone")
            if phone: 
                try:
                    country_code_obj = VerimedCountryCode.objects.get(code=country_code)
                    dialcode = country_code_obj.dial_code
                    phonewithcountrycode = f"{dialcode}-{phone}"
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        try:
            with transaction.atomic():
                contactus=ContactUs.objects.create(
                # Example: access individual fields
                    department = data.get('department'),
                    doctor = data.get('doctor'),
                    full_name = data.get('full_name'),
                    email = data.get('email'),
                    country_code = country_code_obj,
                    phone = phonewithcountrycode,
                    date = data.get('date'),
                    time = data.get('time'))
                contactus.save()
                
                from django.core.mail import EmailMessage
                from django.conf import settings
                def send_api_verticalcontact_mail():
                    subject = f" Sucessfully"
                    message = (
                        f"Department:{contactus.department}\n"
                        f"Doctor: {contactus.doctor}\n"
                        f"Full Name:{contactus.full_name}\n"
                        f"Email: {contactus.email}\n"
                        f"Phone: {contactus.phone}\n"
                        f"Date: {contactus.date}\n"
                        f"Time: {contactus.time}\n"
                        
                    )
                    
                    from_email = settings.DEFAULT_FROM_EMAIL
                    
                    # ✅ Add three recipient emails
                    email = contactus.email
                    
                    recipient_list = [email]

                    
                    try:
                        email_msg = EmailMessage(subject, message, from_email, recipient_list)
                        email_msg.send(fail_silently=False)
                        print("ContactUs Email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Error sending ContactUs email: {e}")
                        return False
                    
                send_api_verticalcontact_mail()
                return Response({"message": "ContactUs Created Successfully Check the Email"}, status=status.HTTP_200_OK)

        
        except Exception as e:
            transaction.set_rollback(True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ContactUsRD(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        data = ContactUs.objects.all()
        serializer = ContactUsViewSlr(data, many=True)  # <-- fixed argument name
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self,request):
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            contactusdeleteids = request.data.get("contactusdeleteids")  # form-data
        else:
            contactusdeleteids = request.data.get("contactusdeleteids", [])  # JSON list

        if not contactusdeleteids:
            return Response(
                {"error": "No ContactUs Deleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = []
        
        for i in contactusdeleteids:
            try:
                contactusdeleteobj=ContactUs.objects.get(id=i)
            except ContactUs.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Doctor Reports Deleteids Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
 
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                for i in contactusdeleteids:
                    try:
                        contactusdeleteobj = ContactUs.objects.get(id=i)

                        # Delete the award
                        contactusdeleteobj.delete()
                             
                    except ContactUs.DoesNotExist:
                        return Response({"error": "Invalid Doctor Report  Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)

                return Response({"message": "ContactUs Deleted sucessfully"}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KetnyproductionCheckC(APIView):
    
    def post(self, request):

        raw_data = request.data.get("ketnyproduct_payload")
        print("raw_data", raw_data)
        
        if isinstance(raw_data, str):
            try:
                dep_data = json.loads(raw_data)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(raw_data, dict):
            dep_data = raw_data
        else:
            return Response(
                {"error": "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )
        name = dep_data.get("name") 
        
        if not name:
            return Response(
                {"error": "Name is mandatory"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        email = dep_data.get("email") 
        
        if not email:
            return Response(
                {"error": "Email is mandatory"},
                status=status.HTTP_400_BAD_REQUEST
            )
          
        countrycode = dep_data.get("country_code")
        if countrycode:

            try:
                countrycode_obj = VerimedCountryCode.objects.get(code=countrycode)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            countrycode_obj=None
            dialcode=None
        
        mobile = dep_data.get("phone")
        if mobile:
            phonewithcountrycode = f"{dialcode}-{mobile}"
        else:
            phonewithcountrycode=None
            
            
        emergency_country_code = dep_data.get("emergency_country_code")
        if emergency_country_code:

            try:
                emergency_country_code_obj = VerimedCountryCode.objects.get(code=emergency_country_code)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            emergency_country_code=None
            dialcode=None
        
        emergency_phone = dep_data.get("emergency_phone")
        if emergency_phone:
            emrphonewithcountrycode = f"{dialcode}-{mobile}"
        else:
            emrphonewithcountrycode=None
        
        
       
        # --- MAIN TRANSACTION ---
        try:
            with transaction.atomic():
                # Create main asset_cleaned_data.get("department")
                verimeddepartment = KetnyproductionCheck.objects.create(
                    name=name,
                    country_code=countrycode_obj,
                    phone=phonewithcountrycode,                    
                    email=email,
                    city=dep_data.get("city"),
                    neighborhood=dep_data.get("neighborhood"),
                    age_range=dep_data.get("age_range"),
                    gender=dep_data.get("gender"),
                    allergies=dep_data.get("allergies"),
                    sugar_kidneytest=dep_data.get("sugar_kidneytest"),
                    medication_sugar_pressure=dep_data.get("medication_sugar_pressure"),
                    emergency_con_name=dep_data.get("emergency_con_name"),
                    emergency_country_code=emergency_country_code_obj,
                    emergency_phone=emrphonewithcountrycode,
                    health_check=dep_data.get("health_check"),
                    comm_preference=dep_data.get("comm_preference"),
                    health_concern=dep_data.get("health_concern"),
                    screening_date=dep_data.get("screening_date"),
                )
            
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings

                from django.conf import settings
                from django.core.mail import EmailMultiAlternatives
                from django.template.loader import render_to_string


                def sendmail(user_email):
                    subject = "Free Diabetes Screening & Kidney Protection Check"
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [user_email]   # must be a list

                    # Render HTML template
                    html_content = render_to_string("user_notification.html")

                    mail = EmailMultiAlternatives(
                        subject=subject,
                        body="Your form submission successfully",  # fallback text
                        from_email=from_email,
                        to=recipient_list
                    )

                    mail.attach_alternative(html_content, "text/html")
                    mail.send()

                    print("Email sent successfully")


                # get email
                email = verimeddepartment.email

                # call function
                sendmail(email)
                # to_email = ["ramraja.e99@gmail.com", "ramraja.e999@gmail.com"]

                # def sendadminmail():
                #     subject = "Form from Client"
                #     message = ""

                #     from_email = settings.DEFAULT_FROM_EMAIL
                #     recipient_list = to_email

                #     send_mail(
                #         subject,
                #         message,
                #         from_email,
                #         recipient_list,
                #         fail_silently=False
                #     )

                #     print("Admin notification email sent successfully")


                # # Call function
                # sendadminmail()
                
            from django.core.mail import EmailMultiAlternatives
            from django.conf import settings
            from django.template.loader import render_to_string


            # to_email = ["ramraja.e99@gmail.com", "karthiksriram682@gmail.com"]

            to_email = ["screenings@verimed.care","info@verimed.care"]

            def sendadminmail(verimeddepartment):

                subject = "Free Diabetes Screening & Kidney Protection Check"
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = to_email

                # Render HTML template
                html_content = render_to_string(
                    "admin_notification.html",
                    {"verimeddepartment": verimeddepartment}
                )

                email = EmailMultiAlternatives(
                    subject=subject,
                    body="New form submission received",  # fallback text
                    from_email=from_email,
                    to=recipient_list
                )

                email.attach_alternative(html_content, "text/html")
                email.send()

                print("Admin notification email sent successfully")
                
            sendadminmail(verimeddepartment)        

            return Response(
                    {"message": "Submitting Successfully"},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KetnyproductionCheckRD(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        data= KetnyproductionCheck.objects.all()
        serializer = KetnyproductionCheckViewSlr(data, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self,request):
            
        # Get list of IDs from request data
        if hasattr(request.data, "getlist"):
            freekidneydeleteids = request.data.get("freekidneydeleteids")  # form-data
        else:
            freekidneydeleteids = request.data.get("freekidneydeleteids", [])  # JSON list

        if not freekidneydeleteids:
            return Response(
                {"error": "No Patient freekidneydeleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = []
        
        for i in freekidneydeleteids:
            try:
                freekidneydeleteobj=KetnyproductionCheck.objects.get(id=i)
            except KetnyproductionCheck.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid Patient Profile Deleteids Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
 
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                try:
                    patientprofiledeleteobj = KetnyproductionCheck.objects.filter(id__in=freekidneydeleteids)
                    patientprofiledeleteobj.delete()
                    return Response({"message": "Deleted sucessfully"}, status=status.HTTP_200_OK)

                except PatientProfile.DoesNotExist:
                    return Response({"error": "Invalid KetnyproductionCheck Profile  Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
       
        
# paymentimport stripe
import stripe
import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order

# IMPORTANT: use SECRET KEY
stripe.api_key = settings.STRIPE_SECRET_KEY


def payment_page(request):
    return render(request, "payment.html")


def create_checkout_session(request):

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1000,   # $10
                    "product_data": {
                        "name": "Consultation Fee",
                    },
                },
                "quantity": 1,
            }
        ],
        success_url="https://verimedramja.pythonanywhere.com/verimed/success/?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://verimedramja.pythonanywhere.com/verimed/cancel/",
        # success_url="http://127.0.0.1:8000/verimed/success/?session_id={CHECKOUT_SESSION_ID}",
        # cancel_url="http://127.0.0.1:8000/verimedramja.pythonanywhere.com/verimed/cancel/",

    )

    # HTTP 303 is recommended
    return redirect(session.url, permanent=False)


def success(request):
    return render(request, "success.html")


def cancel(request):
    return render(request, "cancel.html")


@csrf_exempt
def stripe_webhook(request):

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )

    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)

    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # PAYMENT SUCCESS
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        payment_intent = session.get("payment_intent")
        email = session.get("customer_details", {}).get("email")
        amount = session.get("amount_total")

        Order.objects.get_or_create(
            payment_intent=payment_intent,
            defaults={
                "email": email,
                "amount": amount,
                "status": "paid",
            },
        )

    return HttpResponse(status=200)
