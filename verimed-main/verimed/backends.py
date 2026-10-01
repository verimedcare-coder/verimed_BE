# verimed/backends.py
from django.contrib.auth.backends import BaseBackend
from .models import SponsorUser, PatientUser
from django.contrib.auth.hashers import check_password

class SponsorBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            sponsor = SponsorUser.objects.get(email=email)
            if check_password(password, sponsor.password):
                return sponsor
        except SponsorUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return SponsorUser.objects.get(pk=user_id)
        except SponsorUser.DoesNotExist:
            return None


class PatientBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            patient = PatientUser.objects.get(email=email)
            if check_password(password, patient.password):
                return patient
        except PatientUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return PatientUser.objects.get(pk=user_id)
        except PatientUser.DoesNotExist:
            return None
