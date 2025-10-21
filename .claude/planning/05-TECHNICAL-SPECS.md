# Technical Specifications

**Version:** 1.0
**Last Updated:** 2025-10-21

---

## System Requirements

### Development Environment

**Minimum:**
- Python 3.11+
- 8GB RAM
- 10GB disk space
- Chrome/Chromium browser

**Recommended:**
- Python 3.14t (free-threaded)
- 16GB RAM
- 20GB disk space
- SSD storage
- Chrome/Chromium + Firefox

### Production Environment

**Single User:**
- 2 CPU cores
- 4GB RAM
- 20GB disk space
- 100 Mbps network

**Multi-User (10-50 users):**
- 4-8 CPU cores
- 16GB RAM
- 100GB disk space (with logs/traces)
- 1 Gbps network

**Enterprise (100+ users):**
- 16+ CPU cores
- 64GB RAM
- 500GB disk space
- Load balancer
- Redis for event bus
- PostgreSQL for data storage

---

## Technology Stack

### Backend

```yaml
Core:
  - Python: "3.11-3.14t"
  - browser-use: ">=0.1.48"
  - Playwright: ">=1.40.0"

Web Framework:
  - Gradio: ">=5.27.0" # Primary UI framework
  - FastAPI: ">=0.100.0" # WebSocket/API server (Phase 4)

LLM Integration:
  - langchain-openai: Latest
  - langchain-anthropic: Latest
  - langchain-google-genai: Latest
  - langchain-ollama: Latest
  # ... other LangChain providers

Agent Framework:
  - langgraph: ">=0.3.34" # Multi-agent orchestration
  - langchain-community: ">=0.3.0"

Data & Storage:
  - SQLite: Built-in (development)
  - PostgreSQL: ">=14" (production, optional)
  - Redis: ">=7.0" (event bus, optional)

Utilities:
  - python-dotenv: Environment variables
  - pydantic: Data validation
  - pyperclip: Clipboard operations
  - json-repair: JSON fixing
```

### Frontend

```yaml
Primary:
  - Gradio: ">=5.27.0" # Built-in components

Custom Components (Phase 2+):
  - React: "18.x"
  - TypeScript: "5.x"
  - React Flow: "11.x" # Workflow visualization
  - TanStack Table: "8.x" # Data tables (optional)
  - Recharts: "2.x" # Charts (optional)

Build Tools:
  - Vite: "5.x"
  - ESBuild: Latest
```

### Development Tools

```yaml
Code Quality:
  - Ruff: ">=0.8.0" # Formatting & linting
  - ty: ">=0.0.1a23" # Type checking (alpha)

Testing:
  - pytest: ">=8.0.0"
  - pytest-asyncio: ">=0.23.0"
  - playwright: For E2E tests

Package Management:
  - uv: ">=0.5.0" # Primary package manager
```

---

## Database Schemas

### SQLite Schema (Development)

**File:** `src/web_ui/storage/schema.sql`

