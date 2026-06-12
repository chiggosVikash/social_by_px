from typing import Dict, Type
from services.publishers.base import SocialPublisher
from services.publishers.instagram import InstagramPublisher
from services.publishers.facebook import FacebookPublisher

class PublisherFactory:
    _registry: Dict[str, Type[SocialPublisher]] = {
        "INSTAGRAM": InstagramPublisher,
        "FACEBOOK": FacebookPublisher
    }
    
    @classmethod
    def register(cls, platform: str, publisher_class: Type[SocialPublisher]):
        cls._registry[platform.upper()] = publisher_class

    @classmethod
    def get_publisher(cls, platform: str) -> SocialPublisher:
        platform = platform.upper()
        publisher_class = cls._registry.get(platform)
        if not publisher_class:
            raise ValueError(f"Unsupported social platform: {platform}")
        return publisher_class()
