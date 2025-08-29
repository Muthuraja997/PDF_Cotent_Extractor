"""
Tests for the base module
"""
import unittest
from pdf_parser.base import Section


class TestSection(unittest.TestCase):
    """Test cases for the Section data class"""

    def setUp(self):
        """Set up test fixtures"""
        self.section = Section(
            section_id="2.1.2",
            title="Power Delivery Contract Negotiation",
            page=53,
            level=3,
            parent_id="2.1",
            full_path="2.1.2 Power Delivery Contract Negotiation",
            doc_title="USB Power Delivery Specification",
            tags=["negotiation", "contracts", "power"]
        )

    def test_section_attributes(self):
        """Test the attributes of a section"""
        self.assertEqual(self.section.section_id, "2.1.2")
        self.assertEqual(self.section.title, "Power Delivery Contract Negotiation")
        self.assertEqual(self.section.page, 53)
        self.assertEqual(self.section.level, 3)
        self.assertEqual(self.section.parent_id, "2.1")
        self.assertEqual(
            self.section.full_path, 
            "2.1.2 Power Delivery Contract Negotiation"
        )
        self.assertEqual(
            self.section.doc_title, 
            "USB Power Delivery Specification"
        )
        self.assertListEqual(
            sorted(self.section.tags), 
            sorted(["negotiation", "contracts", "power"])
        )

    def test_section_parent_hierarchy(self):
        """Test the parent-child relationship"""
        parent_section = Section(
            section_id="2.1",
            title="Power Delivery Overview",
            page=50,
            level=2,
            parent_id="2",
            full_path="2.1 Power Delivery Overview",
            doc_title="USB Power Delivery Specification",
            tags=["overview", "power"]
        )
        
        # Test parent ID relationship
        self.assertEqual(self.section.parent_id, parent_section.section_id)
        
        # Test level relationship
        self.assertEqual(self.section.level, parent_section.level + 1)


if __name__ == "__main__":
    unittest.main()
