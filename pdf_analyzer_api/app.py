from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import time
from werkzeug.utils import secure_filename
import logging

import config
import analyzer

# --- App Initialization ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

# --- Pre-run Setup: Ensure all necessary folders exist ---
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.DIGITAL_FOLDER, exist_ok=True)
os.makedirs(config.SCANNED_FOLDER, exist_ok=True)
os.makedirs(config.LOG_FOLDER, exist_ok=True)

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.LOG_FOLDER, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if the uploaded file has a permitted extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }), 200

@app.route('/analyze', methods=['POST'])
def analyze_document():
    """Main endpoint to upload and analyze a PDF file."""
    if 'file' not in request.files:
        logger.warning("Analyze request failed: No file part.")
        return jsonify({"status": "error", "message": "No file part in the request."}), 400

    file = request.files['file']

    if file.filename == '':
        logger.warning("Analyze request failed: No file selected.")
        return jsonify({"status": "error", "message": "No selected file."}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            unique_id = uuid.uuid4().hex[:8]
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")

            file.save(save_path)
            logger.info(f"File '{filename}' saved to '{save_path}' for analysis.")

            # --- Call the core analysis logic ---
            analysis_result = analyzer.analyze_pdf(save_path, filename)

            # --- Clean up the uploaded file ---
            if config.AUTO_CLEANUP_UPLOADS:
                os.remove(save_path)
                logger.info(f"Cleaned up uploaded file: {save_path}")

            return jsonify(analysis_result)

        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis: {e}", exc_info=True)
            return jsonify({"status": "error", "message": f"An internal error occurred: {e}"}), 500
    else:
        logger.warning(f"Analyze request failed: File type not allowed ('{file.filename}').")
        return jsonify({"status": "error", "message": "File type not allowed."}), 400

@app.route('/scanned/<path:filepath>')
def serve_scanned_file(filepath):
    """Serve generated PNG images for scanned pages."""
    return send_from_directory(config.SCANNED_FOLDER, filepath)

@app.route('/digital/<path:filepath>')
def serve_digital_file(filepath):
    """Serve extracted text files for digital pages."""
    return send_from_directory(config.DIGITAL_FOLDER, filepath)

if __name__ == '__main__':
    app.run(debug=True)
