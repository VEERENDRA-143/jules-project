import os
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERSION_FOLDER = os.path.join(BASE_DIR, 'conversions')
LOG_FOLDER = os.path.join(BASE_DIR, 'logs')

# File constraints
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Analysis settings
TEXT_COVERAGE_THRESHOLD = float(os.getenv('TEXT_COVERAGE_THRESHOLD', 80))
MIN_TEXT_LENGTH = 10  # Minimum characters to consider as text

# Image settings
IMAGE_DPI = int(os.getenv('IMAGE_DPI', 150))
IMAGE_FORMAT = 'png'

# Gemini API settings
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-2.5-flash'
GEMINI_TIMEOUT = 30  # seconds
GEMINI_MAX_RETRIES = 3

# Processing settings
REAL_TIME_MODE = True
AUTO_CLEANUP_UPLOADS = True
