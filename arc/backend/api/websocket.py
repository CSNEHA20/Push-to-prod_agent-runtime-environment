import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import Any, Union
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

try:
    from db.redis_client import get_redis
except ImportError:
    from arc.backend.db.redis_client import get_redis

logger = logging.getLogger("arc.api.websocket")

router = APIRouter(tags=["websocket"])


async def publish_event(
    session_id: Union[uuid.UUID, str],
    event_type: str,
    data: Any,
) -> bool:
    """
    Helper function to publish a JSON event to the Redis pub/sub channel for a session.
    Channel name format: session:{session_id}
    """
    channel_name = f"session:{session_id}"
    payload = {
        "event_type": event_type,
        "session_id": str(session_id),
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        redis = await get_redis()
        if redis:
            await redis.publish(channel_name, json.dumps(payload))
            logger.debug(f"Published event '{event_type}' to Redis channel '{channel_name}'")
            return True
    except Exception as e:
        logger.error(f"Failed to publish event to Redis channel '{channel_name}': {e}")
    return False


@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time live streaming of session trace updates via Redis pub/sub.
    """
    await websocket.accept()
    logger.info(f"WebSocket connection accepted for session: {session_id}")

    pubsub = None
    channel_name = f"session:{session_id}"

    try:
        redis = await get_redis()
        if redis:
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel_name)
            logger.info(f"Subscribed to Redis channel '{channel_name}'")

            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, str):
                        try:
                            parsed_json = json.loads(raw_data)
                            await websocket.send_json(parsed_json)
                        except json.JSONDecodeError:
                            await websocket.send_text(raw_data)
                    else:
                        await websocket.send_json(raw_data)

                await asyncio.sleep(0.05)
        else:
            await websocket.send_json({
                "type": "error",
                "message": "Redis connection unavailable for live streaming.",
            })
            await websocket.close()
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected gracefully for session: {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket handler for session {session_id}: {e}", exc_info=True)
    finally:
        if pubsub:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
                logger.info(f"Unsubscribed and closed Redis pubsub for session: {session_id}")
            except Exception as e:
                logger.warning(f"Error closing pubsub for session {session_id}: {e}")