```sql
-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, running, completed, error
    user_id TEXT, -- NULL for single-user mode
    metadata JSON
);

CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

-- Messages table (chat history)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_session_id ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);

-- Execution traces
CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    task TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms REAL,
    status TEXT DEFAULT 'running', -- running, completed, error
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    llm_calls INTEGER DEFAULT 0,
    actions_executed INTEGER DEFAULT 0,
    success BOOLEAN,
    final_output TEXT,
    error TEXT,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_traces_session_id ON traces(session_id);
CREATE INDEX idx_traces_start_time ON traces(start_time DESC);
CREATE INDEX idx_traces_status ON traces(status);

-- Trace spans
CREATE TABLE IF NOT EXISTS trace_spans (
    id TEXT PRIMARY KEY,
    trace_id TEXT NOT NULL,
    parent_id TEXT, -- NULL for root spans
    span_type TEXT NOT NULL, -- agent_run, llm_call, browser_action, etc.
    name TEXT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms REAL,
    inputs JSON,
    outputs JSON,
    metadata JSON,
    model_name TEXT,
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd REAL,
    status TEXT DEFAULT 'running', -- running, completed, error
    error TEXT,
    FOREIGN KEY (trace_id) REFERENCES traces(id) ON DELETE CASCADE
);

CREATE INDEX idx_spans_trace_id ON trace_spans(trace_id);
CREATE INDEX idx_spans_parent_id ON trace_spans(parent_id);
CREATE INDEX idx_spans_start_time ON trace_spans(start_time);

-- Workflow templates
CREATE TABLE IF NOT EXISTS workflow_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT, -- e-commerce, research, data-entry, etc.
    author TEXT,
    tags JSON, -- Array of tags
    parameters JSON, -- Parameter definitions
    workflow_data JSON NOT NULL, -- Recorded actions or workflow graph
    usage_count INTEGER DEFAULT 0,
    rating REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_templates_category ON workflow_templates(category);
CREATE INDEX idx_templates_created_at ON workflow_templates(created_at DESC);
CREATE INDEX idx_templates_usage_count ON workflow_templates(usage_count DESC);

-- Template usage tracking
CREATE TABLE IF NOT EXISTS template_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    user_id TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN,
    parameters JSON,
    FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_template_usage_template_id ON template_usage(template_id);
CREATE INDEX idx_template_usage_executed_at ON template_usage(executed_at DESC);

-- User settings
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    settings JSON NOT NULL, -- LLM preferences, UI preferences, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plugin registry
CREATE TABLE IF NOT EXISTS plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    author TEXT,
    description TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    config JSON, -- Plugin-specific configuration
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled jobs (Phase 4)
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    template_id TEXT,
    cron_expression TEXT NOT NULL,
    parameters JSON,
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    FOREIGN KEY (template_id) REFERENCES workflow_templates(id) ON DELETE SET NULL
);

CREATE INDEX idx_scheduled_jobs_next_run ON scheduled_jobs(next_run_at);
CREATE INDEX idx_scheduled_jobs_enabled ON scheduled_jobs(enabled);
```

### Migration to PostgreSQL (Production)

**Differences for PostgreSQL:**

```sql
-- Use JSONB instead of JSON for better performance
ALTER TABLE sessions ALTER COLUMN metadata TYPE JSONB USING metadata::JSONB;
ALTER TABLE messages ALTER COLUMN metadata TYPE JSONB USING metadata::JSONB;
-- ... similar for all JSON columns

-- Use proper timestamp types
ALTER TABLE sessions ALTER COLUMN created_at TYPE TIMESTAMPTZ;
-- ... similar for all timestamp columns

-- Add full-text search
CREATE INDEX idx_messages_content_fts ON messages
    USING GIN (to_tsvector('english', content));

CREATE INDEX idx_templates_search ON workflow_templates
    USING GIN (to_tsvector('english', name || ' ' || description));

-- Partitioning for large trace tables (optional)
CREATE TABLE traces_partition_2025 PARTITION OF traces
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

---

## API Specifications

### WebSocket API (Phase 4)

**Endpoint:** `ws://localhost:8000/ws/{session_id}`

**Client → Server Messages:**

```typescript
// Start agent
{
  "type": "command",
  "command": "start_agent",
  "data": {
    "task": "Search Google for browser automation tools",
    "max_steps": 100,
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4o",
      "temperature": 0.7
    }
  }
}

// Pause agent
{
  "type": "command",
  "command": "pause_agent"
}

// Resume agent
{
  "type": "command",
  "command": "resume_agent"
}

// Stop agent
{
  "type": "command",
  "command": "stop_agent"
}

// Step through (debugger)
{
  "type": "command",
  "command": "step"
}
```

**Server → Client Messages:**

```typescript
// Agent started
{
  "type": "agent.start",
  "timestamp": 1234567890.123,
  "data": {
    "session_id": "abc123",
    "task": "Search Google for...",
    "max_steps": 100
  }
}

// Agent step
{
  "type": "agent.step",
  "timestamp": 1234567890.456,
  "data": {
    "step": 1,
    "max_steps": 100,
    "progress": 0.01
  }
}

// LLM token (streaming)
{
  "type": "llm.token",
  "timestamp": 1234567890.789,
  "data": {
    "token": "The",
    "model": "gpt-4o"
  }
}

// Action started
{
  "type": "action.start",
  "timestamp": 1234567891.012,
  "data": {
    "action": "click",
    "params": {"selector": "#search-button"},
    "action_id": "action_001"
  }
}

// Action completed
{
  "type": "action.complete",
  "timestamp": 1234567891.234,
  "data": {
    "action_id": "action_001",
    "duration_ms": 222,
    "result": {"success": true}
  }
}

// Trace update
{
  "type": "trace.update",
  "timestamp": 1234567891.456,
  "data": {
    "trace_id": "trace_xyz",
    "total_tokens": 1234,
    "total_cost_usd": 0.0123,
    "llm_calls": 5
  }
}

// Agent completed
{
  "type": "agent.complete",
  "timestamp": 1234567900.000,
  "data": {
    "success": true,
    "output": "Found 10 browser automation tools...",
    "duration_ms": 10000
  }
}

// Error
{
  "type": "agent.error",
  "timestamp": 1234567890.000,
  "data": {
    "error": "Failed to find element",
    "error_type": "ElementNotFoundError",
    "recoverable": true
  }
}
```

