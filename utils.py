"""
Utility functions for USB PD Parser
Includes validation, testing, and helper functions
"""

import json
import jsonlines
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ParserValidator:
    """Utility class for validating parser output"""
    
    def __init__(self):
        self.validation_results = {}
    
    def _create_validation_result(self, jsonl_file: str) -> Dict[str, Any]:
        """Create initial validation result structure"""
        return {
            'file': jsonl_file,
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'missing_fields': [],
            'field_types_valid': True,
            'errors': []
        }
    
    def _check_required_fields(
        self, 
        record: Dict[str, Any],
        required_fields: List[str]
    ) -> List[str]:
        """Check if record has all required fields"""
        return [
            field for field in required_fields 
            if field not in record
        ]
    
    def _check_field_types(
        self,
        record: Dict[str, Any],
        type_checks: Dict[str, type]
    ) -> List[str]:
        """Validate field types in record"""
        type_errors = []
        for field, expected_type in type_checks.items():
            if not isinstance(record[field], expected_type):
                type_errors.append(
                    f"{field}: expected {expected_type.__name__}, "
                    f"got {type(record[field]).__name__}"
                )
        return type_errors
    
    def _update_validation_result(
        self,
        validation_result: Dict[str, Any],
        record_index: int,
        missing_fields: List[str] = None,
        type_errors: List[str] = None
    ) -> None:
        """Update validation result with findings"""
        if missing_fields:
            validation_result['missing_fields'].extend(missing_fields)
            validation_result['invalid_records'] += 1
            validation_result['errors'].append(
                f"Record {record_index + 1}: Missing fields {missing_fields}"
            )
            return False
            
        if type_errors:
            validation_result['field_types_valid'] = False
            validation_result['invalid_records'] += 1
            validation_result['errors'].append(
                f"Record {record_index + 1}: Type errors: {', '.join(type_errors)}"
            )
            return False
            
        validation_result['valid_records'] += 1
        return True

    def validate_jsonl_schema(self, jsonl_file: str) -> Dict[str, Any]:
        """Validate JSONL file against expected schema"""
        required_fields = [
            'section_id', 'title', 'page', 'level',
            'parent_id', 'full_path', 'doc_title', 'tags'
        ]
        
        type_checks = {
            'section_id': str,
            'title': str,
            'page': int,
            'level': int,
            'full_path': str,
            'doc_title': str,
            'tags': list
        }
        
        validation_result = self._create_validation_result(jsonl_file)
        
        try:
            with jsonlines.open(jsonl_file, 'r') as reader:
                for i, record in enumerate(reader):
                    validation_result['total_records'] += 1
                    
                    missing_fields = self._check_required_fields(
                        record, required_fields
                    )
                    if missing_fields:
                        self._update_validation_result(
                            validation_result, i, missing_fields=missing_fields
                        )
                        continue
                    
                    type_errors = self._check_field_types(record, type_checks)
                    if type_errors:
                        self._update_validation_result(
                            validation_result, i, type_errors=type_errors
                        )
                        continue
                    
                    validation_result['valid_records'] += 1
                    
        except Exception as e:
            validation_result['errors'].append(f"File reading error: {str(e)}")
        
        return validation_result
    
    def _create_hierarchy_result(self, jsonl_file: str) -> Dict[str, Any]:
        """Create initial hierarchy validation result structure"""
        return {
            'file': jsonl_file,
            'total_sections': 0,
            'orphaned_sections': [],
            'level_inconsistencies': [],
            'parent_child_mismatches': []
        }

    def _check_orphaned_sections(
        self,
        section: Dict[str, Any],
        section_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if section's parent exists"""
        parent_id = section.get('parent_id')
        if parent_id and parent_id not in section_lookup:
            return {
                'section_id': section['section_id'],
                'title': section['title'],
                'missing_parent': parent_id
            }
        return None

    def _check_level_consistency(
        self,
        section: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if section's level matches its ID structure"""
        section_id = section['section_id']
        level = section['level']
        expected_level = section_id.count('.') + 1
        
        if level != expected_level:
            return {
                'section_id': section_id,
                'title': section['title'],
                'actual_level': level,
                'expected_level': expected_level
            }
        return None

    def _check_parent_child_relationship(
        self,
        section: Dict[str, Any],
        section_lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if parent-child level relationship is valid"""
        parent_id = section.get('parent_id')
        if parent_id and parent_id in section_lookup:
            parent_section = section_lookup[parent_id]
            level = section['level']
            expected_parent_level = level - 1
            
            if parent_section['level'] != expected_parent_level:
                return {
                    'section_id': section['section_id'],
                    'parent_id': parent_id,
                    'section_level': level,
                    'parent_level': parent_section['level'],
                    'expected_parent_level': expected_parent_level
                }
        return None

    def validate_hierarchy(self, jsonl_file: str) -> Dict[str, Any]:
        """Validate section hierarchy consistency"""
        hierarchy_result = self._create_hierarchy_result(jsonl_file)
        
        try:
            # Load all sections
            with jsonlines.open(jsonl_file, 'r') as reader:
                sections = list(reader)
            
            hierarchy_result['total_sections'] = len(sections)
            
            # Create lookup dictionary for efficient access
            section_lookup = {s['section_id']: s for s in sections}
            
            for section in sections:
                # Check orphaned sections
                if orphaned := self._check_orphaned_sections(
                    section, section_lookup
                ):
                    hierarchy_result['orphaned_sections'].append(orphaned)
                
                # Check level consistency
                if inconsistency := self._check_level_consistency(section):
                    hierarchy_result['level_inconsistencies'].append(
                        inconsistency
                    )
                
                # Check parent-child relationships
                if mismatch := self._check_parent_child_relationship(
                    section, section_lookup
                ):
                    hierarchy_result['parent_child_mismatches'].append(
                        mismatch
                    )
        
        except Exception as e:
            hierarchy_result['error'] = str(e)
        
        return hierarchy_result
    
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
        writer: pd.ExcelWriter,
        schema_data: List[Dict[str, Any]],
        hierarchy_data: List[Dict[str, Any]],
        error_data: List[Dict[str, Any]]
    ) -> None:
        """Save validation data to Excel report"""
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

    def generate_comprehensive_report(
        self,
        toc_file: str,
        spec_file: str,
        output_file: str = 'comprehensive_validation_report.xlsx'
    ) -> None:
        """Generate comprehensive validation report"""
        logger.info("Generating comprehensive validation report...")
        
        # Perform validations
        toc_schema = self.validate_jsonl_schema(toc_file)
        spec_schema = self.validate_jsonl_schema(spec_file)
        toc_hierarchy = self.validate_hierarchy(toc_file)
        spec_hierarchy = self.validate_hierarchy(spec_file)
        
        # Prepare report data
        schema_data = self._get_schema_validation_data(toc_schema, spec_schema)
        hierarchy_data = self._get_hierarchy_validation_data(
            toc_hierarchy, spec_hierarchy
        )
        error_data = self._get_detailed_errors(toc_schema, spec_schema)
        
        # Save report
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            self._save_validation_report(
                writer,
                schema_data,
                hierarchy_data,
                error_data
            )
        
        logger.info(f"Comprehensive validation report saved to {output_file}")

class CoverageAnalyzer:
    """Analyzes parsing coverage between ToC and full document sections"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _load_sections(self, file_path: str) -> List[Dict[str, Any]]:
        """Load sections from JSONL file"""
        try:
            with jsonlines.open(file_path, 'r') as reader:
                return list(reader)
        except Exception as e:
            self.logger.error(f"Error loading sections from {file_path}: {e}")
            raise

    def _calculate_metrics(
        self,
        toc_ids: set,
        spec_ids: set
    ) -> Dict[str, Any]:
        """Calculate coverage metrics"""
        total_toc = len(toc_ids)
        total_spec = len(spec_ids)
        common = len(toc_ids & spec_ids)
        toc_only = len(toc_ids - spec_ids)
        spec_only = len(spec_ids - toc_ids)
        
        coverage_percentage = (common / total_toc * 100) if total_toc > 0 else 0
        
        return {
            'total_toc': total_toc,
            'total_spec': total_spec,
            'common': common,
            'toc_only': toc_only,
            'spec_only': spec_only,
            'coverage_percentage': coverage_percentage
        }

    def _print_coverage_report(self, metrics: Dict[str, Any]) -> None:
        """Print coverage analysis results"""
        self.logger.info("Coverage Analysis Results:")
        self.logger.info(f"   ToC sections: {metrics['total_toc']}")
        self.logger.info(f"   Spec sections: {metrics['total_spec']}")
        self.logger.info(f"   Common sections: {metrics['common']}")
        self.logger.info(f"   ToC only: {metrics['toc_only']}")
        self.logger.info(f"   Spec only: {metrics['spec_only']}")
        self.logger.info(
            f"   Coverage: {metrics['coverage_percentage']:.1f}%"
        )
        
        if metrics['toc_only'] > 0:
            self.logger.warning(
                f"{metrics['toc_only']} sections found in ToC but not in "
                "full document parsing"
            )
        
        if metrics['spec_only'] > 0:
            self.logger.warning(
                f"{metrics['spec_only']} sections found in full document "
                "but not in ToC"
            )

    def analyze(self, toc_file: str, spec_file: str) -> Dict[str, Any]:
        """Analyze parsing coverage between ToC and full document"""
        self.logger.info("Analyzing parsing coverage...")
        
        try:
            # Load data and extract section IDs
            toc_sections = self._load_sections(toc_file)
            spec_sections = self._load_sections(spec_file)
            
            toc_ids = set(s['section_id'] for s in toc_sections)
            spec_ids = set(s['section_id'] for s in spec_sections)
            
            # Calculate and print metrics
            metrics = self._calculate_metrics(toc_ids, spec_ids)
            self._print_coverage_report(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing coverage: {e}")
            raise

class TestDataGenerator:
    """Create sample test data for validation"""
    print(" Creating sample test data...")
    
    # Create a sample with intentional errors for testing
    test_data = [
        {
            "section_id": "1",
            "title": "Introduction",
            "page": 10,
            "level": 1,
            "parent_id": None,
            "full_path": "1 Introduction",
            "doc_title": "Test Document",
            "tags": ["intro"]
        },
        {
            "section_id": "1.1",
            "title": "Overview",
            "page": 11,
            "level": 2,
            "parent_id": "1",
            "full_path": "1.1 Overview",
            "doc_title": "Test Document",
            "tags": ["overview"]
        },
        {
            # Intentional error: missing parent "1.2"
            "section_id": "1.2.1",
            "title": "Orphaned Section",
            "page": 15,
            "level": 3,
            "parent_id": "1.2",
            "full_path": "1.2.1 Orphaned Section",
            "doc_title": "Test Document",
            "tags": []
        },
        {
            # Intentional error: wrong level (should be 2, not 3)
            "section_id": "2",
            "title": "Wrong Level Section",
            "page": 20,
            "level": 3,
            "parent_id": None,
            "full_path": "2 Wrong Level Section",
            "doc_title": "Test Document",
            "tags": []
        }
    ]
    
    with jsonlines.open('test_data.jsonl', 'w') as writer:
        for record in test_data:
            writer.write(record)
    
    print(" Sample test data created: test_data.jsonl")

def main():
    """Main function for utility script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='USB PD Parser Utilities')
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation tests'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Analyze parsing coverage'
    )
    parser.add_argument(
        '--test-data',
        action='store_true',
        help='Create sample test data'
    )
    parser.add_argument(
        '--toc-file',
        default='usb_pd_toc.jsonl',
        help='ToC JSONL file'
    )
    parser.add_argument(
        '--spec-file',
        default='usb_pd_spec.jsonl',
        help='Spec JSONL file'
    )
    
    args = parser.parse_args()
    logger = logging.getLogger(__name__)
    
    if args.test_data:
        generator = TestDataGenerator()
        generator.generate()
    
    if args.validate:
        validator = ParserValidator()
        if Path(args.toc_file).exists() and Path(args.spec_file).exists():
            validator.generate_comprehensive_report(
                args.toc_file,
                args.spec_file
            )
        else:
            logger.error(
                "JSONL files not found. Run parser first or use --test-data "
                "to create sample data."
            )
    
    if args.coverage:
        if Path(args.toc_file).exists() and Path(args.spec_file).exists():
            analyzer = CoverageAnalyzer()
            analyzer.analyze(args.toc_file, args.spec_file)
        else:
            logger.error("JSONL files not found. Run parser first.")
    
    if not any([args.validate, args.coverage, args.test_data]):
        logger.info("USB PD Parser Utilities")
        logger.info("Usage:")
        logger.info("  --validate: Run validation tests")
        logger.info("  --coverage: Analyze parsing coverage")
        logger.info("  --test-data: Create sample test data")

if __name__ == "__main__":
    main()

