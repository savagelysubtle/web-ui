# Phase 4: Event-Driven Architecture & Extensibility

**Timeline:** Weeks 15-20
**Priority:** Medium (Enterprise/Scale Requirements)
**Complexity:** Very High

## Overview

Transform the application from a monolithic synchronous system into a scalable, event-driven architecture with plugin extensibility and multi-agent orchestration capabilities.

---

## Feature 4.1: Event-Driven Backend

### Current Architecture Problems

1. **Blocking Operations:** Gradio's request-response model blocks during long operations
2. **Poor Scalability:** Single-threaded execution limits concurrent users
3. **Tight Coupling:** UI directly calls agent methods
4. **No Real-time Updates:** Polling-based updates are inefficient
5. **Difficult to Test:** Monolithic structure makes unit testing hard

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Gradio + React)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat UI      │  │ Workflow Viz │  │ Observability│      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          │ WebSocket/SSE    │                  │
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼──────────────┐
│         ▼                  ▼                  ▼              │
│  ┌────────────────────────────────────────────────────┐     │
│  │           FastAPI WebSocket/SSE Server             │     │
│  └───────────────────────┬────────────────────────────┘     │
│                          │                                   │
│                          ▼                                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │              Event Bus (In-Memory or Redis)        │     │
│  │                                                     │     │
│  │  Events: AGENT_START, LLM_TOKEN, ACTION_START,     │     │
│  │          TRACE_UPDATE, ERROR, COMPLETION            │     │
│  └───────────────────────┬────────────────────────────┘     │
│                          │                                   │
│         ┌────────────────┼────────────────┐                 │
│         ▼                ▼                ▼                 │
│  ┌──────────┐   ┌──────────┐    ┌──────────┐              │
│  │ Agent    │   │ Tracer   │    │ Storage  │              │
│  │ Workers  │   │ Service  │    │ Service  │              │
│  └──────────┘   └──────────┘    └──────────┘              │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────┐             │
│  │        browser-use / Playwright          │             │
│  └──────────────────────────────────────────┘             │
└───────────────────────────────────────────────────────────┘
```

### Implementation

#### Event Bus

**File:** `src/web_ui/events/event_bus.py`

```python
from typing import Dict, Set, Callable, Any, Awaitable
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    """All event types in the system."""
    # Agent lifecycle
    AGENT_START = "agent.start"
    AGENT_STEP = "agent.step"
    AGENT_COMPLETE = "agent.complete"
    AGENT_ERROR = "agent.error"

    # LLM events
    LLM_REQUEST = "llm.request"
    LLM_TOKEN = "llm.token"
    LLM_RESPONSE = "llm.response"

    # Browser events
    ACTION_START = "action.start"
    ACTION_COMPLETE = "action.complete"
    ACTION_ERROR = "action.error"

    # Trace events
    TRACE_SPAN_START = "trace.span.start"
    TRACE_SPAN_END = "trace.span.end"
    TRACE_COMPLETE = "trace.complete"

    # UI events
    UI_CONNECTED = "ui.connected"
    UI_DISCONNECTED = "ui.disconnected"
    UI_COMMAND = "ui.command"

@dataclass
class Event:
    """Base event class."""
    event_type: EventType
    session_id: str
    timestamp: float
    data: Dict[str, Any]
    correlation_id: str = None  # For tracing related events

EventHandler = Callable[[Event], Awaitable[None]]

