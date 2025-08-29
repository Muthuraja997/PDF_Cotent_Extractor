"""
Tests for the report generator module
"""
import unittest
import tempfile
import os
import pandas as pd
from pathlib import Path
from pdf_parser.report_generator import ReportGenerator
from pdf_parser.base import Section


class TestReportGenerator(unittest.TestCase):
    """Test cases for the ReportGenerator class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary test directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_file = os.path.join(self.temp_dir.name, "test_report.xlsx")
        self.report_gen = ReportGenerator(output_file=self.output_file)
        
        # Sample sections for testing
        self.toc_sections = [
            Section(
                section_id="1",
                title="Introduction",
                page=10,
                level=1,
                parent_id=None,
                full_path="1 Introduction",
                doc_title="USB Power Delivery Specification",
                tags=["intro"]
            ),
            Section(
                section_id="1.1",
                title="Overview",
                page=11,
                level=2,
                parent_id="1",
                full_path="1.1 Overview",
                doc_title="USB Power Delivery Specification",
                tags=["overview"]
            ),
            Section(
                section_id="2",
                title="Power Delivery",
                page=20,
                level=1,
                parent_id=None,
                full_path="2 Power Delivery",
                doc_title="USB Power Delivery Specification",
                tags=["power"]
            ),
            Section(
                section_id="2.1",
                title="Power Overview",
                page=21,
                level=2,
                parent_id="2",
                full_path="2.1 Power Overview",
                doc_title="USB Power Delivery Specification",
                tags=["power", "overview"]
            )
        ]
        
        self.all_sections = [
            Section(
                section_id="1",
                title="Introduction",
                page=10,
                level=1,
                parent_id=None,
                full_path="1 Introduction",
                doc_title="USB Power Delivery Specification",
                tags=["intro"]
            ),
            Section(
                section_id="1.1",
                title="Overview",
                page=11,
                level=2,
                parent_id="1",
                full_path="1.1 Overview",
                doc_title="USB Power Delivery Specification",
                tags=["overview"]
            ),
            # 2 is missing from all_sections (mismatch)
            Section(
                section_id="2.1",
                title="Power Overview",
                page=21,
                level=2,
                parent_id="2",
                full_path="2.1 Power Overview",
                doc_title="USB Power Delivery Specification",
                tags=["power", "overview"]
            ),
            # Extra section not in TOC
            Section(
                section_id="3",
                title="Extra Section",
                page=30,
                level=1,
                parent_id=None,
                full_path="3 Extra Section",
                doc_title="USB Power Delivery Specification",
                tags=["extra"]
            )
        ]

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_create_section_dataframes(self):
        """Test creation of DataFrames from sections"""
        toc_df, all_df = self.report_gen._create_section_dataframes(
            self.toc_sections, self.all_sections
        )
        
        # Check DataFrame structures
        self.assertEqual(len(toc_df), len(self.toc_sections))
        self.assertEqual(len(all_df), len(self.all_sections))
        
        # Check column names
        expected_columns = [
            'section_id', 'title', 'page', 'level', 'parent_id',
            'full_path', 'doc_title', 'tags'
        ]
        for col in expected_columns:
            self.assertIn(col, toc_df.columns)
            self.assertIn(col, all_df.columns)

    def test_generate_summary_stats(self):
        """Test generation of summary statistics"""
        summary_df = self.report_gen._generate_summary_stats(
            self.toc_sections, self.all_sections
        )
        
        # Check summary content
        self.assertEqual(len(summary_df), 8)  # 8 metrics
        
        # Convert to dict for easier checking
        summary_dict = dict(zip(summary_df['Metric'], summary_df['Count']))
        
        # Check specific values
        self.assertEqual(summary_dict['Total ToC Sections'], 4)
        self.assertEqual(summary_dict['Total Parsed Sections'], 4)
        self.assertEqual(summary_dict['Sections in Both'], 3)  # 3 sections in both
        self.assertEqual(summary_dict['ToC Only'], 1)  # 1 section only in TOC
        self.assertEqual(summary_dict['Parsed Only'], 1)  # 1 section only in parsed

    def test_find_section_mismatches(self):
        """Test identification of section mismatches"""
        mismatch_df = self.report_gen._find_section_mismatches(
            self.toc_sections, self.all_sections
        )
        
        # Check mismatch content
        self.assertEqual(len(mismatch_df), 2)  # Should be 2 mismatches
        
        # Check if mismatches are correctly identified
        issues = mismatch_df['Issue'].tolist()
        section_ids = mismatch_df['Section ID'].tolist()
        
        self.assertIn('Missing in parsed sections', issues)
        self.assertIn('Extra in parsed sections', issues)
        self.assertIn('2', section_ids)
        self.assertIn('3', section_ids)

    def test_generate_validation_report(self):
        """Test generation of the complete validation report"""
        # Generate the report
        self.report_gen.generate_validation_report(
            self.toc_sections, self.all_sections
        )
        
        # Check if the file was created
        self.assertTrue(os.path.exists(self.output_file))
        
        # Check if the file can be read as Excel
        with pd.ExcelFile(self.output_file) as xls:
            sheet_names = xls.sheet_names
            
            # Check sheet names
            self.assertIn('Summary', sheet_names)
            self.assertIn('ToC Sections', sheet_names)
            self.assertIn('All Sections', sheet_names)
            self.assertIn('Mismatches', sheet_names)
            
            # Check content of sheets
            summary = pd.read_excel(xls, 'Summary')
            self.assertEqual(len(summary), 8)  # 8 metrics
            
            toc_sheet = pd.read_excel(xls, 'ToC Sections')
            self.assertEqual(len(toc_sheet), 4)  # 4 TOC sections
            
            all_sheet = pd.read_excel(xls, 'All Sections')
            self.assertEqual(len(all_sheet), 4)  # 4 parsed sections
            
            mismatches = pd.read_excel(xls, 'Mismatches')
            self.assertEqual(len(mismatches), 2)  # 2 mismatches


if __name__ == "__main__":
    unittest.main()
