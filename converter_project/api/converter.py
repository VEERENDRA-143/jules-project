import os
import subprocess
import fitz  # PyMuPDF
from django.conf import settings

def standardize_to_pdf(file_path, original_filename):
    """
    Converts a file to PDF if it's not already a PDF.
    """
    filename, extension = os.path.splitext(original_filename)
    extension = extension.lower()

    if extension == '.pdf':
        return file_path

    if extension in ['.doc', '.docx', '.txt']:
        output_dir = settings.UPLOAD_FOLDER
        subprocess.run(
            ['soffice', '--headless', '--convert-to', 'pdf', file_path, '--outdir', output_dir],
            check=True
        )
        return os.path.join(output_dir, f"{filename}.pdf")

    raise ValueError(f"Unsupported file type: {extension}")


def convert_pdf_to_images(pdf_path, original_filename):
    """
    Converts a PDF file to a series of PNG images.
    """
    filename, _ = os.path.splitext(original_filename)
    output_folder_name = os.path.basename(filename)
    output_folder = os.path.join(settings.CONVERSION_FOLDER, output_folder_name)
    os.makedirs(output_folder, exist_ok=True)

    image_urls = []
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        image_filename = f"page_{page_num + 1}.png"
        image_path = os.path.join(output_folder, image_filename)
        pix.save(image_path)

        # Construct the web-accessible URL
        image_url = os.path.join(settings.MEDIA_URL, 'conversions', output_folder_name, image_filename).replace('\\', '/')
        image_urls.append(image_url)

    doc.close()
    return image_urls
