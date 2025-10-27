from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import converter as converter
import config as config
import logging, os, uuid, subprocess
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

# Create required directories
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.CONVERSION_FOLDER, exist_ok=True)
os.makedirs(config.LOG_FOLDER, exist_ok=True)

# Setup logging
log_file_path = os.path.join(config.LOG_FOLDER, 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
app.logger.setLevel(logging.INFO)

# Startup check for LibreOffice
libreoffice_available = converter.check_libreoffice_available()
if not libreoffice_available:
    app.logger.warning("LibreOffice not found. DOC/DOCX/TXT conversion will fail.")
else:
    app.logger.info("LibreOffice detected and ready")

app.logger.info(f"Flask app started. Upload folder: {config.UPLOAD_FOLDER}")

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check and system status
    """
    libreoffice_status = converter.check_libreoffice_available()
    timestamp = datetime.utcnow().isoformat() + 'Z'

    response = {
        "status": "healthy",
        "libreoffice_available": libreoffice_status,
        "upload_folder": config.UPLOAD_FOLDER,
        "conversion_folder": config.CONVERSION_FOLDER,
        "timestamp": timestamp
    }

    return jsonify(response), 200

@app.route('/convert', methods=['POST'])
def convert_file():
    """
    Main file conversion endpoint
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400

    original_filename = file.filename
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    is_valid, error_msg = converter.validate_file(original_filename, file_size)
    if not is_valid:
        return jsonify({"status": "error", "message": error_msg}), 400

    secured_name = secure_filename(original_filename)
    unique_filename = f"{uuid.uuid4()}_{secured_name}"
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(upload_path)
    app.logger.info(f"File uploaded: {original_filename} -> {upload_path}")

    pdf_path = None
    intermediate_pdf = False

    try:
        pdf_path = converter.convert_to_pdf(upload_path, config.UPLOAD_FOLDER)
        if pdf_path != upload_path:
            intermediate_pdf = True
            app.logger.info(f"Converted to PDF: {pdf_path}")
        else:
            app.logger.info(f"File is already PDF: {pdf_path}")

        result = converter.pdf_to_images(pdf_path, original_filename)
        app.logger.info(f"Created {result['page_count']} images in {result['folder']}")

        if config.AUTO_CLEANUP_UPLOADS:
            converter.cleanup_file(upload_path)
            app.logger.info(f"Cleaned up: {upload_path}")
            if intermediate_pdf:
                converter.cleanup_file(pdf_path)
                app.logger.info(f"Cleaned up: {pdf_path}")

        response = {
            "status": "success",
            "folder": result['folder'],
            "images": result['image_paths'],
            "page_count": result['page_count'],
            "message": "Conversion completed successfully"
        }
        return jsonify(response), 200

    except FileNotFoundError as e:
        converter.cleanup_file(upload_path)
        return jsonify({"status": "error", "message": str(e)}), 500
    except subprocess.TimeoutExpired:
        converter.cleanup_file(upload_path)
        return jsonify({"status": "error", "message": "File conversion timeout. File may be too large."}), 408
    except Exception as e:
        converter.cleanup_file(upload_path)
        if intermediate_pdf and pdf_path:
            converter.cleanup_file(pdf_path)
        app.logger.error(f"Conversion error: {str(e)}")
        return jsonify({"status": "error", "message": f"Conversion failed: {str(e)}"}), 500


@app.route('/conversions/<path:folder_path>', methods=['GET'])
def serve_conversion(folder_path):
    """
    Serve converted image files
    """
    if '..' in folder_path or folder_path.startswith('/'):
        return jsonify({"status": "error", "message": "Invalid path"}), 400

    full_path = os.path.join(config.CONVERSION_FOLDER, folder_path)

    if not os.path.exists(full_path):
        return jsonify({"status": "error", "message": "File not found"}), 404

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(directory, filename)


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
