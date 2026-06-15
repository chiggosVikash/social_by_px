from typing import List, Dict
from tavily import TavilyClient
from services.search.base import SearchService

class TavilySearchService(SearchService):
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int = 3, **kwargs) -> List[Dict[str, str]]:
        articles = []
        try:
            response = self.client.search(query=query, search_depth="advanced", max_results=max_results, **kwargs)
            for res in response.get("results", []):
                articles.append({
                    "title": res.get("title", ""),
                    "url": res.get("url", ""),
                    "source": res.get("source", "Web"),
                    "published_date": res.get("published_date", ""),
                    "summary": res.get("content", "")
                })
        except Exception as e:
            print(f"Tavily search failed for query '{query}': {str(e)}")
        return articles
