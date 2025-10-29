import google.generativeai as genai
from PIL import Image
import time
import logging

import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Prompt Engineering ---
EXTRACTION_PROMPT = """
You are a text extraction specialist.
Analyze this image and extract ALL visible text.

Instructions:
1. Extract text exactly as it appears.
2. Maintain the original layout and structure.
3. Preserve line breaks and paragraphs.
4. Include all headers, footers, and captions.
5. Do not add any commentary or explanations.
6. If the image contains no text, respond with: "NO_TEXT_FOUND"

Return only the extracted text.
"""

def initialize_gemini():
    """
    Initializes and configures the Gemini API client.
    Returns the generative model instance or None if setup fails.
    """
    try:
        if not config.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found in environment variables.")
            return None
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        return None

# Initialize the model once when the module is loaded
gemini_model = initialize_gemini()

def calculate_confidence(response):
    """
    Calculates a confidence score based on the Gemini API response.
    This is a heuristic and can be adapted.

    Args:
        response: The Gemini API response object.

    Returns:
        float: A confidence score between 0.0 and 1.0.
    """
    # If the response was blocked or had safety issues, confidence is low.
    if not response.parts:
        return 0.1

    # Heuristic: if the extracted text is very short or the "no text" flag,
    # confidence might be high in its conclusion but low for text content.
    text = response.text.strip()
    if text == "NO_TEXT_FOUND" or len(text) < config.MIN_TEXT_LENGTH:
        return 0.95 # Confident that there's no significant text

    # A successful response with content gets a high confidence score.
    return 0.98

def extract_text_from_image(image_path):
    """
    Sends a single image to the Gemini API for text extraction.

    Args:
        image_path (str): The full path to the image file.

    Returns:
        dict: A dictionary containing the extracted text, confidence, and model info.
    """
    if not gemini_model:
        return {"text": "", "confidence": 0.0, "error": "Gemini model not initialized."}

    try:
        img = Image.open(image_path)

        # Generate content with a timeout
        response = gemini_model.generate_content(
            [EXTRACTION_PROMPT, img],
            request_options={"timeout": config.GEMINI_TIMEOUT}
        )

        text = response.text.strip()
        confidence = calculate_confidence(response)

        return {
            "text": text,
            "confidence": confidence,
            "llm_used": config.GEMINI_MODEL
        }
    except Exception as e:
        logger.error(f"Gemini API call failed for {image_path}: {e}")
        return {
            "text": "",
            "confidence": 0.0,
            "error": str(e),
            "llm_used": config.GEMINI_MODEL
        }

def batch_extract_text(images_to_process):
    """
    Processes a list of images, extracting text from each using Gemini.

    Args:
        images_to_process (list of dicts): A list where each dict contains
                                           'page_number' and 'image_path'.

    Returns:
        dict: A dictionary mapping page numbers to their OCR results.
    """
    results = {}
    for item in images_to_process:
        page_number = item["page_number"]
        image_path = item["image_path"]

        logger.info(f"Processing page {page_number} with Gemini...")

        ocr_result = extract_text_from_image(image_path)
        results[page_number] = ocr_result

        # Add a small delay to respect potential rate limits in a high-volume scenario
        time.sleep(0.5)

    return results
