"""
Schema validation module for USB PD Parser
"""

import logging
import jsonlines
from pathlib import Path
from typing import List, Dict, Any, Optional

from pdf_parser.base import BaseValidator

logger = logging.getLogger(__name__)


class SchemaValidator(BaseValidator):
    """Validates JSONL files against expected schema"""
    
    def __init__(self):
        self.required_fields = [
            'section_id', 'title', 'page', 'level',
            'parent_id', 'full_path', 'doc_title', 'tags'
        ]
        
        self.type_checks = {
            'section_id': str,
            'title': str,
            'page': int,
            'level': int,
            'full_path': str,
            'doc_title': str,
            'tags': list
        }
    
    def _create_validation_result(self, file_path: str) -> Dict[str, Any]:
        """Create initial validation result structure"""
        return {
            'file': file_path,
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'missing_fields': [],
            'field_types_valid': True,
            'errors': []
        }
    
    def _check_required_fields(
        self, 
        record: Dict[str, Any]
    ) -> List[str]:
        """Check if record has all required fields"""
        return [
            field for field in self.required_fields 
            if field not in record
        ]
    
    def _check_field_types(
        self,
        record: Dict[str, Any]
    ) -> List[str]:
        """Validate field types in record"""
        type_errors = []
        for field, expected_type in self.type_checks.items():
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
        missing_fields: Optional[List[str]] = None,
        type_errors: Optional[List[str]] = None
    ) -> bool:
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

    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate JSONL file against expected schema"""
        validation_result = self._create_validation_result(file_path)
        
        try:
            with jsonlines.open(file_path, 'r') as reader:
                for i, record in enumerate(reader):
                    validation_result['total_records'] += 1
                    
                    missing_fields = self._check_required_fields(record)
                    if missing_fields:
                        self._update_validation_result(
                            validation_result, i, missing_fields=missing_fields
                        )
                        continue
                    
                    type_errors = self._check_field_types(record)
                    if type_errors:
                        self._update_validation_result(
                            validation_result, i, type_errors=type_errors
                        )
                        continue
                    
                    validation_result['valid_records'] += 1
                    
        except Exception as e:
            validation_result['errors'].append(f"File reading error: {str(e)}")
        
        return validation_result