### REST API (Phase 4)

**Base URL:** `http://localhost:8000/api`

```yaml
# Session Management
POST   /sessions                    # Create new session
GET    /sessions                    # List sessions
GET    /sessions/{session_id}       # Get session details
DELETE /sessions/{session_id}       # Delete session
POST   /sessions/{session_id}/start # Start agent in session
POST   /sessions/{session_id}/stop  # Stop agent

# Templates
GET    /templates                   # List templates
GET    /templates/{template_id}     # Get template
POST   /templates                   # Create template
PUT    /templates/{template_id}     # Update template
DELETE /templates/{template_id}     # Delete template
POST   /templates/{template_id}/use # Use template (execute)

# Traces
GET    /traces                      # List traces
GET    /traces/{trace_id}           # Get trace with spans
GET    /traces/{trace_id}/export    # Export trace (JSON/PDF)

# Plugins
GET    /plugins                     # List available plugins
GET    /plugins/{plugin_id}         # Get plugin info
POST   /plugins/{plugin_id}/enable  # Enable plugin
POST   /plugins/{plugin_id}/disable # Disable plugin
POST   /plugins/{plugin_id}/config  # Update plugin config

# Analytics
GET    /analytics/usage             # Usage statistics
GET    /analytics/costs             # Cost breakdown
GET    /analytics/performance       # Performance metrics
```

### Example REST API Request/Response

**POST /api/templates**

Request:
```json
{
  "name": "LinkedIn Profile Scraper",
  "description": "Extract information from LinkedIn profiles",
  "category": "research",
  "parameters": [
    {
      "name": "profile_url",
      "type": "string",
      "required": true,
      "description": "LinkedIn profile URL"
    }
  ],
  "workflow_data": {
    "steps": [
      {
        "action": "navigate",
        "params": {"url": "{profile_url}"}
      },
      {
        "action": "extract",
        "params": {"selector": ".profile-name"}
      }
    ]
  }
}
```

Response:
```json
{
  "id": "template_abc123",
  "name": "LinkedIn Profile Scraper",
  "created_at": "2025-01-21T10:00:00Z",
  "author": "user@example.com",
  "usage_count": 0,
  "rating": 0.0
}
```

---

## Performance Requirements

### Response Times

| Operation | Target | Maximum |
|-----------|--------|---------|
| UI Load | <1s | <2s |
| Agent Start | <500ms | <1s |
| LLM Token Stream | <100ms | <200ms |
| Action Execution | <2s | <5s |
| Trace Load | <500ms | <1s |
| Template Search | <200ms | <500ms |

### Throughput

| Metric | Target | Notes |
|--------|--------|-------|
| Concurrent Users | 100+ | With proper scaling |
| Concurrent Agents | 20+ | Per server instance |
| Events/Second | 1000+ | Event bus capacity |
| WebSocket Connections | 500+ | With connection pooling |
| Database Queries/Sec | 1000+ | With proper indexing |

### Resource Limits

```yaml
Memory:
  per_agent: "500MB max"
  per_browser: "1GB max"
  total_application: "4GB recommended"

CPU:
  per_agent: "1 core recommended"
  concurrent_limit: "Based on available cores"

Disk:
  traces_retention: "30 days default"
  max_screenshot_size: "5MB"
  max_recording_size: "50MB"

Network:
  max_websocket_message: "10MB"
  rate_limit_api: "100 requests/minute"
```

---

## Security Specifications

### Authentication (Phase 4+)

```python
# JWT-based authentication (optional)
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token."""
    token = credentials.credentials
    # Verify token (implementation depends on auth provider)
    if not is_valid_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return get_user_from_token(token)

# Protected endpoint
@app.get("/api/sessions")
async def list_sessions(user = Depends(verify_token)):
    """List sessions for authenticated user."""
    return get_user_sessions(user.id)
```

