"""
Tests for the hierarchy validator module
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
import jsonlines
from pdf_parser.hierarchy_validator import HierarchyValidator
from pdf_parser.base import Section


class TestHierarchyValidator(unittest.TestCase):
    """Test cases for the HierarchyValidator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.validator = HierarchyValidator()
        
        # Create temporary test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "test_hierarchy.jsonl")
        
        # Sample sections with valid hierarchy
        self.valid_sections = [
            {
                "section_id": "1",
                "title": "Introduction",
                "page": 10,
                "level": 1,
                "parent_id": None,
                "full_path": "1 Introduction",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["intro"]
            },
            {
                "section_id": "1.1",
                "title": "Overview",
                "page": 11,
                "level": 2,
                "parent_id": "1",
                "full_path": "1.1 Overview",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["overview"]
            },
            {
                "section_id": "1.1.1",
                "title": "Scope",
                "page": 12,
                "level": 3,
                "parent_id": "1.1",
                "full_path": "1.1.1 Scope",
                "doc_title": "USB Power Delivery Specification",
                "tags": []
            },
            {
                "section_id": "2",
                "title": "Power Delivery",
                "page": 20,
                "level": 1,
                "parent_id": None,
                "full_path": "2 Power Delivery",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["power"]
            },
            {
                "section_id": "2.1",
                "title": "Power Overview",
                "page": 21,
                "level": 2,
                "parent_id": "2",
                "full_path": "2.1 Power Overview",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["power", "overview"]
            }
        ]
        
        # Sample sections with invalid hierarchy (orphaned section, level inconsistency)
        self.invalid_sections = [
            {
                "section_id": "1",
                "title": "Introduction",
                "page": 10,
                "level": 1,
                "parent_id": None,
                "full_path": "1 Introduction",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["intro"]
            },
            {
                "section_id": "1.1",
                "title": "Overview",
                "page": 11,
                "level": 2,
                "parent_id": "1",
                "full_path": "1.1 Overview",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["overview"]
            },
            {
                "section_id": "1.1.1",
                "title": "Scope",
                "page": 12,
                "level": 3,  # Correct level
                "parent_id": "1.1",
                "full_path": "1.1.1 Scope",
                "doc_title": "USB Power Delivery Specification",
                "tags": []
            },
            {
                "section_id": "2.1",  # Orphaned (no parent "2" section)
                "title": "Power Overview",
                "page": 21,
                "level": 2,
                "parent_id": "2",  # Parent doesn't exist
                "full_path": "2.1 Power Overview",
                "doc_title": "USB Power Delivery Specification",
                "tags": ["power", "overview"]
            },
            {
                "section_id": "3.1.1",
                "title": "Inconsistent Level",
                "page": 30,
                "level": 2,  # Inconsistent level (should be 3)
                "parent_id": "3.1",  # Parent doesn't exist
                "full_path": "3.1.1 Inconsistent Level",
                "doc_title": "USB Power Delivery Specification",
                "tags": []
            }
        ]

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_validate_valid_hierarchy(self):
        """Test hierarchy validation with valid data"""
        # Create a test file with valid hierarchy
        with jsonlines.open(self.temp_file, 'w') as writer:
            for section in self.valid_sections:
                writer.write(section)
        
        # Validate the file
        result = self.validator.validate(self.temp_file)
        
        # Check the result
        self.assertEqual(result['file'], self.temp_file)
        self.assertEqual(result['total_sections'], 5)
        self.assertEqual(len(result['orphaned_sections']), 0)
        self.assertEqual(len(result['level_inconsistencies']), 0)
        self.assertEqual(len(result['parent_child_mismatches']), 0)

    def test_validate_invalid_hierarchy(self):
        """Test hierarchy validation with invalid data"""
        # Create a test file with invalid hierarchy
        with jsonlines.open(self.temp_file, 'w') as writer:
            for section in self.invalid_sections:
                writer.write(section)
        
        # Validate the file
        result = self.validator.validate(self.temp_file)
        
        # Check the result
        self.assertEqual(result['file'], self.temp_file)
        self.assertEqual(result['total_sections'], 5)
        self.assertGreater(len(result['orphaned_sections']), 0)  # Should have orphaned sections
        self.assertGreater(len(result['level_inconsistencies']), 0)  # Should have level inconsistencies
        
        # Verify specific issues
        orphaned_ids = [s['section_id'] for s in result['orphaned_sections']]
        self.assertIn('2.1', orphaned_ids)
        self.assertIn('3.1.1', orphaned_ids)
        
        inconsistent_ids = [s['section_id'] for s in result['level_inconsistencies']]
        self.assertIn('3.1.1', inconsistent_ids)


if __name__ == "__main__":
    unittest.main()
