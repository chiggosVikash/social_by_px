from abc import ABC, abstractmethod
from typing import List, Dict

class SearchService(ABC):
    """
    Strategy pattern interface for web search providers.
    """
    @abstractmethod
    def search(self, query: str, max_results: int = 3, **kwargs) -> List[Dict[str, str]]:
        """
        Executes a search query and returns a list of dictionaries 
        containing 'title', 'url', 'source', 'published_date', and 'summary'.
        """
        pass
