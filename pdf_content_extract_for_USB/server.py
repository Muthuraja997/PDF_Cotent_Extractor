"""
Backend API server for USB PD Parser Frontend

This script provides a Flask-based API to connect the HTML/CSS/JS frontend
with the existing USB PD Parser functionality.
"""

import os
import json
import tempfile
import datetime
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging

# Import the USB PD Parser components
from usb_pd_parser import USBPDParser
from pdf_parser.coverage_analyzer import CoverageAnalyzer
from pdf_parser.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='frontend')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Temporary directory for uploaded files
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / 'usb_pd_parser'
UPLOAD_FOLDER.mkdir(exist_ok=True)

# Custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 error: {request.path}")
    return jsonify({
        'error': 'Resource not found',
        'path': request.path
    }), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}")
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500

# Serve static frontend files
@app.route('/')
def index():
    """Serve the main HTML page"""
    try:
        # Check for required files in the root directory
        root_dir = Path(__file__).parent
        required_files = [
            'usb_pd_toc.jsonl',
            'usb_pd_spec.jsonl',
            'usb_pd_metadata.jsonl',
            'usb_pd_validation_report.xlsx'
        ]
        
        # Log existence of required files
        for file_name in required_files:
            file_path = root_dir / file_name
            if file_path.exists():
                logger.info(f"Found required file: {file_name}")
            else:
                logger.warning(f"Required file not found: {file_name}")
        
        return send_file('frontend/index.html')
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return jsonify({'error': 'Failed to serve index page'}), 500

@app.route('/<path:path>')
def static_files(path):
    """Serve static files from the frontend directory"""
    try:
        # Try different potential paths for the requested file
        base_dir = Path(__file__).parent
        possible_paths = [
            base_dir / 'frontend' / path,  # Standard path
            Path('frontend') / path,       # Relative path
            base_dir / path                # Direct in base directory
        ]
        
        # Try each path
        for file_path in possible_paths:
            if file_path.exists() and file_path.is_file():
                logger.debug(f"Serving static file: {file_path}")
                return send_file(str(file_path))
        
        # Handle special cases
        if path == 'favicon.ico':
            # Return a 204 No Content for favicon requests if the file doesn't exist
            logger.info("Favicon.ico requested but not found, returning 204")
            return '', 204
        else:
            logger.warning(f"Requested file not found: {path}")
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return jsonify({'error': 'Error serving file'}), 500

