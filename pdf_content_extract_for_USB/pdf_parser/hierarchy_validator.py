"""
Hierarchy validation module for USB PD Parser
"""

import logging
import jsonlines
from typing import List, Dict, Any, Optional

from pdf_parser.base import BaseValidator

logger = logging.getLogger(__name__)


class HierarchyValidator(BaseValidator):
    """Validates section hierarchy consistency"""

    def _create_hierarchy_result(self, file_path: str) -> Dict[str, Any]:
        """Create initial hierarchy validation result structure"""
        return {
            'file': file_path,
            'total_sections': 0,
            'orphaned_sections': [],
            'level_inconsistencies': [],
            'parent_child_mismatches': []
        }

    def _check_orphaned_sections(
        self,
        section: Dict[str, Any],
        section_lookup: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
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
    ) -> Optional[Dict[str, Any]]:
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
    ) -> Optional[Dict[str, Any]]:
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

    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate section hierarchy consistency"""
        hierarchy_result = self._create_hierarchy_result(file_path)
        
        try:
            # Load all sections
            with jsonlines.open(file_path, 'r') as reader:
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
