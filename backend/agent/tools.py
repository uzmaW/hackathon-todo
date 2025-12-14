"""MCP-style tools for task management.

These tools are designed to be called by the AI agent to manage tasks.
Each tool follows the MCP pattern with clear inputs and outputs.
"""

from datetime import datetime
from typing import Optional, List, Literal
from sqlmodel import Session, select
from pydantic import BaseModel

from models.task import Task, TaskStatus
from models.project import Project
from models.permission import Permission
from utils.permissions import check_user_permission


class TaskResult(BaseModel):
    """Result of a task operation."""
    success: bool
    task_id: Optional[int] = None
    status: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None


class TaskListResult(BaseModel):
    """Result of listing tasks."""
    success: bool
    tasks: List[dict] = []
    message: Optional[str] = None


def add_task(
    session: Session,
    user_id: str,
    project_id: int,
    title: str,
    description: Optional[str] = None,
    priority: str = "medium",
    due_date: Optional[datetime] = None
) -> TaskResult:
    """
    Add a new task to a project.

    Args:
        session: Database session
        user_id: ID of the user creating the task
        project_id: ID of the project to add the task to
        title: Title of the task
        description: Optional description
        priority: Task priority (low, medium, high)
        due_date: Optional due date

    Returns:
        TaskResult with the created task info
    """
    # Check user has permission to create tasks (member or admin)
    if not check_user_permission(session, user_id, project_id, "member"):
        return TaskResult(
            success=False,
            message="You don't have permission to create tasks in this project"
        )

    # Get max position for ordering
    stmt = select(Task).where(
        Task.project_id == project_id,
        Task.status == TaskStatus.TODO
    ).order_by(Task.position.desc())
    last_task = session.exec(stmt).first()
    new_position = (last_task.position + 1) if last_task else 0

    # Create task
    task = Task(
        project_id=project_id,
        title=title,
        description=description,
        status=TaskStatus.TODO,
        priority=priority,
        position=new_position,
        due_date=due_date,
        created_by=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    return TaskResult(
        success=True,
        task_id=task.id,
        status=task.status.value,
        title=task.title,
        message=f"Task '{title}' created successfully"
    )


def list_tasks(
    session: Session,
    user_id: str,
    project_id: int,
    status: Optional[str] = None
) -> TaskListResult:
    """
    List tasks in a project.

    Args:
        session: Database session
        user_id: ID of the user requesting tasks
        project_id: ID of the project
        status: Optional status filter (todo, in_progress, completed)

    Returns:
        TaskListResult with list of tasks
    """
    # Check user has permission to view tasks
    if not check_user_permission(session, user_id, project_id, "viewer"):
        return TaskListResult(
            success=False,
            message="You don't have permission to view tasks in this project"
        )

    query = select(Task).where(Task.project_id == project_id)

    if status:
        try:
            task_status = TaskStatus(status)
            query = query.where(Task.status == task_status)
        except ValueError:
            return TaskListResult(
                success=False,
                message=f"Invalid status: {status}. Use 'todo', 'in_progress', or 'completed'"
            )

    query = query.order_by(Task.position)
    tasks = session.exec(query).all()

    return TaskListResult(
        success=True,
        tasks=[
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status.value,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "assigned_to": t.assigned_to
            }
            for t in tasks
        ],
        message=f"Found {len(tasks)} tasks"
    )


def complete_task(
    session: Session,
    user_id: str,
    task_id: int
) -> TaskResult:
    """
    Mark a task as completed.

    Args:
        session: Database session
        user_id: ID of the user completing the task
        task_id: ID of the task to complete

    Returns:
        TaskResult with the updated task info
    """
    task = session.get(Task, task_id)
    if not task:
        return TaskResult(
            success=False,
            message=f"Task with ID {task_id} not found"
        )

    # Check user has permission
    if not check_user_permission(session, user_id, task.project_id, "member"):
        return TaskResult(
            success=False,
            message="You don't have permission to update this task"
        )

    task.status = TaskStatus.COMPLETED
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)

    return TaskResult(
        success=True,
        task_id=task.id,
        status=task.status.value,
        title=task.title,
        message=f"Task '{task.title}' marked as completed"
    )


def update_task(
    session: Session,
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[datetime] = None
) -> TaskResult:
    """
    Update a task's properties.

    Args:
        session: Database session
        user_id: ID of the user updating the task
        task_id: ID of the task to update
        title: New title (optional)
        description: New description (optional)
        status: New status (optional)
        priority: New priority (optional)
        due_date: New due date (optional)

    Returns:
        TaskResult with the updated task info
    """
    task = session.get(Task, task_id)
    if not task:
        return TaskResult(
            success=False,
            message=f"Task with ID {task_id} not found"
        )

    # Check user has permission
    if not check_user_permission(session, user_id, task.project_id, "member"):
        return TaskResult(
            success=False,
            message="You don't have permission to update this task"
        )

    # Update fields if provided
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        try:
            task.status = TaskStatus(status)
        except ValueError:
            return TaskResult(
                success=False,
                message=f"Invalid status: {status}"
            )
    if priority is not None:
        task.priority = priority
    if due_date is not None:
        task.due_date = due_date

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)

    return TaskResult(
        success=True,
        task_id=task.id,
        status=task.status.value,
        title=task.title,
        message=f"Task '{task.title}' updated successfully"
    )


def delete_task(
    session: Session,
    user_id: str,
    task_id: int
) -> TaskResult:
    """
    Delete a task.

    Args:
        session: Database session
        user_id: ID of the user deleting the task
        task_id: ID of the task to delete

    Returns:
        TaskResult confirming deletion
    """
    task = session.get(Task, task_id)
    if not task:
        return TaskResult(
            success=False,
            message=f"Task with ID {task_id} not found"
        )

    # Check user has admin permission (only admins can delete)
    if not check_user_permission(session, user_id, task.project_id, "admin"):
        return TaskResult(
            success=False,
            message="Only project admins can delete tasks"
        )

    task_title = task.title
    task_id_saved = task.id

    session.delete(task)
    session.commit()

    return TaskResult(
        success=True,
        task_id=task_id_saved,
        title=task_title,
        message=f"Task '{task_title}' deleted successfully"
    )


def get_user_projects(
    session: Session,
    user_id: str
) -> List[dict]:
    """
    Get all projects a user has access to.

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        List of projects with user's role
    """
    stmt = select(Permission, Project).join(
        Project, Permission.project_id == Project.id
    ).where(Permission.user_id == user_id)

    results = session.exec(stmt).all()

    return [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "role": permission.role
        }
        for permission, project in results
    ]
