import fitz  # PyMuPDF
import os
import uuid
import time
import re

import config

def clean_filename(filename):
    """Remove special characters and limit length for safe file/folder names."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', filename.split('.')[0])[:50]

def calculate_text_coverage(page):
    """
    Calculate the percentage of the page's area covered by text blocks.

    Args:
        page (fitz.Page): The PyMuPDF page object.

    Returns:
        float: The text coverage percentage, rounded to 2 decimal places.
    """
    page_area = page.rect.width * page.rect.height
    if page_area == 0:
        return 0.0

    text_blocks = page.get_text("blocks")
    text_area = 0
    for block in text_blocks:
        x0, y0, x1, y1 = block[:4]
        text_area += (x1 - x0) * (y1 - y0)

    coverage = (text_area / page_area) * 100
    return round(coverage, 2)

def convert_page_to_image(page, output_folder, page_number):
    """
    Convert a single PDF page to a PNG image.

    Args:
        page (fitz.Page): The PyMuPDF page object.
        output_folder (str): The directory to save the image in.
        page_number (int): The current page number (1-based).

    Returns:
        str: The full path to the saved image.
    """
    zoom = config.IMAGE_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image_filename = f"page_{page_number:03d}.{config.IMAGE_FORMAT}"
    image_path = os.path.join(output_folder, image_filename)

    pix.save(image_path)
    return image_path

def analyze_pdf(pdf_path, original_filename):
    """
    Analyzes an entire PDF, classifying pages as digital or scanned.
    - Digital pages: Returns the extracted text.
    - Scanned pages: Converts the page to a PNG image and returns the path.

    Args:
        pdf_path (str): The full path to the uploaded PDF file.
        original_filename (str): The original name of the uploaded file.

    Returns:
        dict: A simplified analysis of the PDF.
    """
    start_time = time.time()

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to open PDF: {e}"}

    # Create a unique output folder for this PDF's images
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = clean_filename(original_filename)
    folder_name = f"{unique_id}_{safe_filename}"
    image_output_folder = os.path.join(config.CONVERSION_FOLDER, folder_name)
    os.makedirs(image_output_folder, exist_ok=True)

    page_results = []
    digital_count = 0
    scanned_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]

        coverage = calculate_text_coverage(page)
        is_digital = coverage >= config.TEXT_COVERAGE_THRESHOLD

        page_data = {
            "page_number": page_num + 1,
            "type": "digital" if is_digital else "scanned",
            "text_coverage": coverage
        }

        if is_digital:
            digital_count += 1
            page_data["text"] = page.get_text()
        else:
            scanned_count += 1
            image_path = convert_page_to_image(page, image_output_folder, page_num + 1)
            page_data["image_path"] = os.path.join('conversions', folder_name, os.path.basename(image_path))

        page_results.append(page_data)

    doc.close()

    processing_time = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "filename": original_filename,
        "total_pages": len(page_results),
        "digital_pages": digital_count,
        "scanned_pages": scanned_count,
        "processing_time": f"{processing_time}s",
        "pages": page_results
    }
