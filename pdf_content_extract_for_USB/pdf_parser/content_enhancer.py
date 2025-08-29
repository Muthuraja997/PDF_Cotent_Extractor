"""
Content enhancement module for USB PD Parser
"""

import logging
import json
import jsonlines
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

logger = logging.getLogger(__name__)


class ContentEnhancer:
    """Enhances content extraction to improve coverage"""
    
    def __init__(self, pdf_path: str, toc_file: str, spec_file: str):
        """Initialize content enhancer
        
        Args:
            pdf_path: Path to PDF file
            toc_file: Path to ToC JSONL file
            spec_file: Path to spec JSONL file
        """
        self.pdf_path = pdf_path
        self.toc_file = toc_file
        self.spec_file = spec_file
        self.logger = logging.getLogger(__name__)
        
        # These will be imported only when needed
        self.pdfplumber = None
        self.fitz = None
    
    def _load_pdfplumber(self):
        """Lazy-load pdfplumber to avoid unnecessary dependencies"""
        if self.pdfplumber is None:
            try:
                import pdfplumber
                self.pdfplumber = pdfplumber
            except ImportError:
                self.logger.error("pdfplumber is required for content enhancement")
                raise ImportError("pdfplumber is required for content enhancement")
    
    def _load_fitz(self):
        """Lazy-load PyMuPDF (fitz) to avoid unnecessary dependencies"""
        if self.fitz is None:
            try:
                import fitz
                self.fitz = fitz
            except ImportError:
                self.logger.error("PyMuPDF (fitz) is required for content enhancement")
                raise ImportError("PyMuPDF (fitz) is required for content enhancement")
    
    def _load_data(self) -> tuple:
        """Load ToC and Spec data from JSONL files
        
        Returns:
            Tuple of (toc_sections, spec_sections)
        """
        # Load ToC data
        toc_sections = []
        with jsonlines.open(self.toc_file, 'r') as reader:
            toc_sections = list(reader)
        
        # Load Spec data
        spec_sections = []
        with jsonlines.open(self.spec_file, 'r') as reader:
            spec_sections = list(reader)
        
        return toc_sections, spec_sections
    
    def analyze_coverage(self) -> float:
        """Analyze current coverage percentage
        
        Returns:
            Coverage percentage (0-100)
        """
        toc_sections, spec_sections = self._load_data()
        
        # Extract section IDs and pages from both datasets
        toc_ids = set(s['section_id'] for s in toc_sections)
        spec_ids = set(s['section_id'] for s in spec_sections)
        
        # Calculate coverage
        if len(toc_ids) > 0:
            coverage = len(toc_ids & spec_ids) / len(toc_ids) * 100
        else:
            coverage = 0.0
        
        return coverage
    
    def _get_missing_section_ids(self) -> Set[str]:
        """Get set of section IDs that are in ToC but not in spec
        
        Returns:
            Set of missing section IDs
        """
        toc_sections, spec_sections = self._load_data()
        
        # Extract section IDs from both datasets
        toc_ids = set(s['section_id'] for s in toc_sections)
        spec_ids = set(s['section_id'] for s in spec_sections)
        
        # Find section IDs that are in ToC but not in spec
        return toc_ids - spec_ids
    
    def _get_missing_pages(self) -> List[int]:
        """Get list of pages that exist in ToC but not in spec
        
        Returns:
            List of page numbers
        """
        toc_sections, spec_sections = self._load_data()
        
        # Extract pages from both datasets
        toc_pages = set(s['page'] for s in toc_sections)
        spec_pages = set(s['page'] for s in spec_sections)
        
        # Find max page to determine range
        max_page = max(
            max(toc_pages) if toc_pages else 0,
            max(spec_pages) if spec_pages else 0
        )
        
        # Find missing pages
        all_pages = set(range(1, max_page + 1))
        missing_pages = list(all_pages - spec_pages)
        missing_pages.sort()
        
        return missing_pages
    
    def _extract_text_from_page(self, page_num: int) -> str:
        """Extract text from a specific page using enhanced methods
        
        Args:
            page_num: Page number (1-based)
            
        Returns:
            Extracted text from the page
        """
        # Try using pdfplumber first
        self._load_pdfplumber()
        
        try:
            with self.pdfplumber.open(self.pdf_path) as pdf:
                if page_num <= len(pdf.pages) and page_num > 0:
                    page = pdf.pages[page_num - 1]  # pdfplumber uses 0-based indexing
                    
                    # Extract text with more aggressive settings
                    text = page.extract_text(
                        x_tolerance=3,  # More tolerant x grouping
                        y_tolerance=5,  # More tolerant y grouping
                    )
                    
                    if text and len(text.strip()) > 0:
                        return text
        except Exception as e:
            self.logger.warning(f"pdfplumber extraction failed for page {page_num}: {e}")
        
        # Fall back to PyMuPDF if pdfplumber didn't work well
        try:
            self._load_fitz()
            doc = self.fitz.open(self.pdf_path)
            
            if 0 <= page_num - 1 < len(doc):
                page = doc[page_num - 1]  # PyMuPDF uses 0-based indexing
                text = page.get_text()
                
                return text if text else ""
        except Exception as e:
            self.logger.error(f"All extraction methods failed for page {page_num}: {e}")
        
        return ""
    
    def _get_toc_entry_for_page(self, page: int) -> Optional[Dict[str, Any]]:
        """Find a ToC entry for a specific page
        
        Args:
            page: Page number
            
        Returns:
            Dictionary with section information or None if not found
        """
        toc_sections, _ = self._load_data()
        
        # Find ToC entries for this page
        page_toc_entries = [
            entry for entry in toc_sections 
            if entry.get('page') == page
        ]
        
        if page_toc_entries:
            # Use the first entry with the lowest level (most specific)
            return min(page_toc_entries, key=lambda x: x.get('level', 999))
        
        return None
    
    def extract_missing_content(self) -> int:
        """Extract content from missing pages and add to spec file
        
        Returns:
            Number of new sections added
        """
        missing_pages = self._get_missing_pages()
        missing_section_ids = self._get_missing_section_ids()
        
        if not missing_pages:
            self.logger.info("No missing pages found")
            return 0
        
        self.logger.info(f"Found {len(missing_pages)} missing pages")
        self.logger.info(f"Found {len(missing_section_ids)} missing section IDs")
        
        # Load existing spec data
        _, spec_sections = self._load_data()
        
        # Process missing pages
        new_sections = []
        for page_num in sorted(missing_pages):
            page_text = self._extract_text_from_page(page_num)
            
            if page_text and len(page_text.strip()) > 50:  # Ensure we have meaningful content
                # Check if we have ToC entries for this page
                toc_entry = self._get_toc_entry_for_page(page_num)
                
                if toc_entry:
                    # Create section based on ToC entry
                    section = {
                        'section_id': toc_entry.get('section_id'),
                        'page': page_num,
                        'title': toc_entry.get('title', f"Page {page_num} Content"),
                        'level': toc_entry.get('level', 1),
                        'parent_id': toc_entry.get('parent_id'),
                        'content': page_text,
                        'enhanced': True  # Mark as enhanced
                    }
                else:
                    # Create a generic section for this page
                    section = {
                        'section_id': f"enhanced_{page_num}",
                        'page': page_num,
                        'title': f"Page {page_num} Content",
                        'level': 1,
                        'content': page_text,
                        'enhanced': True  # Mark as enhanced
                    }
                
                new_sections.append(section)
        
        # Append new sections to spec file
        if new_sections:
            self.logger.info(f"Adding {len(new_sections)} new sections")
            with jsonlines.open(self.spec_file, 'a') as writer:
                writer.write_all(new_sections)
        
        return len(new_sections)
