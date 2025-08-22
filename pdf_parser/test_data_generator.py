"""
Test data generation module for USB PD Parser
"""

import logging
import jsonlines
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Generates sample test data for validation"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _create_test_records(self) -> List[Dict[str, Any]]:
        """Create sample records with intentional validation errors"""
        return [
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

    def generate(self, output_file: str = 'test_data.jsonl') -> None:
        """Generate and save test data"""
        self.logger.info(f"Creating sample test data at {output_file}...")
        
        try:
            test_data = self._create_test_records()
            
            with jsonlines.open(output_file, 'w') as writer:
                for record in test_data:
                    writer.write(record)
            
            self.logger.info(f"Sample test data created: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error generating test data: {e}")
            raise
