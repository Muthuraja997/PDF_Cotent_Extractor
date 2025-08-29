# USB PD Parser Frontend

A modern web interface for the USB PD Specification Parser, allowing users to upload, parse, and analyze USB Power Delivery specification PDFs with a user-friendly interface.

## Features

- **User-friendly interface** for uploading and parsing PDF files
- **Interactive visualization** of parsing results
- **JSON viewer** for examining extracted data
- **Downloadable outputs** in JSONL format
- **Progress tracking** during PDF processing
- **Validation reports** showing parsing coverage and statistics

## Project Structure

```
frontend/
├── index.html            # Main HTML file
├── css/
│   └── styles.css        # CSS styles
└── js/
    └── main.js           # JavaScript functionality
server.py                 # Python backend server
```

## Setup and Usage

### Prerequisites

- Python 3.7 or higher
- Flask and required dependencies

### Installation

1. Install the required Python dependencies:

```bash
pip install flask flask-cors
```

2. Install the USB PD Parser dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

1. Start the backend server:

```bash
python server.py --port 5000
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

3. Use the web interface to upload and parse USB PD specification PDFs.

## Using the Interface

1. **Upload PDF**: Drag and drop a PDF file or click to select one
2. **Configure Options**: Choose parsing options (ToC extraction, full section parsing, etc.)
3. **Parse PDF**: Click the "Parse PDF" button to start processing
4. **View Results**: Examine the extracted data and validation reports
5. **Download Files**: Download the parsed data in JSONL format

## Development

### Frontend Technologies

- HTML5
- CSS3
- JavaScript (ES6+)

### Backend Technologies

- Flask (Python web framework)
- USB PD Parser (existing Python codebase)

## License

This project is licensed under the same terms as the USB PD Parser.

## Acknowledgements

This frontend is designed to work with the USB PD Specification Parser, a comprehensive Python-based parsing system that extracts and structures content from USB PD specification PDFs.
