import httpx
from typing import List
from services.publishers.base import SocialPublisher
from core.config import get_settings

class FacebookPublisher(SocialPublisher):
    async def publish(self, account_id: str, access_token: str, image_urls: List[str], caption: str) -> str:
        settings = get_settings()
        meta_url = settings.META_GRAPH_API_URL
        
        async with httpx.AsyncClient() as client:
            try:
                attached_media = []
                
                # 1. Upload photos (unpublished)
                for url in image_urls:
                    resp = await client.post(
                        f"{meta_url}/{account_id}/photos",
                        params={
                            "url": url,
                            "published": "false",
                            "access_token": access_token
                        }
                    )
                    resp.raise_for_status()
                    attached_media.append({"media_fbid": resp.json()["id"]})
                    
                # 2. Publish post with attached media
                publish_resp = await client.post(
                    f"{meta_url}/{account_id}/feed",
                    json={
                        "message": caption,
                        "attached_media": attached_media,
                        "access_token": access_token
                    }
                )
                publish_resp.raise_for_status()
                return publish_resp.json()["id"]
            except httpx.HTTPStatusError as e:
                print(f"Meta Graph API error on Facebook Publish: {e.response.text}")
                raise