class EventBus:
    """
    Event bus for publish-subscribe pattern.
    Supports both in-memory and Redis backends.
    """

    def __init__(self, backend: str = "memory"):
        self.backend = backend
        self._subscribers: Dict[EventType, Set[EventHandler]] = {}
        self._lock = asyncio.Lock()

        if backend == "redis":
            self._init_redis()

    def _init_redis(self):
        """Initialize Redis pub/sub."""
        try:
            import redis.asyncio as redis
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
            logger.info("Redis event bus initialized")
        except ImportError:
            logger.warning("redis package not installed, falling back to memory")
            self.backend = "memory"

    async def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe to an event type."""
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = set()
            self._subscribers[event_type].add(handler)
            logger.debug(f"Subscribed to {event_type.value}")

    async def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe from an event type."""
        async with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type].discard(handler)

    async def publish(self, event: Event):
        """Publish an event to all subscribers."""
        logger.debug(f"Publishing {event.event_type.value} for session {event.session_id}")

        if self.backend == "redis":
            await self._publish_redis(event)
        else:
            await self._publish_memory(event)

    async def _publish_memory(self, event: Event):
        """Publish to in-memory subscribers."""
        if event.event_type in self._subscribers:
            handlers = list(self._subscribers[event.event_type])

            # Call handlers concurrently
            await asyncio.gather(
                *[self._safe_handle(handler, event) for handler in handlers],
                return_exceptions=True
            )

    async def _publish_redis(self, event: Event):
        """Publish to Redis pub/sub."""
        import json

        channel = f"events:{event.event_type.value}"
        message = json.dumps({
            "session_id": event.session_id,
            "timestamp": event.timestamp,
            "data": event.data,
            "correlation_id": event.correlation_id
        })

        await self.redis.publish(channel, message)

    async def _safe_handle(self, handler: EventHandler, event: Event):
        """Call handler with error handling."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error in event handler: {e}", exc_info=True)

    async def close(self):
        """Clean up resources."""
        if self.backend == "redis" and hasattr(self, 'redis'):
            await self.redis.close()

# Global event bus instance
_event_bus = None

def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(backend=os.getenv("EVENT_BUS_BACKEND", "memory"))
    return _event_bus
```

#### WebSocket Server

**File:** `src/web_ui/api/websocket_server.py`

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set
import json
import asyncio
from datetime import datetime

from src.events.event_bus import get_event_bus, Event, EventType

app = FastAPI(title="Browser Use Web UI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}

class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.event_bus = get_event_bus()

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()

        self.active_connections[session_id].add(websocket)

        # Publish connection event
        await self.event_bus.publish(Event(
            event_type=EventType.UI_CONNECTED,
            session_id=session_id,
            timestamp=datetime.now().timestamp(),
            data={"client": "websocket"}
        ))

    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)

            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        """Send message to all connections for a session."""
        if session_id in self.active_connections:
            disconnected = []

            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, session_id)

    async def broadcast(self, message: dict):
        """Broadcast to all connections."""
        for session_connections in self.active_connections.values():
            for connection in session_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive commands from client
            data = await websocket.receive_json()

            # Handle UI commands
            if data.get("type") == "command":
                await handle_ui_command(session_id, data)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, session_id)

async def handle_ui_command(session_id: str, data: dict):
    """Handle commands from UI."""
    event_bus = get_event_bus()

    await event_bus.publish(Event(
        event_type=EventType.UI_COMMAND,
        session_id=session_id,
        timestamp=datetime.now().timestamp(),
        data=data
    ))

# Subscribe to events and forward to WebSocket clients
async def forward_events_to_websocket():
    """Subscribe to all events and forward to WebSocket clients."""
    event_bus = get_event_bus()

    async def event_handler(event: Event):
        """Forward event to WebSocket clients."""
        message = {
            "type": event.event_type.value,
            "timestamp": event.timestamp,
            "data": event.data
        }
        await manager.send_to_session(event.session_id, message)

    # Subscribe to all event types
    for event_type in EventType:
        await event_bus.subscribe(event_type, event_handler)

@app.on_event("startup")
async def startup():
    """Start event forwarding on startup."""
    asyncio.create_task(forward_events_to_websocket())

@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown."""
    event_bus = get_event_bus()
    await event_bus.close()

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Session management endpoints
@app.post("/api/sessions/{session_id}/start")
async def start_agent_session(session_id: str, task: dict):
    """Start an agent session."""
    # This would trigger the agent to start
    # Implementation depends on how we integrate with existing code
    pass

@app.post("/api/sessions/{session_id}/stop")
async def stop_agent_session(session_id: str):
    """Stop an agent session."""
    pass
```

#### Integration with Agent

**File:** `src/web_ui/agent/browser_use/event_driven_agent.py`

```python
from src.events.event_bus import get_event_bus, Event, EventType
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from datetime import datetime

