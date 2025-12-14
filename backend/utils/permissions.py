"""Permission checking utilities."""

from typing import Optional
from sqlmodel import Session, select
from models.permission import Permission, RoleEnum


def get_user_role(session: Session, user_id: str, project_id: int) -> Optional[RoleEnum]:
    """Get the user's role in a project."""
    stmt = select(Permission).where(
        Permission.user_id == user_id,
        Permission.project_id == project_id
    )
    permission = session.exec(stmt).first()
    return permission.role if permission else None


def check_user_permission(
    session: Session,
    user_id: str,
    project_id: int,
    required_role: str
) -> bool:
    """
    Check if user has the required role or higher in a project.

    Role hierarchy: admin > member > viewer

    Args:
        session: Database session
        user_id: User ID to check
        project_id: Project ID to check
        required_role: Minimum required role ('admin', 'member', 'viewer')

    Returns:
        True if user has required permission, False otherwise
    """
    role = get_user_role(session, user_id, project_id)

    if role is None:
        return False

    # Role hierarchy
    role_hierarchy = {
        RoleEnum.ADMIN: 3,
        RoleEnum.MEMBER: 2,
        RoleEnum.VIEWER: 1
    }

    required_level = role_hierarchy.get(RoleEnum(required_role), 0)
    user_level = role_hierarchy.get(role, 0)

    return user_level >= required_level


def require_permission(required_role: str):
    """
    Decorator factory to require a minimum role for an endpoint.
    Use with FastAPI dependencies.
    """
    from functools import wraps
    from fastapi import HTTPException, status

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, project_id: int, session: Session, current_user, **kwargs):
            if not check_user_permission(session, current_user.id, project_id, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_role} role or higher"
                )
            return await func(*args, project_id=project_id, session=session, current_user=current_user, **kwargs)
        return wrapper
    return decorator
