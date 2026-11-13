from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from fieldscontrol.models import FieldsControlErrors
import json
from django.db import transaction
from django.db.models import Q
from verimed.models import VerimedCountryCode,VerimedDepartment,VerimedBookAppointment,APPOINTMENT_STATUS,SponsorID,PatientID,DoctorID,CaretakerID,AdminID,SponsorProfile,DoctorProfile,CareTakerProfile,PatientProfile,AdminProfile,ROLE_CHOICES,VerimedBookAppointmentLabReports,PatientUploadDocuments,DoctorReports,VerimedDoctorReportsFiles,ContactUs,KetnyproductionCheck
from fieldscontrol.views import field_validate_not_iterate
from .serializers import VerimedCountryCodeViewSlr,VerimedDepartmentViewSlr,VerimedBookAppointmentViewSlr,UserViewSlr,SponsorProfileViewSlr,PatientProfileViewSlr,DoctorProfileViewSlr,CareTakerProfileViewSlr,PatientProfileViewSlr,DoctorReportsViewSlr,ContactUsViewSlr,KetnyproductionCheckViewSlr
from django.contrib.auth.hashers import make_password,check_password
from django.contrib.sessions.backends.db import SessionStore
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny


def get_sponsor_profile(user):
    if not user or not user.is_authenticated:
        return None
    try:
        return user.sponsor_profile
    except SponsorProfile.DoesNotExist:
        return None


def is_sponsor_user(user):
    if not user or not user.is_authenticated or user.is_superuser:
        return False
    role = (getattr(user, "user_role", None) or "").strip().lower()
    if role == "admin":
        return False
    try:
        if user.admin_profile is not None:
            return False
    except AdminProfile.DoesNotExist:
        pass
    return role == "sponsor" or get_sponsor_profile(user) is not None


def resolve_sponsor_profile_by_param(sponsor_val):
    if sponsor_val is None or str(sponsor_val).strip() == "":
        return None
    val_str = str(sponsor_val).strip()
    if val_str.isdigit():
        return SponsorProfile.objects.filter(id=int(val_str)).first()
    return SponsorProfile.objects.filter(
        Q(sponsor_id=val_str) | Q(user__username=val_str)
    ).first()


def _parse_json_payload(raw_data):
    if isinstance(raw_data, (dict, list)):
        return raw_data, None
    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data), None
        except Exception:
            return None, "Invalid JSON format"
    return None, "Invalid data type. Expected JSON string or dict."


def _extract_id_list(request, field_name):
    raw_values = []
    if hasattr(request.data, "getlist"):
        raw_values = request.data.getlist(field_name)
        if len(raw_values) == 1 and raw_values[0] in (None, ""):
            raw_values = []
    if not raw_values:
        raw = request.data.get(field_name, [])
        if raw in (None, "", []):
            raw_values = []
        elif isinstance(raw, (list, tuple)):
            raw_values = list(raw)
        else:
            raw_values = [raw]

    flattened = []
    for item in raw_values:
        if item in (None, ""):
            continue
        if isinstance(item, (list, tuple)):
            flattened.extend(item)
        elif isinstance(item, str):
            stripped = item.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, list):
                        flattened.extend(parsed)
                        continue
                except Exception:
                    pass
            for part in stripped.split(","):
                part = part.strip()
                if part:
                    flattened.append(part)
        else:
            flattened.append(item)

    valid_ids = []
    invalid_ids = []
    for val in flattened:
        try:
            valid_ids.append(int(val))
        except (TypeError, ValueError):
            invalid_ids.append(val)
    return valid_ids, invalid_ids


def _extract_str_list(data_source, field_name):
    if hasattr(data_source, "getlist"):
        vals = list(data_source.getlist(field_name))
    else:
        raw = data_source.get(field_name)
        if raw in (None, ""):
            vals = []
        elif isinstance(raw, (list, tuple)):
            vals = list(raw)
        else:
            vals = [raw]
    if len(vals) == 1 and isinstance(vals[0], str) and "," in vals[0]:
        return [part.strip() for part in vals[0].split(",")]
    return vals


def _format_phone_with_dial(dialcode, mobile):
    if mobile is None:
        return None
    mobile_str = str(mobile).strip()
    if not mobile_str:
        return None
    dial_str = str(dialcode).strip() if dialcode else ""
    if dial_str:
        dial_digits = dial_str.lstrip("+")
        if mobile_str.startswith(f"{dial_str}-"):
            return mobile_str
        if mobile_str.startswith(dial_str):
            rest = mobile_str[len(dial_str):].lstrip("- ")
            return f"{dial_str}-{rest}" if rest else None
        if dial_digits and mobile_str.startswith(f"{dial_digits}-"):
            rest = mobile_str[len(dial_digits) + 1:].lstrip("- ")
            return f"{dial_str}-{rest}" if rest else None
        return f"{dial_str}-{mobile_str}"
    return mobile_str


