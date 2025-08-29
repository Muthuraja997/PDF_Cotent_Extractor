"""
Base classes and interfaces for the PDF parser modules
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Section:
    """Data class representing a document section"""
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    doc_title: str
    tags: List[str]


class BaseValidator(ABC):
    """Base class for validators"""
    
    @abstractmethod
    def validate(self, file_path: str) -> Dict[str, Any]:
        """Validate a file and return results"""
        pass