class EventDrivenAgent(BrowserUseAgent):
    """Agent that publishes events for all operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_bus = get_event_bus()
        self.session_id = kwargs.get("session_id", str(uuid.uuid4()))

    async def run(self, max_steps: int = 100):
        """Run with event publishing."""

        # Publish start event
        await self.event_bus.publish(Event(
            event_type=EventType.AGENT_START,
            session_id=self.session_id,
            timestamp=datetime.now().timestamp(),
            data={
                "task": self.task,
                "max_steps": max_steps
            }
        ))

        try:
            for step in range(max_steps):
                # Publish step event
                await self.event_bus.publish(Event(
                    event_type=EventType.AGENT_STEP,
                    session_id=self.session_id,
                    timestamp=datetime.now().timestamp(),
                    data={"step": step, "max_steps": max_steps}
                ))

                # Get LLM response
                await self.event_bus.publish(Event(
                    event_type=EventType.LLM_REQUEST,
                    session_id=self.session_id,
                    timestamp=datetime.now().timestamp(),
                    data={"messages": self.message_manager.get_messages()}
                ))

                # Stream LLM tokens
                async for token in self.llm.astream(messages):
                    await self.event_bus.publish(Event(
                        event_type=EventType.LLM_TOKEN,
                        session_id=self.session_id,
                        timestamp=datetime.now().timestamp(),
                        data={"token": token}
                    ))

                # Execute actions
                for action in model_output.actions:
                    await self.event_bus.publish(Event(
                        event_type=EventType.ACTION_START,
                        session_id=self.session_id,
                        timestamp=datetime.now().timestamp(),
                        data={
                            "action": action.name,
                            "params": action.params
                        }
                    ))

                    try:
                        result = await self.execute_action(action)

                        await self.event_bus.publish(Event(
                            event_type=EventType.ACTION_COMPLETE,
                            session_id=self.session_id,
                            timestamp=datetime.now().timestamp(),
                            data={
                                "action": action.name,
                                "result": result
                            }
                        ))
                    except Exception as e:
                        await self.event_bus.publish(Event(
                            event_type=EventType.ACTION_ERROR,
                            session_id=self.session_id,
                            timestamp=datetime.now().timestamp(),
                            data={
                                "action": action.name,
                                "error": str(e)
                            }
                        ))

                if model_output.done:
                    break

            # Publish completion
            await self.event_bus.publish(Event(
                event_type=EventType.AGENT_COMPLETE,
                session_id=self.session_id,
                timestamp=datetime.now().timestamp(),
                data={
                    "success": True,
                    "output": model_output.output
                }
            ))

            return self.state.history

        except Exception as e:
            await self.event_bus.publish(Event(
                event_type=EventType.AGENT_ERROR,
                session_id=self.session_id,
                timestamp=datetime.now().timestamp(),
                data={"error": str(e)}
            ))
            raise
```

---

## Feature 4.2: Plugin System

### Plugin Architecture

```
src/web_ui/plugins/
├── __init__.py
├── plugin_manager.py         # Core plugin management
├── plugin_interface.py        # Base plugin class
├── plugin_loader.py           # Dynamic loading
├── plugin_registry.py         # Registry of installed plugins
└── builtin/                   # Built-in plugins
    ├── pdf_extractor/
    │   ├── __init__.py
    │   ├── plugin.py
    │   └── manifest.json
    ├── api_integrator/
    │   ├── __init__.py
    │   ├── plugin.py
    │   └── manifest.json
    └── screenshot_annotator/
        ├── __init__.py
        ├── plugin.py
        └── manifest.json
```

### Plugin Interface

**File:** `src/web_ui/plugins/plugin_interface.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class PluginManifest:
    """Plugin metadata."""
    id: str
    name: str
    version: str
    author: str
    description: str
    dependencies: List[str] = None
    permissions: List[str] = None

    # Entry points
    controller_actions: List[str] = None  # New browser actions
    ui_components: List[str] = None       # New UI tabs/components
    event_handlers: Dict[str, str] = None  # Event type -> handler method

class Plugin(ABC):
    """
    Base class for all plugins.

    Plugins can extend functionality by:
    1. Adding new browser actions
    2. Adding UI components
    3. Listening to events
    4. Providing utilities
    """

    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.enabled = True

    @abstractmethod
    async def initialize(self):
        """Initialize the plugin. Called when plugin is loaded."""
        pass

    @abstractmethod
    async def shutdown(self):
        """Clean up resources. Called when plugin is unloaded."""
        pass

    def get_controller_actions(self) -> Dict[str, callable]:
        """
        Return custom browser actions this plugin provides.

        Returns:
            Dict mapping action name to action function
        """
        return {}

    def get_ui_components(self) -> Dict[str, callable]:
        """
        Return UI components this plugin provides.

        Returns:
            Dict mapping component name to Gradio component function
        """
        return {}

    def get_event_handlers(self) -> Dict[str, callable]:
        """
        Return event handlers this plugin provides.

        Returns:
            Dict mapping event type to handler function
        """
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for plugin configuration.

        Used to generate configuration UI.
        """
        return {}
