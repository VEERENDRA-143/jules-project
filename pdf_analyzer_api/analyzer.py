import fitz  # PyMuPDF
import os
import uuid
import time
import re

import config

def clean_filename(filename):
    """Remove special characters and limit length for safe file/folder names."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', filename.split('.')[0])[:50]

def is_page_scanned(page, threshold=0.7):
    """
    Determines if a page is scanned by checking for large images.

    Args:
        page (fitz.Page): The PyMuPDF page object.
        threshold (float): The area ratio an image must exceed to be considered a full-page scan.

    Returns:
        bool: True if the page is likely scanned, False otherwise.
    """
    page_area = page.rect.width * page.rect.height
    if page_area == 0:
        return False

    image_list = page.get_images(full=True)
    if not image_list:
        return False

    for img_info in image_list:
        # Get the image's bounding box in the page
        img_bbox = page.get_image_bbox(img_info)
        img_area = (img_bbox.x1 - img_bbox.x0) * (img_bbox.y1 - img_bbox.y0)

        if img_area / page_area > threshold:
            return True

    return False

def save_digital_text(page, output_folder, page_number):
    """
    Extracts text from a digital page and saves it to a .txt file.

    Args:
        page (fitz.Page): The PyMuPDF page object.
        output_folder (str): The directory to save the text file in.
        page_number (int): The current page number.

    Returns:
        str: The web-accessible path to the saved text file.
    """
    text = page.get_text()
    txt_filename = f"page_{page_number:03d}.txt"
    txt_path = os.path.join(output_folder, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return os.path.join('digital', os.path.basename(output_folder), txt_filename)


def save_scanned_image(page, output_folder, page_number):
    """
    Converts a scanned page to a PNG image and saves it.

    Args:
        page (fitz.Page): The PyMuPDF page object.
        output_folder (str): The directory to save the image in.
        page_number (int): The current page number.

    Returns:
        str: The web-accessible path to the saved image.
    """
    zoom = config.IMAGE_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image_filename = f"page_{page_number:03d}.{config.IMAGE_FORMAT}"
    image_path = os.path.join(output_folder, image_filename)

    pix.save(image_path)
    return os.path.join('scanned', os.path.basename(output_folder), image_filename)


def analyze_pdf(pdf_path, original_filename):
    """
    Analyzes a PDF to classify pages as digital or scanned, saving the
    appropriate output to structured folders.
    """
    start_time = time.time()

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"status": "error", "message": f"Failed to open PDF: {e}"}

    # Create a unique subfolder for this document's outputs
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = clean_filename(original_filename)
    folder_name = f"{unique_id}_{safe_filename}"

    digital_output_folder = os.path.join(config.DIGITAL_FOLDER, folder_name)
    scanned_output_folder = os.path.join(config.SCANNED_FOLDER, folder_name)

    # Ensure they exist
    os.makedirs(digital_output_folder, exist_ok=True)
    os.makedirs(scanned_output_folder, exist_ok=True)

    page_results = []
    digital_count = 0
    scanned_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]

        page_number = page_num + 1
        scanned = is_page_scanned(page)

        page_data = {
            "page_number": page_number,
            "type": "scanned" if scanned else "digital"
        }

        if scanned:
            scanned_count += 1
            page_data["output_path"] = save_scanned_image(page, scanned_output_folder, page_number)
        else:
            digital_count += 1
            page_data["output_path"] = save_digital_text(page, digital_output_folder, page_number)

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
