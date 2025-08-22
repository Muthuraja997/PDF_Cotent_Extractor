"""
USB Power Delivery (USB PD) Specification PDF Parser

This script parses USB PD specification PDF files and extracts:
1. Table of Contents (ToC) hierarchy
2. All sections and subsections
3. Generates structured JSONL output files
4. Creates validation reports in Excel format
"""

import re
import json
import pandas as pd
import pdfplumber
import fitz  # PyMuPDF
import jsonlines
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import asdict
import logging
from tqdm import tqdm

# Import from pdf_parser module
from pdf_parser.base import Section
from pdf_parser.schema_validator import SchemaValidator
from pdf_parser.hierarchy_validator import HierarchyValidator
from pdf_parser.coverage_analyzer import CoverageAnalyzer
from pdf_parser.report_generator import ReportGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFExtractor:
    """Base class for PDF extraction functionality"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
    def extract_text_from_page(self, page_num: int) -> str:
        """Extract text from a specific page using pdfplumber"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if 0 <= page_num < len(pdf.pages):
                    return pdf.pages[page_num].extract_text() or ""
                else:
                    logger.warning(f"Page {page_num} out of range")
                    return ""
        except Exception as e:
            logger.error(f"Error extracting text from page {page_num}: {e}")
            return ""


class SectionExtractor(PDFExtractor):
    """Extracts sections from PDF documents"""
    
    def __init__(self, pdf_path: str, doc_title: str = "USB Power Delivery Specification"):
        super().__init__(pdf_path)
        self.doc_title = doc_title
        
        # Regex patterns for section identification
        self.section_patterns = [
            # Pattern: "2.1.2 Section Title ... 53"
            r'^(\d+(?:\.\d+)*)\s+([^.]+?)\s*\.{2,}\s*(\d+)$',
            # Pattern: "2.1.2 Section Title 53"
            r'^(\d+(?:\.\d+)*)\s+([^0-9]+?)\s+(\d+)$',
            # Pattern with tabs: "2.1.2\tSection Title\t53"
            r'^(\d+(?:\.\d+)*)\s*\t+([^\t]+?)\t+(\d+)$'
        ]
        
    def _parse_section_header(self, line: str, page_num: int) -> Optional[Section]:
        """Parse a single line to extract section information"""
        for pattern in self.section_patterns:
            match = re.match(pattern, line.strip())
            if match:
                section_id = match.group(1)
                title = match.group(2).strip()
                level = section_id.count('.') + 1
                
                # Determine parent ID
                parent_id = None
                if '.' in section_id:
                    parent_id = section_id.rsplit('.', 1)[0]
                
                full_path = f"{section_id} {title}"
                tags = self._generate_tags(title)
                
                return Section(
                    section_id=section_id,
                    title=title,
                    page=page_num,
                    level=level,
                    parent_id=parent_id,
                    full_path=full_path,
                    doc_title=self.doc_title,
                    tags=tags
                )
        return None
    
    def _generate_tags(self, title: str) -> List[str]:
        """Generate semantic tags based on section title"""
        title_lower = title.lower()
        tags = []
        
        # Define tag mappings
        tag_mappings = {
            'power': ['power'],
            'contract': ['contracts'],
            'negotiation': ['negotiation'],
            'communication': ['communication'],
            'cable': ['cable'],
            'device': ['devices'],
            'protocol': ['protocol'],
            'state': ['state-machine'],
            'message': ['messaging'],
            'data': ['data'],
            'control': ['control'],
            'source': ['source'],
            'sink': ['sink'],
            'vbus': ['vbus'],
            'cc': ['cc-line'],
            'sop': ['sop'],
            'collision': [
                'collision',
                'avoidance'
            ],
            'revision': ['revision'],
            'compatibility': ['compatibility'],
            'introduction': ['intro'],
            'overview': ['overview']
        }
        
        for keyword, tag_list in tag_mappings.items():
            if keyword in title_lower:
                tags.extend(tag_list)
        
        return list(set(tags))  # Remove duplicates

    def extract_toc_sections(self) -> List[Section]:
        """Extract Table of Contents sections from PDF"""
        logger.info("Extracting Table of Contents...")
        toc_sections = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Look for ToC in first 20 pages
                for page_num in range(min(20, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    if not text:
                        continue
                        
                    lines = text.split('\n')
                    
                    # Check if this page contains ToC
                    keywords = ['contents', 'table of contents']
                    is_toc_page = any(
                        keyword in line.lower() 
                        for keyword in keywords
                        for line in lines[:5]
                    )
                    
                    if not is_toc_page:
                        # Also check for numbered sections
                        section_pattern = r'^\d+(?:\.\d+)*\s+'
                        numbered_lines = [
                            line for line in lines 
                            if re.match(section_pattern, line.strip())
                        ]
                        if len(numbered_lines) < 3:
                            continue
                    
                    # Extract sections from this page
                    for line in lines:
                        section = self._parse_section_header(
                            line, 
                            page_num + 1
                        )
                        if section:
                            toc_sections.append(section)
        except Exception as e:
            logger.error(f"Error extracting ToC: {e}")
            
        logger.info(f"Extracted {len(toc_sections)} sections from ToC")
        return toc_sections
        
    def extract_all_sections(self) -> List[Section]:
        """Extract all sections from entire PDF document"""
        logger.info("Extracting all sections from PDF...")
        all_sections = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                pages_iter = tqdm(
                    pdf.pages,
                    desc="Processing pages"
                )
                for page_num, page in enumerate(pages_iter):
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    lines = text.split('\n')
                    
                    for line in lines:
                        section = self._parse_section_header(
                            line, 
                            page_num + 1
                        )
                        if section:
                            all_sections.append(section)
                            
        except Exception as e:
            logger.error(f"Error extracting all sections: {e}")
            
        logger.info(f"Extracted {len(all_sections)} sections from PDF")
        return all_sections
    
class USBPDParser:
    """Main parser class for USB PD specification documents"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.doc_title = "USB Power Delivery Specification"
        
    def extract_document_title(self) -> str:
        """Extract document title from the first few pages"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Check first 3 pages for title
                for page_num in range(min(3, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    text = page.extract_text()
                    
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            line_lower = line.lower()
                            has_usb = 'usb' in line_lower
                            has_pd = ('power delivery' in line_lower or 
                                     'pd' in line_lower)
                            has_spec = ('specification' in line_lower or 
                                       'spec' in line_lower)
                            
                            if has_usb and has_pd and has_spec:
                                return line
                                    
        except Exception as e:
            logger.warning(f"Could not extract document title: {e}")
            
        return "USB Power Delivery Specification"
    
    def save_to_jsonl(self, sections: List[Section], output_file: str) -> None:
        """Save sections to JSONL file"""
        with jsonlines.open(output_file, 'w') as writer:
            for section in sections:
                writer.write(asdict(section))
        logger.info(f"Saved {len(sections)} sections to {output_file}")
    
    def save_metadata(
        self, 
        toc_sections: List[Section], 
        all_sections: List[Section]
    ) -> None:
        """Save metadata about the parsing process"""
        import datetime
        
        metadata = {
            "doc_title": self.doc_title,
            "total_toc_sections": len(toc_sections),
            "total_sections": len(all_sections),
            "processing_date": datetime.datetime.now().isoformat(),
            "source_file": self.pdf_path.name
        }
        
        with open('usb_pd_metadata.jsonl', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        logger.info("Saved metadata to usb_pd_metadata.jsonl")
    
    def process_pdf(self) -> Tuple[List[Section], List[Section]]:
        """Process PDF and extract all content"""
        logger.info(f"Processing PDF: {self.pdf_path}")
        
        # Extract document title
        self.doc_title = self.extract_document_title()
        logger.info(f"Document title: {self.doc_title}")
        
        # Create section extractor
        extractor = SectionExtractor(str(self.pdf_path), self.doc_title)
        
        # Extract ToC and all sections
        toc_sections = extractor.extract_toc_sections()
        all_sections = extractor.extract_all_sections()
        
        # Save outputs
        self.save_to_jsonl(toc_sections, 'usb_pd_toc.jsonl')
        self.save_to_jsonl(all_sections, 'usb_pd_spec.jsonl')
        self.save_metadata(toc_sections, all_sections)
        
        # Generate validation report
        report_generator = ReportGenerator()
        report_generator.generate_validation_report(toc_sections, all_sections)
        
        return toc_sections, all_sections

def main():
    """Main entry point for the parser"""
    import argparse
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='USB PD Specification PDF Parser'
    )
    parser.add_argument(
        'pdf_file',
        help='Path to the USB PD specification PDF file'
    )
    
    args = parser.parse_args()
    
    try:
        # Process the PDF
        usb_parser = USBPDParser(args.pdf_file)
        toc_sections, all_sections = usb_parser.process_pdf()
        
        logger.info("PDF processing completed successfully")
        print("\nProcessing completed successfully!")
        print("Generated files:")
        print("- usb_pd_toc.jsonl (Table of Contents)")
        print("- usb_pd_spec.jsonl (All sections)")
        print("- usb_pd_metadata.jsonl (Metadata)")
        print("- usb_pd_validation_report.xlsx (Validation report)")
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
