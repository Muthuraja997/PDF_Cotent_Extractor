"""
Coverage analysis module for USB PD Parser
"""

import logging
import jsonlines
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)


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

    def _extract_section_ids(self, sections: List[Dict[str, Any]]) -> Set[str]:
        """Extract section IDs from sections list"""
        return set(s['section_id'] for s in sections)

    def _calculate_metrics(
        self,
        toc_ids: Set[str],
        spec_ids: Set[str]
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
            
            toc_ids = self._extract_section_ids(toc_sections)
            spec_ids = self._extract_section_ids(spec_sections)
            
            # Calculate and print metrics
            metrics = self._calculate_metrics(toc_ids, spec_ids)
            self._print_coverage_report(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error analyzing coverage: {e}")
            raise
