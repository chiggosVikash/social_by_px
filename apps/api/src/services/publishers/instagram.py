import httpx
from typing import List
from services.publishers.base import SocialPublisher

META_GRAPH_API_URL = "https://graph.facebook.com/v19.0"

class InstagramPublisher(SocialPublisher):
    async def publish(self, account_id: str, access_token: str, image_urls: List[str], caption: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                container_ids = []
                
                # 1. Create item containers for each image
                for url in image_urls:
                    resp = await client.post(
                        f"{META_GRAPH_API_URL}/{account_id}/media",
                        params={
                            "image_url": url,
                            "is_carousel_item": "true",
                            "access_token": access_token
                        }
                    )
                    resp.raise_for_status()
                    container_ids.append(resp.json()["id"])
                    
                # 2. Create the carousel container
                resp = await client.post(
                    f"{META_GRAPH_API_URL}/{account_id}/media",
                    params={
                        "media_type": "CAROUSEL",
                        "children": ",".join(container_ids),
                        "caption": caption,
                        "access_token": access_token
                    }
                )
                resp.raise_for_status()
                creation_id = resp.json()["id"]
                
                # 3. Publish the carousel container
                publish_resp = await client.post(
                    f"{META_GRAPH_API_URL}/{account_id}/media_publish",
                    params={
                        "creation_id": creation_id,
                        "access_token": access_token
                    }
                )
                publish_resp.raise_for_status()
                return publish_resp.json()["id"]
            except httpx.HTTPStatusError as e:
                print(f"Meta Graph API error on Instagram Publish: {e.response.text}")
                raise
