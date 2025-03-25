from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    """Abstract base class for data analyzers."""
    
    @abstractmethod
    def analyze(self, data, config: dict):
        """Perform analysis on input data."""
        pass