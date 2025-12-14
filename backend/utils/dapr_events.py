"""Dapr Pub/Sub event publishing utilities.

This module provides a resilient way to publish events to Dapr pub/sub.
If Dapr is not available, events are logged but CRUD operations continue.
"""

import logging
from typing import Any, Dict, Optional
import httpx
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Dapr sidecar HTTP endpoint
DAPR_HTTP_URL = f"http://localhost:{settings.dapr_http_port}"
PUBSUB_NAME = "pubsub"

# Event topic names
class EventTopics:
    """Event topic constants."""
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    TASK_COMPLETED = "task.completed"
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    MEMBER_ADDED = "project.member.added"
    MEMBER_REMOVED = "project.member.removed"


async def publish_event(
    topic: str,
    data: Dict[str, Any],
    metadata: Optional[Dict[str, str]] = None
) -> bool:
    """
    Publish an event to Dapr pub/sub.

    Args:
        topic: The topic name (e.g., 'task.created')
        data: The event payload
        metadata: Optional metadata for the event

    Returns:
        True if event was published successfully, False otherwise
    """
    url = f"{DAPR_HTTP_URL}/v1.0/publish/{PUBSUB_NAME}/{topic}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json=data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in (200, 204):
                logger.info(f"Event published to {topic}: {data.get('id', 'unknown')}")
                return True
            else:
                logger.warning(
                    f"Failed to publish event to {topic}: {response.status_code} - {response.text}"
                )
                return False

    except httpx.ConnectError:
        logger.warning(f"Dapr sidecar not available. Event not published to {topic}")
        return False
    except httpx.TimeoutException:
        logger.warning(f"Timeout publishing event to {topic}")
        return False
    except Exception as e:
        logger.error(f"Error publishing event to {topic}: {str(e)}")
        return False


async def check_dapr_health() -> bool:
    """
    Check if Dapr sidecar is healthy.

    Returns:
        True if Dapr is healthy, False otherwise
    """
    url = f"{DAPR_HTTP_URL}/v1.0/healthz"

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(url)
            return response.status_code == 200
    except Exception:
        return False


# Convenience functions for specific event types

async def publish_task_created(
    task_id: int,
    project_id: int,
    title: str,
    created_by: str,
    status: str = "todo"
) -> bool:
    """Publish task.created event."""
    return await publish_event(
        EventTopics.TASK_CREATED,
        {
            "id": task_id,
            "project_id": project_id,
            "title": title,
            "created_by": created_by,
            "status": status,
            "event_type": "task.created"
        }
    )


async def publish_task_updated(
    task_id: int,
    project_id: int,
    updated_by: str,
    changes: Dict[str, Any]
) -> bool:
    """Publish task.updated event."""
    return await publish_event(
        EventTopics.TASK_UPDATED,
        {
            "id": task_id,
            "project_id": project_id,
            "updated_by": updated_by,
            "changes": changes,
            "event_type": "task.updated"
        }
    )


async def publish_task_deleted(
    task_id: int,
    project_id: int,
    deleted_by: str,
    title: str
) -> bool:
    """Publish task.deleted event."""
    return await publish_event(
        EventTopics.TASK_DELETED,
        {
            "id": task_id,
            "project_id": project_id,
            "deleted_by": deleted_by,
            "title": title,
            "event_type": "task.deleted"
        }
    )


async def publish_task_completed(
    task_id: int,
    project_id: int,
    completed_by: str,
    title: str
) -> bool:
    """Publish task.completed event."""
    return await publish_event(
        EventTopics.TASK_COMPLETED,
        {
            "id": task_id,
            "project_id": project_id,
            "completed_by": completed_by,
            "title": title,
            "event_type": "task.completed"
        }
    )


async def publish_project_created(
    project_id: int,
    name: str,
    owner_id: str
) -> bool:
    """Publish project.created event."""
    return await publish_event(
        EventTopics.PROJECT_CREATED,
        {
            "id": project_id,
            "name": name,
            "owner_id": owner_id,
            "event_type": "project.created"
        }
    )


async def publish_project_updated(
    project_id: int,
    updated_by: str,
    changes: Dict[str, Any]
) -> bool:
    """Publish project.updated event."""
    return await publish_event(
        EventTopics.PROJECT_UPDATED,
        {
            "id": project_id,
            "updated_by": updated_by,
            "changes": changes,
            "event_type": "project.updated"
        }
    )


async def publish_project_deleted(
    project_id: int,
    deleted_by: str,
    name: str
) -> bool:
    """Publish project.deleted event."""
    return await publish_event(
        EventTopics.PROJECT_DELETED,
        {
            "id": project_id,
            "deleted_by": deleted_by,
            "name": name,
            "event_type": "project.deleted"
        }
    )


async def publish_member_added(
    project_id: int,
    user_id: str,
    role: str,
    added_by: str
) -> bool:
    """Publish project.member.added event."""
    return await publish_event(
        EventTopics.MEMBER_ADDED,
        {
            "project_id": project_id,
            "user_id": user_id,
            "role": role,
            "added_by": added_by,
            "event_type": "project.member.added"
        }
    )


async def publish_member_removed(
    project_id: int,
    user_id: str,
    removed_by: str
) -> bool:
    """Publish project.member.removed event."""
    return await publish_event(
        EventTopics.MEMBER_REMOVED,
        {
            "project_id": project_id,
            "user_id": user_id,
            "removed_by": removed_by,
            "event_type": "project.member.removed"
        }
    )