### Browser Security

```python
# Sandboxing configuration
browser_config = BrowserConfig(
    headless=True,
    disable_security=False,  # Keep security features enabled

    # Content Security Policy
    extra_chromium_args=[
        '--disable-web-security',  # ONLY for development
        '--no-sandbox',  # ONLY if running in container
    ]
)

# Validate URLs before navigation
from urllib.parse import urlparse

ALLOWED_PROTOCOLS = ['http', 'https']
BLOCKED_DOMAINS = ['malicious-site.com']

def validate_url(url: str) -> bool:
    """Validate URL before navigation."""
    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_PROTOCOLS:
        raise ValueError(f"Protocol {parsed.scheme} not allowed")

    if parsed.netloc in BLOCKED_DOMAINS:
        raise ValueError(f"Domain {parsed.netloc} is blocked")

    return True
```

### Data Protection

```python
# Encrypt sensitive data
from cryptography.fernet import Fernet

class SecureStorage:
    """Encrypt sensitive data in database."""

    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)

    def encrypt(self, data: str) -> str:
        """Encrypt data."""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Use for passwords, API keys, etc.
storage = SecureStorage(encryption_key=os.getenv("ENCRYPTION_KEY").encode())
encrypted_api_key = storage.encrypt(api_key)
```

---

## Monitoring & Logging

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Console handler
        logging.StreamHandler(),

        # File handler with rotation
        RotatingFileHandler(
            'logs/browser_use.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)

# Structured logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Usage
logger.info("agent_started", session_id="abc123", task="Search Google")
```

### Metrics Collection

```python
# Prometheus metrics (optional)
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
agent_executions = Counter(
    'browser_use_agent_executions_total',
    'Total number of agent executions',
    ['status', 'llm_provider']
)

execution_duration = Histogram(
    'browser_use_execution_duration_seconds',
    'Agent execution duration',
    ['llm_provider']
)

active_agents = Gauge(
    'browser_use_active_agents',
    'Number of currently active agents'
)

# Record metrics
agent_executions.labels(status='success', llm_provider='openai').inc()
execution_duration.labels(llm_provider='openai').observe(12.5)
active_agents.set(5)
```

---

## Configuration Management

### Environment Variables

```bash
# .env file structure

# Core Settings
BROWSER_USE_LOGGING_LEVEL=info  # result | info | debug
ANONYMIZED_TELEMETRY=false

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
DEFAULT_LLM=openai

# Browser Settings
BROWSER_PATH=
BROWSER_USER_DATA=
BROWSER_DEBUGGING_PORT=9222
KEEP_BROWSER_OPEN=true
USE_OWN_BROWSER=false

# Database (Phase 3+)
DATABASE_URL=sqlite:///./tmp/browser_use.db
# Or PostgreSQL: postgresql://user:pass@localhost/browser_use

# Event Bus (Phase 4)
EVENT_BUS_BACKEND=memory  # memory | redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Server (Phase 4)
API_HOST=0.0.0.0
API_PORT=8000
WEBSOCKET_PORT=8001

# Security (Phase 4+)
ENCRYPTION_KEY=...  # For encrypting sensitive data
JWT_SECRET=...      # For JWT authentication
SESSION_SECRET=...  # For session cookies

# Performance
MAX_CONCURRENT_AGENTS=10
TRACE_RETENTION_DAYS=30
MAX_SCREENSHOT_SIZE_MB=5

# Features (Feature Flags)
ENABLE_OBSERVABILITY=true
ENABLE_PLUGINS=false
ENABLE_MULTI_AGENT=false
```

### Runtime Configuration

```python
# config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment."""

    # Core
    browser_use_logging_level: str = "info"
    anonymized_telemetry: bool = False

    # LLM
    default_llm: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None

    # Browser
    browser_path: Optional[str] = None
    browser_user_data: Optional[str] = None
    keep_browser_open: bool = True

    # Database
    database_url: str = "sqlite:///./tmp/browser_use.db"

    # Event Bus
    event_bus_backend: str = "memory"
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Performance
    max_concurrent_agents: int = 10
    trace_retention_days: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

---

## Deployment Specifications

See [06-DEPLOYMENT-GUIDE.md](06-DEPLOYMENT-GUIDE.md) for detailed deployment instructions.

---

**Last Updated:** 2025-10-21
**Next Review:** Before Phase 4 implementation