@app.route('/api/parse', methods=['POST'])
def parse_pdf():
    """
    API endpoint to parse a PDF file
    
    Expected request:
    - Multipart form with 'file' containing the PDF
    - Form fields for options: extractToc, extractSections, generateReport, enhanceContent
    
    Returns:
    - JSON with parsing results and file references
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        pdf_file = request.files['file']
        if pdf_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Uploaded file must be a PDF'}), 400
        
        # Get options
        extract_toc = request.form.get('extractToc', 'true').lower() == 'true'
        extract_sections = request.form.get('extractSections', 'true').lower() == 'true'
        generate_report = request.form.get('generateReport', 'true').lower() == 'true'
        enhance_content = request.form.get('enhanceContent', 'false').lower() == 'true'
        
        # Create unique ID for this parsing job
        import uuid
        job_id = str(uuid.uuid4())
        job_folder = UPLOAD_FOLDER / job_id
        job_folder.mkdir(exist_ok=True)
        
        logger.info(f"Created job folder: {job_folder}")
        
        # Save uploaded file
        pdf_path = job_folder / pdf_file.filename
        pdf_file.save(pdf_path)
        
        logger.info(f"Saved PDF file to: {pdf_path}")
        
        # Output file paths
        toc_file = job_folder / 'usb_pd_toc.jsonl'
        spec_file = job_folder / 'usb_pd_spec.jsonl'
        metadata_file = job_folder / 'usb_pd_metadata.jsonl'
        report_file = job_folder / 'usb_pd_validation_report.xlsx'
        
        # Process the PDF
        parser = USBPDParser(str(pdf_path))
        toc_sections, all_sections = parser.process_pdf()
        
        # The USBPDParser creates files in the root directory by default
        # We need to copy them to our job folder
        root_dir = Path(__file__).parent
        
        # Copy the generated files to the job folder
        if (root_dir / 'usb_pd_toc.jsonl').exists():
            shutil.copy2(root_dir / 'usb_pd_toc.jsonl', toc_file)
            logger.info(f"Copied TOC file to job folder")
        else:
            logger.warning(f"TOC file not found in root directory")
            
        if (root_dir / 'usb_pd_spec.jsonl').exists():
            shutil.copy2(root_dir / 'usb_pd_spec.jsonl', spec_file)
            logger.info(f"Copied spec file to job folder")
        else:
            logger.warning(f"Spec file not found in root directory")
            
        if (root_dir / 'usb_pd_metadata.jsonl').exists():
            shutil.copy2(root_dir / 'usb_pd_metadata.jsonl', metadata_file)
            logger.info(f"Copied metadata file to job folder")
        else:
            logger.warning(f"Metadata file not found in root directory")
            
        if (root_dir / 'usb_pd_validation_report.xlsx').exists():
            shutil.copy2(root_dir / 'usb_pd_validation_report.xlsx', report_file)
            logger.info(f"Copied report file to job folder")
        else:
            logger.warning(f"Report file not found in root directory")
        
        # Read data with proper error handling
        toc_data = []
        try:
            if toc_file.exists():
                with open(toc_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            toc_data.append(json.loads(line))
                logger.info(f"Loaded {len(toc_data)} TOC sections from job folder file")
            elif (root_dir / 'usb_pd_toc.jsonl').exists():
                with open(root_dir / 'usb_pd_toc.jsonl', 'r') as f:
                    for line in f:
                        if line.strip():
                            toc_data.append(json.loads(line))
                logger.info(f"Loaded {len(toc_data)} TOC sections from root directory file")
            else:
                logger.error("No TOC data found")
        except Exception as e:
            logger.error(f"Error loading TOC data: {e}")
            toc_data = []
        
        sections_data = []
        try:
            if spec_file.exists():
                with open(spec_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            sections_data.append(json.loads(line))
                logger.info(f"Loaded {len(sections_data)} sections from job folder file")
            elif (root_dir / 'usb_pd_spec.jsonl').exists():
                with open(root_dir / 'usb_pd_spec.jsonl', 'r') as f:
                    for line in f:
                        if line.strip():
                            sections_data.append(json.loads(line))
                logger.info(f"Loaded {len(sections_data)} sections from root directory file")
            else:
                logger.error("No section data found")
        except Exception as e:
            logger.error(f"Error loading sections data: {e}")
            sections_data = []
        
        # Load metadata
        metadata = {}
        try:
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    try:
                        metadata = json.load(f)
                        logger.info(f"Loaded metadata from job folder file as JSON")
                    except:
                        # Try reading as JSONL
                        f.seek(0)  # Reset file pointer
                        for line in f:
                            if line.strip():
                                metadata = json.loads(line)
                                logger.info(f"Loaded metadata from job folder file as JSONL")
                                break
            elif (root_dir / 'usb_pd_metadata.jsonl').exists():
                with open(root_dir / 'usb_pd_metadata.jsonl', 'r') as f:
                    try:
                        metadata = json.load(f)
                        logger.info(f"Loaded metadata from root directory file as JSON")
                    except:
                        # Try reading as JSONL
                        f.seek(0)  # Reset file pointer
                        for line in f:
                            if line.strip():
                                metadata = json.loads(line)
                                logger.info(f"Loaded metadata from root directory file as JSONL")
                                break
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            # Create default metadata
            metadata = {
                "doc_title": "USB Power Delivery Specification",
                "total_toc_sections": len(toc_data),
                "total_sections": len(sections_data),
                "processing_date": datetime.datetime.now().isoformat(),
                "source_file": pdf_file.filename
            }
            logger.info(f"Created default metadata due to loading error")
        
        # Calculate coverage metrics
        total_toc = len(toc_data)
        total_spec = len(sections_data)
        
        # Extract section IDs for comparison
        toc_ids = set(s.get('section_id', '') for s in toc_data)
        spec_ids = set(s.get('section_id', '') for s in sections_data)
        
        common = len(toc_ids & spec_ids)
        toc_only = len(toc_ids - spec_ids)
        spec_only = len(spec_ids - toc_ids)
        coverage_percentage = (common / total_toc * 100) if total_toc > 0 else 0
        
        coverage_metrics = {
            'total_toc': total_toc,
            'total_spec': total_spec,
            'common': common,
            'toc_only': toc_only,
            'spec_only': spec_only,
            'coverage_percentage': coverage_percentage
        }
        
        # Return results
        return jsonify({
            'job_id': job_id,
            'metadata': metadata,
            'toc_count': total_toc,
            'sections_count': total_spec,
            'coverage': coverage_metrics,
            'file_paths': {
                'pdf': str(pdf_path),
                'toc': str(toc_file),
                'spec': str(spec_file),
                'metadata': str(metadata_file),
                'report': str(report_file)
            }
        })
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<job_id>/<file_type>', methods=['GET'])
def get_file(job_id, file_type):
    """
    API endpoint to retrieve generated files
    
    Parameters:
    - job_id: The unique ID of the parsing job
    - file_type: Type of file to retrieve (toc, spec, metadata, report)
    
    Returns:
    - The requested file for download
    """
    job_folder = UPLOAD_FOLDER / job_id
    root_dir = Path(__file__).parent
    
    if not job_folder.exists():
        logger.warning(f"Job folder not found: {job_folder}")
        # Check if we should return root files instead
        if file_type in ['toc', 'spec', 'metadata', 'report']:
            root_files = {
                'toc': root_dir / 'usb_pd_toc.jsonl',
                'spec': root_dir / 'usb_pd_spec.jsonl',
                'metadata': root_dir / 'usb_pd_metadata.jsonl',
                'report': root_dir / 'usb_pd_validation_report.xlsx'
            }
            if root_files[file_type].exists():
                logger.info(f"Using root file instead: {root_files[file_type]}")
                file_path = root_files[file_type]
            else:
                logger.error(f"No file found for {file_type} in root directory")
                return jsonify({'error': 'File not found'}), 404
        else:
            return jsonify({'error': 'Job not found'}), 404
    else:
        file_paths = {
            'toc': job_folder / 'usb_pd_toc.jsonl',
            'spec': job_folder / 'usb_pd_spec.jsonl',
            'metadata': job_folder / 'usb_pd_metadata.jsonl',
            'report': job_folder / 'usb_pd_validation_report.xlsx'
        }
        
        if file_type not in file_paths:
            return jsonify({'error': 'Invalid file type'}), 400
        
        file_path = file_paths[file_type]
        
        if not file_path.exists():
            # If the file doesn't exist in the job folder, try to use the one from project root
            root_file_path = root_dir / file_path.name
            
            if root_file_path.exists():
                logger.info(f"Using root file instead: {root_file_path}")
                file_path = root_file_path
            else:
                logger.error(f"File not found: {file_path} or {root_file_path}")
                return jsonify({'error': 'File not found'}), 404
    
    # Set the appropriate content type
    content_types = {
        'toc': 'application/json',
        'spec': 'application/json',
        'metadata': 'application/json',
        'report': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    try:
        return send_file(
            str(file_path),
            mimetype=content_types.get(file_type, 'application/octet-stream'),
            as_attachment=True,
            download_name=file_path.name
        )
    except Exception as e:
        logger.error(f"Error sending file {file_path}: {e}")
        return jsonify({'error': f'Error serving file: {str(e)}'}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    API endpoint to check job status
    
    Parameters:
    - job_id: The unique ID of the parsing job
    
    Returns:
    - Status and information about the job
    """
    job_folder = UPLOAD_FOLDER / job_id
    root_dir = Path(__file__).parent
    
    if not job_folder.exists():
        logger.warning(f"Job folder not found: {job_folder}")
        # Check if we have files in the root directory
        root_files = [
            root_dir / 'usb_pd_toc.jsonl',
            root_dir / 'usb_pd_spec.jsonl',
            root_dir / 'usb_pd_metadata.jsonl',
            root_dir / 'usb_pd_validation_report.xlsx'
        ]
        existing_root_files = [f for f in root_files if f.exists()]
        
        if existing_root_files:
            logger.info(f"Found {len(existing_root_files)} files in root directory")
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'files': [f.name for f in existing_root_files],
                'note': 'Using root directory files'
            })
        else:
            return jsonify({'error': 'Job not found'}), 404
    
    try:
        files = list(job_folder.glob('*'))
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'files': [f.name for f in files]
        })
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import argparse
    import signal
    import sys
    
    # Handle keyboard interrupts gracefully
    def signal_handler(sig, frame):
        logger.info("Server shutdown requested. Exiting...")
        sys.exit(0)
    
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    parser = argparse.ArgumentParser(description='USB PD Parser Frontend Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting USB PD Parser Frontend Server on http://localhost:{args.port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        app.run(host='0.0.0.0', port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested. Exiting...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