```

### Example Plugin: PDF Extractor

**File:** `src/web_ui/plugins/builtin/pdf_extractor/plugin.py`

```python
from src.plugins.plugin_interface import Plugin, PluginManifest
from browser_use.controller.views import ActionResult
from browser_use.browser.context import BrowserContext
import PyPDF2

class PDFExtractorPlugin(Plugin):
    """Plugin to extract text from PDF files."""

    def __init__(self):
        manifest = PluginManifest(
            id="pdf_extractor",
            name="PDF Text Extractor",
            version="1.0.0",
            author="Browser Use Team",
            description="Extract text content from PDF files",
            dependencies=["PyPDF2"],
            permissions=["file_system"],
            controller_actions=["extract_pdf_text"]
        )
        super().__init__(manifest)

    async def initialize(self):
        """Initialize the plugin."""
        print(f"PDF Extractor plugin v{self.manifest.version} initialized")

    async def shutdown(self):
        """Shutdown the plugin."""
        print("PDF Extractor plugin shut down")

    def get_controller_actions(self):
        """Register custom actions."""
        return {
            "extract_pdf_text": self.extract_pdf_text
        }

    async def extract_pdf_text(
        self,
        pdf_url: str,
        browser_context: BrowserContext
    ) -> ActionResult:
        """
        Extract text from a PDF file.

        Args:
            pdf_url: URL of the PDF file
            browser_context: Browser context for downloading

        Returns:
            ActionResult with extracted text
        """
        try:
            # Download PDF
            page = await browser_context.get_current_page()
            response = await page.request.get(pdf_url)
            pdf_bytes = await response.body()

            # Extract text
            from io import BytesIO
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page_obj = pdf_reader.pages[page_num]
                text += page_obj.extract_text()

            return ActionResult(
                extracted_content=text,
                error=None,
                include_in_memory=True
            )

        except Exception as e:
            return ActionResult(
                extracted_content=None,
                error=f"Failed to extract PDF: {str(e)}",
                include_in_memory=True
            )
```

**File:** `src/web_ui/plugins/builtin/pdf_extractor/manifest.json`

```json
{
  "id": "pdf_extractor",
  "name": "PDF Text Extractor",
  "version": "1.0.0",
  "author": "Browser Use Team",
  "description": "Extract text content from PDF files downloaded by the browser",
  "homepage": "https://github.com/browser-use/web-ui/tree/main/plugins/pdf_extractor",
  "license": "MIT",
  "dependencies": {
    "python": ">=3.11",
    "packages": ["PyPDF2>=3.0.0"]
  },
  "permissions": [
    "file_system",
    "network"
  ],
  "entry_points": {
    "controller_actions": ["extract_pdf_text"],
    "ui_components": [],
    "event_handlers": {}
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "max_file_size_mb": {
        "type": "number",
        "default": 10,
        "description": "Maximum PDF file size to process (in MB)"
      },
      "extract_images": {
        "type": "boolean",
        "default": false,
        "description": "Also extract images from PDF"
      }
    }
  }
}
```

### Plugin Manager

**File:** `src/web_ui/plugins/plugin_manager.py`

```python
from typing import Dict, List, Optional
from pathlib import Path
import importlib.util
import json
import logging

from src.plugins.plugin_interface import Plugin, PluginManifest

logger = logging.getLogger(__name__)

