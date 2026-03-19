from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


# ============================================================
# Enums - define allowed values for status and priority fields
# Using Python Enum so FastAPI validates input automatically
# ============================================================

class TaskStatus(str, Enum):
    todo        = "todo"
    in_progress = "in_progress"
    done        = "done"


class TaskPriority(str, Enum):
    low    = "low"
    medium = "medium"
    high   = "high"


# ============================================================
# Helper function: return current UTC time
# Used as default_factory so each document gets its own timestamp
# (if we used `default=datetime.now()` it would be evaluated once
#  at import time and every document would share the same timestamp)
# ============================================================

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# User document
#
# In MongoDB, this becomes the "users" collection.
# Beanie's Document class maps directly to a MongoDB collection.
#
# `Indexed(str, unique=True)` tells Beanie to create a unique
# index on that field in MongoDB — equivalent to UNIQUE constraint
# in SQL. This prevents duplicate usernames or emails.
# ============================================================

class User(Document):
    username:        Indexed(str, unique=True)
    email:           Indexed(str, unique=True)
    hashed_password: str
    created_at:      datetime = Field(default_factory=utcnow)

    class Settings:
        # MongoDB collection name
        name = "users"


# ============================================================
# Category document
#
# In a relational DB we would use a foreign key for user_id.
# In MongoDB we store the user's string ID directly.
# We do NOT embed categories inside users because:
#   - categories can be queried independently
#   - a user may have many categories (unbounded growth)
# ============================================================

class Category(Document):
    user_id:    str               # stores User.id as string
    name:       str
    color:      str = "#6366f1"   # default indigo hex color
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "categories"


# ============================================================
# Task document
#
# This is the main document. Note:
#   - category_id is Optional because a task may be uncategorized
#   - updated_at is updated manually in the route handler
#     (MongoDB has no built-in equivalent of SQL's ON UPDATE trigger)
# ============================================================

class Task(Document):
    user_id:     str
    category_id: Optional[str] = None
    title:       str
    description: Optional[str] = None
    status:      TaskStatus   = TaskStatus.todo
    priority:    TaskPriority = TaskPriority.medium
    due_date:    Optional[datetime] = None
    created_at:  datetime = Field(default_factory=utcnow)
    updated_at:  datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tasks"