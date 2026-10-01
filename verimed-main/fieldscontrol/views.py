from rest_framework.response import Response
from rest_framework import status
import re
from django.utils.dateparse import parse_datetime
from .serializers import ValidationsCodeSlr,ValidateFieldValidationPageInfoSlr
from rest_framework.views import APIView
from rest_framework.response import Response
import json
from django.db import transaction
from rest_framework import status
from .models import FieldsControlClassInfo,FieldsControlFields,FieldsControlCode,FieldsControlErrors
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from datetime import date, datetime,time






def allvalidate(value, field_name, display_name, checks=None):
    """
    Runs multiple validation checks on a single field.
    
    Args:
        value: the field value
        field_name: string name for error messages
        checks: list of validation rules
    
    Rules:
        1 -> Mandatory
        2 -> Must be integer
        3 -> Min length >= 3 (for strings)
        4 -> Max length <= 10 (for strings)
    """
    errors = []
    if not checks:
        return errors
    print("value",value)
    print("field_name",display_name)
    
    for check in checks:
        print("cheddck",check)
        
        if not checks:
            return errors
        # 1. Maximum length 100
        if check == "max100char":
            # Check if the value is None or empty string
            value = str(value).strip()
            print("value",value) 
            count = len(value)
            print("count",count)
            if count >= 100:
                error_code = "1002"
                try:
                    error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                    errors.append(f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}")
                    
                except FieldsControlErrors.DoesNotExist:
                    raise ValueError("Error code not found")
        # 1. Maximum length 15
        if check == "max15char":
            # Check if the value is None or empty string
            value = str(value).strip()
            print("value",value) 
            count = len(value)
            print("count",count)
            if count > 15:
                error_code = "1003"
                try:
                    error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                    errors.append(f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}")
                    
                except FieldsControlErrors.DoesNotExist:
                    raise ValueError("Error code not found")
        # 3. Email format    
        if check == "email":
            if value is None or value == "":
                # Accept null (None or empty string) as valid
                continue
            else:
                pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
                if not re.match(pattern, str(value)):
                    error_code = "1004"   # Assign a new error code for email validation
                    try:
                        error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                        errors.append(f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}")
                    except FieldsControlErrors.DoesNotExist:  
                        raise ValueError("Error code not found")
        # 4. Integer check                        
        if check == "int":
            print("value display",value,display_name)
            try:
                int(value)
            except (ValueError, TypeError):
                error_code = "1005"
                try:
                    error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                    errors.append(f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}")

                except FieldsControlErrors.DoesNotExist:
                    raise ValueError("Error code not found")   
                
        # 5. Date Format
        if check == "date_format":
            if value:  # make sure it's not None or empty
                if isinstance(value, str):
                    try:
                        parsed_date = datetime.strptime(value.strip(), "%Y-%m-%d").date()
                        # ✅ Valid format
                    except ValueError:
                        error_code = "1006"
                        try:
                            error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                            errors.append(
                                f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}"
                            )
                        except FieldsControlErrors.DoesNotExist:
                           raise ValueError("Error code not found")  
                else:
                    # Not even a string (maybe already a date object?)
                    if not isinstance(value, date):
                        error_code = "1006"
                        try:
                            error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                            errors.append(
                                f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}"
                            )
                        except FieldsControlErrors.DoesNotExist:
                           raise ValueError("Error code not found")  
        
        # 6. Time Format
        if check == "time_format":
            if value:  # make sure it's not None or empty
                parsed_time = None
            if isinstance(value, time):
                parsed_time = value
            elif isinstance(value, str):
                try:
                    parsed_time = datetime.strptime(value.strip(), "%H:%M:%S").time()
                except ValueError:
                    try:
                        parsed_time = datetime.strptime(value.strip(), "%H:%M").time()
                    except ValueError:
                        error_code = "1007"
                        try:
                            error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                            errors.append(
                                f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}"
                            )
                        except FieldsControlErrors.DoesNotExist:
                            raise ValueError("Error code not found")


        # 8. Maximum length 20
        if check == "max20char":
            # Check if the value is None or empty string
            value = str(value).strip()
            print("value",value) 
            count = len(value)
            print("count",count)
            if count > 20:
                error_code = "1008"
                try:
                    error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                    errors.append(f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}")
                    
                except FieldsControlErrors.DoesNotExist:
                    raise ValueError("Error code not found")

        # 9. Boolean check
        if check == "isboolean":
            # Convert to string and normalize
            value_str = str(value).strip().lower()
            print("value", value_str)

            # Allowed values: True/False (boolean) or "true"/"false"/"1"/"0"
            if value not in [True, False] and value_str not in ["true", "false", "1", "0"]:
                error_code = "1009"  # your custom error code for boolean check
                try:
                    error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                    errors.append(
                        f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}"
                    )
                except FieldsControlErrors.DoesNotExist:
                    raise ValueError("Error code not found")

        
        #  None or Empty check              
        if check == "noneempty":
            print("dddddd")
            if value in (None, "", "null", "None"):
                error_code = "1001"
                try:
                    error_obj = FieldsControlErrors.objects.get(error_code=error_code)
                    errors.append(f"{error_code}~^~{field_name}~^~{display_name} {error_obj.error_name}")

                except FieldsControlErrors.DoesNotExist:
                    raise ValueError("Error code not found")



            
    return errors


