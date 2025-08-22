# USB Power Delivery (USB PD) Specification Parser

A comprehensive Python-based parsing system that extracts and structures content from USB PD specification PDF documents into machine-readable JSONL format.

## Project Overview

This system parses USB Power Delivery specification PDFs and produces:
- **Structured JSONL output** representing Table of Contents (ToC) hierarchy
- **Complete section extraction** with metadata preservation
- **Validation reports** comparing ToC against parsed content
- **Hierarchical data** with proper parent-child relationships

## Features

- **PDF Text Extraction** using multiple libraries (pdfplumber, PyMuPDF)
- **Table of Contents Parsing** with regex pattern matching
- **Hierarchical Section Detection** (chapters, sections, subsections)
- **JSONL Output Generation** with standardized schema
- **Validation Reporting** in Excel format
- **Semantic Tag Generation** based on content analysis
- **Robust Error Handling** and logging
- **Progress Tracking** with tqdm progress bars
- **Modular Structure** with specialized components

## Project Structure

```
pdf_content_extract/
├── usb_pd_parser.py          # Main parser script
├── utils.py                  # Utility functions
├── README.md                 # Project documentation
├── requirements.txt          # Dependencies
├── usb_pd_toc.jsonl          # Table of Contents output
├── usb_pd_spec.jsonl         # All sections output
├── usb_pd_metadata.jsonl     # Parsing metadata
├── usb_pd_validation_report.xlsx  # Validation report
└── pdf_parser/               # Modular components
    ├── __init__.py           # Package initialization
    ├── base.py               # Base classes and interfaces
    ├── schema_validator.py   # JSON schema validation
    ├── hierarchy_validator.py # Section hierarchy validation
    ├── coverage_analyzer.py  # Content coverage analysis
    ├── report_generator.py   # Report generation utilities
    ├── test_data_generator.py # Test data generation
    └── cli.py                # Command-line interface
```


## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/usb-pd-parser.git
cd usb-pd-parser

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Parse a USB PD specification PDF
python -m pdf_parser.cli --parse path/to/usb_pd_spec.pdf

# Run validation on existing output files
python -m pdf_parser.cli --validate

# Analyze parsing coverage
python -m pdf_parser.cli --coverage

# Generate test data
python -m pdf_parser.cli --test-data
```

### Advanced Usage

```python
from pdf_content_extract.usb_pd_parser import USBPDParser
from pdf_parser.report_generator import ReportGenerator
from pdf_parser.coverage_analyzer import CoverageAnalyzer

# Parse a PDF
parser = USBPDParser("path/to/usb_pd_spec.pdf")
toc_sections, all_sections = parser.process_pdf()

# Generate validation report
report_gen = ReportGenerator()
report_gen.generate_validation_report(toc_sections, all_sections)

# Analyze coverage
analyzer = CoverageAnalyzer()
analyzer.analyze("usb_pd_toc.jsonl", "usb_pd_spec.jsonl")
```


## Output Files

### JSONL Schema

Each line in the JSONL files contains a section object with these fields:

| Field | Type | Description |
|-------|------|-------------|
| `section_id` | string | Hierarchical identifier (e.g., "2.1.2") |
| `title` | string | Section title (without numbering) |
| `page` | integer | Starting page number |
| `level` | integer | Depth level (1=chapter, 2=section, 3=subsection) |
| `parent_id` | string/null | Parent section ID (null for top level) |
| `full_path` | string | Complete section path with ID and title |
| `doc_title` | string | Document name/version |
| `tags` | array | Semantic tags for content categorization |

## Supported Section Patterns

The parser recognizes these ToC formats:

1. **Dotted leaders**: `2.1.2 Section Title ........ 53`
2. **Simple spacing**: `2.1.2 Section Title 53`  
3. **Tab-separated**: `2.1.2\tSection Title\t53`
## Validation Report

The Excel validation report includes:

- **Summary Sheet**: Statistics comparing ToC vs parsed sections
- **ToC Sections**: Complete Table of Contents data
- **All Sections**: All parsed sections from document
- **Mismatches**: Sections missing or extra in parsing
- **Schema Validation**: Data format validation results
- **Hierarchy Validation**: Parent-child relationship checks

## Module Components

### Base Module (base.py)
Provides core data structures and interfaces used throughout the system.

### Schema Validator (schema_validator.py)
Validates the JSONL output files against the expected schema.

### Hierarchy Validator (hierarchy_validator.py)
Verifies proper parent-child relationships in the section hierarchy.

### Coverage Analyzer (coverage_analyzer.py)
Analyzes the completeness of parsed content compared to the ToC.

### Report Generator (report_generator.py)
Creates detailed reports in Excel format for quality assessment.

### CLI Interface (cli.py)
Provides a command-line interface for all parser functionality.

## Dependencies

- **pdfplumber**: PDF text extraction and layout analysis
- **PyMuPDF (fitz)**: Alternative PDF processing
- **pandas**: Data manipulation and Excel export
- **openpyxl**: Excel file creation
- **jsonlines**: JSONL file handling
- **tqdm**: Progress bar display

## Troubleshooting

### Common Issues

1. **"PDF file not found"**: Check file path and permissions
2. **"No sections extracted"**: Verify PDF has extractable text
3. **"Pattern not matching"**: PDF may use different ToC format
4. **"Memory errors"**: Large PDFs may need processing optimization

## Testing

The project includes a comprehensive test suite to ensure functionality and reliability:

```bash
# Run all tests
python -m tests.run_tests

# Run specific test module
python -m unittest tests.test_base
python -m unittest tests.test_schema_validator
python -m unittest tests.test_hierarchy_validator
python -m unittest tests.test_report_generator
python -m unittest tests.test_pdf_extractor
```

Test coverage includes:
- Base data structures validation
- Schema validation testing
- Hierarchy validation testing
- Report generation verification
- PDF extraction testing with mocks

## Support

For questions or issues:
- Review the validation report for parsing accuracy
- Check logs for detailed error information
- Verify PDF text is extractable (not scanned images)
- Ensure all dependencies are installed correctly

## License

[MIT License](LICENSE)




