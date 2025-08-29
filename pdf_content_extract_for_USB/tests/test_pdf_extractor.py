"""
Tests for the PDF extractor classes
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from pdf_parser.base import Section
from pdf_content_extract.usb_pd_parser import PDFExtractor, SectionExtractor


class TestPDFExtractor(unittest.TestCase):
    """Test cases for the PDFExtractor base class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock for pdfplumber to avoid needing an actual PDF
        self.pdfplumber_patcher = patch('pdf_content_extract.usb_pd_parser.pdfplumber')
        self.mock_pdfplumber = self.pdfplumber_patcher.start()
        
        # Set up mock PDF structure
        self.mock_pdf = MagicMock()
        self.mock_page = MagicMock()
        self.mock_page.extract_text.return_value = "Sample PDF text"
        self.mock_pdf.pages = [self.mock_page, self.mock_page, self.mock_page]
        self.mock_pdfplumber.open.return_value.__enter__.return_value = self.mock_pdf
        
        # Create temporary test directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = os.path.join(self.temp_dir.name, "test.pdf")
        
        # Create an empty file
        with open(self.pdf_path, 'w') as f:
            f.write("Mock PDF file")
        
        # Create the extractor
        self.extractor = PDFExtractor(self.pdf_path)

    def tearDown(self):
        """Clean up test fixtures"""
        self.pdfplumber_patcher.stop()
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of PDFExtractor"""
        self.assertEqual(self.extractor.pdf_path, Path(self.pdf_path))
        
    def test_extract_text_from_page(self):
        """Test text extraction from a page"""
        text = self.extractor.extract_text_from_page(1)
        self.assertEqual(text, "Sample PDF text")
        
        # Test page out of range
        self.mock_pdfplumber.open.reset_mock()
        text = self.extractor.extract_text_from_page(10)
        self.assertEqual(text, "")
        
        # Test exception handling
        self.mock_pdfplumber.open.side_effect = Exception("Mock error")
        text = self.extractor.extract_text_from_page(1)
        self.assertEqual(text, "")


class TestSectionExtractor(unittest.TestCase):
    """Test cases for the SectionExtractor class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock for pdfplumber to avoid needing an actual PDF
        self.pdfplumber_patcher = patch('pdf_content_extract.usb_pd_parser.pdfplumber')
        self.mock_pdfplumber = self.pdfplumber_patcher.start()
        
        # Set up mock PDF structure with ToC page
        self.mock_pdf = MagicMock()
        self.mock_toc_page = MagicMock()
        self.mock_toc_page.extract_text.return_value = (
            "Table of Contents\n"
            "1 Introduction ... 10\n"
            "1.1 Overview ... 11\n"
            "2 Power Delivery ... 20\n"
            "2.1 Power Overview ... 21\n"
        )
        
        self.mock_content_page = MagicMock()
        self.mock_content_page.extract_text.return_value = (
            "2 Power Delivery\n"
            "This section describes power delivery."
        )
        
        self.mock_pdf.pages = [
            self.mock_toc_page,  # Page 0
            MagicMock(),         # Page 1
            self.mock_content_page,  # Page 2
        ]
        self.mock_pdfplumber.open.return_value.__enter__.return_value = self.mock_pdf
        
        # Create temporary test directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pdf_path = os.path.join(self.temp_dir.name, "test.pdf")
        
        # Create an empty file
        with open(self.pdf_path, 'w') as f:
            f.write("Mock PDF file")
        
        # Create the extractor
        self.extractor = SectionExtractor(self.pdf_path)

    def tearDown(self):
        """Clean up test fixtures"""
        self.pdfplumber_patcher.stop()
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of SectionExtractor"""
        self.assertEqual(self.extractor.pdf_path, Path(self.pdf_path))
        self.assertEqual(self.extractor.doc_title, "USB Power Delivery Specification")
        self.assertEqual(len(self.extractor.section_patterns), 3)
        
    def test_parse_section_header(self):
        """Test parsing of section headers"""
        # Test pattern with dots
        section = self.extractor._parse_section_header("1.1 Overview ... 11", 1)
        self.assertIsNotNone(section)
        self.assertEqual(section.section_id, "1.1")
        self.assertEqual(section.title, "Overview")
        self.assertEqual(section.page, 1)
        self.assertEqual(section.level, 2)
        self.assertEqual(section.parent_id, "1")
        
        # Test pattern with spaces
        section = self.extractor._parse_section_header("2 Power Delivery 20", 2)
        self.assertIsNotNone(section)
        self.assertEqual(section.section_id, "2")
        self.assertEqual(section.title, "Power Delivery")
        self.assertEqual(section.page, 2)
        self.assertEqual(section.level, 1)
        self.assertIsNone(section.parent_id)
        
        # Test invalid pattern
        section = self.extractor._parse_section_header("Invalid Line", 3)
        self.assertIsNone(section)
        
    def test_generate_tags(self):
        """Test generation of tags"""
        tags = self.extractor._generate_tags("Power Delivery Overview")
        self.assertIn("power", tags)
        self.assertIn("overview", tags)
        
        tags = self.extractor._generate_tags("Communication Protocol")
        self.assertIn("communication", tags)
        self.assertIn("protocol", tags)
        
    def test_extract_toc_sections(self):
        """Test extraction of ToC sections"""
        sections = self.extractor.extract_toc_sections()
        self.assertEqual(len(sections), 4)
        
        # Check if sections are properly extracted
        section_ids = [s.section_id for s in sections]
        self.assertIn("1", section_ids)
        self.assertIn("1.1", section_ids)
        self.assertIn("2", section_ids)
        self.assertIn("2.1", section_ids)
        
    def test_extract_all_sections(self):
        """Test extraction of all sections"""
        # Set up mock for tqdm
        with patch('pdf_content_extract.usb_pd_parser.tqdm') as mock_tqdm:
            mock_tqdm.return_value = self.mock_pdf.pages
            
            sections = self.extractor.extract_all_sections()
            self.assertEqual(len(sections), 1)  # Only one valid section in our mock
            
            # Check if the section is properly extracted
            self.assertEqual(sections[0].section_id, "2")
            self.assertEqual(sections[0].title, "Power Delivery")


if __name__ == "__main__":
    unittest.main()
