"""
Tests for the coverage analyzer module
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from pdf_parser.coverage_analyzer import CoverageAnalyzer
from pdf_parser.content_enhancer import ContentEnhancer


class TestCoverageAnalyzer(unittest.TestCase):
    """Test the CoverageAnalyzer class"""
    
    def setUp(self):
        """Set up test data"""
        self.analyzer = CoverageAnalyzer()
        
        # Create temp files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.toc_file = os.path.join(self.temp_dir.name, "toc.jsonl")
        self.spec_file = os.path.join(self.temp_dir.name, "spec.jsonl")
        
        # Sample ToC data
        toc_data = [
            {"section_id": "1", "title": "Section 1", "page": 1, "level": 1},
            {"section_id": "1.1", "title": "Section 1.1", "page": 2, "level": 2},
            {"section_id": "1.2", "title": "Section 1.2", "page": 3, "level": 2},
            {"section_id": "2", "title": "Section 2", "page": 4, "level": 1},
        ]
        
        # Sample Spec data
        spec_data = [
            {"section_id": "1", "title": "Section 1", "page": 1, "content": "Content 1"},
            {"section_id": "1.1", "title": "Section 1.1", "page": 2, "content": "Content 1.1"},
            # Section 1.2 is missing
            {"section_id": "2", "title": "Section 2", "page": 4, "content": "Content 2"},
        ]
        
        # Write to temp files
        with open(self.toc_file, "w") as f:
            for item in toc_data:
                f.write(json.dumps(item) + "\n")
        
        with open(self.spec_file, "w") as f:
            for item in spec_data:
                f.write(json.dumps(item) + "\n")
    
    def tearDown(self):
        """Clean up temp files"""
        self.temp_dir.cleanup()
    
    def test_analyze(self):
        """Test the analyze method"""
        metrics = self.analyzer.analyze(self.toc_file, self.spec_file)
        
        # Check metrics
        self.assertEqual(metrics["total_toc"], 4)
        self.assertEqual(metrics["total_spec"], 3)
        self.assertEqual(metrics["common"], 3)
        self.assertEqual(metrics["toc_only"], 1)
        self.assertEqual(metrics["spec_only"], 0)
        self.assertAlmostEqual(metrics["coverage_percentage"], 75.0)


class TestContentEnhancer(unittest.TestCase):
    """Test the ContentEnhancer class"""
    
    def setUp(self):
        """Set up test data"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.toc_file = os.path.join(self.temp_dir.name, "toc.jsonl")
        self.spec_file = os.path.join(self.temp_dir.name, "spec.jsonl")
        self.pdf_path = os.path.join(self.temp_dir.name, "test.pdf")
        
        # Create a dummy PDF file
        with open(self.pdf_path, "wb") as f:
            f.write(b"%PDF-1.4\n%EOF")
        
        # Sample ToC data
        toc_data = [
            {"section_id": "1", "title": "Section 1", "page": 1, "level": 1},
            {"section_id": "1.1", "title": "Section 1.1", "page": 2, "level": 2},
            {"section_id": "1.2", "title": "Section 1.2", "page": 3, "level": 2},
            {"section_id": "2", "title": "Section 2", "page": 4, "level": 1},
        ]
        
        # Sample Spec data
        spec_data = [
            {"section_id": "1", "title": "Section 1", "page": 1, "content": "Content 1"},
            {"section_id": "1.1", "title": "Section 1.1", "page": 2, "content": "Content 1.1"},
            # Section 1.2 is missing
            {"section_id": "2", "title": "Section 2", "page": 4, "content": "Content 2"},
        ]
        
        # Write to temp files
        with open(self.toc_file, "w") as f:
            for item in toc_data:
                f.write(json.dumps(item) + "\n")
        
        with open(self.spec_file, "w") as f:
            for item in spec_data:
                f.write(json.dumps(item) + "\n")
        
        self.enhancer = ContentEnhancer(self.pdf_path, self.toc_file, self.spec_file)
    
    def tearDown(self):
        """Clean up temp files"""
        self.temp_dir.cleanup()
    
    def test_analyze_coverage(self):
        """Test the analyze_coverage method"""
        with patch('jsonlines.open') as mock_jsonlines:
            # Setup mock to return our test data
            mock_jsonlines.return_value.__enter__.return_value = MagicMock()
            mock_jsonlines.return_value.__enter__.return_value.__iter__.side_effect = [
                [
                    {"section_id": "1", "title": "Section 1", "page": 1, "level": 1},
                    {"section_id": "1.1", "title": "Section 1.1", "page": 2, "level": 2},
                    {"section_id": "1.2", "title": "Section 1.2", "page": 3, "level": 2},
                    {"section_id": "2", "title": "Section 2", "page": 4, "level": 1},
                ],
                [
                    {"section_id": "1", "title": "Section 1", "page": 1, "content": "Content 1"},
                    {"section_id": "1.1", "title": "Section 1.1", "page": 2, "content": "Content 1.1"},
                    {"section_id": "2", "title": "Section 2", "page": 4, "content": "Content 2"},
                ]
            ]
            
            coverage = self.enhancer.analyze_coverage()
            self.assertAlmostEqual(coverage, 75.0)
    
    def test_extract_missing_content(self):
        """Test the extract_missing_content method"""
        with patch('pdf_parser.content_enhancer.ContentEnhancer._extract_text_from_page') as mock_extract:
            # Setup mock to return text for missing page
            mock_extract.return_value = "Enhanced content for page 3"
            
            # Mock _get_missing_pages to return page 3
            with patch('pdf_parser.content_enhancer.ContentEnhancer._get_missing_pages') as mock_missing:
                mock_missing.return_value = [3]
                
                # Mock _get_missing_section_ids to return section 1.2
                with patch('pdf_parser.content_enhancer.ContentEnhancer._get_missing_section_ids') as mock_missing_ids:
                    mock_missing_ids.return_value = {"1.2"}
                    
                    # Mock _get_toc_entry_for_page to return a ToC entry
                    with patch('pdf_parser.content_enhancer.ContentEnhancer._get_toc_entry_for_page') as mock_toc:
                        mock_toc.return_value = {
                            "section_id": "1.2", 
                            "title": "Section 1.2", 
                            "page": 3, 
                            "level": 2
                        }
                        
                        # Mock jsonlines for appending to spec file
                        with patch('jsonlines.open') as mock_jsonlines:
                            # Mock for reading the spec data
                            mock_reader = MagicMock()
                            mock_reader.__iter__.return_value = [
                                {"section_id": "1", "title": "Section 1", "page": 1, "content": "Content 1"},
                                {"section_id": "1.1", "title": "Section 1.1", "page": 2, "content": "Content 1.1"},
                                {"section_id": "2", "title": "Section 2", "page": 4, "content": "Content 2"},
                            ]
                            
                            # Mock for writing new sections
                            mock_writer = MagicMock()
                            
                            mock_jsonlines.return_value.__enter__.side_effect = [mock_reader, mock_writer]
                            
                            # Call the method
                            new_sections = self.enhancer.extract_missing_content()
                            
                            # Check that a new section was added
                            self.assertEqual(new_sections, 1)
                            
                            # Check that write_all was called with the expected data
                            mock_writer.write_all.assert_called_once()
                            args = mock_writer.write_all.call_args[0][0]
                            self.assertEqual(len(args), 1)
                            self.assertEqual(args[0]["section_id"], "1.2")
                            self.assertEqual(args[0]["page"], 3)
                            self.assertEqual(args[0]["enhanced"], True)


if __name__ == "__main__":
    unittest.main()
