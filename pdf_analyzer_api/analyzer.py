import fitz  # PyMuPDF
import os
import uuid
import time
import re

import config

def clean_filename(filename):
    """Remove special characters and limit length for safe file/folder names."""
    return re.sub(r'[^a-zA-Z0-9_-]', '', filename.split('.')[0])[:50]

def classify_page(page):
    """
    Analyzes a single PDF page to determine if it is digital native,
    scanned+OCR, or image-only.

    Args:
        page (fitz.Page): The PyMuPDF page object.

    Returns:
        str: The classification type ('digital_native', 'scanned_ocr', 'scanned_image_only').
    """
    has_text = len(page.get_text().strip()) > 0
    is_scanned = False

    images = page.get_images(full=True)
    if images:
        page_area = page.rect.width * page.rect.height
        if page_area > 0:
            for img_info in images:
                img_bbox = page.get_image_bbox(img_info)
                img_area = img_bbox.width * img_bbox.height
                # If an image takes up > 90% of the page, it's likely a full-page scan
                if img_area / page_area > 0.90:
                    is_scanned = True
                    break

    # --- Final Logic ---
    if has_text and is_scanned:
        return "scanned_ocr"
    elif has_text and not is_scanned:
        return "digital_native"
    else: # This covers "not has_text" cases
        return "scanned_image_only"

def save_text_output(page, output_folder, page_number):
    """Saves extracted text to a .txt file."""
    text = page.get_text("text")
    txt_filename = f"page_{page_number:03d}.txt"
    txt_path = os.path.join(output_folder, txt_filename)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    return txt_path

def save_image_output(page, output_folder, page_number):
    """Saves a rendered page as a PNG image."""
    zoom = config.IMAGE_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, alpha=False)

    image_filename = f"page_{page_number:03d}.{config.IMAGE_FORMAT}"
    image_path = os.path.join(output_folder, image_filename)

    pix.save(image_path)
    return image_path

def analyze_pdf(pdf_path, original_filename):
    """
    Analyzes a PDF, classifies each page, and saves the appropriate
    output to a structured directory.
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

    page_results = []
    summary = {
        "digital_native": 0,
        "scanned_ocr": 0,
        "scanned_image_only": 0
    }

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_number = page_num + 1

        page_type = classify_page(page)
        summary[page_type] += 1

        page_data = {
            "page_number": page_number,
            "type": page_type,
        }

        # Determine output path and save the file
        if page_type == 'digital_native':
            output_folder = os.path.join(config.DIGITAL_NATIVE_FOLDER, folder_name)
            os.makedirs(output_folder, exist_ok=True)
            save_text_output(page, output_folder, page_number)
            page_data["output_path"] = os.path.join('output', 'digital_native', folder_name, f"page_{page_number:03d}.txt")

        elif page_type == 'scanned_ocr':
            output_folder = os.path.join(config.SCANNED_OCR_FOLDER, folder_name)
            os.makedirs(output_folder, exist_ok=True)
            save_text_output(page, output_folder, page_number)
            page_data["output_path"] = os.path.join('output', 'scanned_ocr', folder_name, f"page_{page_number:03d}.txt")

        elif page_type == 'scanned_image_only':
            output_folder = os.path.join(config.SCANNED_IMAGE_ONLY_FOLDER, folder_name)
            os.makedirs(output_folder, exist_ok=True)
            save_image_output(page, output_folder, page_number)
            page_data["output_path"] = os.path.join('output', 'scanned_image_only', folder_name, f"page_{page_number:03d}.png")

        page_results.append(page_data)

    doc.close()

    processing_time = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "filename": original_filename,
        "total_pages": len(page_results),
        "page_counts": summary,
        "processing_time": f"{processing_time}s",
        "pages": page_results
    }
