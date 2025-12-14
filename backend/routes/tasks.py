"""Task CRUD routes."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session, select, func

from db import get_session
from auth import get_current_user
from models.user import User
from models.task import Task, TaskCreate, TaskRead, TaskUpdate, TaskStatus
from models.permission import Permission
from utils.permissions import check_user_permission
from utils.dapr_events import (
    publish_task_created,
    publish_task_updated,
    publish_task_deleted,
    publish_task_completed
)

router = APIRouter()


@router.get("", response_model=List[TaskRead])
async def list_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filter by status"),
    sort: Optional[str] = Query("position", description="Sort by: position, created, title, due_date"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    List tasks the user has access to.

    - **project_id**: Filter by specific project
    - **status**: Filter by status (todo, in_progress, completed) or 'all'
    - **sort**: Sort by position, created, title, or due_date
    """
    # Get all project IDs user has access to
    stmt = select(Permission.project_id).where(Permission.user_id == current_user.id)
    accessible_projects = [p for p in session.exec(stmt).all()]

    if not accessible_projects:
        return []

    # Build query
    query = select(Task)

    if project_id:
        # Check user has access to this specific project
        if project_id not in accessible_projects:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this project"
            )
        query = query.where(Task.project_id == project_id)
    else:
        query = query.where(Task.project_id.in_(accessible_projects))

    # Status filter
    if status_filter:
        query = query.where(Task.status == status_filter)

    # Sorting
    if sort == "created":
        query = query.order_by(Task.created_at.desc())
    elif sort == "title":
        query = query.order_by(Task.title)
    elif sort == "due_date":
        query = query.order_by(Task.due_date.asc().nullslast())
    else:  # default: position
        query = query.order_by(Task.position.asc())

    tasks = session.exec(query).all()

    return [
        TaskRead(
            id=t.id,
            title=t.title,
            description=t.description,
            status=t.status,
            due_date=t.due_date,
            project_id=t.project_id,
            creator_id=t.creator_id,
            assigned_to=t.assigned_to,
            completed=t.completed,
            position=t.position,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in tasks
    ]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new task.

    User must be a member (not viewer) of the project.

    - **title**: Task title (1-200 characters)
    - **description**: Optional task description
    - **project_id**: Project to create task in
    - **due_date**: Optional due date
    - **assigned_to**: Optional user ID to assign to
    """
    # Check permission (member+ required)
    if not check_user_permission(session, current_user.id, task_data.project_id, "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need member access to create tasks in this project"
        )

    # Calculate position (count of existing tasks in project)
    count_stmt = select(func.count()).select_from(Task).where(Task.project_id == task_data.project_id)
    position = session.exec(count_stmt).one()

    # Create task
    task = Task(
        title=task_data.title,
        description=task_data.description,
        project_id=task_data.project_id,
        creator_id=current_user.id,
        assigned_to=task_data.assigned_to,
        due_date=task_data.due_date,
        status=TaskStatus.TODO,
        completed=False,
        position=position,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.created event via Dapr (non-blocking)
    background_tasks.add_task(
        publish_task_created,
        task_id=task.id,
        project_id=task.project_id,
        title=task.title,
        created_by=current_user.id,
        status=task.status.value
    )

    return TaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        project_id=task.project_id,
        creator_id=task.creator_id,
        assigned_to=task.assigned_to,
        completed=task.completed,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single task by ID.

    User must have viewer+ access to the task's project.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check permission
    if not check_user_permission(session, current_user.id, task.project_id, "viewer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this task"
        )

    return TaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        project_id=task.project_id,
        creator_id=task.creator_id,
        assigned_to=task.assigned_to,
        completed=task.completed,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task.

    User must be a member (not viewer) of the task's project.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check permission
    if not check_user_permission(session, current_user.id, task.project_id, "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need member access to update tasks"
        )

    # Update fields
    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    # Sync completed flag with status
    if task_data.status == TaskStatus.COMPLETED:
        task.completed = True
    elif task_data.completed is not None:
        if task_data.completed and task.status != TaskStatus.COMPLETED:
            task.status = TaskStatus.COMPLETED

    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    # Publish task.updated event via Dapr (non-blocking)
    changes = task_data.model_dump(exclude_unset=True)
    if changes:
        # Check if task was completed
        if task.status == TaskStatus.COMPLETED and "status" in changes:
            background_tasks.add_task(
                publish_task_completed,
                task_id=task.id,
                project_id=task.project_id,
                completed_by=current_user.id,
                title=task.title
            )
        else:
            background_tasks.add_task(
                publish_task_updated,
                task_id=task.id,
                project_id=task.project_id,
                updated_by=current_user.id,
                changes=changes
            )

    return TaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        project_id=task.project_id,
        creator_id=task.creator_id,
        assigned_to=task.assigned_to,
        completed=task.completed,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a task.

    Only project admins can delete tasks.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check admin permission
    if not check_user_permission(session, current_user.id, task.project_id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project admins can delete tasks"
        )

    # Store info before deletion for event
    deleted_task_id = task.id
    deleted_project_id = task.project_id
    deleted_title = task.title

    session.delete(task)
    session.commit()

    # Publish task.deleted event via Dapr (non-blocking)
    background_tasks.add_task(
        publish_task_deleted,
        task_id=deleted_task_id,
        project_id=deleted_project_id,
        deleted_by=current_user.id,
        title=deleted_title
    )

    return {"task_id": task_id, "status": "deleted"}


@router.put("/{task_id}/position")
async def update_task_position(
    task_id: int,
    new_position: int,
    new_status: Optional[TaskStatus] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update a task's position (for drag-and-drop).

    Optionally change status when moving between columns.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Check permission
    if not check_user_permission(session, current_user.id, task.project_id, "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You need member access to reorder tasks"
        )

    old_position = task.position

    # Update positions of other tasks
    if new_position < old_position:
        # Moving up: shift tasks down
        stmt = select(Task).where(
            Task.project_id == task.project_id,
            Task.position >= new_position,
            Task.position < old_position,
            Task.id != task_id
        )
        affected_tasks = session.exec(stmt).all()
        for t in affected_tasks:
            t.position += 1
            session.add(t)
    elif new_position > old_position:
        # Moving down: shift tasks up
        stmt = select(Task).where(
            Task.project_id == task.project_id,
            Task.position > old_position,
            Task.position <= new_position,
            Task.id != task_id
        )
        affected_tasks = session.exec(stmt).all()
        for t in affected_tasks:
            t.position -= 1
            session.add(t)

    # Update the moved task
    task.position = new_position
    if new_status:
        task.status = new_status
        task.completed = (new_status == TaskStatus.COMPLETED)
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    return TaskRead(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        due_date=task.due_date,
        project_id=task.project_id,
        creator_id=task.creator_id,
        assigned_to=task.assigned_to,
        completed=task.completed,
        position=task.position,
        created_at=task.created_at,
        updated_at=task.updated_at
    )
