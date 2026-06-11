from abc import ABC, abstractmethod
from typing import List

class SocialPublisher(ABC):
    """
    Strategy pattern interface for social media publishers.
    """
    @abstractmethod
    async def publish(self, account_id: str, access_token: str, image_urls: List[str], caption: str) -> str:
        """
        Publishes a carousel or sequence of images to a social network.
        Returns the ID or URL of the published post.
        """
        pass
