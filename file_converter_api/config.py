import os
import platform

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERSION_FOLDER = os.path.join(BASE_DIR, 'conversions')
LOG_FOLDER = os.path.join(BASE_DIR, 'logs')

# File constraints
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Conversion settings
IMAGE_DPI = 150  # Balance between quality and file size
IMAGE_FORMAT = 'png'

# LibreOffice settings for Windows
LIBREOFFICE_TIMEOUT = 120  # seconds
LIBREOFFICE_PATHS = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    r"soffice.exe"  # If in PATH
]

# Cleanup settings
AUTO_CLEANUP_UPLOADS = True  # Delete uploaded files after conversion
