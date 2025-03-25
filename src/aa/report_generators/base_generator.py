from abc import ABC, abstractmethod

class BaseReportGenerator(ABC):
    """Abstract base class for report generators."""
    
    @abstractmethod
    def generate(self, analysis_results, config: dict):
        """Generate reports from analysis results."""
        pass