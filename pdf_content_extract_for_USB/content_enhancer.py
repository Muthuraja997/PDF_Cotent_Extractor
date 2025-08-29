"""
PDF Content Enhancer

This script helps improve content coverage by enhancing the extraction
capability for USB PD specification PDFs.
"""

import argparse
import logging
import json
import re
from pathlib import Path
import pdfplumber
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContentEnhancer:
    """Enhances PDF content extraction to improve coverage"""
    
    def __init__(self, pdf_path, toc_file='usb_pd_toc.jsonl', spec_file='usb_pd_spec.jsonl'):
        """Initialize with paths to PDF and JSONL files"""
        self.pdf_path = Path(pdf_path)
        self.toc_file = Path(toc_file)
        self.spec_file = Path(spec_file)
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        if not self.toc_file.exists():
            raise FileNotFoundError(f"ToC file not found: {toc_file}")
        if not self.spec_file.exists():
            raise FileNotFoundError(f"Spec file not found: {spec_file}")
            
        # Load existing data
        self.toc_sections = self._load_jsonl(self.toc_file)
        self.spec_sections = self._load_jsonl(self.spec_file)
        
        # Track coverage stats
        self.covered_pages = set()
        self.missing_pages = set()
        self.total_pages = 0
    
    def _load_jsonl(self, file_path):
        """Load data from JSONL file"""
        data = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
    
    def _save_jsonl(self, data, file_path):
        """Save data to JSONL file"""
        with open(file_path, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        logger.info(f"Saved {len(data)} items to {file_path}")
    
    def analyze_coverage(self):
        """Analyze current coverage"""
        # Get covered pages from existing sections
        for section in self.spec_sections:
            self.covered_pages.add(section['page'])
        
        # Get total pages from PDF
        with pdfplumber.open(self.pdf_path) as pdf:
            self.total_pages = len(pdf.pages)
            
        # Find missing pages
        self.missing_pages = set(range(1, self.total_pages + 1)) - self.covered_pages
        
        # Calculate coverage
        coverage_pct = len(self.covered_pages) / self.total_pages * 100
        
        logger.info(f"Current coverage: {coverage_pct:.1f}%")
        logger.info(f"Pages covered: {len(self.covered_pages)}/{self.total_pages}")
        logger.info(f"Missing pages: {len(self.missing_pages)}")
        
        return coverage_pct
    
    def extract_missing_content(self):
        """Extract content from missing pages"""
        if not self.missing_pages:
            logger.info("No missing pages to process")
            return
            
        logger.info(f"Extracting content from {len(self.missing_pages)} missing pages")
        
        # Get existing section IDs to avoid duplication
        existing_ids = set(s['section_id'] for s in self.spec_sections)
        
        # Extract from missing pages
        new_sections = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num in tqdm(sorted(self.missing_pages)):
                if page_num < 1 or page_num > len(pdf.pages):
                    continue
                    
                page = pdf.pages[page_num - 1]  # Convert to 0-based index
                text = page.extract_text()
                
                if not text:
                    continue
                    
                # Look for potential section headers in the page
                lines = text.split('\n')
                for line in lines:
                    # Try to match section headers with more relaxed patterns
                    section = self._parse_section_from_line(line, page_num)
                    if section and section['section_id'] not in existing_ids:
                        new_sections.append(section)
                        existing_ids.add(section['section_id'])
        
        logger.info(f"Extracted {len(new_sections)} new sections")
        
        # Merge with existing sections
        self.spec_sections.extend(new_sections)
        
        # Sort by section_id
        self.spec_sections.sort(key=lambda s: self._section_sort_key(s['section_id']))
        
        # Save updated data
        if new_sections:
            self._save_jsonl(self.spec_sections, self.spec_file)
            
        return len(new_sections)
    
    def _section_sort_key(self, section_id):
        """Create a sort key for section IDs"""
        parts = section_id.split('.')
        return [int(p) if p.isdigit() else p for p in parts]
    
    def _parse_section_from_line(self, line, page_num):
        """Parse a section from a text line with more relaxed patterns"""
        # Common section patterns
        patterns = [
            # Standard section pattern: "2.1.2 Section Title"
            r'^(\d+(?:\.\d+)*)\s+([A-Z][\w\s\-\–\,\:\;\/\&\(\)\'\"]+)$',
            # All caps headers that might be sections
            r'^([A-Z]{2,}[\s\-]*[A-Z\s\-]+)$',
            # Appendix style: "Appendix A: Title"
            r'^Appendix\s+([A-Z])\s*[\:\-]?\s*(.+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line.strip())
            if match:
                if len(match.groups()) == 2:
                    # Regular section
                    section_id = match.group(1)
                    title = match.group(2).strip()
                    
                    # Validate section_id format
                    if not re.match(r'^\d+(?:\.\d+)*$', section_id):
                        continue
                    
                    # Calculate level
                    level = section_id.count('.') + 1
                    
                    # Determine parent_id
                    parent_id = None
                    if '.' in section_id:
                        parent_id = section_id.rsplit('.', 1)[0]
                    
                    return {
                        'section_id': section_id,
                        'title': title,
                        'page': page_num,
                        'level': level,
                        'parent_id': parent_id,
                        'full_path': f"{section_id} {title}",
                        'doc_title': "USB Power Delivery Specification",
                        'tags': self._generate_tags(title)
                    }
                elif len(match.groups()) == 1:
                    # All-caps header (treat as level 1)
                    title = match.group(1).strip()
                    
                    # Generate a pseudo section ID
                    existing_l1 = [
                        int(s['section_id']) 
                        for s in self.spec_sections 
                        if s['level'] == 1 and s['section_id'].isdigit()
                    ]
                    next_id = max(existing_l1) + 1 if existing_l1 else 1
                    
                    return {
                        'section_id': str(next_id),
                        'title': title,
                        'page': page_num,
                        'level': 1,
                        'parent_id': None,
                        'full_path': f"{next_id} {title}",
                        'doc_title': "USB Power Delivery Specification",
                        'tags': self._generate_tags(title)
                    }
        
        return None
    
    def _generate_tags(self, title):
        """Generate tags from title text"""
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
            'collision': ['collision', 'avoidance'],
            'revision': ['revision'],
            'compatibility': ['compatibility'],
            'introduction': ['intro'],
            'overview': ['overview'],
            'appendix': ['appendix'],
            'requirements': ['requirements'],
            'table': ['table'],
            'figure': ['figure'],
            'diagram': ['diagram'],
        }
        
        for keyword, tag_list in tag_mappings.items():
            if keyword in title_lower:
                tags.extend(tag_list)
        
        return list(set(tags))  # Remove duplicates


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Enhance PDF content extraction to improve coverage'
    )
    parser.add_argument(
        'pdf_file',
        help='Path to the USB PD specification PDF file'
    )
    parser.add_argument(
        '--toc-file',
        default='usb_pd_toc.jsonl',
        help='Path to the ToC JSONL file'
    )
    parser.add_argument(
        '--spec-file',
        default='usb_pd_spec.jsonl',
        help='Path to the spec JSONL file'
    )
    
    args = parser.parse_args()
    
    try:
        enhancer = ContentEnhancer(
            args.pdf_file,
            args.toc_file,
            args.spec_file
        )
        
        # Analyze current coverage
        initial_coverage = enhancer.analyze_coverage()
        
        # Extract missing content
        new_sections = enhancer.extract_missing_content()
        
        # Analyze updated coverage
        final_coverage = enhancer.analyze_coverage()
        
        if new_sections:
            improvement = final_coverage - initial_coverage
            logger.info(f"Coverage improved by {improvement:.1f}%")
            logger.info(f"Added {new_sections} new sections")
        else:
            logger.info("No new sections added")
            
    except Exception as e:
        logger.error(f"Error enhancing content: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
