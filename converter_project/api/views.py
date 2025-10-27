from django.http import JsonResponse
import os
from django.conf import settings
from . import converter
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

@csrf_exempt # Disable CSRF for this stateless API endpoint
def convert_file_view(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST method is allowed."}, status=405)

    if 'file' not in request.FILES:
        return JsonResponse({"status": "error", "message": "No file provided."}, status=400)

    try:
        # 1. Get and Save Uploaded File
        uploaded_file = request.FILES['file']

        # Save the file using Django's storage system
        saved_filename = default_storage.save(
            os.path.join('uploads', uploaded_file.name),
            uploaded_file
        )
        saved_filepath = os.path.join(settings.MEDIA_ROOT, saved_filename)

        # 2. Step 1 (Standardize)
        pdf_path = converter.standardize_to_pdf(saved_filepath, uploaded_file.name)

        # 3. Step 2 (Convert)
        image_paths = converter.convert_pdf_to_images(pdf_path, uploaded_file.name)

        # 4. Return JSON
        return JsonResponse({"status": "success", "image_paths": image_paths})

    except Exception as e:
        # 5. Add Error Handling
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
