import os
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
LOG_FOLDER = os.path.join(BASE_DIR, 'logs')

# Output directories
OUTPUT_BASE_FOLDER = os.path.join(BASE_DIR, 'output')
DIGITAL_NATIVE_FOLDER = os.path.join(OUTPUT_BASE_FOLDER, 'digital_native')
SCANNED_OCR_FOLDER = os.path.join(OUTPUT_BASE_FOLDER, 'scanned_ocr')
SCANNED_IMAGE_ONLY_FOLDER = os.path.join(OUTPUT_BASE_FOLDER, 'scanned_image_only')

# File constraints
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Analysis settings
TEXT_COVERAGE_THRESHOLD = float(os.getenv('TEXT_COVERAGE_THRESHOLD', 80))
MIN_TEXT_LENGTH = 10  # Minimum characters to consider as text

# Image settings
IMAGE_DPI = int(os.getenv('IMAGE_DPI', 150))
IMAGE_FORMAT = 'png'


# Processing settings
REAL_TIME_MODE = True
AUTO_CLEANUP_UPLOADS = True
