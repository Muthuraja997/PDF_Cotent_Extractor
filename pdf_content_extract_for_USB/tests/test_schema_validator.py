"""
Tests for the schema validator module
"""
import unittest
import json
import tempfile
import os
from pathlib import Path
from pdf_parser.schema_validator import SchemaValidator
from pdf_parser.base import Section


class TestSchemaValidator(unittest.TestCase):
    """Test cases for the SchemaValidator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.validator = SchemaValidator()
        
        # Create temporary test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file = os.path.join(self.temp_dir.name, "test_file.jsonl")
        
        # Sample valid section
        self.valid_section = {
            "section_id": "2.1.2",
            "title": "Power Delivery Contract Negotiation",
            "page": 53,
            "level": 3,
            "parent_id": "2.1",
            "full_path": "2.1.2 Power Delivery Contract Negotiation",
            "doc_title": "USB Power Delivery Specification",
            "tags": ["negotiation", "contracts", "power"]
        }
        
        # Sample invalid section (missing required fields)
        self.invalid_section = {
            "section_id": "2.1.3",
            "title": "Power Rules",
            # Missing page
            "level": 3,
            # Missing parent_id
            "full_path": "2.1.3 Power Rules",
            "doc_title": "USB Power Delivery Specification",
            # Missing tags
        }

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_validate_valid_schema(self):
        """Test schema validation with valid data"""
        # Create a test file with valid data
        with open(self.temp_file, 'w') as f:
            json.dump(self.valid_section, f)
            f.write('\n')  # Add newline for JSONL format
        
        # Validate the file
        result = self.validator.validate(self.temp_file)
        
        # Check the result
        self.assertEqual(result['file'], self.temp_file)
        self.assertEqual(result['total_records'], 1)
        self.assertEqual(result['valid_records'], 1)
        self.assertEqual(result['invalid_records'], 0)
        self.assertTrue(result['field_types_valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_validate_invalid_schema(self):
        """Test schema validation with invalid data"""
        # Create a test file with invalid data
        with open(self.temp_file, 'w') as f:
            json.dump(self.invalid_section, f)
            f.write('\n')  # Add newline for JSONL format
        
        # Validate the file
        result = self.validator.validate(self.temp_file)
        
        # Check the result
        self.assertEqual(result['file'], self.temp_file)
        self.assertEqual(result['total_records'], 1)
        self.assertEqual(result['valid_records'], 0)
        self.assertEqual(result['invalid_records'], 1)
        self.assertFalse(result['field_types_valid'])
        self.assertGreater(len(result['errors']), 0)

    def test_validate_mixed_schema(self):
        """Test schema validation with mixed valid and invalid data"""
        # Create a test file with mixed data
        with open(self.temp_file, 'w') as f:
            json.dump(self.valid_section, f)
            f.write('\n')
            json.dump(self.invalid_section, f)
            f.write('\n')
        
        # Validate the file
        result = self.validator.validate(self.temp_file)
        
        # Check the result
        self.assertEqual(result['file'], self.temp_file)
        self.assertEqual(result['total_records'], 2)
        self.assertEqual(result['valid_records'], 1)
        self.assertEqual(result['invalid_records'], 1)
        self.assertFalse(result['field_types_valid'])
        self.assertGreater(len(result['errors']), 0)


if __name__ == "__main__":
    unittest.main()
