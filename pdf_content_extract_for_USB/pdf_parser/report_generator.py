"""
Report generation module for USB PD Parser
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import asdict

from pdf_parser.base import Section
from pdf_parser.schema_validator import SchemaValidator
from pdf_parser.hierarchy_validator import HierarchyValidator

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive validation reports"""
    
    def __init__(self, output_file: str = 'usb_pd_validation_report.xlsx'):
        self.schema_validator = SchemaValidator()
        self.hierarchy_validator = HierarchyValidator()
        self.output_file = output_file
        self.logger = logging.getLogger(__name__)
        
    def _get_schema_validation_data(
        self,
        toc_validation: Dict[str, Any],
        spec_validation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prepare schema validation summary data"""
        schema_data = []
        for validation in [toc_validation, spec_validation]:
            schema_data.append({
                'File': Path(validation['file']).name,
                'Total Records': validation['total_records'],
                'Valid Records': validation['valid_records'],
                'Invalid Records': validation['invalid_records'],
                'Field Types Valid': validation['field_types_valid'],
                'Error Count': len(validation['errors'])
            })
        return schema_data

    def _get_hierarchy_validation_data(
        self,
        toc_validation: Dict[str, Any],
        spec_validation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Prepare hierarchy validation summary data"""
        hierarchy_data = []
        for validation in [toc_validation, spec_validation]:
            hierarchy_data.append({
                'File': Path(validation['file']).name,
                'Total Sections': validation['total_sections'],
                'Orphaned Sections': len(validation['orphaned_sections']),
                'Level Inconsistencies': len(validation['level_inconsistencies']),
                'Parent-Child Mismatches': len(validation['parent_child_mismatches'])
            })
        return hierarchy_data

    def _get_detailed_errors(
        self,
        toc_validation: Dict[str, Any],
        spec_validation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Collect all validation errors"""
        all_errors = []
        for validation in [toc_validation, spec_validation]:
            for error in validation['errors']:
                all_errors.append({
                    'File': Path(validation['file']).name,
                    'Error': error
                })
        return all_errors

    def _save_validation_report(
        self,
        output_file: str,
        schema_data: List[Dict[str, Any]],
        hierarchy_data: List[Dict[str, Any]],
        error_data: List[Dict[str, Any]]
    ) -> None:
        """Save validation data to Excel report"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            pd.DataFrame(schema_data).to_excel(
                writer,
                sheet_name='Schema Validation',
                index=False
            )
            
            pd.DataFrame(hierarchy_data).to_excel(
                writer,
                sheet_name='Hierarchy Validation',
                index=False
            )
            
            if error_data:
                pd.DataFrame(error_data).to_excel(
                    writer,
                    sheet_name='Detailed Errors',
                    index=False
                )
        
        self.logger.info(f"Validation report saved to {output_file}")

    def generate_report(
        self,
        toc_file: str,
        spec_file: str,
        output_file: str = 'validation_report.xlsx'
    ) -> None:
        """Generate comprehensive validation report"""
        self.logger.info("Generating validation report...")
        
        # Perform validations
        toc_schema = self.schema_validator.validate(toc_file)
        spec_schema = self.schema_validator.validate(spec_file)
        toc_hierarchy = self.hierarchy_validator.validate(toc_file)
        spec_hierarchy = self.hierarchy_validator.validate(spec_file)
        
        # Prepare report data
        schema_data = self._get_schema_validation_data(toc_schema, spec_schema)
        hierarchy_data = self._get_hierarchy_validation_data(
            toc_hierarchy, spec_hierarchy
        )
        error_data = self._get_detailed_errors(toc_schema, spec_schema)
        
        # Save report
        self._save_validation_report(
            output_file,
            schema_data,
            hierarchy_data,
            error_data
        )

    def _create_section_dataframes(
        self, 
        toc_sections: List[Section], 
        all_sections: List[Section]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create DataFrames from ToC and parsed sections."""
        toc_df = pd.DataFrame([asdict(s) for s in toc_sections])
        all_df = pd.DataFrame([asdict(s) for s in all_sections])
        return toc_df, all_df

    def _generate_summary_stats(
        self, 
        toc_sections: List[Section], 
        all_sections: List[Section]
    ) -> pd.DataFrame:
        """Generate summary statistics comparing ToC and parsed sections."""
        toc_ids = set(s.section_id for s in toc_sections)
        all_ids = set(s.section_id for s in all_sections)
        
        summary_data = {
            'Metric': [
                'Total ToC Sections',
                'Total Parsed Sections',
                'Sections in Both',
                'ToC Only',
                'Parsed Only',
                'Level 1 Sections (ToC)',
                'Level 2 Sections (ToC)',
                'Level 3+ Sections (ToC)'
            ],
            'Count': [
                len(toc_sections),
                len(all_sections),
                len(toc_ids & all_ids),
                len(toc_ids - all_ids),
                len(all_ids - toc_ids),
                len([s for s in toc_sections if s.level == 1]),
                len([s for s in toc_sections if s.level == 2]),
                len([s for s in toc_sections if s.level >= 3])
            ]
        }
        return pd.DataFrame(summary_data)

    def _find_section_mismatches(
        self, 
        toc_sections: List[Section], 
        all_sections: List[Section]
    ) -> pd.DataFrame:
        """Identify mismatches between ToC and parsed sections."""
        toc_ids = set(s.section_id for s in toc_sections)
        all_ids = set(s.section_id for s in all_sections)
        
        mismatch_data = []
        
        # Find sections missing in parsed content
        for section_id in (toc_ids - all_ids):
            toc_section = next(
                s for s in toc_sections 
                if s.section_id == section_id
            )
            mismatch_data.append({
                'Section ID': section_id,
                'Title': toc_section.title,
                'Issue': 'Missing in parsed sections',
                'ToC Page': toc_section.page,
                'Parsed Page': 'N/A'
            })
        
        # Find extra sections in parsed content
        for section_id in (all_ids - toc_ids):
            all_section = next(
                s for s in all_sections 
                if s.section_id == section_id
            )
            mismatch_data.append({
                'Section ID': section_id,
                'Title': all_section.title,
                'Issue': 'Extra in parsed sections',
                'ToC Page': 'N/A',
                'Parsed Page': all_section.page
            })
        
        return pd.DataFrame(mismatch_data)

    def _save_sections_report(
        self, 
        summary_df: pd.DataFrame, 
        toc_df: pd.DataFrame,
        all_df: pd.DataFrame, 
        mismatch_df: pd.DataFrame,
        output_file: str = None
    ) -> None:
        """Save section comparison data to Excel file."""
        if output_file is None:
            output_file = self.output_file
            
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            if not toc_df.empty:
                toc_df.to_excel(writer, sheet_name='ToC Sections', index=False)
            if not all_df.empty:
                all_df.to_excel(writer, sheet_name='All Sections', index=False)
            if not mismatch_df.empty:
                mismatch_df.to_excel(writer, sheet_name='Mismatches', index=False)
        
        logger.info(f"Validation report saved to {output_file}")

    def generate_validation_report(
        self, 
        toc_sections: List[Section], 
        all_sections: List[Section],
        output_file: str = None
    ) -> None:
        """Generate Excel validation report comparing ToC and parsed sections."""
        logger.info("Generating validation report...")
        
        if output_file is None:
            output_file = self.output_file
        
        try:
            # Create DataFrames
            toc_df, all_df = self._create_section_dataframes(toc_sections, all_sections)
            
            # Generate statistics
            summary_df = self._generate_summary_stats(toc_sections, all_sections)
            
            # Find mismatches
            mismatch_df = self._find_section_mismatches(toc_sections, all_sections)
            
            # Save to Excel
            self._save_sections_report(
                summary_df,
                toc_df,
                all_df,
                mismatch_df,
                output_file
            )
            
            # Calculate coverage percentage
            if toc_sections:
                toc_ids = set(s.section_id for s in toc_sections)
                all_ids = set(s.section_id for s in all_sections)
                coverage = len(toc_ids & all_ids) / len(toc_ids) * 100
                logger.info(f"Coverage: {coverage:.1f}% of ToC sections found in parsed content")
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            raise
