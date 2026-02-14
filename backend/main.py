from fastapi import FastAPI, HTTPException, Depends, Header, Cookie, Response, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, AsyncIterator, Dict
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path

from models import (
    LogCreate,
    LogBatchCreate,
    LogResponse,
    LogQuery,
    AppCreate,
    AppResponse,
    ApiKeyCreate,
    ApiKeyResponse,
    LoginRequest,
    UserResponse,
    UserCreate,
    UserUpdate,
    UserRole,
    PasswordChangeRequest,
    PasswordResetRequest,
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
)
from database import (
    init_database,
    create_app,
    get_app_by_id,
    get_app_by_name,
    list_apps,
    create_api_key,
    get_api_key,
    get_api_key_tags,
    list_api_keys,
    revoke_api_key,
    update_api_key_tags,
    create_log,
    query_logs,
    count_logs,
    get_all_log_tags,
    create_web_user,
    get_web_user,
    get_web_user_by_id,
    list_web_users,
    update_web_user,
    update_user_password,
    update_last_login,
    delete_web_user,
)
from write_queue import get_log_writer
from auth import (
    generate_api_key,
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
)

app = FastAPI(title="jlo - Just Logs", version="1.0.0")

# CORS middleware for development
# Note: allow_origins must be specific when using allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend dev server
        "http://localhost:8000",  # Backend/production
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

    # Create default admin user if not exists (username: admin, password: admin)
    if not get_web_user("admin"):
        create_web_user(
            username="admin",
            password_hash=hash_password("admin"),
            email="admin@example.com",
            full_name="Administrator",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        print("Created default admin user (username: admin, password: admin)")

    # Create default retention policies if they don't exist
    from database import get_retention_policies_for_app, create_retention_policy

    global_policies = get_retention_policies_for_app(None)
    if not global_policies:
        # High priority (FATAL, ERROR): 90 days
        create_retention_policy(
            app_id=None,
            priority_tier="high",
            retention_type="time_based",
            retention_days=90,
            retention_count=None,
            enabled=True,
        )
        # Medium priority (WARN, INFO): 30 days
        create_retention_policy(
            app_id=None,
            priority_tier="medium",
            retention_type="time_based",
            retention_days=30,
            retention_count=None,
            enabled=True,
        )
        # Low priority (DEBUG, TRACE): 7 days
        create_retention_policy(
            app_id=None,
            priority_tier="low",
            retention_type="time_based",
            retention_days=7,
            retention_count=None,
            enabled=True,
        )
        print("Created default retention policies (High: 90d, Medium: 30d, Low: 7d)")

    # Start retention cleanup scheduler
    from retention_scheduler import start_retention_scheduler

    start_retention_scheduler()
    print("Started retention cleanup scheduler (runs hourly)")

    # Start high-performance write queue for log ingestion
    log_writer = get_log_writer(
        batch_size=100,  # Write every 100 logs
        flush_interval=0.1,  # Or every 100ms (whichever comes first)
        queue_maxsize=10000,  # Buffer up to 10k logs
    )
    log_writer.start()
    print(
        f"🚀 Started OPTIMIZED async write queue: batch_size={log_writer.batch_size}, flush_interval={log_writer.flush_interval}s"
    )

    # Create default app and API key for testing
    if not get_app_by_name("default"):
        app_id = create_app("default")
        api_key = generate_api_key()
        create_api_key(api_key, app_id)
        print(f"Created default app with API key: {api_key}")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully shutdown write queue on server stop"""
    log_writer = get_log_writer()
    log_writer.stop(timeout=5.0)
    print("Stopped async write queue")


# Dependency: Verify API key for log ingestion
async def verify_api_key_header(x_api_key: Optional[str] = Header(None)) -> dict:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    api_key_data = get_api_key(x_api_key)
    if not api_key_data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key_data


# Dependency: Verify web user session
async def verify_web_session(session_token: Optional[str] = Cookie(None)) -> dict:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(session_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid session")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = get_web_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is inactive")

    return user


# Role-based authorization dependencies
def require_role(*allowed_roles: UserRole):
    """Decorator factory to require specific roles"""

    async def role_checker(user: dict = Depends(verify_web_session)) -> dict:
        user_role = user.get("role", "viewer")
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=403, detail="Insufficient permissions for this action"
            )
        return user

    return role_checker


# Specific role dependencies for convenience
async def require_admin(user: dict = Depends(verify_web_session)) -> dict:
    """Require admin role"""
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_admin_or_editor(user: dict = Depends(verify_web_session)) -> dict:
    """Require admin or editor role"""
    user_role = user.get("role", "viewer")
    if user_role not in [UserRole.ADMIN.value, UserRole.EDITOR.value]:
        raise HTTPException(status_code=403, detail="Admin or Editor access required")
    return user


# Store for SSE connections
sse_connections: List[asyncio.Queue] = []


# Log ingestion endpoints (require API key)
# NOTE: Changed to 202 Accepted - logs are queued for async processing
@app.post("/api/logs", status_code=202)
async def ingest_logs(
    request: Request, api_key_data: dict = Depends(verify_api_key_header)
):
    """
    Ingest log entries - accepts single log or array of logs.

    Logs are queued for async batch processing for high throughput.
    Returns 202 Accepted immediately (non-blocking).
    """
    # Parse the body to determine if it's a single log or array
    body = await request.json()

    # If it's a list, process as batch
    if isinstance(body, list):
        logs_data = body
    # If it's a single object, wrap it in a list
    else:
        logs_data = [body]

    # Get API key tags
    api_key_tags = api_key_data.get("tags", {})

    # Get the write queue
    log_writer = get_log_writer()

    accepted = 0
    dropped = 0

    for log_dict in logs_data:
        # Parse log entry
        log = LogCreate(**log_dict)
        timestamp = log.timestamp or datetime.utcnow()

        # Prepare log for queue
        log_data = {
            "app_id": api_key_data["app_id"],
            "level": log.level.value,
            "message": log.message,
            "structured_data": log.structured_data,
            "tags": api_key_tags,  # Attach API key tags
            "timestamp": timestamp,
        }

        # Enqueue for async processing (non-blocking)
        if log_writer.enqueue(log_data):
            accepted += 1

            # Notify SSE listeners (best effort)
            sse_log_data = {
                "id": None,  # ID not yet assigned
                "app_id": api_key_data["app_id"],
                "app_name": api_key_data["app_name"],
                "level": log.level.value,
                "message": log.message,
                "structured_data": log.structured_data,
                "tags": api_key_tags,
                "timestamp": timestamp.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }

            for queue in sse_connections:
                try:
                    queue.put_nowait(sse_log_data)
                except asyncio.QueueFull:
                    pass
        else:
            dropped += 1

    # Return appropriate response
    if dropped > 0:
        raise HTTPException(
            status_code=503,
            detail=f"Write queue full: {accepted} accepted, {dropped} dropped",
        )

    if len(logs_data) == 1:
        return {"message": "Log accepted for processing"}
    else:
        return {
            "accepted": accepted,
            "message": f"Accepted {accepted} logs for processing",
        }


@app.post("/api/logs/batch", status_code=202)
async def ingest_logs_batch(
    batch: LogBatchCreate, api_key_data: dict = Depends(verify_api_key_header)
):
    """
    Ingest multiple log entries (batch endpoint).

    Logs are queued for async batch processing for high throughput.
    Returns 202 Accepted immediately (non-blocking).
    """
    # Get API key tags
    api_key_tags = api_key_data.get("tags", {})

    # Get the write queue
    log_writer = get_log_writer()

    accepted = 0
    dropped = 0

    for log in batch.logs:
        timestamp = log.timestamp or datetime.utcnow()

        # Prepare log for queue
        log_data = {
            "app_id": api_key_data["app_id"],
            "level": log.level.value,
            "message": log.message,
            "structured_data": log.structured_data,
            "tags": api_key_tags,
            "timestamp": timestamp,
        }

        # Enqueue for async processing (non-blocking)
        if log_writer.enqueue(log_data):
            accepted += 1

            # Notify SSE listeners (best effort)
            sse_log_data = {
                "id": None,  # ID not yet assigned
                "app_id": api_key_data["app_id"],
                "app_name": api_key_data["app_name"],
                "level": log.level.value,
                "message": log.message,
                "structured_data": log.structured_data,
                "tags": api_key_tags,
                "timestamp": timestamp.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
            }

            for queue in sse_connections:
                try:
                    queue.put_nowait(sse_log_data)
                except asyncio.QueueFull:
                    pass
        else:
            dropped += 1

    # Return response
    if dropped > 0:
        raise HTTPException(
            status_code=503,
            detail=f"Write queue full: {accepted} accepted, {dropped} dropped",
        )

    return {"accepted": accepted, "message": f"Accepted {accepted} logs for processing"}


# Authentication endpoints
@app.post("/api/auth/login")
async def login(credentials: LoginRequest, response: Response):
    """Web UI login"""
    user = get_web_user(credentials.username)
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is inactive")

    # Update last login timestamp
    update_last_login(user["id"])

    access_token = create_access_token(data={"sub": user["username"]})

    # Set HTTP-only cookie
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        max_age=60 * 60 * 24,  # 24 hours
        samesite="lax",
        path="/",
        # Note: secure=True should be used in production with HTTPS
    )

    return {
        "message": "Login successful",
        "username": user["username"],
        "role": user.get("role", "viewer"),
        "full_name": user.get("full_name"),
    }


@app.post("/api/auth/logout")
async def logout(response: Response):
    """Web UI logout"""
    response.delete_cookie("session_token")
    return {"message": "Logout successful"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(user: dict = Depends(verify_web_session)):
    """Get current logged-in user"""
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        full_name=user.get("full_name"),
        role=UserRole(user.get("role", "viewer")),
        is_active=user.get("is_active", True),
        last_login=user.get("last_login"),
        created_at=user["created_at"],
    )


# Log retrieval endpoints (require web session)
@app.get("/api/logs", response_model=List[LogResponse])
async def get_logs(
    app_id: Optional[int] = None,
    level: Optional[str] = None,
    levels: Optional[str] = None,  # Comma-separated list of levels
    search: Optional[str] = None,
    tags: Optional[str] = None,  # Format: "env=prod,region=us-east"
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    user: dict = Depends(verify_web_session),
):
    """Get logs with filtering and pagination"""
    # Handle multiple levels
    level_list = None
    if levels:
        level_list = [l.strip().upper() for l in levels.split(",")]
    elif level:
        level_list = level.upper()

    # Parse tags
    tag_filters = {}
    if tags:
        for tag in tags.split(","):
            if "=" in tag:
                k, v = tag.split("=", 1)
                tag_filters[k.strip()] = v.strip()

    logs = query_logs(
        app_id=app_id,
        level=level_list,
        search=search,
        tags=tag_filters if tag_filters else None,
        start_time=start_time,
        end_time=end_time,
        limit=min(limit, 1000),
        offset=offset,
    )

    return [LogResponse(**log) for log in logs]


@app.get("/api/logs/count")
async def get_logs_count(
    app_id: Optional[int] = None,
    level: Optional[str] = None,
    levels: Optional[str] = None,  # Comma-separated list of levels
    search: Optional[str] = None,
    tags: Optional[str] = None,  # Format: "env=prod,region=us-east"
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user: dict = Depends(verify_web_session),
):
    """Get count of logs matching filters"""
    # Handle multiple levels
    level_list = None
    if levels:
        level_list = [l.strip().upper() for l in levels.split(",")]
    elif level:
        level_list = [level.upper()]

    # Parse tags
    tag_filters = {}
    if tags:
        for tag in tags.split(","):
            if "=" in tag:
                k, v = tag.split("=", 1)
                tag_filters[k.strip()] = v.strip()

    total = count_logs(
        app_id=app_id,
        level=level_list,
        search=search,
        tags=tag_filters if tag_filters else None,
        start_time=start_time,
        end_time=end_time,
    )
    return {"total": total}


@app.get("/api/logs/tags")
async def get_logs_tags(user: dict = Depends(verify_web_session)):
    """Get all unique tag keys and values from logs"""
    tags = get_all_log_tags()
    return {"tags": tags}


@app.get("/api/logs/stream")
async def stream_logs(request: Request, user: dict = Depends(verify_web_session)):
    """Server-Sent Events endpoint for real-time log streaming"""

    async def event_generator() -> AsyncIterator[str]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        sse_connections.append(queue)

        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait for new log with timeout
                    log_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(log_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            sse_connections.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/logs/export")
async def export_logs(
    format: str = "json",
    app_id: Optional[int] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user: dict = Depends(verify_web_session),
):
    """Export logs as JSON or CSV"""
    logs = query_logs(
        app_id=app_id,
        level=level,
        search=search,
        start_time=start_time,
        end_time=end_time,
        limit=10000,
        offset=0,
    )

    if format == "json":
        return {"logs": logs}
    elif format == "csv":
        import io
        import csv

        output = io.StringIO()
        if logs:
            fieldnames = [
                "id",
                "app_name",
                "level",
                "message",
                "timestamp",
                "created_at",
            ]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()

            for log in logs:
                writer.writerow(
                    {
                        "id": log["id"],
                        "app_name": log["app_name"],
                        "level": log["level"],
                        "message": log["message"],
                        "timestamp": log["timestamp"],
                        "created_at": log["created_at"],
                    }
                )

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=logs.csv"},
        )
    else:
        raise HTTPException(
            status_code=400, detail="Invalid format. Use 'json' or 'csv'"
        )


# Application management endpoints
@app.post("/api/apps", response_model=AppResponse, status_code=201)
async def create_application(
    app_data: AppCreate, user: dict = Depends(require_admin_or_editor)
):
    """Create a new application (admin or editor only)"""
    if get_app_by_name(app_data.name):
        raise HTTPException(status_code=400, detail="App name already exists")

    app_id = create_app(app_data.name)
    app = get_app_by_id(app_id)
    if app:
        return AppResponse(id=app["id"], name=app["name"], created_at=app["created_at"])
    raise HTTPException(status_code=500, detail="Failed to create app")


@app.get("/api/apps", response_model=List[AppResponse])
async def get_apps(user: dict = Depends(verify_web_session)):
    """List all applications"""
    apps = list_apps()
    return [AppResponse(**app) for app in apps]


# API key management endpoints
@app.post("/api/api-keys", response_model=ApiKeyResponse, status_code=201)
async def create_new_api_key(
    key_data: ApiKeyCreate, user: dict = Depends(require_admin_or_editor)
):
    """Generate a new API key for an application (admin or editor only)"""
    app = get_app_by_id(key_data.app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    api_key = generate_api_key()
    key_id = create_api_key(api_key, key_data.app_id)

    # Add tags if provided
    if key_data.tags:
        update_api_key_tags(key_id, key_data.tags)

    return ApiKeyResponse(
        id=key_id,
        key=api_key,
        app_id=app["id"],
        app_name=app["name"],
        is_active=True,
        tags=key_data.tags or {},
        created_at=datetime.utcnow(),
    )


@app.get("/api/api-keys", response_model=List[ApiKeyResponse])
async def get_api_keys(user: dict = Depends(verify_web_session)):
    """List all API keys"""
    keys = list_api_keys()
    return [ApiKeyResponse(**key) for key in keys]


@app.put("/api/api-keys/{key_id}/tags")
async def update_key_tags(
    key_id: int, tags: Dict[str, str], user: dict = Depends(require_admin_or_editor)
):
    """Update tags for an API key (admin or editor only)"""
    update_api_key_tags(key_id, tags)
    return {"message": "Tags updated successfully"}


@app.delete("/api/api-keys/{key_id}")
async def delete_api_key(key_id: int, user: dict = Depends(require_admin_or_editor)):
    """Revoke an API key (admin or editor only)"""
    success = revoke_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked"}


# User management endpoints (admin only)
@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, admin: dict = Depends(require_admin)):
    """Create a new user (admin only)"""
    # Check if username already exists
    if get_web_user(user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = create_web_user(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        email=user_data.email,
        full_name=user_data.full_name,
        role=user_data.role.value,
        is_active=user_data.is_active,
    )

    user = get_web_user_by_id(user_id)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        full_name=user.get("full_name"),
        role=UserRole(user.get("role", "viewer")),
        is_active=user.get("is_active", True),
        last_login=user.get("last_login"),
        created_at=user["created_at"],
    )


@app.get("/api/users", response_model=List[UserResponse])
async def get_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    users = list_web_users()
    return [
        UserResponse(
            id=user["id"],
            username=user["username"],
            email=user.get("email"),
            full_name=user.get("full_name"),
            role=UserRole(user.get("role", "viewer")),
            is_active=user.get("is_active", True),
            last_login=user.get("last_login"),
            created_at=user["created_at"],
        )
        for user in users
    ]


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, admin: dict = Depends(require_admin)):
    """Get a specific user (admin only)"""
    user = get_web_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        full_name=user.get("full_name"),
        role=UserRole(user.get("role", "viewer")),
        is_active=user.get("is_active", True),
        last_login=user.get("last_login"),
        created_at=user["created_at"],
    )


@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_data: UserUpdate, admin: dict = Depends(require_admin)
):
    """Update user details (admin only)"""
    user = get_web_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prepare update parameters
    update_params = {}
    if user_data.email is not None:
        update_params["email"] = user_data.email
    if user_data.full_name is not None:
        update_params["full_name"] = user_data.full_name
    if user_data.role is not None:
        update_params["role"] = user_data.role.value
    if user_data.is_active is not None:
        update_params["is_active"] = user_data.is_active

    if update_params:
        update_web_user(user_id, **update_params)

    # Return updated user
    user = get_web_user_by_id(user_id)
    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user.get("email"),
        full_name=user.get("full_name"),
        role=UserRole(user.get("role", "viewer")),
        is_active=user.get("is_active", True),
        last_login=user.get("last_login"),
        created_at=user["created_at"],
    )


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    """Delete a user (admin only)"""
    # Prevent deleting yourself
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    user = get_web_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    success = delete_web_user(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete user")

    return {"message": "User deleted successfully"}


# Password management endpoints
@app.post("/api/auth/change-password")
async def change_password(
    password_data: PasswordChangeRequest, user: dict = Depends(verify_web_session)
):
    """Change own password"""
    # Verify current password
    if not verify_password(password_data.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    # Update password
    new_hash = hash_password(password_data.new_password)
    success = update_user_password(user["id"], new_hash)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")

    return {"message": "Password updated successfully"}


@app.post("/api/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordResetRequest,
    admin: dict = Depends(require_admin),
):
    """Reset user password (admin only)"""
    user = get_web_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update password
    new_hash = hash_password(password_data.new_password)
    success = update_user_password(user_id, new_hash)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset password")

    return {"message": "Password reset successfully"}


# Retention Policy Endpoints
@app.get("/api/retention-policies")
async def get_retention_policies(
    app_id: Optional[int] = None,
    current_user: Dict = Depends(verify_web_session),
):
    """Get all retention policies (global or for specific app)"""
    from database import get_retention_policies_for_app, list_all_retention_policies

    if app_id is None:
        policies = list_all_retention_policies()
    else:
        policies = get_retention_policies_for_app(app_id)

    return {"policies": policies}


@app.post("/api/retention-policies")
async def create_retention_policy_endpoint(
    policy: RetentionPolicyCreate,
    current_user: Dict = Depends(require_admin_or_editor),
):
    """Create a new retention policy"""
    from database import create_retention_policy

    policy_id = create_retention_policy(
        app_id=policy.app_id,
        priority_tier=policy.priority_tier.value,
        retention_type=policy.retention_type.value,
        retention_days=policy.retention_days,
        retention_count=policy.retention_count,
        enabled=policy.enabled,
    )

    return {"id": policy_id, "message": "Retention policy created successfully"}


@app.get("/api/retention-policies/{policy_id}")
async def get_retention_policy_endpoint(
    policy_id: int,
    current_user: Dict = Depends(verify_web_session),
):
    """Get a specific retention policy"""
    from database import get_retention_policy

    policy = get_retention_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Retention policy not found")

    return policy


@app.put("/api/retention-policies/{policy_id}")
async def update_retention_policy_endpoint(
    policy_id: int,
    updates: RetentionPolicyUpdate,
    current_user: Dict = Depends(require_admin_or_editor),
):
    """Update a retention policy"""
    from database import update_retention_policy

    success = update_retention_policy(
        policy_id=policy_id,
        retention_type=updates.retention_type.value if updates.retention_type else None,
        retention_days=updates.retention_days,
        retention_count=updates.retention_count,
        enabled=updates.enabled,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Retention policy not found")

    return {"message": "Retention policy updated successfully"}


@app.delete("/api/retention-policies/{policy_id}")
async def delete_retention_policy_endpoint(
    policy_id: int,
    current_user: Dict = Depends(require_admin_or_editor),
):
    """Delete a retention policy"""
    from database import delete_retention_policy

    success = delete_retention_policy(policy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Retention policy not found")

    return {"message": "Retention policy deleted successfully"}


@app.get("/api/apps/{app_id}/retention-policies")
async def get_app_retention_policies(
    app_id: int,
    current_user: Dict = Depends(verify_web_session),
):
    """Get retention policies for a specific app"""
    from database import get_retention_policies_for_app, get_app_by_id

    app = get_app_by_id(app_id)
    if not app:
        raise HTTPException(status_code=404, detail="App not found")

    policies = get_retention_policies_for_app(app_id)
    return {"policies": policies}


# Retention Cleanup Operations
@app.post("/api/retention/run-cleanup")
async def run_retention_cleanup_endpoint(
    app_id: Optional[int] = None,
    current_user: Dict = Depends(require_admin),
):
    """Manually trigger retention cleanup"""
    from database import (
        apply_retention_policies,
        create_retention_run,
        update_retention_run,
    )

    run_id = create_retention_run(trigger_type="manual", user_id=current_user.get("id"))

    try:
        results = apply_retention_policies(app_id=app_id)
        total_deleted = sum(results.values())

        update_retention_run(run_id, "completed", total_deleted, None)

        return {
            "run_id": run_id,
            "logs_deleted": total_deleted,
            "details": results,
            "message": f"Cleanup completed: {total_deleted} logs deleted",
        }
    except Exception as e:
        error_msg = str(e)
        update_retention_run(run_id, "failed", 0, error_msg)
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {error_msg}")


@app.get("/api/retention/preview")
async def preview_retention_cleanup_endpoint(
    app_id: Optional[int] = None,
    current_user: Dict = Depends(verify_web_session),
):
    """Preview what would be deleted by retention policies (dry run)"""
    from database import preview_retention_cleanup

    previews = preview_retention_cleanup(app_id=app_id)
    total_logs_to_delete = sum(p["log_count"] for p in previews)

    return {
        "previews": previews,
        "total_logs_to_delete": total_logs_to_delete,
        "message": f"Would delete {total_logs_to_delete} logs",
    }


@app.get("/api/retention/runs")
async def get_retention_runs_endpoint(
    limit: int = 20,
    offset: int = 0,
    current_user: Dict = Depends(verify_web_session),
):
    """Get retention cleanup run history"""
    from database import list_retention_runs

    runs = list_retention_runs(limit=limit, offset=offset)
    return {"runs": runs}


@app.get("/api/retention/runs/{run_id}")
async def get_retention_run_endpoint(
    run_id: int,
    current_user: Dict = Depends(verify_web_session),
):
    """Get details of a specific retention run"""
    from database import get_retention_run

    run = get_retention_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Retention run not found")

    return run


# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jlo"}


@app.get("/api/metrics")
async def get_metrics(user: dict = Depends(verify_web_session)):
    """
    Get performance metrics for monitoring.

    Returns:
        - Write queue statistics
        - Database size
        - Log counts
        - Write throughput
    """
    import os
    from database import count_logs

    # Get write queue stats
    log_writer = get_log_writer()
    queue_stats = log_writer.get_stats()

    # Calculate write rate (logs per second over last minute)
    write_rate_per_min = (
        queue_stats["total_written"] / 60 if queue_stats["total_written"] > 0 else 0
    )

    # Get database size
    db_path = Path(__file__).parent / "jlo.db"
    db_size_mb = os.path.getsize(db_path) / (1024 * 1024) if db_path.exists() else 0

    # Get total log count
    total_logs = count_logs()

    return {
        "service": "jlo",
        "timestamp": datetime.utcnow().isoformat(),
        "write_queue": {
            "queue_size": queue_stats["queue_size"],
            "queue_capacity": queue_stats["queue_capacity"],
            "queue_utilization_pct": (
                queue_stats["queue_size"] / queue_stats["queue_capacity"]
            )
            * 100,
            "is_running": queue_stats["is_running"],
        },
        "throughput": {
            "total_enqueued": queue_stats["total_enqueued"],
            "total_written": queue_stats["total_written"],
            "total_dropped": queue_stats["total_dropped"],
            "total_errors": queue_stats["total_errors"],
            "estimated_write_rate_per_min": round(write_rate_per_min, 2),
        },
        "database": {
            "size_mb": round(db_size_mb, 2),
            "total_logs": total_logs,
        },
    }


# Serve static files (Vue app) - will be added after building frontend
# Mount this after all API routes to avoid conflicts
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Serve static assets (js, css, etc)
    app.mount(
        "/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets"
    )

    # Catch-all route to serve index.html for SPA routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for all non-API routes (SPA catch-all)"""
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not built")