class PluginManager:
    """Manage plugin lifecycle and registration."""

    def __init__(self, plugin_dir: str = "./plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Plugin] = {}
        self.enabled_plugins: set = set()

    async def discover_plugins(self) -> List[PluginManifest]:
        """Discover all available plugins."""
        plugins = []

        # Scan plugin directory
        if not self.plugin_dir.exists():
            return plugins

        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue

            manifest_path = plugin_path / "manifest.json"
            if not manifest_path.exists():
                continue

            try:
                with open(manifest_path) as f:
                    manifest_data = json.load(f)

                manifest = PluginManifest(**manifest_data)
                plugins.append(manifest)

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_path.name}: {e}")

        return plugins

    async def load_plugin(self, plugin_id: str) -> bool:
        """Load and initialize a plugin."""
        try:
            plugin_path = self.plugin_dir / plugin_id

            # Load manifest
            with open(plugin_path / "manifest.json") as f:
                manifest_data = json.load(f)
            manifest = PluginManifest(**manifest_data)

            # Dynamically import plugin module
            spec = importlib.util.spec_from_file_location(
                f"plugins.{plugin_id}",
                plugin_path / "plugin.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Instantiate plugin
            plugin_class = getattr(module, f"{plugin_id.title().replace('_', '')}Plugin")
            plugin = plugin_class()

            # Initialize
            await plugin.initialize()

            # Register
            self.plugins[plugin_id] = plugin
            self.enabled_plugins.add(plugin_id)

            logger.info(f"Loaded plugin: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}", exc_info=True)
            return False

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin."""
        if plugin_id not in self.plugins:
            return False

        try:
            plugin = self.plugins[plugin_id]
            await plugin.shutdown()

            del self.plugins[plugin_id]
            self.enabled_plugins.discard(plugin_id)

            logger.info(f"Unloaded plugin: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a loaded plugin."""
        return self.plugins.get(plugin_id)

    def get_all_controller_actions(self) -> Dict[str, callable]:
        """Get all custom actions from all enabled plugins."""
        actions = {}

        for plugin_id in self.enabled_plugins:
            plugin = self.plugins[plugin_id]
            actions.update(plugin.get_controller_actions())

        return actions

# Global plugin manager
_plugin_manager = None

def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
```

---

## Feature 4.3: Multi-Agent Orchestration

### LangGraph Integration

```python
# File: src/web_ui/orchestration/multi_agent_graph.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    """State shared between agents."""
    task: str
    results: Annotated[list, add]  # Accumulate results
    current_agent: str
    iteration: int
    max_iterations: int

def create_multi_agent_workflow(agents: List[BrowserUseAgent]):
    """
    Create a LangGraph workflow with multiple browser agents.

    Example workflow:
    1. Research Agent: Search and gather information
    2. Analysis Agent: Analyze gathered data
    3. Report Agent: Generate final report
    """

    workflow = StateGraph(AgentState)

    # Add agent nodes
    for agent in agents:
        workflow.add_node(agent.name, agent.run)

    # Define edges (agent transitions)
    workflow.add_edge("research_agent", "analysis_agent")
    workflow.add_edge("analysis_agent", "report_agent")
    workflow.add_edge("report_agent", END)

    # Set entry point
    workflow.set_entry_point("research_agent")

    return workflow.compile()

# Example usage
research_agent = BrowserUseAgent(task="Research topic X", name="research_agent")
analysis_agent = BrowserUseAgent(task="Analyze research results", name="analysis_agent")
report_agent = BrowserUseAgent(task="Generate report", name="report_agent")

app = create_multi_agent_workflow([research_agent, analysis_agent, report_agent])

# Run workflow
result = await app.ainvoke({
    "task": "Research and report on AI browser automation tools",
    "results": [],
    "current_agent": "research_agent",
    "iteration": 0,
    "max_iterations": 10
})
```

---

## Success Metrics

- [ ] Event bus handles 1000+ events/sec
- [ ] WebSocket supports 100+ concurrent connections
- [ ] Plugin system allows dynamic loading/unloading
- [ ] Multi-agent workflows complete successfully
- [ ] <5% performance overhead from events

---

**Status:** Detailed architecture specification complete
**Next:** Implementation in sprints 8-10