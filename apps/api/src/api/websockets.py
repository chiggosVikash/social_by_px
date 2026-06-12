from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import redis.asyncio as redis
from core.config import get_settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/projects/{project_id}/progress")
async def project_progress_ws(websocket: WebSocket, project_id: int):
    await websocket.accept()
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    
    channel_name = f"workflow:progress:{project_id}"
    await pubsub.subscribe(channel_name)
    logger.info(f"WebSocket client connected and subscribed to {channel_name}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    payload = data.decode("utf-8")
                else:
                    payload = str(data)
                
                await websocket.send_text(payload)
                
            # Optional: Allow the client to ping to keep the connection alive
            # But we don't necessarily need to block on client receive, 
            # so we'll just check if the socket is still open via asyncio.sleep
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from {channel_name}")
    except Exception as e:
        logger.error(f"WebSocket error on {channel_name}: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await redis_client.aclose()