def field_validate_cheak(payload, validate_error_code):
    try:
        validate_pageinfo = ValidatePageInfo.objects.get(code=validate_error_code)
        validate_data = ValidateFieldValidation.objects.filter(page_info=validate_pageinfo.id)
    except ValidatePageInfo.DoesNotExist:
        validate_data = []
                
    print("validate_data",validate_data)
    all_errors = []
    cleaned_data = []

    for idx, item in enumerate(payload, start=1):
        errors = []
        cleaned_row = {}
        # put validation rules into a dict for quick lookup
    rules_map = {rule.field_name: rule for rule in validate_data}

    for idx, item in enumerate(payload, start=1):
        errors = []
        cleaned_row = {}

        for field_name, value in item.items():
            if field_name in rules_map:
                rule = rules_map[field_name]
                display_name = rule.display_name
                validations = rule.validation

                # Convert string like "[1,2]" → list
                if isinstance(validations, str):
                    import ast
                    try:
                        validations = ast.literal_eval(validations)
                    except Exception:
                        validations = []

                errs = allvalidate(value,field_name, display_name, validations)

                if errs:
                    errors.extend(errs)
                else:
                    cleaned_row[field_name] = value
            else:
                # no validation rule → just copy
                cleaned_row[field_name] = value

        if errors:
            all_errors.append({
                "row": idx,
                "errors": "; ".join(errors)
            })
        else:
            cleaned_data.append(cleaned_row)
            print("cleaned_data", cleaned_data)
            print("validate_data", validate_data)

    return all_errors, cleaned_data, validate_data

def field_validate_not_iterate(payload, validate_error_code):
    try:
        validate_classinfo = FieldsControlClassInfo.objects.get(code=validate_error_code)
        validate_data = FieldsControlFields.objects.filter(class_info=validate_classinfo.id)
    except FieldsControlClassInfo.DoesNotExist:
        validate_data = []

    print("validate_data", validate_data)

    errors = []
    cleaned_row = {}

    # Map validation rules by field_name
    rules_map = {rule.field_name: rule for rule in validate_data}

    for field_name, value in payload.items():
        if field_name in rules_map:
            rule = rules_map[field_name]
            display_name = rule.display_name
            validations = rule.fields_control

            # Convert validation string like "[1,2]" into list
            if isinstance(validations, str):
                import ast
                try:
                    validations = ast.literal_eval(validations)
                except Exception:
                    validations = []

            errs = allvalidate(value, field_name, display_name, validations)

            if errs:
                errors.extend(errs)
            else:
                cleaned_row[field_name] = value
        else:
            # No validation rule → just copy
            cleaned_row[field_name] = value

    # Format output like your specification
    if errors:
        formatted_errors = [
            {
                "errors": "; ".join(errors)
            }
        ]
    else:
        formatted_errors = []

    return formatted_errors, cleaned_row, validate_data


