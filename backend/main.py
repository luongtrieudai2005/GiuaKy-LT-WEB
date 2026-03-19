import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models import User, Category, Task
from routers import users, categories, tasks


# ============================================================
# Database connection
#
# We use a module-level variable to hold the MongoDB client.
# Motor is async — it does NOT block the event loop.
# The client is created once at startup and reused for every
# request (connection pooling is handled by Motor internally).
# ============================================================

mongo_client: AsyncIOMotorClient = None


# ============================================================
# Lifespan context manager
#
# FastAPI's recommended way to run startup/shutdown logic.
# Replaces the old @app.on_event("startup") decorator pattern.
#
# Flow:
#   1. Code BEFORE `yield` runs at startup
#   2. `yield` hands control to FastAPI (app runs normally)
#   3. Code AFTER `yield` runs at shutdown
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mongo_client

    # --- STARTUP ---
    mongodb_url     = os.getenv("MONGODB_URL")
    mongodb_db_name = os.getenv("MONGODB_DB_NAME", "taskmanager")

    if not mongodb_url:
        raise RuntimeError("MONGODB_URL environment variable is not set")

    # Create the Motor async client
    # maxPoolSize controls how many connections Motor keeps open
    mongo_client = AsyncIOMotorClient(mongodb_url, maxPoolSize=10)

    # init_beanie registers our Document models with the database.
    # After this call, Beanie knows which collection each model maps to
    # and creates any indexes defined with Indexed().
    await init_beanie(
        database=mongo_client[mongodb_db_name],
        document_models=[User, Category, Task],
    )

    print(f"Connected to MongoDB: {mongodb_db_name}")

    yield   # <-- app runs here

    # --- SHUTDOWN ---
    # Cleanly close all connections in the pool
    mongo_client.close()
    print("MongoDB connection closed")


# ============================================================
# FastAPI application instance
# ============================================================

app = FastAPI(
    title="Task Manager API",
    description="REST API for managing tasks, built with FastAPI + MongoDB",
    version="1.0.0",
    lifespan=lifespan,
    # In production you may want to hide the docs:
    # docs_url=None, redoc_url=None
)


# ============================================================
# CORS middleware
#
# CORS (Cross-Origin Resource Sharing) controls which origins
# (domains) are allowed to call this API from a browser.
#
# During local development: allow all origins ("*") for simplicity.
# In production: replace "*" with your actual domain, e.g.:
#   allow_origins=["https://yourdomain.com"]
#
# allow_credentials=True is needed if the frontend sends cookies
# or Authorization headers. When using JWT in the Authorization
# header, this must be True.
#
# Note: allow_origins=["*"] and allow_credentials=True cannot
# be used together — use the specific domain in production.
# ============================================================

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, PUT, PATCH, DELETE, OPTIONS
    allow_headers=["*"],   # Authorization, Content-Type, etc.
)


# ============================================================
# Routers
#
# Each router handles one resource group:
#   /auth       → register, login (returns JWT)
#   /users      → get current user profile
#   /categories → CRUD for task categories
#   /tasks      → CRUD for tasks
#
# prefix    : URL prefix applied to all routes in that router
# tags      : grouping label shown in /docs (Swagger UI)
# ============================================================

app.include_router(users.router,      prefix="/auth",       tags=["auth"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(tasks.router,      prefix="/tasks",       tags=["tasks"])


# ============================================================
# Serve frontend static files
#
# FastAPI can serve the HTML/CSS/JS frontend directly.
# The frontend/ folder is mounted at "/" so that:
#   GET /          → frontend/index.html
#   GET /style.css → frontend/style.css
#   GET /app.js    → frontend/app.js
#
# IMPORTANT: mount static files AFTER routers so that
# API routes take priority over static file serving.
# If /tasks is registered before StaticFiles, then
# GET /tasks hits the router, not a static file.
#
# html=True means requests to "/" return index.html automatically.
# ============================================================

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


# ============================================================
# Health check endpoint
#
# Used by Docker, load balancers, and monitoring tools to check
# whether the app is running. Returns 200 OK if the app is up.
# Also shows whether the database connection is alive.
# ============================================================

@app.get("/health", tags=["health"])
async def health_check():
    try:
        # ping the MongoDB server — raises an exception if unreachable
        await mongo_client.admin.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "database": db_status,
    }