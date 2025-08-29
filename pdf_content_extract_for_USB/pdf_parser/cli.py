"""
Command-line interface for USB PD Parser utilities
"""

import argparse
import logging
import sys
from pathlib import Path

from pdf_parser.schema_validator import SchemaValidator
from pdf_parser.hierarchy_validator import HierarchyValidator
from pdf_parser.coverage_analyzer import CoverageAnalyzer
from pdf_parser.report_generator import ReportGenerator
from pdf_parser.test_data_generator import TestDataGenerator
from pdf_content_extract.usb_pd_parser import USBPDParser
from pdf_content_extract.content_enhancer import ContentEnhancer

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='USB PD Parser Utilities')
    
    parser.add_argument(
        '--parse',
        metavar='PDF_FILE',
        help='Parse a USB PD specification PDF file'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation tests'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Analyze parsing coverage'
    )
    parser.add_argument(
        '--enhance',
        metavar='PDF_FILE',
        help='Enhance content extraction to improve coverage'
    )
    parser.add_argument(
        '--test-data',
        action='store_true',
        help='Create sample test data'
    )
    parser.add_argument(
        '--toc-file',
        default='usb_pd_toc.jsonl',
        help='ToC JSONL file'
    )
    parser.add_argument(
        '--spec-file',
        default='usb_pd_spec.jsonl',
        help='Spec JSONL file'
    )
    parser.add_argument(
        '--output',
        default='validation_report.xlsx',
        help='Output report file name'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the command-line interface"""
    setup_logging()
    args = parse_arguments()
    
    # Parse PDF
    if args.parse:
        pdf_path = args.parse
        if not Path(pdf_path).exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return 1
            
        try:
            logger.info(f"Parsing PDF: {pdf_path}")
            parser = USBPDParser(pdf_path)
            parser.process_pdf()
            logger.info("PDF parsing completed successfully")
            print("\nProcessing completed successfully!")
            print("Generated files:")
            print("- usb_pd_toc.jsonl (Table of Contents)")
            print("- usb_pd_spec.jsonl (All sections)")
            print("- usb_pd_metadata.jsonl (Metadata)")
            print("- usb_pd_validation_report.xlsx (Validation report)")
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 1
    
    # Enhance content extraction
    if args.enhance:
        pdf_path = args.enhance
        if not Path(pdf_path).exists():
            logger.error(f"PDF file not found: {pdf_path}")
            return 1
            
        try:
            logger.info(f"Enhancing content extraction from: {pdf_path}")
            enhancer = ContentEnhancer(
                pdf_path,
                args.toc_file,
                args.spec_file
            )
            initial_coverage = enhancer.analyze_coverage()
            new_sections = enhancer.extract_missing_content()
            final_coverage = enhancer.analyze_coverage()
            
            if new_sections:
                improvement = final_coverage - initial_coverage
                print(f"\nContent coverage improved by {improvement:.1f}%")
                print(f"Added {new_sections} new sections")
            else:
                print("\nNo new sections added")
                
        except Exception as e:
            logger.error(f"Error enhancing content: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 1
    
    # Generate test data
    if args.test_data:
        generator = TestDataGenerator()
        generator.generate()
        logger.info("Test data generated successfully")
    
    # Run validation
    if args.validate:
        if Path(args.toc_file).exists() and Path(args.spec_file).exists():
            report_gen = ReportGenerator()
            report_gen.generate_report(
                args.toc_file,
                args.spec_file,
                args.output
            )
            logger.info(f"Validation report saved to {args.output}")
        else:
            logger.error(
                "JSONL files not found. Run parser first or use --test-data "
                "to create sample data."
            )
    
    # Analyze coverage
    if args.coverage:
        if Path(args.toc_file).exists() and Path(args.spec_file).exists():
            analyzer = CoverageAnalyzer()
            analyzer.analyze(args.toc_file, args.spec_file)
            logger.info("Coverage analysis completed")
        else:
            logger.error("JSONL files not found. Run parser first.")
    
    # Show help if no action specified
    if not any([args.parse, args.validate, args.coverage, args.test_data, args.enhance]):
        logger.info("USB PD Parser Utilities")
        logger.info("Usage:")
        logger.info("  --parse PDF_FILE: Parse a USB PD specification PDF")
        logger.info("  --enhance PDF_FILE: Enhance content extraction to improve coverage")
        logger.info("  --validate: Run validation tests")
        logger.info("  --coverage: Analyze parsing coverage")
        logger.info("  --test-data: Create sample test data")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
