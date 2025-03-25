from abc import ABC, abstractmethod
import logging

logging.basicConfig(level=logging.DEBUG)
class BaseDataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load(self, config: dict):
        """Load data from configured source."""
        pass
