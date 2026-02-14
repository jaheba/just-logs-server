from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class UserRole(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class LogCreate(BaseModel):
    level: LogLevel = LogLevel.INFO
    message: str
    structured_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


class LogBatchCreate(BaseModel):
    logs: List[LogCreate]


class LogResponse(BaseModel):
    id: int
    app_id: int
    app_name: str
    level: str
    message: str
    structured_data: Optional[Dict[str, Any]]
    tags: Optional[Dict[str, str]] = None
    timestamp: datetime
    created_at: datetime


class AppCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class AppResponse(BaseModel):
    id: int
    name: str
    created_at: datetime


class ApiKeyCreate(BaseModel):
    app_id: int
    tags: Optional[Dict[str, str]] = None


class ApiKeyResponse(BaseModel):
    id: int
    key: str
    app_id: int
    app_name: str
    is_active: bool
    tags: Dict[str, str] = {}
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.VIEWER
    is_active: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class PasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=6)


class LogQuery(BaseModel):
    app_id: Optional[int] = None
    level: Optional[LogLevel] = None
    search: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)


class RetentionType(str, Enum):
    TIME_BASED = "time_based"
    COUNT_BASED = "count_based"


class PriorityTier(str, Enum):
    HIGH = "high"  # FATAL, ERROR
    MEDIUM = "medium"  # WARN, INFO
    LOW = "low"  # DEBUG, TRACE
    ALL = "all"  # Global default


class RetentionPolicy(BaseModel):
    id: Optional[int] = None
    app_id: Optional[int] = None  # NULL = global default
    priority_tier: PriorityTier
    retention_type: RetentionType
    retention_days: Optional[int] = None
    retention_count: Optional[int] = None
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RetentionPolicyCreate(BaseModel):
    app_id: Optional[int] = None
    priority_tier: PriorityTier
    retention_type: RetentionType
    retention_days: Optional[int] = Field(None, gt=0)
    retention_count: Optional[int] = Field(None, gt=0)
    enabled: bool = True


class RetentionPolicyUpdate(BaseModel):
    retention_type: Optional[RetentionType] = None
    retention_days: Optional[int] = Field(None, gt=0)
    retention_count: Optional[int] = Field(None, gt=0)
    enabled: Optional[bool] = None


class RetentionRun(BaseModel):
    id: Optional[int] = None
    trigger_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    logs_deleted: int = 0
    error_message: Optional[str] = None
    triggered_by_user_id: Optional[int] = None


class RetentionPreview(BaseModel):
    """Preview of logs that would be deleted"""

    app_id: Optional[int] = None
    app_name: Optional[str] = None
    priority_tier: str
    log_count: int
    oldest_log: Optional[datetime] = None
    newest_log: Optional[datetime] = None
