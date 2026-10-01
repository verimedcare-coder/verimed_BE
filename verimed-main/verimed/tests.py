from django.test import TestCase

# # Create your tests here.


# # Step 4: Handle uploaded files
#         upload_files = list(request.FILES.getlist("patient_upload_files"))
#         upload_files_ids = list(request.data.getlist("patient_files_ids"))
#         upload_files_name = list(request.data.getlist("patient_files_name"))
        
        
#         print("upload_files",upload_files)
#         print("upload_files_ids",upload_files_ids)
#         print(len(upload_files))
#         print(len(upload_files_ids))
        
#        # --- Normalize upload_files_ids ---
#         # Handle case where input is like ['1,2,null']
#         if len(upload_files_ids) == 1 and "," in upload_files_ids[0]:
#             upload_files_ids = upload_files_ids[0].split(",")

#         # Clean up invalid or placeholder values
#         cleaned_upload_files_ids = []
#         for val in upload_files_ids:
#             if val and val.lower() not in ["null", "none", ""]:
#                 try:
#                     cleaned_upload_files_ids.append(int(val))
#                 except ValueError:
#                     cleaned_upload_files_ids.append(None)
#             else:
#                 cleaned_upload_files_ids.append(None)
                
#         # --- Normalize upload_files_name ---
#         # Handle case where input is like ['1,2,null']
#         if len(upload_files_name) == 1 and "," in upload_files_name[0]:
#             upload_files_name = upload_files_name[0].split(",")

#         # Clean up invalid or placeholder values
#         cleaned_upload_files_name = []
#         for val in upload_files_ids:
#             if val and val.lower() not in ["null", "none", ""]:
#                 try:
#                     cleaned_upload_files_name.append(int(val))
#                 except ValueError:
#                     cleaned_upload_files_name.append(None)
#             else:
#                 cleaned_upload_files_name.append(None)

#         if len(upload_files) != len(cleaned_upload_files_ids) != len(cleaned_upload_files_name) :
#             return Response(
#                 {
#                     "error": f"The number of upload_files ({len(upload_files)}) "
#                             f"does not match the number of patient_files_ids ({len(upload_files_ids)})"
#                             f"does not match the number of patient_files_name ({len(upload_files_ids)})"
                            
#                 },
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#  # Handle lab reports (update or create)
#             for index, file_obj in enumerate(upload_files):
#                 report_id = cleaned_upload_files_ids[index]
#                 file_name = cleaned_upload_files_name[index]
                

#                 if report_id:
#                     try:
#                         report = PatientUploadDocuments.objects.get(id=report_id)
#                         report.file = file_obj
#                         report.save()
#                     except PatientUploadDocuments.DoesNotExist:
#                         raise NotFound(detail=f"Invalid patient upload document ID: {report_id}")
#                 else:
#                     PatientUploadDocuments.objects.create(
#                         patient_profile=patient_profileobj,
#                         file=file_obj,
#                         patient=appointmentobj.patient,
#                         referid=appointmentobj.id
#                     )

#             return Response({"message": "Appointment updated successfully"}, status=status.HTTP_200_OK)   give me a correct