def filter_queryset_by_sponsor(queryset, sponsor_profile):
    return queryset.filter(
        (
            Q(sponsor=sponsor_profile)
            & (
                Q(patient__isnull=True)
                | Q(patient__sponsor__isnull=True)
                | Q(patient__sponsor=sponsor_profile)
            )
        )
        | Q(patient__sponsor=sponsor_profile)
    ).distinct()

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
        verification_link = f"{settings.FRONTEND_URL.rstrip('/')}/verimed/verify-email/?token={token}"
        send_mail(
            subject="Verify Your Email",
            message=f"Click the link to verify your email and complete signup: {verification_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "Verification email sent"}, status=status.HTTP_200_OK)


class UserEmailVerify(APIView):
    permission_classes = [AllowAny]

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
        
        countrycode_obj = None
        dialcode = None
        phonewithcountrycode = None
        country_code = payload.get("country_code") or payload.get("countrycode")
        if country_code:
            try:
                countrycode_obj = VerimedCountryCode.objects.get(code=country_code)
                dialcode = countrycode_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        phone = payload.get("phone")
        if phone:
            phonewithcountrycode = _format_phone_with_dial(dialcode, phone)
                 

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
                    sponsor_id = (
                        payload.get("sponser_id")
                        or payload.get("sponsor_id")
                        or payload.get("sponsorid")
                    )
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

                    if caretaker_id:
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
                    admin_id = f"A{int(last_data.admin_id)}" if last_data else "A1"
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
    permission_classes = [AllowAny]

    def post(self, request):
        user_signup_data_raw = request.data.get("user_signup")
        if not user_signup_data_raw:
            return Response({"error": "user_signup is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

        user_signup_data, parse_err = _parse_json_payload(user_signup_data_raw)
        if parse_err:
            return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)

         # Update photo if provided
        photo = request.data.get("photo", None)
        if photo:
            photo = photo

        countrycode = user_signup_data.get("countrycode") or user_signup_data.get("country_code")
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
            countrycode_obj = None
            dialcode = None

        mobile = user_signup_data.get("phone")
        phonewithcountrycode = _format_phone_with_dial(dialcode, mobile)
        is_active = (
            user_signup_data.get("is_active_state")
            if user_signup_data.get("is_active_state") is not None
            else True
        )
        
        role =user_signup_data.get("role")
        if not role:
            return Response(
                    {"error": "Role is important"},  
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            with transaction.atomic():
                # files sending
                from django.core.mail import EmailMessage
                from django.conf import settings
                url = getattr(
                    settings,
                    "FRONTEND_DASHBOARD_URL",
                    "https://verimed-fe.vercel.app/",
                )

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
                    if not (email or "").strip():
                        return False
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
                    if not (email or "").strip():
                        return False
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
                        is_active_state=is_active
                    )

                    SponsorProfile.objects.create(
                        user=user,
                        sponsor_verified=True,
                        sponsor_id=sponsor_id
                    )

                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()
                    send_api_verticalcontact_mail(
                        user.first_name or user.username or "Valued Family Member",
                        user.username,
                        user_signup_data.get("password"),
                        user.email,
                    )

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
                        is_active_state=is_active
                    )

                    DoctorProfile.objects.create(
                        user=user,
                        doctor_verified=True,
                        doctor_id=doctor_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()
                    
                    
                    send_api_verticalcontact_mail(
                        user.first_name or user.username or "Doctor",
                        user.username,
                        user_signup_data.get("password"),
                        user.email,
                    )
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
                        is_active_state=is_active
                    )

                    CareTakerProfile.objects.create(
                        user=user,
                        caretaker_verified=True,
                        caretaker_id=caretaker_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()

                    send_api_caretaker_mail(
                        user.first_name or user.username or "Team Member",
                        user.username,
                        user_signup_data.get("password"),
                        user.email,
                    )
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
                    admin_id = f"A{int(last_data.admin_id)}" if last_data else "A1"
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
                        is_active_state=is_active
                    )

                    AdminProfile.objects.create(
                        user=user,
                        admin_verified=True,
                        admin_id=admin_id
                    )
                    # ✅ Soft delete (mark token as used)
                    # verification.mark_as_used()
                    
                    send_api_verticalcontact_mail(
                        user.first_name or user.username or "Admin",
                        user.username,
                        user_signup_data.get("password"),
                        user.email,
                    )
                    response_msg = {"message": "Admin created successfully Check the Email", "admin_id": admin_id}

                
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
        user_update_data_raw = request.data.get("user_update_data")
        if not user_update_data_raw:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_update_data, parse_err = _parse_json_payload(user_update_data_raw)
        if parse_err:
            return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)

        # Get user object
        try:
            user = User.objects.get(id=user_update_data.get("updateid"))
        except User.DoesNotExist:
            return Response({"error": "Give me a valid user"}, status=status.HTTP_404_NOT_FOUND)
        
        has_country_code = "countrycode" in user_update_data or "country_code" in user_update_data
        if has_country_code:
            countrycode = user_update_data.get("countrycode")
            if countrycode is None:
                countrycode = user_update_data.get("country_code")
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
                countrycode_obj = None
                dialcode = None
        else:
            countrycode_obj = user.country_code
            dialcode = countrycode_obj.dial_code if countrycode_obj else None
        
        has_phone = "phone" in user_update_data
        if has_phone:
            mobile = user_update_data.get("phone")
            phonewithcountrycode = _format_phone_with_dial(dialcode, mobile)
      
        try:
            with transaction.atomic():
        
                # Update user fields
                user.first_name = user_update_data.get("first_name", user.first_name)
                user.last_name = user_update_data.get("last_name", user.last_name)
                user.email = user_update_data.get("email", user.email)
                user.service_purchased = user_update_data.get("service_purchased", user.service_purchased)
                if has_country_code:
                    user.country_code = countrycode_obj
                if has_phone:
                    user.phone = phonewithcountrycode
                user.is_active_state = user_update_data.get("is_active_state", user.is_active_state)

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
                code = user.country_code.code if user and user.country_code else None
                
                return Response({
                    "message": "User updated successfully",
                    "user": {
                        # "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "countrycode": code,
                        "phone": user.phone,
                        "role": user.user_role,
                        "service_purchased": user.service_purchased
                    }
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
                

class UserUpdateUser(APIView):
    permission_classes = [AllowAny]

    def patch(self, request):
        # Ensure 'user_update_data' exists
        user_update_data_raw = request.data.get("user_update_data")
        if not user_update_data_raw:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_update_data, parse_err = _parse_json_payload(user_update_data_raw)
        if parse_err:
            return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)

        username = user_update_data.get("username")
        # Get user object
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": f"no user name found {username}"}, status=status.HTTP_404_NOT_FOUND)        
        
        has_country_code = "countrycode" in user_update_data or "country_code" in user_update_data
        if has_country_code:
            countrycode = user_update_data.get("countrycode")
            if countrycode is None:
                countrycode = user_update_data.get("country_code")
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
                countrycode_obj = None
                dialcode = None
        else:
            countrycode_obj = user.country_code
            dialcode = countrycode_obj.dial_code if countrycode_obj else None
        
        has_phone = "phone" in user_update_data
        if has_phone:
            mobile = user_update_data.get("phone")
            phonewithcountrycode = _format_phone_with_dial(dialcode, mobile)
      
        try:
            with transaction.atomic():
                
                # Update user fields
                user.first_name = user_update_data.get("first_name", user.first_name)
                user.last_name = user_update_data.get("last_name", user.last_name)
                user.email = user_update_data.get("email", user.email)
                user.service_purchased = user_update_data.get("service_purchased", user.service_purchased)
                if has_country_code:
                    user.country_code = countrycode_obj
                if has_phone and phonewithcountrycode:
                    user.phone = phonewithcountrycode
                user.is_active_state = user_update_data.get("is_active_state", user.is_active_state)

                # Update photo if provided
                photo = request.data.get("photo")   
                if photo:
                    user.photo = photo

                # Update password if provided
                password = user_update_data.get("password")
                if password:
                    user.password = make_password(password)

                user.save()

                from django.core.mail import EmailMessage
                from django.conf import settings
                url = getattr(
                    settings,
                    "FRONTEND_DASHBOARD_URL",
                    "https://verimed-fe.vercel.app/",
                )
                
                if password and (user.email or "").strip():
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

                code = user.country_code.code if user and user.country_code else None
                    
                return Response({
                    "message": "User updated successfully",
                    "user": {
                        "id": user.id,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "countrycode": code,
                        "phone": user.phone,
                        "role": user.user_role,
                        "service_purchased": user.service_purchased
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
        valid_ids, invalid_format_ids = _extract_id_list(request, "deleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No user IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        notvalidids = list(invalid_format_ids)

        for i in valid_ids:
            if not User.objects.filter(id=i).exists():
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
                User.objects.filter(id__in=valid_ids).delete()
                return Response(
                    {"message": "User Deleted successfully"},
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
        if not raw_data:
            return Response({"error": "verimed_department is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        dep_data, parse_err = _parse_json_payload(raw_data)
        if parse_err:
            return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)

        doc_id = dep_data.get("docid") 
        doc_obj = None
        if doc_id:
            try:
                doc_obj = DoctorProfile.objects.get(id=doc_id)
            except DoctorProfile.DoesNotExist:
                return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        countrycode = dep_data.get("country_code") or dep_data.get("countrycode")
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
            countrycode_obj = None
            dialcode = None
        
        mobile = dep_data.get("contact_phone")
        phonewithcountrycode = _format_phone_with_dial(dialcode, mobile)
       
        # --- MAIN TRANSACTION ---
        try:
            with transaction.atomic():
                VerimedDepartment.objects.create(
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
            if not raw_data:
                return Response({"error": "verimed_department is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
            dep_data, parse_err = _parse_json_payload(raw_data)
            if parse_err:
                return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)
                
            depupdateid = dep_data.get("depupdateid") 
            if depupdateid:
                try:
                    dep_obj = VerimedDepartment.objects.get(id=depupdateid)
                except VerimedDepartment.DoesNotExist:
                    return Response({"error": "Invalid DepartmentUpdateid ID"}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response(
                    {"error": "depupdateid is Mandatory."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            has_docid = "docid" in dep_data
            doc_obj = dep_obj.doctor
            if has_docid:
                doc_id = dep_data.get("docid")
                if doc_id:
                    try:
                        doc_obj = DoctorProfile.objects.get(id=doc_id)
                    except DoctorProfile.DoesNotExist:
                        return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)
                else:
                    doc_obj = None

            has_country_code = "country_code" in dep_data or "countrycode" in dep_data
            if has_country_code:
                countrycode = dep_data.get("country_code")
                if countrycode is None:
                    countrycode = dep_data.get("countrycode")
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
                    countrycode_obj = None
                    dialcode = None
            else:
                countrycode_obj = dep_obj.country_code
                dialcode = countrycode_obj.dial_code if countrycode_obj else None
            
            has_phone = "contact_phone" in dep_data
            if has_phone:
                mobile = dep_data.get("contact_phone")
                phonewithcountrycode = _format_phone_with_dial(dialcode, mobile)
        
            # --- MAIN TRANSACTION ---
            try:
                with transaction.atomic():
                    for field in [
                        "dep_name",
                        "dep_type",
                        "contact_email",
                        "address",
                        "description",
                        "dep_ID",
                        "status",
                        "dep_city",
                        "dep_state",
                        "dep_country",
                        "dep_pincode",
                    ]:
                        if field in dep_data:
                            setattr(dep_obj, field, dep_data.get(field))
                    if has_country_code:
                        dep_obj.country_code = countrycode_obj
                    if has_phone:
                        dep_obj.contact_phone = phonewithcountrycode
                    if has_docid:
                        dep_obj.doctor = doc_obj
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
        valid_ids, invalid_format_ids = _extract_id_list(request, "departmentdeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No Department Delete IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        notvalidids = list(invalid_format_ids)

        for i in valid_ids:
            if not VerimedDepartment.objects.filter(id=i).exists():
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
                VerimedDepartment.objects.filter(id__in=valid_ids).delete()
                return Response(
                    {"message": "Department Deleted successfully"},
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
                    

APPOINTMENT_PENDING_PAYMENT_STATUS = "PaymentPending"

_APPOINTMENT_SERVICE_PRICE_CATALOG = (
    ("Comprehensive Physician Intake In Person", 12500),
    ("In Home Follow Up Physician Visit", 9500),
    ("Virtual Physician Visit", 5500),
    ("Nurse Wellness Check", 5000),
    ("Rehydration & IV Fluid Therapy", 6000),
    ("Infusion Therapy for Prescribed Medications", 9000),
    ("Care Management & Navigation", 10000),
    ("Wellness Coaching", 7500),
    ("Diabetes Coaching & Chronic Illness Management", 11500),
    ("Live-in Family Wellness Nurse", 49500),
)


def _normalize_service_name(name):
    import re
    cleaned = str(name or "").lower()
    cleaned = re.sub(r"[()\-_&,/]+", " ", cleaned)
    cleaned = re.sub(r"\bmedications\b", "medication", cleaned)
    cleaned = re.sub(r"\bfollow[\s-]?ups?\b", "follow up", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _is_matching_service(service_a, service_b):
    a = _normalize_service_name(service_a)
    b = _normalize_service_name(service_b)
    if not a or not b:
        return False
    return a == b or a in b or b in a


def _resolve_appointment_service_pricing(appointment_type=None, dep_obj=None, raw_amount=None):
    import re
    from decimal import Decimal, InvalidOperation

    candidates = [
        str(appointment_type or "").strip(),
        str(getattr(dep_obj, "dep_name", None) or "").strip(),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        for catalog_name, cents in _APPOINTMENT_SERVICE_PRICE_CATALOG:
            if _is_matching_service(candidate, catalog_name):
                return cents, catalog_name

        clean = candidate.lower()
        if "comprehensive" in clean or "intake" in clean:
            return 12500, "Comprehensive Physician Intake In Person"
        if "home" in clean and ("visit" in clean or "follow" in clean):
            return 9500, "In Home Follow Up Physician Visit"
        if "virtual" in clean:
            return 5500, "Virtual Physician Visit"
        if "live-in" in clean or "live in" in clean or "family wellness nurse" in clean:
            return 49500, "Live-in Family Wellness Nurse"
        if "nurse" in clean and "wellness" in clean:
            return 5000, "Nurse Wellness Check"
        if "rehydration" in clean or "fluid" in clean or re.search(r"\biv\b", clean):
            return 6000, "Rehydration & IV Fluid Therapy"
        if "infusion" in clean:
            return 9000, "Infusion Therapy for Prescribed Medications"
        if "navigation" in clean or "care management" in clean:
            return 10000, "Care Management & Navigation"
        if "diabetes" in clean or "chronic" in clean:
            return 11500, "Diabetes Coaching & Chronic Illness Management"
        if "wellness coaching" in clean or "coaching" in clean:
            return 7500, "Wellness Coaching"

    fallback_name = next((c for c in candidates if c), "VeriMED Medical Appointment")
    if raw_amount is not None and str(raw_amount).strip() != "":
        amt_match = re.match(r"^\s*\$?\s*(\d+(?:\.\d{1,2})?)\s*$", str(raw_amount))
        if amt_match:
            try:
                cents = int((Decimal(amt_match.group(1)) * Decimal("100")).quantize(Decimal("1")))
                if cents > 0:
                    return cents, fallback_name
            except (InvalidOperation, ValueError):
                pass
    return None, fallback_name


def _user_has_prepaid_service(request_user, sponsor_obj, service_name=None, dep_obj=None):
    candidates = [service_name, getattr(dep_obj, "dep_name", None)]
    owned_plans = [
        getattr(getattr(sponsor_obj, "user", None), "service_purchased", None),
        getattr(request_user, "service_purchased", None),
    ]
    for owned in owned_plans:
        if not owned:
            continue
        for candidate in candidates:
            if candidate and _is_matching_service(owned, candidate):
                return True, str(owned).strip()
    return False, None


def _exclude_unpaid_appointment_drafts(queryset):
    return queryset.exclude(appointment_status=APPOINTMENT_PENDING_PAYMENT_STATUS)


def _send_appointment_request_email(appointment):
    from html import escape as html_escape
    from django.core.mail import EmailMessage
    from django.conf import settings

    effective_sponsor = (
        appointment.sponsor
        or getattr(appointment.patient, "sponsor", None)
    )
    sponsor_user = getattr(effective_sponsor, "user", None)
    sponsoremail = (getattr(sponsor_user, "email", None) or "").strip()
    sponsorname = (
        (getattr(sponsor_user, "first_name", None) or "").strip()
        or (getattr(sponsor_user, "username", None) or "").strip()
        or "Valued Family Member"
    )

    if not sponsoremail:
        return False, "Sponsor email address is missing."

    subject = "Thank You — Your Appointment Request Is Being Processed"
    message = f"""
        <p>Hello <strong>{html_escape(sponsorname)}</strong>,</p>

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
        email_msg.content_subtype = "html"
        email_msg.body = message
        email_msg.send(fail_silently=False)
        print("Vertical contact email sent successfully")
        return True, None
    except Exception as e:
        print(f"Appoinment Booking Post sending vertical contact email: {e}")
        return False, str(e)


def _validate_and_resolve_appointment_request(request):
    raw_data = request.data.get("bookappoinment_data")
    if not raw_data:
        return None, Response({"error": "bookappoinment_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(raw_data, str):
        try:
            report_data = json.loads(raw_data)
        except json.JSONDecodeError:
            return None, Response({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
    elif isinstance(raw_data, dict):
        report_data = raw_data
    else:
        return None, Response(
            {"error": "Invalid data type. Expected JSON string or dict."},
            status=status.HTTP_400_BAD_REQUEST
        )

    sponid = report_data.get("sponsor")
    spon_obj = None
    if sponid:
        try:
            spon_obj = SponsorProfile.objects.get(id=sponid)
        except SponsorProfile.DoesNotExist:
            return None, Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)

    dep_id = report_data.get("dep")
    dep_obj = None
    if dep_id:
        try:
            dep_obj = VerimedDepartment.objects.get(id=dep_id)
        except VerimedDepartment.DoesNotExist:
            return None, Response({"error": "Invalid department ID"}, status=status.HTTP_404_NOT_FOUND)

    doc_id = report_data.get("doc")
    doc_obj = None
    if doc_id:
        try:
            doc_obj = DoctorProfile.objects.get(id=doc_id)
        except DoctorProfile.DoesNotExist:
            return None, Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

    caretaker_id = report_data.get("caretaker")
    caretaker_obj = None
    if caretaker_id:
        try:
            caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
        except CareTakerProfile.DoesNotExist:
            return None, Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)

    patient_id = report_data.get("patient")
    patient_obj = None
    if patient_id:
        try:
            patient_obj = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return None, Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)

    if spon_obj is None and patient_obj is not None and patient_obj.sponsor is not None:
        spon_obj = patient_obj.sponsor

    if is_sponsor_user(request.user):
        logged_sponsor = get_sponsor_profile(request.user)
        if logged_sponsor is None:
            return None, Response({"error": "Sponsor profile not found"}, status=status.HTTP_403_FORBIDDEN)
        if spon_obj is not None and spon_obj.id != logged_sponsor.id:
            return None, Response(
                {"error": "You can only create appointments for your own sponsor account."},
                status=status.HTTP_403_FORBIDDEN
            )
        spon_obj = logged_sponsor
        if patient_obj is not None and patient_obj.sponsor_id != logged_sponsor.id:
            return None, Response(
                {"error": "You can only book appointments for your own loved ones/patients."},
                status=status.HTTP_403_FORBIDDEN
            )

    resolved = {
        "report_data": report_data,
        "spon_obj": spon_obj,
        "dep_obj": dep_obj,
        "doc_obj": doc_obj,
        "caretaker_obj": caretaker_obj,
        "patient_obj": patient_obj,
        "lab_report_files": request.FILES.getlist("lab_reports"),
    }
    return resolved, None


def _create_appointment_record(resolved, appointment_status_value="Pending", service_purchased_value=False, amount_override=None):
    report_data = resolved["report_data"]
    spon_obj = resolved["spon_obj"]
    dep_obj = resolved["dep_obj"]
    doc_obj = resolved["doc_obj"]
    caretaker_obj = resolved["caretaker_obj"]
    patient_obj = resolved["patient_obj"]
    lab_report_files = resolved["lab_report_files"]

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
            amount=amount_override if amount_override is not None else report_data.get("amount"),
            subscription_plan=report_data.get("subscription_plan"),
            height=report_data.get("height"),
            weight=report_data.get("weight"),
            blood_pressure=report_data.get("blood_pressure"),
            blood_sugar=report_data.get("blood_sugar"),
            medical_history=report_data.get("medical_history"),
            appointment_history=report_data.get("appointment_history"),
            time_line=report_data.get("time_line"),
            appointment_reason=report_data.get("appointment_reason"),
            appointment_status=appointment_status_value,
            preferred_dates=report_data.get("preferred_dates"),
            preferred_times=report_data.get("preferred_times"),
            service_purchased=service_purchased_value,
        )

        if lab_report_files:
            for file_obj in lab_report_files:
                VerimedBookAppointmentLabReports.objects.create(
                    appointment=appointment,
                    file=file_obj,
                    patient=patient_obj,
                    referid=appointment.id
                )

    return appointment


def _resolve_frontend_appointments_url(request):
    from django.conf import settings
    from urllib.parse import urlparse

    default_base = (
        getattr(settings, "FRONTEND_DASHBOARD_URL", "https://verimed-fe.vercel.app/")
        or "https://verimed-fe.vercel.app/"
    ).rstrip("/")
    raw_origin = str(request.data.get("frontend_origin") or "").strip().rstrip("/")
    raw_return_path = str(request.data.get("return_path") or "/appointments").strip() or "/appointments"
    if not raw_return_path.startswith("/"):
        raw_return_path = f"/{raw_return_path}"

    allowed_hosts = {
        "verimed-fe.vercel.app",
        "verimed.care",
        "portal.verimed.care",
        "localhost",
        "127.0.0.1",
    }
    chosen_base = default_base
    if raw_origin:
        parsed = urlparse(raw_origin)
        hostname = (parsed.hostname or "").lower()
        if parsed.scheme in ("http", "https") and (
            hostname in allowed_hosts or hostname.endswith(".vercel.app")
        ):
            chosen_base = f"{parsed.scheme}://{parsed.netloc}"
    return f"{chosen_base}{raw_return_path}"


def _session_field(session_obj, key, default=None):
    if session_obj is None:
        return default
    if isinstance(session_obj, dict):
        return session_obj.get(key, default)
    return getattr(session_obj, key, default)


def _finalize_paid_appointment_draft(draft_id, session_obj=None):
    with transaction.atomic():
        updated_count = VerimedBookAppointment.objects.filter(
            id=draft_id,
            appointment_status=APPOINTMENT_PENDING_PAYMENT_STATUS,
        ).update(
            appointment_status="Pending",
            service_purchased=True,
        )
        appointment = VerimedBookAppointment.objects.select_related(
            "sponsor__user", "patient__sponsor__user"
        ).get(id=draft_id)

        if session_obj is not None:
            payment_ref = _session_field(session_obj, "payment_intent") or _session_field(session_obj, "id")
            if payment_ref:
                customer_details = _session_field(session_obj, "customer_details") or {}
                cust_email = (
                    (_session_field(customer_details, "email") or "").strip()
                    or (_session_field(session_obj, "customer_email") or "").strip()
                    or (
                        getattr(
                            getattr(appointment.sponsor or getattr(appointment.patient, "sponsor", None), "user", None),
                            "email",
                            None,
                        )
                        or ""
                    ).strip()
                    or "noreply@verimed.care"
                )
                amount_total = int(_session_field(session_obj, "amount_total") or 0)
                Order.objects.get_or_create(
                    payment_intent=str(payment_ref),
                    defaults={
                        "email": cust_email,
                        "amount": amount_total,
                        "status": "paid",
                    },
                )

    if updated_count == 1:
        email_sent, email_error = _send_appointment_request_email(appointment)
        return appointment, True, email_sent, email_error

    return appointment, False, True, None


class VerimedBookAppoinmentCreateUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        resolved, error_response = _validate_and_resolve_appointment_request(request)
        if error_response is not None:
            return error_response

        report_data = resolved["report_data"]
        spon_obj = resolved["spon_obj"]
        dep_obj = resolved["dep_obj"]
        requested_service_name = report_data.get("appointment_type") or getattr(dep_obj, "dep_name", None)
        is_prepaid, matched_plan = _user_has_prepaid_service(
            request.user,
            spon_obj,
            service_name=requested_service_name,
            dep_obj=dep_obj,
        )

        if not is_prepaid:
            return Response(
                {
                    "error": "Stripe payment completion is required before creating this appointment request and sending confirmation email.",
                    "payment_required": True,
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        try:
            target_status = report_data.get("appointment_status") or "Pending"
            if target_status == APPOINTMENT_PENDING_PAYMENT_STATUS:
                target_status = "Pending"
            appointment = _create_appointment_record(
                resolved,
                appointment_status_value=target_status,
                service_purchased_value=True,
            )
            email_sent, email_error = _send_appointment_request_email(appointment)

            return Response(
                {
                    "message": "Patient appointment booked successfully",
                    "appointment_id": appointment.id,
                    "covered_plan": matched_plan,
                    "email_sent": email_sent,
                    **({"email_error": email_error} if email_error else {}),
                },
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

        if appointmentobj.appointment_status == APPOINTMENT_PENDING_PAYMENT_STATUS:
            return Response(
                {"error": "Cannot update an unpaid appointment draft before Stripe payment is completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if is_sponsor_user(request.user):
            logged_sponsor = get_sponsor_profile(request.user)
            if logged_sponsor is None:
                return Response({"error": "Sponsor profile not found"}, status=status.HTTP_403_FORBIDDEN)
            owns_appointment = (
                appointmentobj.sponsor_id == logged_sponsor.id
                or (appointmentobj.patient is not None and appointmentobj.patient.sponsor_id == logged_sponsor.id)
            )
            if not owns_appointment:
                return Response(
                    {"error": "You do not have permission to update this appointment."},
                    status=status.HTTP_403_FORBIDDEN
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

        if is_sponsor_user(request.user):
            if spon_obj is not None and spon_obj.id != logged_sponsor.id:
                return Response(
                    {"error": "You cannot assign an appointment to another sponsor."},
                    status=status.HTTP_403_FORBIDDEN
                )
            if patient_obj is not None and patient_obj.sponsor_id != logged_sponsor.id:
                return Response(
                    {"error": "You can only assign your own loved ones/patients."},
                    status=status.HTTP_403_FORBIDDEN
                )


        # Step 4: Handle uploaded files
        lab_report_files = list(request.FILES.getlist("lab_reports"))
        if hasattr(request.data, "getlist"):
            lab_report_ids = list(request.data.getlist("lab_report_ids"))
        else:
            raw_ids = request.data.get("lab_report_ids")
            if raw_ids in (None, ""):
                lab_report_ids = []
            elif isinstance(raw_ids, (list, tuple)):
                lab_report_ids = list(raw_ids)
            else:
                lab_report_ids = [raw_ids]
        print("lab_report_files",lab_report_files)
        print("lab_report_ids",lab_report_ids)
        print(len(lab_report_files))
        print(len(lab_report_ids))
        
        if lab_report_files or lab_report_ids:
            # --- Normalize lab_report_ids ---
            # Handle case where input is like ['1,2,null']
            if len(lab_report_ids) == 1 and isinstance(lab_report_ids[0], str) and "," in lab_report_ids[0]:
                lab_report_ids = lab_report_ids[0].split(",")

            # Clean up invalid or placeholder values
            cleaned_ids = []
            for val in lab_report_ids:
                val_str = str(val).strip() if val is not None else ""
                if val_str and val_str.lower() not in ["null", "none", ""]:
                    try:
                        cleaned_ids.append(int(val_str))
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
                
                effective_patient = patient_obj or appointmentobj.patient
                effective_sponsor = (
                    spon_obj
                    or appointmentobj.sponsor
                    or getattr(effective_patient, "sponsor", None)
                )
                effective_dep = dep_obj or appointmentobj.dep
                effective_doc = doc_obj or appointmentobj.doc
                effective_caretaker = caretaker_obj or appointmentobj.caretaker

                # Fetch all lab reports for this appointment & patient
                if effective_patient is not None:
                    lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                        appointment_id=appointmentobj.id,
                        patient_id=effective_patient.id
                    )
                else:
                    lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                        appointment_id=appointmentobj.id
                    )
                print("lab_reports_qs", lab_reports_qs)

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

                sponsor_user = getattr(effective_sponsor, "user", None)
                sponsorname = (
                    (getattr(sponsor_user, "first_name", None) or "").strip()
                    or (getattr(sponsor_user, "username", None) or "").strip()
                    or "Valued Family Member"
                )
                sponsoremail = (getattr(sponsor_user, "email", None) or "").strip()
                departmentname = effective_dep.dep_name if effective_dep else None
                doctorname = (
                    effective_doc.user.first_name
                    if effective_doc and effective_doc.user
                    else None
                )
                patientname = (
                    effective_patient.patient_name
                    if effective_patient
                    else None
                )
                caretakername = (
                    effective_caretaker.user.first_name
                    if effective_caretaker and effective_caretaker.user
                    else None
                )
                date = appointmentobj.appointment_date
                time = appointmentobj.appointment_time
                print("sponsorname", sponsorname)

            from html import escape as html_escape
            from django.core.mail import EmailMessage
            from django.conf import settings
            portal_url = getattr(
                settings,
                "FRONTEND_DASHBOARD_URL",
                "https://verimed-fe.vercel.app/",
            )

            def send_api_care_update_mail(sponsorname, sponsoremail):
                if not sponsoremail:
                    return False, "Sponsor email address is missing."

                subject = "Your appointment is confirmed and updated in your VeriMED Portal."
                message = f"""
                    <p>Dear <strong>{html_escape(sponsorname)}</strong>,</p>

                    <p>Your appointment is confirmed.</p>

                    <p>
                        Our healthcare team will complete the service as scheduled, and the clinical
                        documentation will be securely uploaded for your review.
                    </p>

                    <p>Depending on the service and visit, the documentation may include:</p>
                    <ul>
                        <li>Clinical observations and nursing or physician notes</li>
                        <li>Changes in health status</li>
                        <li>Vital signs and assessment findings</li>
                        <li>Medications or treatment updates</li>
                        <li>Recommendations and follow-up plans</li>
                        <li>Photos or supporting documents (when appropriate)</li>
                    </ul>

                    <p>To review the latest information, simply log in to your VeriMED Portal at your convenience.</p>

                    <p><strong>Login URL:</strong> <a href="{html_escape(portal_url)}">{html_escape(portal_url)}</a></p>

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
                recipient_list = [sponsoremail]

                try:
                    email_msg = EmailMessage(subject, "", from_email, recipient_list)
                    email_msg.content_subtype = "html"  # VERY IMPORTANT
                    email_msg.body = message
                    email_msg.send(fail_silently=False)
                    print("Appointment confirmation email sent successfully")
                    return True, None
                except Exception as e:
                    print(f"Error sending appointment confirmation email: {e}")
                    return False, str(e)

            email_sent, email_error = send_api_care_update_mail(sponsorname, sponsoremail)

            response_message = (
                "Appointment updated successfully Check the Email"
                if email_sent
                else "Appointment updated successfully, but confirmation email could not be sent."
            )
            return Response(
                {
                    "message": response_message,
                    "email_sent": email_sent,
                    **({"email_error": email_error} if email_error else {}),
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        try:
            appointments_qs = _exclude_unpaid_appointment_drafts(VerimedBookAppointment.objects.all())

            if is_sponsor_user(request.user):
                sponsor_profile = get_sponsor_profile(request.user)
                if sponsor_profile is None:
                    return Response([], status=status.HTTP_200_OK)
                appointments_qs = filter_queryset_by_sponsor(appointments_qs, sponsor_profile)
            else:
                sponsor_param = (
                    request.query_params.get("sponsor_id")
                    or request.query_params.get("sponsorid")
                    or request.query_params.get("sponsor")
                )
                if sponsor_param:
                    sponsor_obj = resolve_sponsor_profile_by_param(sponsor_param)
                    if sponsor_obj is None:
                        return Response([], status=status.HTTP_200_OK)
                    appointments_qs = filter_queryset_by_sponsor(appointments_qs, sponsor_obj)

            patient_param = (
                request.query_params.get("patient_id")
                or request.query_params.get("patientid")
                or request.query_params.get("patient")
            )
            if patient_param:
                appointments_qs = appointments_qs.filter(patient_id=patient_param)

            appointments_qs = appointments_qs.order_by('-id')
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

    def delete(self, request):
        valid_ids, invalid_format_ids = _extract_id_list(request, "appoinmentdeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No Appoinment Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        sponsor_user = is_sponsor_user(request.user)
        logged_sponsor = get_sponsor_profile(request.user) if sponsor_user else None
        if sponsor_user and logged_sponsor is None:
            return Response({"error": "Sponsor profile not found."}, status=status.HTTP_403_FORBIDDEN)
        
        notvalidids = list(invalid_format_ids)
        appointments_to_delete = []
        
        for i in valid_ids:
            try:
                appointmentdeleteobj = VerimedBookAppointment.objects.get(id=i)
                if sponsor_user:
                    owns_appointment = (
                        appointmentdeleteobj.sponsor_id == logged_sponsor.id
                        or (appointmentdeleteobj.patient is not None and appointmentdeleteobj.patient.sponsor_id == logged_sponsor.id)
                    )
                    if not owns_appointment:
                        return Response(
                            {"error": "You do not have permission to delete another sponsor's appointment."},
                            status=status.HTTP_403_FORBIDDEN
                        )
                appointments_to_delete.append(appointmentdeleteobj)
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

        # --- DATABASE DELETE ---
        try:
            with transaction.atomic():
                for appointmentdeleteobj in appointments_to_delete:
                    VerimedBookAppointmentLabReports.objects.filter(
                        Q(appointment=appointmentdeleteobj)
                        | Q(referid=str(appointmentdeleteobj.id))
                    ).delete()
                    appointmentdeleteobj.delete()

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
        sponsorid = request.data.get("sponsorid") or request.data.get("sponsor_id")
        try:
                if is_sponsor_user(request.user):
                    sponsor_profile = get_sponsor_profile(request.user)
                    if sponsor_profile is None:
                        return Response([], status=status.HTTP_200_OK)
                    appointments_qs = filter_queryset_by_sponsor(
                        _exclude_unpaid_appointment_drafts(VerimedBookAppointment.objects.all()), sponsor_profile
                    )
                    if patientprofileid:
                        appointments_qs = appointments_qs.filter(patient_id=patientprofileid)
                    appointments_qs = appointments_qs.order_by('-id')
                else:
                    if patientprofileid:
                        appointments_qs = _exclude_unpaid_appointment_drafts(
                            VerimedBookAppointment.objects.filter(patient_id=patientprofileid)
                        )
                        if sponsorid:
                            sponsor_obj = resolve_sponsor_profile_by_param(sponsorid)
                            if sponsor_obj is None:
                                return Response([], status=status.HTTP_200_OK)
                            appointments_qs = filter_queryset_by_sponsor(appointments_qs, sponsor_obj)
                        appointments_qs = appointments_qs.order_by('-id')
                    elif sponsorid:
                        sponsor_obj = resolve_sponsor_profile_by_param(sponsorid)
                        if sponsor_obj is None:
                            return Response([], status=status.HTTP_200_OK)
                        appointments_qs = filter_queryset_by_sponsor(
                            _exclude_unpaid_appointment_drafts(VerimedBookAppointment.objects.all()), sponsor_obj
                        ).order_by('-id')
                    else:
                        appointments_qs = VerimedBookAppointment.objects.none()

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
                appointments_qs = _exclude_unpaid_appointment_drafts(
                    VerimedBookAppointment.objects.filter(doc_id=doctorprofileid)
                )
                if is_sponsor_user(request.user):
                    sponsor_profile = get_sponsor_profile(request.user)
                    if sponsor_profile is None:
                        return Response([], status=status.HTTP_200_OK)
                    appointments_qs = filter_queryset_by_sponsor(appointments_qs, sponsor_profile)
                appointments_qs = appointments_qs.order_by('-id')                
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


class VB_SponsorAppoinment_List(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        sponsorid = (
            request.data.get("sponsorprofileid")
            or request.data.get("sponsorid")
            or request.data.get("sponsor_id")
        )
        patientprofileid = request.data.get("patientprofileid") or request.data.get("patient_id")
        try:
            if is_sponsor_user(request.user):
                sponsor_obj = get_sponsor_profile(request.user)
                if sponsor_obj is None:
                    return Response([], status=status.HTTP_200_OK)
                if sponsorid:
                    requested_sponsor = resolve_sponsor_profile_by_param(sponsorid)
                    if requested_sponsor is None or requested_sponsor.id != sponsor_obj.id:
                        return Response(
                            {"error": "You do not have permission to view another sponsor's appointments."},
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                if not sponsorid:
                    return Response(
                        {"error": "sponsorid is required"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                sponsor_obj = resolve_sponsor_profile_by_param(sponsorid)
                if sponsor_obj is None:
                    return Response(
                        {"error": "Please provide a valid sponsor ID."},
                        status=status.HTTP_404_NOT_FOUND
                    )

            appointments_qs = filter_queryset_by_sponsor(
                _exclude_unpaid_appointment_drafts(VerimedBookAppointment.objects.all()), sponsor_obj
            )
            if patientprofileid:
                appointments_qs = appointments_qs.filter(patient_id=patientprofileid)
            appointments_qs = appointments_qs.order_by('-id')

            serializer = VerimedBookAppointmentViewSlr(
                appointments_qs, many=True, context={'request': request}
            )

            response_data = []

            for item in serializer.data:
                appointment_id = item["id"]
                patient_id = item["patient"]["id"] if item.get("patient") else None

                lab_reports_qs = VerimedBookAppointmentLabReports.objects.filter(
                    appointment_id=appointment_id,
                    patient_id=patient_id
                )

                documents = []
                for report in lab_reports_qs:
                    documents.append({
                        "id": report.id,
                        "filename": report.file.name if report.file else None,
                        "uploaded_at": report.uploaded_at,
                        "view_link": request.build_absolute_uri(report.file.url) if report.file else None,
                        "download_link": request.build_absolute_uri(report.file.url) if report.file else None
                    })

                item_with_docs = dict(item)
                item_with_docs["documents"] = documents
                response_data.append(item_with_docs)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DoctorProfileUpdate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        update_data = request.data.get("doctorprofile_update_data")
        if not update_data:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        data, parse_err = _parse_json_payload(update_data)
        if parse_err:
            return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            doc_updateobj = DoctorProfile.objects.get(id=data.get("doc_profile_updateid"))
        except DoctorProfile.DoesNotExist:
            return Response({"error": "Give me a valid DoctorProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        has_dep = "dep" in data
        dep_obj = doc_updateobj.dep
        if has_dep:
            dep = data.get("dep")
            if dep:
                try:
                    dep_obj = VerimedDepartment.objects.get(id=dep)
                except VerimedDepartment.DoesNotExist:
                    return Response({"error": "Give me a valid Department"}, status=status.HTTP_404_NOT_FOUND)
            else:
                dep_obj = None
    
        has_country_code = "doc_country_code" in data
        if has_country_code:
            countrycode = data.get("doc_country_code")
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
                countrycode_obj = None
                dialcode = None
        else:
            countrycode_obj = doc_updateobj.doc_country_code
            dialcode = countrycode_obj.dial_code if countrycode_obj else None

        has_phone = "doc_phone" in data
        if has_phone:
            phonewithcountrycode = _format_phone_with_dial(dialcode, data.get("doc_phone"))
        
        try:
            with transaction.atomic():
                if has_dep:
                    doc_updateobj.dep = dep_obj
                if has_country_code:
                    doc_updateobj.doc_country_code = countrycode_obj
                if has_phone:
                    doc_updateobj.doc_phone = phonewithcountrycode

                doc_updateobj.doc_address = data.get("doc_address", doc_updateobj.doc_address)
                doc_updateobj.doc_exprience = data.get("doc_exprience", doc_updateobj.doc_exprience)
                doc_updateobj.doc_gender = data.get("doc_gender", doc_updateobj.doc_gender)
                doc_updateobj.speciality = data.get("speciality", doc_updateobj.speciality)
                doc_updateobj.joining_date = data.get("joining_date", doc_updateobj.joining_date)
                doc_updateobj.doc_licence_no = data.get("doc_licence_no", doc_updateobj.doc_licence_no)
                doc_updateobj.doc_city = data.get("doc_city", doc_updateobj.doc_city)
                doc_updateobj.doc_state = data.get("doc_state", doc_updateobj.doc_state)
                doc_updateobj.doc_country = data.get("doc_country", doc_updateobj.doc_country)
                doc_updateobj.doc_pincode = data.get("doc_pincode", doc_updateobj.doc_pincode)
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
        serializer = DoctorProfileViewSlr(doctor_profiles, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientProfileCreateUpdate(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]
    
    def post(self, request):
        update_data = request.data.get("patientprofile_data")
        if not update_data:
            return Response({"error": "patientprofile_data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        data, parse_err = _parse_json_payload(update_data)
        if parse_err:
            return Response({"error": f"{parse_err} patientprofile_data"}, status=status.HTTP_400_BAD_REQUEST)

        medication_data = request.data.get("medication")
        if medication_data:
            medication, med_err = _parse_json_payload(medication_data)
            if med_err:
                return Response({"error": f"{med_err} medication"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            medication = None
        
        sponsorobj = None
        sponsorid = data.get("sponsorid")
        if sponsorid:
            try:
                sponsorobj = SponsorProfile.objects.get(id=sponsorid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Give me a valid SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "Give me a SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)

        caretakerobj = None
        caretakerid = data.get("caretakerid")
        if caretakerid:
            try:
                caretakerobj = CareTakerProfile.objects.get(id=caretakerid)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Give me a valid CareTakerProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        country_code_obj = None
        dialcode = None
        country_code = data.get("country_code")
        if country_code:
            try:
                country_code_obj = VerimedCountryCode.objects.get(code=country_code)
                dialcode = country_code_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid country_code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        phonewithcountrycode = _format_phone_with_dial(dialcode, data.get("phone"))
    
        emer_con_country_code_obj = None
        emer_dialcode = None
        emer_con_country_code = data.get("emer_con_country_code")
        if emer_con_country_code:
            try:
                emer_con_country_code_obj = VerimedCountryCode.objects.get(code=emer_con_country_code)
                emer_dialcode = emer_con_country_code_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid emer_con_country_code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        emer_con_phonewithcountrycode = _format_phone_with_dial(
            emer_dialcode, data.get("emer_con_phone")
        )
        
        local_con_country_code_obj = None
        local_dialcode = None
        local_con_country_code = data.get("local_con_country_code")
        if local_con_country_code:
            try:
                local_con_country_code_obj = VerimedCountryCode.objects.get(code=local_con_country_code)
                local_dialcode = local_con_country_code_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid local_con_country_code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        local_con_phonewithcountrycode = _format_phone_with_dial(
            local_dialcode, data.get("local_con_phone")
        )
                    
        # Step 4: Handle uploaded files
        upload_files = list(request.FILES.getlist("patient_upload_files"))
        cleaned_upload_files_name = _extract_str_list(request.data, "patient_files_name")
        
        if upload_files or cleaned_upload_files_name:
            if len(upload_files) != len(cleaned_upload_files_name):
                return Response(
                    {
                        "error": (
                            f"Mismatch in counts: upload_files ({len(upload_files)}), "
                            f"patient_files_name ({len(cleaned_upload_files_name)})"
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        photo = request.data.get("patient_photo", None)

        try:
            with transaction.atomic():
                patient_profile = PatientProfile.objects.create(
                    sponsor=sponsorobj,
                    caretaker=caretakerobj,
                    country_code=country_code_obj,
                    phone=phonewithcountrycode,
                    photo=photo,
                    emer_con_country_code=emer_con_country_code_obj,
                    emer_con_phone=emer_con_phonewithcountrycode,
                    local_con_country_code=local_con_country_code_obj,
                    local_con_phone=local_con_phonewithcountrycode,
                    email=data.get("email") or None,
                    age=data.get("age"),
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
                    emer_con_name=data.get("emer_con_name") or None,
                    emer_con_relation=data.get("emer_con_relation") or None,
                    emer_con_coun_of_residen=data.get("emer_con_coun_of_residen") or None,
                    emer_con_email=data.get("emer_con_email") or None,
                    local_con_name=data.get("local_con_name") or None,
                    local_con_relation=data.get("local_con_relation") or None,
                    reason_enrollment=data.get("reason_enrollment") or None,
                    reason_other=data.get("reason_other") or None,
                    medical_his_diagnosis=data.get("medical_his_diagnosis") or None,
                    medical_his_cancer=data.get("medical_his_cancer") or None,
                    medical_his_other=data.get("medical_his_other") or None,
                    medical_his_provided_medi_care=data.get("medical_his_provided_medi_care") or None,
                    medical_his_major_surgeries=data.get("medical_his_major_surgeries") or None,
                    medical_his_curr_symp=data.get("medical_his_curr_symp") or None,
                    medication=medication,
                    allergies_issues=data.get("allergies_issues") or False,
                    allergies_drug=data.get("allergies_drug") or None,
                    allergies_food=data.get("allergies_food") or None,
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
                    lifestyle_daily_routine=data.get("lifestyle_daily_routine") or None,
                    lifestyle_dietary_habits=data.get("lifestyle_dietary_habits") or None,
                    lifestyle_sleep_quality=data.get("lifestyle_sleep_quality") or None,
                    lifestyle_physical_activity=data.get("lifestyle_physical_activity") or None,
                    lifestyle_alcohol_use=data.get("lifestyle_alcohol_use") or None,
                    lifestyle_pain_complaints=data.get("lifestyle_pain_complaints") or None,
                    lifestyle_pain_where=data.get("lifestyle_pain_where") or None,
                    social_emotion_health=data.get("social_emotion_health") or None,
                    social_spiritual_needs=data.get("social_spiritual_needs") or None,
                    social_trusted_person=data.get("social_trusted_person") or False,
                    social_name=data.get("social_name") or None,
                    goals_family_hope=data.get("goals_family_hope") or None,
                    goals_special_instructions=data.get("goals_special_instructions") or None,
                    goals_term_membership=data.get("goals_term_membership") or None,
                )
                
                patient_profile.save()
                
                if upload_files:
                    for index, file_obj in enumerate(upload_files):
                        file_name = cleaned_upload_files_name[index]
                        PatientUploadDocuments.objects.create(
                            patient_profile=patient_profile,
                            file=file_obj,
                            filename=file_name,
                            referid=patient_profile.id
                        )
                        
                sponsor_user = getattr(sponsorobj, "user", None)
                sponsorname = (
                    (getattr(sponsor_user, "first_name", None) or "").strip()
                    or (getattr(sponsor_user, "username", None) or "").strip()
                    or "Valued Family Member"
                )
                sponsoremail = (getattr(sponsor_user, "email", None) or "").strip()

                from django.core.mail import EmailMessage
                from django.conf import settings
                portal_url = getattr(
                    settings,
                    "FRONTEND_DASHBOARD_URL",
                    "https://verimed-fe.vercel.app/",
                )

                def send_api_verticalcontact_mail(sponsorname, sponsoremail):
                    if not sponsoremail:
                        return False

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
                    <p><strong>Login URL:</strong> <a href="{portal_url}">{portal_url}</a></p>

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
                    recipient_list = [sponsoremail]

                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                        email_msg.content_subtype = "html"
                        email_msg.body = message
                        email_msg.send(fail_silently=False)
                        print("Appoinment Booking email sent successfully")
                        return True
                    except Exception as e:
                        print(f"Error sending vertical contact email: {e}")
                        return False
                    
                send_api_verticalcontact_mail(sponsorname, sponsoremail)

                return Response(
                    {"message": "Patient Profile Created successfully"},
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
             
    def patch(self, request):
        update_data = request.data.get("patientprofile_update_data")
        if not update_data:
            return Response({"error": "data is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        
        data, parse_err = _parse_json_payload(update_data)
        if parse_err:
            return Response({"error": parse_err}, status=status.HTTP_400_BAD_REQUEST)

        medication_data = request.data.get("medication")
        if medication_data:
            medication, med_err = _parse_json_payload(medication_data)
            if med_err:
                return Response({"error": f"{med_err} medication"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            medication = None
        
        try:
            patient_updateobj = PatientProfile.objects.get(id=data.get("patient_profile_updateid"))
        except PatientProfile.DoesNotExist:
            return Response({"error": "Give me a valid PatientProfile"}, status=status.HTTP_404_NOT_FOUND)
        
        sponsorobj = None
        sponsorid = data.get("sponsorid")
        if sponsorid:
            try:
                sponsorobj = SponsorProfile.objects.get(id=sponsorid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Give me a valid SponsorProfile"}, status=status.HTTP_404_NOT_FOUND)
    
        has_caretakerid = "caretakerid" in data
        caretakerobj = patient_updateobj.caretaker
        if has_caretakerid:
            caretakerid = data.get("caretakerid")
            if caretakerid:
                try:
                    caretakerobj = CareTakerProfile.objects.get(id=caretakerid)
                except CareTakerProfile.DoesNotExist:
                    return Response({"error": "Give me a valid CareTakerProfile"}, status=status.HTTP_404_NOT_FOUND)
            else:
                caretakerobj = None
        
        has_country_code = "country_code" in data
        if has_country_code:
            country_code = data.get("country_code")
            if country_code:
                try:
                    country_code_obj = VerimedCountryCode.objects.get(code=country_code)
                    dialcode = country_code_obj.dial_code
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                country_code_obj = None
                dialcode = None
        else:
            country_code_obj = patient_updateobj.country_code
            dialcode = country_code_obj.dial_code if country_code_obj else None

        has_phone = "phone" in data
        if has_phone:
            phonewithcountrycode = _format_phone_with_dial(dialcode, data.get("phone"))
        
        has_emer_cc = "emer_con_country_code" in data
        if has_emer_cc:
            emer_con_country_code = data.get("emer_con_country_code")
            if emer_con_country_code:
                try:
                    emer_con_country_code_obj = VerimedCountryCode.objects.get(code=emer_con_country_code)
                    emer_dialcode = emer_con_country_code_obj.dial_code
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid emer_con_country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                emer_con_country_code_obj = None
                emer_dialcode = None
        else:
            emer_con_country_code_obj = patient_updateobj.emer_con_country_code
            emer_dialcode = emer_con_country_code_obj.dial_code if emer_con_country_code_obj else None

        has_emer_phone = "emer_con_phone" in data
        if has_emer_phone:
            emer_con_phonewithcountrycode = _format_phone_with_dial(
                emer_dialcode, data.get("emer_con_phone")
            )
                    
        has_local_cc = "local_con_country_code" in data
        if has_local_cc:
            local_con_country_code = data.get("local_con_country_code")
            if local_con_country_code:
                try:
                    local_con_country_code_obj = VerimedCountryCode.objects.get(code=local_con_country_code)
                    local_dialcode = local_con_country_code_obj.dial_code
                except VerimedCountryCode.DoesNotExist:
                    return Response(
                        {"error": "Invalid local_con_country_code"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                local_con_country_code_obj = None
                local_dialcode = None
        else:
            local_con_country_code_obj = patient_updateobj.local_con_country_code
            local_dialcode = local_con_country_code_obj.dial_code if local_con_country_code_obj else None

        has_local_phone = "local_con_phone" in data
        if has_local_phone:
            local_con_phonewithcountrycode = _format_phone_with_dial(
                local_dialcode, data.get("local_con_phone")
            )
                    
        # Step 4: Handle uploaded files
        upload_files = list(request.FILES.getlist("patient_upload_files"))
        upload_files_ids = _extract_str_list(request.data, "patient_files_ids")
        cleaned_upload_files_name = _extract_str_list(request.data, "patient_files_name")
        
        if upload_files or upload_files_ids or cleaned_upload_files_name:
            cleaned_upload_files_ids = []
            for val in upload_files_ids:
                val_str = str(val).strip() if val is not None else ""
                if val_str and val_str.lower() not in ["null", "none", ""]:
                    try:
                        cleaned_upload_files_ids.append(int(val_str))
                    except ValueError:
                        cleaned_upload_files_ids.append(None)
                else:
                    cleaned_upload_files_ids.append(None)
            
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
        
        photo = request.data.get("patient_photo", None)

        try:
            with transaction.atomic():
                if sponsorobj:
                    patient_updateobj.sponsor = sponsorobj
                if has_caretakerid:
                    patient_updateobj.caretaker = caretakerobj
                if has_country_code:
                    patient_updateobj.country_code = country_code_obj
                if has_phone:
                    patient_updateobj.phone = phonewithcountrycode
                if has_emer_cc:
                    patient_updateobj.emer_con_country_code = emer_con_country_code_obj
                if has_emer_phone:
                    patient_updateobj.emer_con_phone = emer_con_phonewithcountrycode
                if has_local_cc:
                    patient_updateobj.local_con_country_code = local_con_country_code_obj
                if has_local_phone:
                    patient_updateobj.local_con_phone = local_con_phonewithcountrycode
                if photo:
                    patient_updateobj.photo = photo
                    
                patient_updateobj.email = data.get("email", patient_updateobj.email)
                patient_updateobj.age = data.get("age", patient_updateobj.age)
                patient_updateobj.height = data.get("height", patient_updateobj.height)
                patient_updateobj.weight = data.get("weight", patient_updateobj.weight)
                patient_updateobj.blood_pressure = data.get("blood_pressure", patient_updateobj.blood_pressure)
                patient_updateobj.blood_sugar = data.get("blood_sugar", patient_updateobj.blood_sugar)
                patient_updateobj.heart_rate = data.get("heart_rate", patient_updateobj.heart_rate)
                patient_updateobj.oxygen = data.get("oxygen", patient_updateobj.oxygen)
                patient_updateobj.temperature = data.get("temperature", patient_updateobj.temperature)
                patient_updateobj.respiratory_rate = data.get("respiratory_rate", patient_updateobj.respiratory_rate)
                     
                patient_updateobj.patient_name = data.get("patient_name", patient_updateobj.patient_name)
                patient_updateobj.patient_dob = data.get("patient_dob", patient_updateobj.patient_dob)
                patient_updateobj.patient_gender = data.get("patient_gender", patient_updateobj.patient_gender)
                patient_updateobj.blood_group = data.get("blood_group", patient_updateobj.blood_group)
                patient_updateobj.patient_home_address = data.get("patient_home_address", patient_updateobj.patient_home_address)
                patient_updateobj.primary_language = data.get("primary_language", patient_updateobj.primary_language)
                patient_updateobj.religion = data.get("religion", patient_updateobj.religion)
                patient_updateobj.escalate_to_physician = data.get("escalate_to_physician", patient_updateobj.escalate_to_physician)
                
                patient_updateobj.emer_con_name = data.get("emer_con_name", patient_updateobj.emer_con_name)
                patient_updateobj.emer_con_relation = data.get("emer_con_relation", patient_updateobj.emer_con_relation)
                patient_updateobj.emer_con_coun_of_residen = data.get("emer_con_coun_of_residen", patient_updateobj.emer_con_coun_of_residen)
                patient_updateobj.emer_con_email = data.get("emer_con_email", patient_updateobj.emer_con_email)
                
                patient_updateobj.local_con_name = data.get("local_con_name", patient_updateobj.local_con_name)
                patient_updateobj.local_con_relation = data.get("local_con_relation", patient_updateobj.local_con_relation)
                
                patient_updateobj.reason_enrollment = data.get("reason_enrollment", patient_updateobj.reason_enrollment)
                patient_updateobj.reason_other = data.get("reason_other", patient_updateobj.reason_other)
                
                patient_updateobj.medical_his_diagnosis = data.get("medical_his_diagnosis", patient_updateobj.medical_his_diagnosis)
                patient_updateobj.medical_his_cancer = data.get("medical_his_cancer", patient_updateobj.medical_his_cancer)
                patient_updateobj.medical_his_other = data.get("medical_his_other", patient_updateobj.medical_his_other)
                patient_updateobj.medical_his_provided_medi_care = data.get("medical_his_provided_medi_care", patient_updateobj.medical_his_provided_medi_care)
                patient_updateobj.medical_his_major_surgeries = data.get("medical_his_major_surgeries", patient_updateobj.medical_his_major_surgeries)
                patient_updateobj.medical_his_curr_symp = data.get("medical_his_curr_symp", patient_updateobj.medical_his_curr_symp)
                
                patient_updateobj.medication = medication or patient_updateobj.medication
                
                patient_updateobj.allergies_issues = data.get("allergies_issues", patient_updateobj.allergies_issues)
                patient_updateobj.allergies_drug = data.get("allergies_drug", patient_updateobj.allergies_drug)
                patient_updateobj.allergies_food = data.get("allergies_food", patient_updateobj.allergies_food)
                
                patient_updateobj.functional_bathe = data.get("functional_bathe", patient_updateobj.functional_bathe)
                patient_updateobj.functional_dress = data.get("functional_dress", patient_updateobj.functional_dress)
                patient_updateobj.functional_eat = data.get("functional_eat", patient_updateobj.functional_eat)
                patient_updateobj.functional_walk = data.get("functional_walk", patient_updateobj.functional_walk)
                patient_updateobj.functional_use_bathroom = data.get("functional_use_bathroom", patient_updateobj.functional_use_bathroom)
                patient_updateobj.functional_daily_activity = data.get("functional_daily_activity", patient_updateobj.functional_daily_activity)
                patient_updateobj.functional_manage_finance = data.get("functional_manage_finance", patient_updateobj.functional_manage_finance)
                patient_updateobj.functional_any_falls = data.get("functional_any_falls", patient_updateobj.functional_any_falls)
                patient_updateobj.functional_how_many = data.get("functional_how_many", patient_updateobj.functional_how_many)
                patient_updateobj.functional_memory_pbms = data.get("functional_memory_pbms", patient_updateobj.functional_memory_pbms)
                
                patient_updateobj.lifestyle_daily_routine = data.get("lifestyle_daily_routine", patient_updateobj.lifestyle_daily_routine)
                patient_updateobj.lifestyle_dietary_habits = data.get("lifestyle_dietary_habits", patient_updateobj.lifestyle_dietary_habits)
                patient_updateobj.lifestyle_sleep_quality = data.get("lifestyle_sleep_quality", patient_updateobj.lifestyle_sleep_quality)
                patient_updateobj.lifestyle_physical_activity = data.get("lifestyle_physical_activity", patient_updateobj.lifestyle_physical_activity)
                patient_updateobj.lifestyle_alcohol_use = data.get("lifestyle_alcohol_use", patient_updateobj.lifestyle_alcohol_use)
                patient_updateobj.lifestyle_pain_complaints = data.get("lifestyle_pain_complaints", patient_updateobj.lifestyle_pain_complaints)
                patient_updateobj.lifestyle_pain_where = data.get("lifestyle_pain_where", patient_updateobj.lifestyle_pain_where)
                
                patient_updateobj.social_emotion_health = data.get("social_emotion_health", patient_updateobj.social_emotion_health)
                patient_updateobj.social_spiritual_needs = data.get("social_spiritual_needs", patient_updateobj.social_spiritual_needs)
                patient_updateobj.social_trusted_person = data.get("social_trusted_person", patient_updateobj.social_trusted_person)
                patient_updateobj.social_name = data.get("social_name", patient_updateobj.social_name)
                
                patient_updateobj.goals_family_hope = data.get("goals_family_hope", patient_updateobj.goals_family_hope)
                patient_updateobj.goals_special_instructions = data.get("goals_special_instructions", patient_updateobj.goals_special_instructions)
                patient_updateobj.goals_term_membership = data.get("goals_term_membership", patient_updateobj.goals_term_membership)
                
                patient_updateobj.save()
                
                if upload_files:
                    for index, file_obj in enumerate(upload_files):
                        report_id = cleaned_upload_files_ids[index]
                        file_name = cleaned_upload_files_name[index]

                        if report_id:
                            try:
                                report = PatientUploadDocuments.objects.get(id=report_id)
                                report.file = file_obj
                                report.filename = file_name or report.filename
                                report.save()
                            except PatientUploadDocuments.DoesNotExist:
                                raise NotFound(detail=f"Invalid patient upload document ID: {report_id}")
                        else:
                            PatientUploadDocuments.objects.create(
                                patient_profile=patient_updateobj,
                                file=file_obj,
                                filename=file_name,
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
            if is_sponsor_user(request.user):
                sponsor_profile = get_sponsor_profile(request.user)
                if sponsor_profile is None:
                    return Response([], status=status.HTTP_200_OK)
                verimed_doctor_qs = PatientProfile.objects.filter(sponsor=sponsor_profile)
            else:
                sponsor_param = (
                    request.query_params.get("sponsor_id")
                    or request.query_params.get("sponsorid")
                    or request.query_params.get("sponsor")
                )
                if sponsor_param:
                    sponsor_obj = resolve_sponsor_profile_by_param(sponsor_param)
                    if sponsor_obj is None:
                        return Response([], status=status.HTTP_200_OK)
                    verimed_doctor_qs = PatientProfile.objects.filter(sponsor=sponsor_obj)
                else:
                    verimed_doctor_qs = PatientProfile.objects.all()
            serializer = PatientProfileViewSlr(
                verimed_doctor_qs, many=True, context={"request": request}
            )
            
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
        valid_ids, invalid_format_ids = _extract_id_list(request, "patientprofiledeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No Patient Profile Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sponsor_user = is_sponsor_user(request.user)
        logged_sponsor = get_sponsor_profile(request.user) if sponsor_user else None
        if sponsor_user and logged_sponsor is None:
            return Response({"error": "Sponsor profile not found."}, status=status.HTTP_403_FORBIDDEN)

        notvalidids = list(invalid_format_ids)
        
        for i in valid_ids:
            try:
                patiend_deleteobj=PatientProfile.objects.get(id=i)
                if sponsor_user and patiend_deleteobj.sponsor_id != logged_sponsor.id:
                    return Response(
                        {"error": "You do not have permission to delete another sponsor's patient."},
                        status=status.HTTP_403_FORBIDDEN
                    )
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
                    id__in=valid_ids
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
        sponsorid = request.data.get("sponsorid") or request.data.get("sponsor_id")
        if is_sponsor_user(request.user):
            sponsor = get_sponsor_profile(request.user)
            if sponsor is None:
                return Response([], status=status.HTTP_200_OK)
            if sponsorid:
                requested_sponsor = resolve_sponsor_profile_by_param(sponsorid)
                if requested_sponsor is None or requested_sponsor.id != sponsor.id:
                    return Response(
                        {"error": "You do not have permission to view another sponsor's patients."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        else:
            sponsor = resolve_sponsor_profile_by_param(sponsorid)
            if sponsor is None:
                return Response(
                    {"error": "Please provide a valid sponsor ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        try:
            
            verimed_doctor_qs = PatientProfile.objects.filter(sponsor=sponsor.id)
            serializer = PatientProfileViewSlr(
                verimed_doctor_qs, many=True, context={"request": request}
            )
            
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
        sponsorid = request.data.get("sponsorid") or request.data.get("sponsor_id")
        if is_sponsor_user(request.user):
            sponsor = get_sponsor_profile(request.user)
            if sponsor is None:
                return Response({"error": "Sponsor profile not found."}, status=status.HTTP_403_FORBIDDEN)
            if sponsorid:
                requested_sponsor = resolve_sponsor_profile_by_param(sponsorid)
                if requested_sponsor is None or requested_sponsor.id != sponsor.id:
                    return Response(
                        {"error": "You do not have permission to delete another sponsor's patients."},
                        status=status.HTTP_403_FORBIDDEN
                    )
        else:
            sponsor = resolve_sponsor_profile_by_param(sponsorid)
            if sponsor is None:
                return Response(
                    {"error": "Please provide a valid sponsor ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        valid_ids, invalid_format_ids = _extract_id_list(request, "patientprofiledeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No Patient Deleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = list(invalid_format_ids)
        
        for i in valid_ids:
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
                for i in valid_ids:
                    try:
                        patientprofiledeleteobj = PatientProfile.objects.get(id=i,sponsor=sponsor)
                        
                        
                        # Delete related documents
                        PatientUploadDocuments.objects.filter(
                            Q(patient_profile=patientprofiledeleteobj) | Q(referid=str(patientprofiledeleteobj.id))
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
        
        data, parse_err = _parse_json_payload(update_data)
        if parse_err or not isinstance(data, dict):
            return Response({"error": parse_err or "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        
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
            valid_ids, invalid_format_ids = _extract_id_list(request, "sponsorprofiledeleteids")
    
            if not valid_ids and not invalid_format_ids:
                return Response(
                    {"error": "No SponsorProfile Deleted IDs provided."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            notvalidids = list(invalid_format_ids)
            
            for i in valid_ids:
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
                        id__in=valid_ids
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
        
        data, parse_err = _parse_json_payload(update_data)
        if parse_err or not isinstance(data, dict):
            return Response({"error": parse_err or "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)

        
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

        report_data, parse_err = _parse_json_payload(raw_data)
        if parse_err or not isinstance(report_data, dict):
            return Response(
                {"error": parse_err or "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 2: Validate Foreign Keys
        doc_id = report_data.get("doctor") or report_data.get("doc")
        if not doc_id:
            return Response({"error": "doctor ID is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            doc_obj = DoctorProfile.objects.get(id=doc_id)
        except DoctorProfile.DoesNotExist:
            return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        patient_id = report_data.get("patient")
        if not patient_id:
            return Response({"error": "patient ID is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            patient_obj = PatientProfile.objects.get(id=patient_id)
        except PatientProfile.DoesNotExist:
            return Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)

        sponid = report_data.get("sponsor")
        spon_obj = None
        if sponid:
            try:
                spon_obj = SponsorProfile.objects.get(id=sponid)
            except SponsorProfile.DoesNotExist:
                return Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)
        elif patient_obj is not None:
            spon_obj = patient_obj.sponsor

        caretaker_id = report_data.get("caretaker")
        caretaker_obj = None
        if caretaker_id:
            try:
                caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
            except CareTakerProfile.DoesNotExist:
                return Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)
            
        # Step 3: Get uploaded files (multiple), avoiding duplicates
        doctor_report_files = list(request.FILES.getlist("doc_reports"))
        if not doctor_report_files:
            doctor_report_files = (
                list(request.FILES.getlist("results_records"))
                + list(request.FILES.getlist("diagnostic_images"))
                + list(request.FILES.getlist("voice_notes"))
            )


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
                
                sponsorname = getattr(getattr(spon_obj, "user", None), "first_name", None) or "Valued Client"
                sponsoremail = getattr(getattr(spon_obj, "user", None), "email", None)
                doctoremail = getattr(getattr(doc_obj, "user", None), "email", None)
                recipient_list = [e for e in (sponsoremail, doctoremail) if e]
                
                from django.core.mail import EmailMessage
                from django.conf import settings
                portal_url = getattr(
                    settings,
                    "FRONTEND_DASHBOARD_URL",
                    "https://verimed-fe.vercel.app/",
                )

                def send_api_verticalcontact_mail(recipient_name):
                    if not recipient_list:
                        return False
                    subject = "Your VeriMED Service Report Will Be Available Soon"

                    message = f"""
                    <p>Hello <strong>{recipient_name}</strong>,</p>

                    <p>
                        Your recent VeriMED service or consultation has been completed.
                        A detailed report will be uploaded to your portal shortly for your review.
                    </p>

                    <p><strong>Login URL:</strong> <a href="{portal_url}">{portal_url}</a></p>

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
                    
                    try:
                        email_msg = EmailMessage(subject, "", from_email, recipient_list)
                       

                        # ✅ Attach each uploaded file to the email
                        for f in doctor_report_files:
                            if hasattr(f, "seek"):
                                f.seek(0)
                            email_msg.attach(
                                f.name,
                                f.read(),
                                getattr(f, "content_type", None) or "application/octet-stream",
                            )

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

        report_data, parse_err = _parse_json_payload(raw_data)
        if parse_err or not isinstance(report_data, dict):
            return Response(
                {"error": parse_err or "Invalid data type. Expected JSON string or dict."},
                status=status.HTTP_400_BAD_REQUEST
            )

        doc_report_updateid=report_data.get("doc_report_updateid")
        
        if doc_report_updateid:
            try:
                updateobj = DoctorReports.objects.get(id=doc_report_updateid)
            except DoctorReports.DoesNotExist:
                return Response({"error": "Invalid doc_report_updateid ID"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "doc_report_updateid ID is mandatory"}, status=status.HTTP_400_BAD_REQUEST)
            

        # Step 2: Validate Foreign Keys (only when provided in payload)
        has_sponsor_key = "sponsor" in report_data
        spon_obj = updateobj.sponsor
        if has_sponsor_key:
            sponid = report_data.get("sponsor")
            if sponid:
                try:
                    spon_obj = SponsorProfile.objects.get(id=sponid)
                except SponsorProfile.DoesNotExist:
                    return Response({"error": "Invalid sponsor ID"}, status=status.HTTP_404_NOT_FOUND)
            else:
                spon_obj = None

        has_doctor_key = "doctor" in report_data or "doc" in report_data
        doc_obj = updateobj.doctor
        if has_doctor_key:
            doc_id = report_data.get("doctor") or report_data.get("doc")
            if doc_id:
                try:
                    doc_obj = DoctorProfile.objects.get(id=doc_id)
                except DoctorProfile.DoesNotExist:
                    return Response({"error": "Invalid doctor ID"}, status=status.HTTP_404_NOT_FOUND)

        has_caretaker_key = "caretaker" in report_data
        caretaker_obj = updateobj.caretaker
        if has_caretaker_key:
            caretaker_id = report_data.get("caretaker")
            if caretaker_id:
                try:
                    caretaker_obj = CareTakerProfile.objects.get(id=caretaker_id)
                except CareTakerProfile.DoesNotExist:
                    return Response({"error": "Invalid caretaker ID"}, status=status.HTTP_404_NOT_FOUND)
            else:
                caretaker_obj = None

        has_patient_key = "patient" in report_data
        patient_obj = updateobj.patient
        if has_patient_key:
            patient_id = report_data.get("patient")
            if patient_id:
                try:
                    patient_obj = PatientProfile.objects.get(id=patient_id)
                except PatientProfile.DoesNotExist:
                    return Response({"error": "Invalid patient ID"}, status=status.HTTP_404_NOT_FOUND)
            
        # Step 4: Handle uploaded files
        doc_report_files = list(request.FILES.getlist("doc_reports"))
        doc_report_ids = _extract_str_list(request.data, "doc_report_ids")

        # Clean up invalid or placeholder values
        cleaned_ids = []
        for val in doc_report_ids:
            val_str = str(val).strip() if val is not None else ""
            if val_str and val_str.lower() not in ["null", "none", ""]:
                try:
                    cleaned_ids.append(int(val_str))
                except ValueError:
                    cleaned_ids.append(None)
            else:
                cleaned_ids.append(None)

        if len(doc_report_files) != len(cleaned_ids):
            return Response(
                {
                    "error": f"The number of lab_reports ({len(doc_report_files)}) "
                            f"does not match the number of lab_report_ids ({len(cleaned_ids)})"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        

        # Step 4: Transaction block to ensure atomic save
        try:
            with transaction.atomic():
                # Foreign Keys
                updateobj.sponsor = spon_obj
                updateobj.doctor = doc_obj
                updateobj.patient = patient_obj
                updateobj.caretaker = caretaker_obj
                # Patient Info & Vitals (preserve existing when omitted)
                updateobj.patient_name = report_data.get("patient_name", updateobj.patient_name)
                updateobj.blood_group = report_data.get("blood_group", updateobj.blood_group)
                updateobj.bp = report_data.get("bp", updateobj.bp)
                updateobj.heart_rate = report_data.get("heart_rate", updateobj.heart_rate)
                updateobj.sugar = report_data.get("sugar", updateobj.sugar)
                updateobj.oxygen = report_data.get("oxygen", updateobj.oxygen)
                updateobj.temperature = report_data.get("temperature", updateobj.temperature)
                updateobj.respiratory_rate = report_data.get("respiratory_rate", updateobj.respiratory_rate)
                updateobj.weight = report_data.get("weight", updateobj.weight)
                updateobj.doctor_notes = report_data.get("doctor_notes", updateobj.doctor_notes)
                updateobj.initial_visit = report_data.get("initial_visit", updateobj.initial_visit)
                
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

        except NotFound as e:
            return Response({"error": str(e.detail)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self,request):
        try:
            verimed_doctor_qs = DoctorReports.objects.all()
            if is_sponsor_user(request.user):
                sponsor_profile = get_sponsor_profile(request.user)
                if sponsor_profile is None:
                    return Response([], status=status.HTTP_200_OK)
                verimed_doctor_qs = filter_queryset_by_sponsor(verimed_doctor_qs, sponsor_profile)
            else:
                sponsor_param = (
                    request.query_params.get("sponsor_id")
                    or request.query_params.get("sponsorid")
                    or request.query_params.get("sponsor")
                )
                if sponsor_param:
                    sponsor_obj = resolve_sponsor_profile_by_param(sponsor_param)
                    if sponsor_obj is None:
                        return Response([], status=status.HTTP_200_OK)
                    verimed_doctor_qs = filter_queryset_by_sponsor(verimed_doctor_qs, sponsor_obj)

            patient_param = (
                request.query_params.get("patient_id")
                or request.query_params.get("patientid")
                or request.query_params.get("patient")
            )
            if patient_param:
                try:
                    verimed_doctor_qs = verimed_doctor_qs.filter(patient_id=int(patient_param))
                except (TypeError, ValueError):
                    return Response([], status=status.HTTP_200_OK)

            verimed_doctor_qs = verimed_doctor_qs.order_by("-id")
            serializer = DoctorReportsViewSlr(verimed_doctor_qs, many=True,context={"request": request})
            
            response_data = []

            for item in serializer.data:
                docreport_id = item["id"]

                # Fetch all lab reports for this report
                lab_reports_qs = VerimedDoctorReportsFiles.objects.filter(
                    Q(doc_report_files_id=docreport_id) | Q(referid=str(docreport_id))
                ).distinct()

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
        valid_ids, invalid_format_ids = _extract_id_list(request, "doctorreportsdeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No Doctor Reports Deleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = list(invalid_format_ids)
        
        for i in valid_ids:
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
                for i in valid_ids:
                    try:
                        doctorreportsdeleteobj = DoctorReports.objects.get(id=i)
                        
                        # Delete related documents
                        VerimedDoctorReportsFiles.objects.filter(
                            Q(doc_report_files=doctorreportsdeleteobj) | Q(referid=str(doctorreportsdeleteobj.id))
                        ).delete()

                        # Delete the report
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
    permission_classes = [AllowAny]
    def post(self,request):
        data=request.data
        country_code_obj=None
        dialcode=None
        country_code = data.get("country_code")
        if country_code:
            try:
                country_code_obj = VerimedCountryCode.objects.get(code=country_code)
                dialcode = country_code_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid country_code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        phonewithcountrycode = _format_phone_with_dial(dialcode, data.get("phone"))
        
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
                    if not contactus.email:
                        return False
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
                    recipient_list = [contactus.email]
                    
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
        valid_ids, invalid_format_ids = _extract_id_list(request, "contactusdeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No ContactUs Deleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = list(invalid_format_ids)
        
        for i in valid_ids:
            try:
                contactusdeleteobj=ContactUs.objects.get(id=i)
            except ContactUs.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid ContactUs Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
 
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                for i in valid_ids:
                    try:
                        contactusdeleteobj = ContactUs.objects.get(id=i)
                        contactusdeleteobj.delete()
                    except ContactUs.DoesNotExist:
                        return Response({"error": "Invalid ContactUs Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)

                return Response({"message": "ContactUs Deleted sucessfully"}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KetnyproductionCheckC(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):

        raw_data = request.data.get("ketnyproduct_payload")
        if not raw_data:
            return Response(
                {"error": "ketnyproduct_payload is mandatory"},
                status=status.HTTP_400_BAD_REQUEST
            )

        dep_data, parse_err = _parse_json_payload(raw_data)
        if parse_err or not isinstance(dep_data, dict):
            return Response(
                {"error": parse_err or "Invalid data type. Expected JSON string or dict."},
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
        
        phonewithcountrycode = _format_phone_with_dial(dialcode, dep_data.get("phone"))
            
            
        emergency_country_code = dep_data.get("emergency_country_code")
        if emergency_country_code:

            try:
                emergency_country_code_obj = VerimedCountryCode.objects.get(code=emergency_country_code)
                emr_dialcode = emergency_country_code_obj.dial_code
            except VerimedCountryCode.DoesNotExist:
                return Response(
                    {"error": "Invalid Country Code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            emergency_country_code_obj=None
            emr_dialcode=None
        
        emrphonewithcountrycode = _format_phone_with_dial(emr_dialcode, dep_data.get("emergency_phone"))
        
        
       
        # --- MAIN TRANSACTION ---
        try:
            with transaction.atomic():
                # Create screening check record
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
            from django.template.loader import render_to_string

            def sendmail(user_email):
                if not user_email:
                    return False
                try:
                    subject = "Free Diabetes Screening & Kidney Protection Check"
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [user_email]

                    html_content = render_to_string("user_notification.html")

                    mail = EmailMultiAlternatives(
                        subject=subject,
                        body="Your form submission successfully",
                        from_email=from_email,
                        to=recipient_list
                    )

                    mail.attach_alternative(html_content, "text/html")
                    mail.send()
                    print("Email sent successfully")
                    return True
                except Exception as mail_err:
                    print(f"Error sending user screening email: {mail_err}")
                    return False

            sendmail(verimeddepartment.email)

            to_email = ["screenings@verimed.care","info@verimed.care"]

            def sendadminmail(verimed_entry):
                try:
                    subject = "Free Diabetes Screening & Kidney Protection Check"
                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = to_email

                    html_content = render_to_string(
                        "admin_notification.html",
                        {"verimeddepartment": verimed_entry}
                    )

                    mail = EmailMultiAlternatives(
                        subject=subject,
                        body="New form submission received",
                        from_email=from_email,
                        to=recipient_list
                    )

                    mail.attach_alternative(html_content, "text/html")
                    mail.send()
                    print("Admin notification email sent successfully")
                    return True
                except Exception as mail_err:
                    print(f"Error sending admin screening email: {mail_err}")
                    return False
                
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
        valid_ids, invalid_format_ids = _extract_id_list(request, "freekidneydeleteids")

        if not valid_ids and not invalid_format_ids:
            return Response(
                {"error": "No Patient freekidneydeleteids Deleted IDs provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notvalidids = list(invalid_format_ids)
        
        for i in valid_ids:
            try:
                freekidneydeleteobj=KetnyproductionCheck.objects.get(id=i)
            except KetnyproductionCheck.DoesNotExist:
                notvalidids.append(i)

        if notvalidids:
            return Response(
                {
                    "error": "Invalid KetnyproductionCheck Deleted IDs.",
                    "invalid_ids": notvalidids
                },
                status=status.HTTP_400_BAD_REQUEST
            )
 
        
        # --- DATABASE DE choose LETE ---
        try:
            with transaction.atomic():
                deleted_count, _ = KetnyproductionCheck.objects.filter(id__in=valid_ids).delete()
                if deleted_count == 0:
                    return Response({"error": "Invalid KetnyproductionCheck Deleteid ID"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"message": "Deleted sucessfully"}, status=status.HTTP_200_OK)
                    
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
       
        
# paymentimport stripe
try:
    import stripe
except ImportError:
    stripe = None
import json
from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order


def _configure_stripe():
    secret_key = (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
    if stripe is None:
        return None, "Stripe SDK is not installed on the server."
    if not secret_key or secret_key == "sk_test_placeholder":
        return None, "Stripe is not configured on the server. Please set STRIPE_SECRET_KEY in environment variables."
    stripe.api_key = secret_key
    return secret_key, None


def payment_page(request):
    return render(request, "payment.html")


def create_checkout_session(request):
    _, stripe_err = _configure_stripe()
    if stripe_err:
        return HttpResponse(stripe_err, status=503)

    backend_base_url = getattr(
        settings, "FRONTEND_URL", "https://verimed-be.vercel.app"
    ).rstrip("/")

    session = stripe.checkout.Session.create(
        mode="payment",
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
        success_url=f"{backend_base_url}/verimed/success/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{backend_base_url}/verimed/cancel/",
    )

    # HTTP 303 is recommended
    return redirect(session.url, permanent=False)


class CreateAppointmentCheckoutSession(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        resolved, error_response = _validate_and_resolve_appointment_request(request)
        if error_response is not None:
            return error_response

        report_data = resolved["report_data"]
        spon_obj = resolved["spon_obj"]
        dep_obj = resolved["dep_obj"]
        requested_service_name = report_data.get("appointment_type") or getattr(dep_obj, "dep_name", None)

        # If the sponsor/user already owns this exact active plan, create & email directly
        is_prepaid, matched_plan = _user_has_prepaid_service(
            request.user,
            spon_obj,
            service_name=requested_service_name,
            dep_obj=dep_obj,
        )
        if is_prepaid:
            try:
                target_status = report_data.get("appointment_status") or "Pending"
                if target_status == APPOINTMENT_PENDING_PAYMENT_STATUS:
                    target_status = "Pending"
                appointment = _create_appointment_record(
                    resolved,
                    appointment_status_value=target_status,
                    service_purchased_value=True,
                )
                email_sent, email_error = _send_appointment_request_email(appointment)
                return Response(
                    {
                        "payment_required": False,
                        "created": True,
                        "appointment_id": appointment.id,
                        "covered_plan": matched_plan,
                        "message": "Patient appointment booked successfully",
                        "email_sent": email_sent,
                        **({"email_error": email_error} if email_error else {}),
                    },
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Otherwise require Stripe Checkout BEFORE finalizing/emailing the appointment
        _, stripe_err = _configure_stripe()
        if stripe_err:
            return Response({"error": stripe_err}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        unit_amount_cents, canonical_service_name = _resolve_appointment_service_pricing(
            appointment_type=report_data.get("appointment_type"),
            dep_obj=dep_obj,
            raw_amount=report_data.get("amount"),
        )
        if not unit_amount_cents or unit_amount_cents <= 0:
            return Response(
                {"error": "A valid billable service fee is required to initiate Stripe Checkout."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        appointments_url = _resolve_frontend_appointments_url(request)
        effective_sponsor_user = getattr(spon_obj, "user", None)
        customer_email = (
            (getattr(effective_sponsor_user, "email", None) or "").strip()
            or (getattr(request.user, "email", None) or "").strip()
            or None
        )

        draft = None
        try:
            draft_amount = Decimal(unit_amount_cents) / Decimal("100")
            draft = _create_appointment_record(
                resolved,
                appointment_status_value=APPOINTMENT_PENDING_PAYMENT_STATUS,
                service_purchased_value=False,
                amount_override=draft_amount,
            )

            checkout_kwargs = {
                "mode": "payment",
                "line_items": [
                    {
                        "price_data": {
                            "currency": "usd",
                            "unit_amount": int(unit_amount_cents),
                            "product_data": {
                                "name": canonical_service_name,
                            },
                        },
                        "quantity": 1,
                    }
                ],
                "client_reference_id": str(draft.id),
                "metadata": {
                    "appointment_draft_id": str(draft.id),
                    "requested_by_user_id": str(request.user.id),
                    "service_name": canonical_service_name[:120],
                },
                "success_url": f"{appointments_url}?stripe_payment=success&session_id={{CHECKOUT_SESSION_ID}}&draft_id={draft.id}",
                "cancel_url": f"{appointments_url}?stripe_payment=cancelled&draft_id={draft.id}",
            }
            if customer_email:
                checkout_kwargs["customer_email"] = customer_email

            session = stripe.checkout.Session.create(**checkout_kwargs)
            return Response(
                {
                    "payment_required": True,
                    "checkout_url": _session_field(session, "url"),
                    "session_id": _session_field(session, "id"),
                    "draft_id": draft.id,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            if draft is not None:
                try:
                    with transaction.atomic():
                        VerimedBookAppointmentLabReports.objects.filter(
                            Q(appointment=draft) | Q(referid=str(draft.id))
                        ).delete()
                        draft.delete()
                except Exception:
                    pass
            return Response(
                {"error": f"Unable to create Stripe Checkout session: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )


class VerifyAppointmentCheckoutSession(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = (request.data.get("session_id") or "").strip()
        requested_draft_id = request.data.get("draft_id")

        if not session_id:
            return Response({"error": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        _, stripe_err = _configure_stripe()
        if stripe_err:
            return Response({"error": stripe_err}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except Exception as e:
            return Response(
                {"error": f"Failed to verify Stripe Checkout session: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_status = (_session_field(session, "payment_status") or "").lower()
        metadata = _session_field(session, "metadata") or {}
        meta_draft_id = _session_field(metadata, "appointment_draft_id") or _session_field(
            session, "client_reference_id"
        )

        if requested_draft_id and meta_draft_id and str(requested_draft_id) != str(meta_draft_id):
            return Response(
                {"error": "Stripe session does not match the specified appointment draft."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolved_draft_id = meta_draft_id or requested_draft_id
        if not resolved_draft_id or not str(resolved_draft_id).isdigit():
            return Response(
                {"error": "Missing or invalid appointment draft reference on Stripe session."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        draft_pk = int(resolved_draft_id)

        try:
            draft_obj = VerimedBookAppointment.objects.select_related("patient").get(id=draft_pk)
        except VerimedBookAppointment.DoesNotExist:
            return Response(
                {"error": "Appointment draft was not found or was cancelled."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if is_sponsor_user(request.user):
            logged_sponsor = get_sponsor_profile(request.user)
            owns_draft = logged_sponsor is not None and (
                draft_obj.sponsor_id == logged_sponsor.id
                or (draft_obj.patient is not None and draft_obj.patient.sponsor_id == logged_sponsor.id)
            )
            if not owns_draft:
                return Response(
                    {"error": "You do not have permission to verify another sponsor's appointment payment."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if payment_status != "paid":
            return Response(
                {
                    "paid": False,
                    "payment_status": payment_status or "unpaid",
                    "error": "Stripe payment is not completed yet. Appointment was not created.",
                },
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        appointment, transitioned, email_sent, email_error = _finalize_paid_appointment_draft(
            draft_pk, session_obj=session
        )

        return Response(
            {
                "paid": True,
                "created": transitioned,
                "already_finalized": not transitioned,
                "appointment_id": appointment.id,
                "appointment_status": appointment.appointment_status,
                "email_sent": email_sent,
                **({"email_error": email_error} if email_error else {}),
                "message": (
                    "Payment verified and appointment request sent!"
                    if email_sent
                    else "Payment verified and appointment requested, but sponsor email could not be sent."
                ),
            },
            status=status.HTTP_200_OK,
        )


class CancelAppointmentCheckoutSession(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        draft_id = request.data.get("draft_id")
        if not draft_id or not str(draft_id).isdigit():
            return Response({"error": "Valid draft_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        draft_pk = int(draft_id)
        try:
            draft_obj = VerimedBookAppointment.objects.select_related("patient").get(id=draft_pk)
        except VerimedBookAppointment.DoesNotExist:
            return Response({"cancelled": True, "deleted": False}, status=status.HTTP_200_OK)

        if is_sponsor_user(request.user):
            logged_sponsor = get_sponsor_profile(request.user)
            owns_draft = logged_sponsor is not None and (
                draft_obj.sponsor_id == logged_sponsor.id
                or (draft_obj.patient is not None and draft_obj.patient.sponsor_id == logged_sponsor.id)
            )
            if not owns_draft:
                return Response(
                    {"error": "You do not have permission to cancel another sponsor's draft."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        if draft_obj.appointment_status != APPOINTMENT_PENDING_PAYMENT_STATUS:
            return Response(
                {"cancelled": False, "already_paid": True, "appointment_id": draft_obj.id},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            VerimedBookAppointmentLabReports.objects.filter(
                Q(appointment=draft_obj) | Q(referid=str(draft_obj.id))
            ).delete()
            draft_obj.delete()

        return Response({"cancelled": True, "deleted": True}, status=status.HTTP_200_OK)


def success(request):
    return render(request, "success.html")


def cancel(request):
    return render(request, "cancel.html")


@csrf_exempt
def stripe_webhook(request):
    if stripe is None:
        return HttpResponse(status=503)

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    sig_error_cls = getattr(stripe, "SignatureVerificationError", None) or getattr(
        getattr(stripe, "error", None), "SignatureVerificationError", Exception
    )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )

    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)

    except sig_error_cls:
        # Invalid signature
        return HttpResponse(status=400)

    # PAYMENT SUCCESS
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        payment_intent = session.get("payment_intent") or session.get("id")
        email = (session.get("customer_details") or {}).get("email") or session.get("customer_email") or "noreply@verimed.care"
        amount = session.get("amount_total") or 0

        if payment_intent:
            Order.objects.get_or_create(
                payment_intent=payment_intent,
                defaults={
                    "email": email,
                    "amount": amount,
                    "status": "paid",
                },
            )

        payment_status = (session.get("payment_status") or "").lower()
        metadata = session.get("metadata") or {}
        draft_ref = metadata.get("appointment_draft_id") or session.get("client_reference_id")
        if payment_status == "paid" and draft_ref and str(draft_ref).isdigit():
            try:
                _finalize_paid_appointment_draft(int(draft_ref), session_obj=session)
            except VerimedBookAppointment.DoesNotExist:
                pass

    return HttpResponse(status=200)
