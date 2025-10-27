import os
import subprocess
import uuid
import fitz  # PyMuPDF
import re
import time
from config import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    LIBREOFFICE_PATHS,
    LIBREOFFICE_TIMEOUT,
    CONVERSION_FOLDER,
    IMAGE_DPI,
    IMAGE_FORMAT,
)


def validate_file(filename, file_size):
    """
    Purpose: Validate file type and size before processing
    """
    if not filename:
        return False, "No filename provided."

    _, ext = os.path.splitext(filename)
    if ext.lower().strip('.') not in ALLOWED_EXTENSIONS:
        return False, f"File type {ext} not allowed."

    if file_size > MAX_FILE_SIZE:
        return False, f"File size {file_size} exceeds the maximum of {MAX_FILE_SIZE} bytes."

    return True, ""


def find_libreoffice_path():
    """
    Purpose: Locate LibreOffice installation on Windows
    """
    for path in LIBREOFFICE_PATHS:
        if os.path.exists(path):
            return path
    return None


def check_libreoffice_available():
    """
    Purpose: Verify LibreOffice is installed and accessible
    """
    path = find_libreoffice_path()
    if path is None:
        return False
    try:
        result = subprocess.run([path, '--version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def convert_to_pdf(file_path, output_folder):
    """
    Purpose: Convert DOC/DOCX/TXT to PDF using LibreOffice
    """
    _, ext = os.path.splitext(file_path)

    if ext.lower().strip('.') == 'pdf':
        return file_path

    if ext.lower().strip('.') in ['doc', 'docx', 'txt']:
        libreoffice_path = find_libreoffice_path()
        if not libreoffice_path:
            raise FileNotFoundError("LibreOffice not found.")

        command = [
            libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_folder,
            file_path,
        ]

        try:
            # Windows specific flag
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW

            subprocess.run(
                command,
                timeout=LIBREOFFICE_TIMEOUT,
                check=True,
                capture_output=True,
                creationflags=creationflags,
            )

            base_filename = os.path.splitext(os.path.basename(file_path))[0]
            pdf_path = os.path.join(output_folder, f"{base_filename}.pdf")

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF conversion failed. Expected file not found at: {pdf_path}")

            return pdf_path

        except subprocess.TimeoutExpired:
            raise TimeoutError("Conversion timeout exceeded")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"LibreOffice conversion failed: {e.stderr.decode()}")

    else:
        raise ValueError(f"Unsupported file type for conversion: {ext}")


def pdf_to_images(pdf_path, original_filename):
    """
    Purpose: Convert PDF pages to PNG images using PyMuPDF
    """
    try:
        unique_id = str(uuid.uuid4())
        clean_filename = re.sub(r'[^a-zA-Z0-9_.-]', '', os.path.splitext(original_filename)[0])
        folder_name = f"{unique_id}_{clean_filename}"
        output_folder = os.path.join(CONVERSION_FOLDER, folder_name)
        os.makedirs(output_folder, exist_ok=True)

        doc = fitz.open(pdf_path)

        zoom = IMAGE_DPI / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        image_paths = []
        page_count = len(doc)

        for page_num in range(page_count):
            page = doc[page_num]

            image_filename = f"page_{page_num + 1:03d}.{IMAGE_FORMAT}"
            image_path = os.path.join(output_folder, image_filename)

            pix = page.get_pixmap(matrix=matrix)
            pix.save(image_path)

            relative_path = os.path.join(folder_name, image_filename).replace('\\\\', '/')
            image_paths.append(relative_path)

        doc.close()

        return {
            "folder": folder_name,
            "image_paths": image_paths,
            "page_count": page_count,
        }
    except fitz.FileDataError:
        raise ValueError("Invalid or corrupted PDF file.")
    except Exception as e:
        raise RuntimeError(f"Image conversion failed: {e}")


def cleanup_file(file_path):
    """
    Purpose: Delete temporary files safely
    """
    if not file_path or not os.path.exists(file_path):
        return

    try:
        os.remove(file_path)
    except PermissionError:
        time.sleep(0.5)
        try:
            os.remove(file_path)
        except Exception:
            pass
    except Exception:
        pass
