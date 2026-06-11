from src.services.publishers.base import SocialPublisher
from src.services.publishers.instagram import InstagramPublisher
from src.services.publishers.facebook import FacebookPublisher

class PublisherFactory:
    @staticmethod
    def get_publisher(platform: str) -> SocialPublisher:
        platform = platform.upper()
        if platform == "INSTAGRAM":
            return InstagramPublisher()
        elif platform == "FACEBOOK":
            return FacebookPublisher()
        else:
            raise ValueError(f"Unsupported social platform: {platform}")
