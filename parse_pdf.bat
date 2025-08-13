@echo off
REM USB PD Parser Batch Script
REM This script provides easy access to parser functions

setlocal

REM Set the Python executable path
set PYTHON_EXE=E:\USB\.venv\Scripts\python.exe

echo.
echo ========================================
echo    USB PD Specification Parser
echo ========================================
echo.

if "%1"=="" (
    echo Usage: parse_pdf.bat [command] [options]
    echo.
    echo Commands:
    echo   parse [pdf_file]     - Parse a PDF file
    echo   demo                 - Run demonstration
    echo   validate             - Validate existing output
    echo   test                 - Create test data
    echo   coverage             - Analyze coverage
    echo   help                 - Show this help
    echo.
    echo Examples:
    echo   parse_pdf.bat parse my_usb_pd_spec.pdf
    echo   parse_pdf.bat demo
    echo   parse_pdf.bat validate
    echo.
    goto :end
)

if "%1"=="demo" (
    echo Running demonstration...
    %PYTHON_EXE% demo.py
    goto :end
)

if "%1"=="parse" (
    if "%2"=="" (
        echo Error: Please specify a PDF file to parse
        echo Usage: parse_pdf.bat parse [pdf_file]
        goto :end
    )
    echo Parsing PDF file: %2
    %PYTHON_EXE% usb_pd_parser.py "%2"
    goto :end
)

if "%1"=="validate" (
    echo Running validation...
    %PYTHON_EXE% utils.py --validate
    goto :end
)

if "%1"=="test" (
    echo Creating test data...
    %PYTHON_EXE% utils.py --test-data
    goto :end
)

if "%1"=="coverage" (
    echo Analyzing coverage...
    %PYTHON_EXE% utils.py --coverage
    goto :end
)

if "%1"=="help" (
    echo.
    echo USB PD Parser - Detailed Help
    echo ===============================
    echo.
    echo This tool parses USB Power Delivery specification PDFs and converts
    echo them into structured JSONL format with validation reporting.
    echo.
    echo Output Files:
    echo   usb_pd_toc.jsonl                 - Table of Contents
    echo   usb_pd_spec.jsonl                - All sections
    echo   usb_pd_metadata.jsonl            - Document metadata
    echo   usb_pd_validation_report.xlsx    - Validation report
    echo.
    echo Requirements:
    echo   - PDF file must have extractable text (not scanned images)
    echo   - Table of Contents should follow standard numbering (1, 1.1, 1.1.1)
    echo   - Python dependencies must be installed (see requirements.txt)
    echo.
    goto :end
)

echo Unknown command: %1
echo Use 'parse_pdf.bat help' for detailed information

:end
endlocal
