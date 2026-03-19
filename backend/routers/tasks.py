from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from beanie import PydanticObjectId

from models import Task, TaskStatus, TaskPriority, User
from schemas import TaskCreate, TaskUpdate, TaskResponse, document_to_response
from database import get_current_user

router = APIRouter()


# ============================================================
# Helper: fetch a task by ID and verify ownership
#
# Reused by GET /tasks/{id}, PATCH /tasks/{id}, DELETE /tasks/{id}
# Raises 404 if not found, 403 if the task belongs to another user.
# ============================================================

async def get_task_or_raise(task_id: str, current_user: User) -> Task:
    try:
        object_id = PydanticObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task ID format")

    task = await Task.get(object_id)

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if task.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return task


# ============================================================
# GET /tasks
#
# Returns all tasks for the current user.
# Supports optional query parameters for filtering:
#   ?status=todo
#   ?priority=high
#   ?category_id=<id>
# ============================================================

@router.get("/", response_model=list[TaskResponse])
async def get_tasks(
    status_filter:   Optional[TaskStatus]   = Query(default=None, alias="status"),
    priority_filter: Optional[TaskPriority] = Query(default=None, alias="priority"),
    category_id:     Optional[str]          = Query(default=None),
    current_user:    User                   = Depends(get_current_user),
):
    # Always filter by the logged-in user's ID first
    query = Task.find(Task.user_id == str(current_user.id))

    # Chain additional filters only if provided
    if status_filter:
        query = query.find(Task.status == status_filter)
    if priority_filter:
        query = query.find(Task.priority == priority_filter)
    if category_id:
        query = query.find(Task.category_id == category_id)

    tasks = await query.sort(-Task.created_at).to_list()

    return [document_to_response(t, TaskResponse) for t in tasks]


# ============================================================
# POST /tasks
#
# Creates a new task for the current user.
# ============================================================

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    body:         TaskCreate = ...,
    current_user: User       = Depends(get_current_user),
):
    new_task = Task(
        user_id=str(current_user.id),
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        due_date=body.due_date,
        category_id=body.category_id,
    )
    await new_task.insert()

    return document_to_response(new_task, TaskResponse)


# ============================================================
# GET /tasks/{task_id}
#
# Returns a single task by ID.
# ============================================================

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id:      str,
    current_user: User = Depends(get_current_user),
):
    task = await get_task_or_raise(task_id, current_user)
    return document_to_response(task, TaskResponse)


# ============================================================
# PATCH /tasks/{task_id}
#
# Partial update — only fields provided in the request body
# are changed. Fields not included stay as they are.
#
# We use PATCH (not PUT) because PUT would require the client
# to send the entire task object even for a small change.
# ============================================================

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id:      str,
    body:         TaskUpdate,
    current_user: User = Depends(get_current_user),
):
    task = await get_task_or_raise(task_id, current_user)

    # Build a dict of only the fields that were actually provided
    # exclude_unset=True means fields the client did not send are excluded
    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update",
        )

    # Always refresh updated_at on any change
    update_data["updated_at"] = datetime.now(timezone.utc)

    # Apply the update to the MongoDB document
    await task.set(update_data)

    return document_to_response(task, TaskResponse)


# ============================================================
# DELETE /tasks/{task_id}
#
# Permanently deletes a task.
# Returns 204 No Content (no body) on success.
# ============================================================

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id:      str,
    current_user: User = Depends(get_current_user),
):
    task = await get_task_or_raise(task_id, current_user)
    await task.delete()