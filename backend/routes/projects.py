"""Project CRUD routes."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session, select

from db import get_session
from auth import get_current_user
from models.user import User
from models.project import Project, ProjectCreate, ProjectRead, ProjectUpdate
from models.permission import Permission, RoleEnum
from models.task import Task
from utils.permissions import check_user_permission, get_user_role
from utils.dapr_events import (
    publish_project_created,
    publish_project_updated,
    publish_project_deleted,
    publish_member_added,
    publish_member_removed
)

router = APIRouter()


class ProjectWithRole(ProjectRead):
    """Project response with user's role."""
    role: RoleEnum


@router.get("", response_model=List[ProjectWithRole])
async def list_projects(
    role: Optional[RoleEnum] = Query(None, description="Filter by user role"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List all projects the user belongs to.

    - **role**: Optional filter by user's role in project (admin, member, viewer)
    """
    # Get all project IDs user has access to
    stmt = select(Permission).where(Permission.user_id == current_user.id)
    if role:
        stmt = stmt.where(Permission.role == role)

    permissions = session.exec(stmt).all()
    project_ids = [p.project_id for p in permissions]
    role_map = {p.project_id: p.role for p in permissions}

    if not project_ids:
        return []

    # Get projects
    stmt = select(Project).where(Project.id.in_(project_ids)).order_by(Project.created_at.desc())
    projects = session.exec(stmt).all()

    return [
        ProjectWithRole(
            id=p.id,
            name=p.name,
            description=p.description,
            owner_id=p.owner_id,
            created_at=p.created_at,
            updated_at=p.updated_at,
            role=role_map[p.id]
        )
        for p in projects
    ]


@router.post("", response_model=ProjectWithRole, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project.

    The creating user automatically becomes the project admin.

    - **name**: Project name (1-100 characters)
    - **description**: Optional project description (max 500 characters)
    """
    # Create project
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    # Create admin permission for creator
    permission = Permission(
        user_id=current_user.id,
        project_id=project.id,
        role=RoleEnum.ADMIN,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(permission)
    session.commit()

    # Publish project.created event via Dapr (non-blocking)
    background_tasks.add_task(
        publish_project_created,
        project_id=project.id,
        name=project.name,
        owner_id=current_user.id
    )

    return ProjectWithRole(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        role=RoleEnum.ADMIN
    )


@router.get("/{project_id}", response_model=ProjectWithRole)
async def get_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single project by ID.

    User must be a member of the project.
    """
    # Check permission
    role = get_user_role(session, current_user.id, project_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this project"
        )

    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return ProjectWithRole(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        role=role
    )


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a project.

    Only project admins or managers can update.

    - **name**: New project name (optional)
    - **description**: New project description (optional)
    """
    # Check permission (admin or member with elevated rights)
    if not check_user_permission(session, current_user.id, project_id, "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project admins or managers can update projects"
        )

    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    project.updated_at = datetime.utcnow()

    session.add(project)
    session.commit()
    session.refresh(project)

    # Publish project.updated event via Dapr (non-blocking)
    changes = project_data.model_dump(exclude_unset=True)
    if changes:
        background_tasks.add_task(
            publish_project_updated,
            project_id=project.id,
            updated_by=current_user.id,
            changes=changes
        )

    return ProjectRead(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project.

    Only project admins can delete. This also deletes all associated tasks and permissions.
    """
    # Check admin permission
    if not check_user_permission(session, current_user.id, project_id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project admins can delete projects"
        )

    # Get project
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Store info before deletion for event
    deleted_project_id = project.id
    deleted_project_name = project.name

    # Delete all tasks in project
    stmt = select(Task).where(Task.project_id == project_id)
    tasks = session.exec(stmt).all()
    for task in tasks:
        session.delete(task)

    # Delete all permissions for project
    stmt = select(Permission).where(Permission.project_id == project_id)
    permissions = session.exec(stmt).all()
    for permission in permissions:
        session.delete(permission)

    # Delete project
    session.delete(project)
    session.commit()

    # Publish project.deleted event via Dapr (non-blocking)
    background_tasks.add_task(
        publish_project_deleted,
        project_id=deleted_project_id,
        deleted_by=current_user.id,
        name=deleted_project_name
    )

    return {"project_id": project_id, "status": "deleted"}


# Member management endpoints

@router.post("/{project_id}/members")
async def add_member(
    project_id: int,
    user_id: str,
    role: RoleEnum = RoleEnum.MEMBER,
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Add a member to a project. Only admins can add members."""
    # Check admin permission
    if not check_user_permission(session, current_user.id, project_id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project admins can add members"
        )

    # Check if user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already a member
    existing = session.exec(
        select(Permission).where(
            Permission.user_id == user_id,
            Permission.project_id == project_id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this project"
        )

    # Add permission
    permission = Permission(
        user_id=user_id,
        project_id=project_id,
        role=role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(permission)
    session.commit()

    # Publish member.added event via Dapr (non-blocking)
    if background_tasks:
        background_tasks.add_task(
            publish_member_added,
            project_id=project_id,
            user_id=user_id,
            role=role.value,
            added_by=current_user.id
        )

    return {"message": f"User {user_id} added as {role.value}"}


@router.delete("/{project_id}/members/{user_id}")
async def remove_member(
    project_id: int,
    user_id: str,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a project. Only admins can remove members."""
    # Check admin permission
    if not check_user_permission(session, current_user.id, project_id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project admins can remove members"
        )

    # Can't remove yourself if you're the owner
    project = session.get(Project, project_id)
    if project and project.owner_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the project owner"
        )

    # Find and delete permission
    permission = session.exec(
        select(Permission).where(
            Permission.user_id == user_id,
            Permission.project_id == project_id
        )
    ).first()

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project"
        )

    session.delete(permission)
    session.commit()

    # Publish member.removed event via Dapr (non-blocking)
    background_tasks.add_task(
        publish_member_removed,
        project_id=project_id,
        user_id=user_id,
        removed_by=current_user.id
    )

    return {"message": f"User {user_id} removed from project"}