class FieldsControlCodeView(APIView):
    authentication_classes = [TokenAuthentication]  # Requires Token authentication
    permission_classes = [IsAuthenticated]  # Only logged-in users can log out

    def get(self, request):
        validate_codes = FieldsControlCode.objects.all()
        serializer = ValidationsCodeSlr(validate_codes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class FieldsControlClassInfoCreate(APIView):
    authentication_classes = [TokenAuthentication]  # Requires Token authentication
    permission_classes = [IsAuthenticated]  # Only logged-in users can log out

    def post(self, request):
        pageinfo_raw = request.data.get("pageinfo")
        fieldvalidation_raw = request.data.get("fieldvalidation")

        # ---- Parse pageinfo ----
        if not pageinfo_raw:
            return Response({"error": "pageinfo is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            pageinfo_data = json.loads(pageinfo_raw)
        except Exception:
            return Response({"error": "Invalid JSON format in pageinfo"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(pageinfo_data, dict):
            return Response({"error": "pageinfo must be a JSON object"}, status=status.HTTP_400_BAD_REQUEST)

        # ---- Parse fieldvalidation ----
        fieldvalidation_data = []
        if fieldvalidation_raw:
            try:
                fieldvalidation_data = json.loads(fieldvalidation_raw)
            except Exception:
                return Response({"error": "Invalid JSON format in fieldvalidation"}, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(fieldvalidation_data, list):
                return Response({"error": "fieldvalidation must be a list of objects"}, status=status.HTTP_400_BAD_REQUEST)

        # ---- Save in DB ----
        try:
            with transaction.atomic():
                # Create pageinfo
                pageinfo_obj = FieldsControlClassInfo.objects.create(
                    name=pageinfo_data.get("name"),
                    code=pageinfo_data.get("code"),
                    url_name=pageinfo_data.get("url_name"),
                    app_name=pageinfo_data.get("app_name"),
                    model_name=pageinfo_data.get("model_name"),
                    view_class_name=pageinfo_data.get("view_class_name"),
                    lock=pageinfo_data.get("lock"),
                    flag=pageinfo_data.get("flag"),
                    createvia=pageinfo_data.get("createvia"),
                )

                # Create fieldvalidation(s)
                for fv in fieldvalidation_data:
                    FieldsControlFields.objects.create(
                        page_info=pageinfo_obj,
                        field_name=fv.get("field_name"),
                        display_name=fv.get("display_name"),
                        validation=fv.get("validation"),
                        verify_order=fv.get("verify_order"),
                        lock=fv.get("lock"),
                        flag=fv.get("flag"),
                        createvia=fv.get("createvia"),
                    )

                return Response(
                    {"message": "PageInfo and FieldValidation saved successfully"},
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FieldsControlClassInfoDelete(APIView):
    authentication_classes = [TokenAuthentication]  # Requires Token authentication
    permission_classes = [IsAuthenticated]  # Only logged-in users can log out

    def delete(self, request, id):
        try:
            pageinfo = FieldsControlClassInfo.objects.get(pk=id)
            validate = FieldsControlFields.objects.filter(page_info=pageinfo)
            validate.delete()
            pageinfo.delete()
            return Response({"message": "PageInfo deleted successfully"}, status=status.HTTP_200_OK)
        except FieldsControlClassInfo.DoesNotExist:
            return Response({"error": "PageInfo not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class FieldsControlFieldsDelete(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        ids = request.data.get("ids", [])

        if not isinstance(ids, list) or not ids:
            return Response(
                {"error": "Please provide a list of IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                not_found = []
                for pk in ids:
                    try:
                        fieldvalidation = FieldsControlFields.objects.get(pk=pk)
                        fieldvalidation.delete()
                    except FieldsControlFields.DoesNotExist:
                        not_found.append(pk)

                if not_found:
                    # rollback transaction
                    raise ValueError(f"IDs not found: {not_found}")

            return Response(
                {"message": f"FieldValidation(s) with IDs {ids} deleted successfully"},
                status=status.HTTP_200_OK
            )

        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
# class ValidateFieldValidationPageInfoView(APIView):
#     authentication_classes = [TokenAuthentication]  # Requires Token authentication
#     permission_classes = [IsAuthenticated]  # Only logged-in users can log out

#     def get(self, request):
#         validate_codes = ValidateFieldValidation.objects.all()
#         serializer = ValidateFieldValidationPageInfoSlr(validate_codes, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)