from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from models import TaskStatus, TaskPriority


# ============================================================
# Why separate schemas from models?
#
# models.py  → defines how data is STORED in MongoDB (Beanie Document)
# schemas.py → defines what the API ACCEPTS and RETURNS (Pydantic BaseModel)
#
# This separation is important because:
#   1. We never return hashed_password in any response
#   2. The client sends plain password, DB stores hashed version
#   3. MongoDB's internal "_id" field needs to be exposed as "id" string
#   4. Some fields (created_at, id) are set by the server, not the client
# ============================================================


# ============================================================
# USER schemas
# ============================================================

class UserCreate(BaseModel):
    """
    Schema for POST /auth/register request body.
    Client sends username, email, and plain password.
    """
    username: str = Field(min_length=3, max_length=50)
    email:    EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    """
    Schema for POST /auth/login request body.
    """
    email:    EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Schema for user data returned in responses.
    Notice: no password field — never expose it.
    """
    id:         str
    username:   str
    email:      str
    created_at: datetime

    class Config:
        # Allow Pydantic to read data from object attributes
        # (needed when converting a Beanie Document to this schema)
        from_attributes = True


class TokenResponse(BaseModel):
    """
    Schema returned after successful login.
    access_token is a JWT string the client stores and sends
    in the Authorization header for protected routes.
    """
    access_token: str
    token_type:   str = "bearer"


# ============================================================
# CATEGORY schemas
# ============================================================

class CategoryCreate(BaseModel):
    """
    Schema for POST /categories request body.
    user_id is NOT here — it comes from the JWT token, not the client.
    """
    name:  str = Field(min_length=1, max_length=100)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryUpdate(BaseModel):
    """
    Schema for PATCH /categories/{id} request body.
    All fields are Optional — client only sends what they want to change.
    """
    name:  Optional[str]  = Field(default=None, min_length=1, max_length=100)
    color: Optional[str]  = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryResponse(BaseModel):
    """
    Schema for category data returned in responses.
    """
    id:         str
    user_id:    str
    name:       str
    color:      str
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# TASK schemas
# ============================================================

class TaskCreate(BaseModel):
    """
    Schema for POST /tasks request body.
    user_id comes from JWT — not from client input.
    """
    title:       str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    status:      TaskStatus   = TaskStatus.todo
    priority:    TaskPriority = TaskPriority.medium
    due_date:    Optional[datetime] = None
    category_id: Optional[str] = None


class TaskUpdate(BaseModel):
    """
    Schema for PATCH /tasks/{id} request body.
    All fields Optional — partial update pattern.
    When updated_at should be refreshed, the route handler sets it.
    """
    title:       Optional[str]         = Field(default=None, min_length=1, max_length=200)
    description: Optional[str]         = None
    status:      Optional[TaskStatus]  = None
    priority:    Optional[TaskPriority]= None
    due_date:    Optional[datetime]    = None
    category_id: Optional[str]         = None


class TaskResponse(BaseModel):
    """
    Schema for task data returned in responses.
    Includes resolved fields (id as string, both timestamps).
    """
    id:          str
    user_id:     str
    category_id: Optional[str]
    title:       str
    description: Optional[str]
    status:      TaskStatus
    priority:    TaskPriority
    due_date:    Optional[datetime]
    created_at:  datetime
    updated_at:  datetime

    class Config:
        from_attributes = True


# ============================================================
# Utility: convert a Beanie Document to a response schema
#
# Beanie stores the primary key as "_id" (BSON ObjectId).
# We expose it as a plain string "id" in API responses.
# This helper handles that conversion for any document type.
#
# Usage in a route:
#   task = await Task.get(task_id)
#   return document_to_response(task, TaskResponse)
# ============================================================

def document_to_response(document, response_schema: type) -> dict:
    data = document.model_dump()
    data["id"] = str(document.id)   # convert ObjectId to string
    return response_schema(**data)