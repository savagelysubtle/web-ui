# Phase 2: Visual Workflow Builder & Templates

**Timeline:** Weeks 3-6
**Priority:** High (Competitive Differentiator)
**Complexity:** High

## Overview

Create a visual workflow builder using React Flow to visualize agent execution in real-time, plus a record/replay system and template marketplace for reusable workflows.

---

## Feature 2.1: Real-time Workflow Visualization

### Goal
Transform agent execution from a black box into a transparent, visual workflow graph that updates in real-time.

### Architecture

#### Component Structure
```
src/web_ui/webui/components/workflow_visualizer/
├── __init__.py
├── workflow_graph.py          # Main React Flow component
├── node_types.py               # Custom node definitions
├── edge_types.py               # Custom edge styles
├── layout_engine.py            # Auto-layout logic
└── export_utils.py             # Export to PNG/SVG/JSON
```

### Implementation

#### Custom Gradio Component (React Flow)
**File:** `src/web_ui/webui/components/workflow_visualizer/workflow_graph.py`

```python
import gradio as gr
from typing import List, Dict, Any
import json

# We'll create a custom Gradio component using the Custom Components framework
# https://www.gradio.app/guides/custom-components-in-five-minutes

class WorkflowGraph(gr.Component):
    """
    Custom Gradio component for React Flow workflow visualization.
    """

    def __init__(
        self,
        value: Dict[str, Any] = None,
        height: int = 600,
        **kwargs
    ):
        self.height = height
        super().__init__(value=value or {"nodes": [], "edges": []}, **kwargs)

    def preprocess(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process user interactions (node clicks, etc.)"""
        return payload

    def postprocess(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """Format data for frontend"""
        return value

    def get_template_context(self):
        return {
            "height": self.height,
        }

    def as_example(self):
        return {
            "nodes": [
                {"id": "1", "type": "start", "data": {"label": "Start"}},
                {"id": "2", "type": "action", "data": {"label": "Navigate"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"}
            ]
        }
```

#### React Frontend Component
**File:** `src/web_ui/webui/components/workflow_visualizer/WorkflowGraph.tsx` (new)

```typescript
import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    NodeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom Node Types
import ActionNode from './nodes/ActionNode';
import ThinkingNode from './nodes/ThinkingNode';
import ResultNode from './nodes/ResultNode';

const nodeTypes: NodeTypes = {
    action: ActionNode,
    thinking: ThinkingNode,
    result: ResultNode,
};

interface WorkflowGraphProps {
    value: {
        nodes: Node[];
        edges: Edge[];
    };
    onChange: (value: { nodes: Node[]; edges: Edge[] }) => void;
}

const WorkflowGraph: React.FC<WorkflowGraphProps> = ({ value, onChange }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState(value.nodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(value.edges);
    const [selectedNode, setSelectedNode] = useState<Node | null>(null);

    // Update when value changes (from Python backend)
    useEffect(() => {
        setNodes(value.nodes);
        setEdges(value.edges);
    }, [value]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges]
    );

    const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        setSelectedNode(node);
        // Send event back to Python
        onChange({ nodes, edges });
    }, [nodes, edges, onChange]);

    return (
        <div style={{ width: '100%', height: '600px' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                nodeTypes={nodeTypes}
                fitView
            >
                <Background />
                <Controls />
                <MiniMap />
            </ReactFlow>

            {selectedNode && (
                <NodeDetailsPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
            )}
        </div>
    );
};

export default WorkflowGraph;
```

#### Custom Node Components
**File:** `src/web_ui/webui/components/workflow_visualizer/nodes/ActionNode.tsx`

```typescript
import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface ActionNodeData {
    label: string;
    action: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    duration?: number;
    screenshot?: string;
}

const ActionNode: React.FC<NodeProps<ActionNodeData>> = ({ data }) => {
    const statusColors = {
        pending: '#9E9E9E',
        running: '#2196F3',
        completed: '#4CAF50',
        error: '#F44336',
    };

    const statusIcons = {
        pending: '⏳',
        running: '▶️',
        completed: '✅',
        error: '❌',
    };

    return (
        <div
            style={{
                background: 'white',
                border: `2px solid ${statusColors[data.status]}`,
                borderRadius: '8px',
                padding: '12px',
                minWidth: '180px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
        >
            <Handle type="target" position={Position.Top} />

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <span style={{ fontSize: '1.2em' }}>{statusIcons[data.status]}</span>
                <strong>{data.label}</strong>
            </div>

            <div style={{ fontSize: '0.85em', color: '#666', marginBottom: '4px' }}>
                {data.action}
            </div>

            {data.duration && (
                <div style={{ fontSize: '0.75em', color: '#999' }}>
                    {data.duration}ms
                </div>
            )}

            {data.status === 'running' && (
                <div
                    style={{
                        marginTop: '8px',
                        height: '2px',
                        background: '#E0E0E0',
                        borderRadius: '1px',
                        overflow: 'hidden',
                    }}
                >
                    <div
                        style={{
                            height: '100%',
                            background: statusColors.running,
                            animation: 'progress 1.5s ease-in-out infinite',
                        }}
                    />
                </div>
            )}

            <Handle type="source" position={Position.Bottom} />
        </div>
    );
};

export default memo(ActionNode);
```

#### Python Integration
**File:** `src/web_ui/agent/browser_use/browser_use_agent.py`

```python
from typing import List, Dict, Any
import time

class WorkflowGraphBuilder:
    """Builds workflow graph data from agent execution."""

    def __init__(self):
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.node_counter = 0

    def add_start_node(self, task: str) -> str:
        """Add the starting node."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1

        self.nodes.append({
            "id": node_id,
            "type": "start",
            "position": {"x": 250, "y": 0},
            "data": {
                "label": "Start",
                "task": task
            }
        })
        return node_id

    def add_thinking_node(self, parent_id: str, content: str) -> str:
        """Add a thinking/reasoning node."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1

        # Calculate position based on parent
        parent_node = next((n for n in self.nodes if n["id"] == parent_id), None)
        y_pos = parent_node["position"]["y"] + 120 if parent_node else 120

        self.nodes.append({
            "id": node_id,
            "type": "thinking",
            "position": {"x": 250, "y": y_pos},
            "data": {
                "label": "Thinking",
                "content": content,
                "status": "running"
            }
        })

        # Add edge from parent
        self.edges.append({
            "id": f"edge_{parent_id}_{node_id}",
            "source": parent_id,
            "target": node_id,
            "animated": True
        })

        return node_id

    def add_action_node(
        self,
        parent_id: str,
        action: str,
        params: Dict[str, Any],
        status: str = "pending"
    ) -> str:
        """Add an action node."""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1

        parent_node = next((n for n in self.nodes if n["id"] == parent_id), None)
        y_pos = parent_node["position"]["y"] + 120 if parent_node else 120

        self.nodes.append({
            "id": node_id,
            "type": "action",
            "position": {"x": 250, "y": y_pos},
            "data": {
                "label": action.replace("_", " ").title(),
                "action": str(params),
                "status": status
            }
        })

        self.edges.append({
            "id": f"edge_{parent_id}_{node_id}",
            "source": parent_id,
            "target": node_id
        })

        return node_id

    def update_node_status(
        self,
        node_id: str,
        status: str,
        duration: float = None,
        result: Any = None
    ):
        """Update a node's status."""
        node = next((n for n in self.nodes if n["id"] == node_id), None)
        if node:
            node["data"]["status"] = status
            if duration:
                node["data"]["duration"] = duration
            if result:
                node["data"]["result"] = str(result)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for Gradio component."""
        return {
            "nodes": self.nodes,
            "edges": self.edges
        }


class BrowserUseAgent(Agent):
    """Enhanced agent with workflow visualization."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow_graph = WorkflowGraphBuilder()

    async def run_with_visualization(
        self,
        max_steps: int = 100
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run agent and yield workflow graph updates."""

        # Add start node
        current_node = self.workflow_graph.add_start_node(self.task)

        for step in range(max_steps):
            # Add thinking node
            thinking_node = self.workflow_graph.add_thinking_node(
                current_node,
                "Analyzing current state..."
            )
            yield self.workflow_graph.to_dict()

            # Get LLM response
            model_output = await self.get_next_action()

            # Update thinking node as complete
            self.workflow_graph.update_node_status(thinking_node, "completed")
            yield self.workflow_graph.to_dict()

            # Add action nodes for each action
            for action in model_output.actions:
                action_node = self.workflow_graph.add_action_node(
                    thinking_node,
                    action.name,
                    action.params,
                    status="running"
                )
                yield self.workflow_graph.to_dict()

                # Execute action
                start_time = time.time()
                try:
                    result = await self.execute_action(action)
                    duration = (time.time() - start_time) * 1000

                    self.workflow_graph.update_node_status(
                        action_node,
                        "completed",
                        duration=duration,
                        result=result
                    )
                except Exception as e:
                    self.workflow_graph.update_node_status(
                        action_node,
                        "error",
                        result=str(e)
                    )

                yield self.workflow_graph.to_dict()
                current_node = action_node

            # Check if done
            if model_output.done:
                break

        return self.workflow_graph.to_dict()
```

#### Gradio Tab Integration
**File:** `src/web_ui/webui/components/browser_use_agent_tab.py`

```python
from src.webui.components.workflow_visualizer.workflow_graph import WorkflowGraph

def create_browser_use_agent_tab(ui_manager: WebuiManager):
    with gr.Column():
        # Add workflow graph
        with gr.Tab("💬 Chat View"):
            chatbot = gr.Chatbot(...)
            # ... existing chat UI

        with gr.Tab("📊 Workflow View"):
            gr.Markdown("### Real-time Execution Graph")

            workflow_graph = WorkflowGraph(height=700)

            # Node details panel
            with gr.Accordion("Node Details", open=False):
                node_info = gr.JSON(label="Selected Node Data")

        # Update function
        async def run_with_workflow_viz(task, *args):
            """Run agent with both chat and workflow updates."""

            async for graph_data in agent.run_with_visualization():
                # Update workflow graph
                yield {
                    workflow_graph: graph_data,
                    chatbot: chatbot_messages,
                }
```

---

## Feature 2.2: Record & Replay System

### Architecture

```
src/web_ui/recorder/
├── __init__.py
├── action_recorder.py      # Records browser actions
├── workflow_generator.py    # Generates workflow from recording
├── parameter_extractor.py   # Identifies parameterizable values
└── replay_engine.py         # Replays recorded workflows
```

### Recording Flow

1. **User clicks "Record"**
2. **Browser opens in recording mode** (special instrumentation)
3. **All actions logged** (clicks, typing, navigation, etc.)
4. **User clicks "Stop Recording"**
5. **System analyzes actions** and suggests:
   - Task description
   - Parameterizable fields (e.g., "Search query", "Email address")
   - Reusable steps
6. **User reviews/edits**
7. **Saves as template**

### Implementation

**File:** `src/web_ui/recorder/action_recorder.py`

```python
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class RecordedAction:
    """A single recorded browser action."""
    timestamp: float
    action_type: str  # click, type, navigate, etc.
    selector: str
    value: Any
    screenshot: str  # base64
    url: str
    description: str  # human-readable

class ActionRecorder:
    """Records browser actions for later playback."""

    def __init__(self, browser_context):
        self.browser_context = browser_context
        self.actions: List[RecordedAction] = []
        self.recording = False
        self.start_time = None

    async def start_recording(self):
        """Start recording browser actions."""
        self.recording = True
        self.start_time = datetime.now().timestamp()
        self.actions = []

        # Inject recording script into all pages
        await self.browser_context.add_init_script("""
            // Intercept clicks
            document.addEventListener('click', (e) => {
                const selector = getUniqueSelector(e.target);
                window._recordedActions = window._recordedActions || [];
                window._recordedActions.push({
                    type: 'click',
                    selector: selector,
                    timestamp: Date.now(),
                    text: e.target.innerText?.substring(0, 50)
                });
            }, true);

            // Intercept input
            document.addEventListener('input', (e) => {
                const selector = getUniqueSelector(e.target);
                window._recordedActions = window._recordedActions || [];
                window._recordedActions.push({
                    type: 'input',
                    selector: selector,
                    value: e.target.value,
                    timestamp: Date.now()
                });
            }, true);

            // Helper: Generate unique selector
            function getUniqueSelector(element) {
                if (element.id) return `#${element.id}`;
                if (element.className) {
                    const classes = element.className.split(' ').filter(c => c);
                    if (classes.length) return `.${classes[0]}`;
                }
                // Fallback: nth-child
                const parent = element.parentElement;
                if (parent) {
                    const index = Array.from(parent.children).indexOf(element);
                    return `${getUniqueSelector(parent)} > :nth-child(${index + 1})`;
                }
                return element.tagName.toLowerCase();
            }
        """)

    async def stop_recording(self) -> List[RecordedAction]:
        """Stop recording and return recorded actions."""
        self.recording = False

        # Fetch recorded actions from page
        pages = self.browser_context.pages
        for page in pages:
            try:
                recorded = await page.evaluate("window._recordedActions || []")

                for action_data in recorded:
                    # Take screenshot at this point (or retrieve from history)
                    screenshot = await page.screenshot(type="png")
                    screenshot_b64 = base64.b64encode(screenshot).decode()

                    action = RecordedAction(
                        timestamp=action_data["timestamp"],
                        action_type=action_data["type"],
                        selector=action_data["selector"],
                        value=action_data.get("value", action_data.get("text", "")),
                        screenshot=screenshot_b64,
                        url=page.url,
                        description=self._generate_description(action_data)
                    )
                    self.actions.append(action)

            except Exception as e:
                logger.warning(f"Failed to get recorded actions from page: {e}")

        return self.actions

    def _generate_description(self, action_data: Dict) -> str:
        """Generate human-readable description of action."""
        action_type = action_data["type"]
        selector = action_data["selector"]

        if action_type == "click":
            text = action_data.get("text", "")
            return f"Click on '{text[:30]}'" if text else f"Click {selector}"
        elif action_type == "input":
            value = action_data.get("value", "")
            return f"Type '{value[:30]}...' into {selector}"
        else:
            return f"{action_type} {selector}"

    def save_to_file(self, filepath: str):
        """Save recording to JSON file."""
        data = {
            "version": "1.0",
            "recorded_at": datetime.now().isoformat(),
            "actions": [asdict(action) for action in self.actions]
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> List[RecordedAction]:
        """Load recording from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        return [RecordedAction(**action) for action in data["actions"]]
```

### Workflow Generation

**File:** `src/web_ui/recorder/workflow_generator.py`

```python
from typing import List, Dict, Any
import re

class WorkflowGenerator:
    """Generates reusable workflows from recorded actions."""

    def __init__(self, actions: List[RecordedAction]):
        self.actions = actions

    def generate_workflow(self) -> Dict[str, Any]:
        """Generate workflow with identified parameters."""

        # Group actions into logical steps
        steps = self._group_actions_into_steps()

        # Extract parameters (values that should be configurable)
        parameters = self._extract_parameters()

        # Generate task description using LLM (optional)
        task_description = self._generate_task_description()

        return {
            "name": task_description,
            "description": f"Recorded workflow with {len(steps)} steps",
            "parameters": parameters,
            "steps": steps,
            "metadata": {
                "total_actions": len(self.actions),
                "duration": self._calculate_duration(),
                "urls_visited": self._get_unique_urls()
            }
        }

    def _group_actions_into_steps(self) -> List[Dict[str, Any]]:
        """Group related actions into logical steps."""
        steps = []
        current_step = []

        for i, action in enumerate(self.actions):
            current_step.append(action)

            # Create new step after navigation or significant pause
            is_navigation = action.action_type == "navigate"
            is_last = i == len(self.actions) - 1

            if is_navigation or is_last:
                if current_step:
                    steps.append({
                        "name": self._infer_step_name(current_step),
                        "actions": current_step
                    })
                    current_step = []

        return steps

    def _extract_parameters(self) -> List[Dict[str, Any]]:
        """Identify parameterizable values from actions."""
        parameters = []
        param_id = 1

        for action in self.actions:
            if action.action_type == "input":
                # Input values are likely parameters
                param_name = self._suggest_param_name(action)
                parameters.append({
                    "id": f"param_{param_id}",
                    "name": param_name,
                    "type": "string",
                    "default_value": action.value,
                    "description": f"Value to enter in {action.selector}",
                    "action_index": self.actions.index(action)
                })
                param_id += 1

        return parameters

    def _suggest_param_name(self, action: RecordedAction) -> str:
        """Suggest a parameter name based on action context."""
        selector = action.selector.lower()

        # Common patterns
        if "email" in selector:
            return "email"
        elif "password" in selector:
            return "password"
        elif "search" in selector or "query" in selector:
            return "search_query"
        elif "name" in selector:
            return "name"
        else:
            # Generic name
            return f"input_{action.selector.replace('#', '').replace('.', '_')[:20]}"

    def _generate_task_description(self) -> str:
        """Generate a description of what this workflow does."""
        # Simple heuristic-based description
        url = self.actions[0].url if self.actions else ""
        action_count = len(self.actions)

        if "google.com" in url and any("search" in a.selector for a in self.actions):
            return "Search on Google"
        elif "linkedin.com" in url:
            return "LinkedIn automation"
        elif any(a.action_type == "input" for a in self.actions):
            return "Fill out form"
        else:
            return f"Recorded workflow ({action_count} actions)"

    def _calculate_duration(self) -> float:
        """Calculate total duration of recording."""
        if not self.actions:
            return 0.0
        return self.actions[-1].timestamp - self.actions[0].timestamp

    def _get_unique_urls(self) -> List[str]:
        """Get list of unique URLs visited."""
        return list(set(action.url for action in self.actions))
```

### Replay Engine

**File:** `src/web_ui/recorder/replay_engine.py`

```python
class ReplayEngine:
    """Replays recorded workflows with parameter substitution."""

    def __init__(self, browser_context):
        self.browser_context = browser_context

    async def replay_workflow(
        self,
        workflow: Dict[str, Any],
        parameters: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Replay a recorded workflow with given parameters."""

        parameters = parameters or {}

        for step in workflow["steps"]:
            yield f"Executing step: {step['name']}"

            for action in step["actions"]:
                # Check if this action has a parameter
                param = self._get_parameter_for_action(workflow, action)
                if param and param["id"] in parameters:
                    # Substitute parameter value
                    action.value = parameters[param["id"]]

                # Execute action
                await self._execute_action(action)
                yield f"Completed: {action.description}"

        yield "Workflow completed successfully"

    async def _execute_action(self, action: RecordedAction):
        """Execute a single recorded action."""
        page = await self.browser_context.get_current_page()

        if action.action_type == "click":
            await page.click(action.selector)
        elif action.action_type == "input":
            await page.fill(action.selector, str(action.value))
        elif action.action_type == "navigate":
            await page.goto(action.url)
        else:
            logger.warning(f"Unknown action type: {action.action_type}")

    def _get_parameter_for_action(
        self,
        workflow: Dict[str, Any],
        action: RecordedAction
    ) -> Dict[str, Any] | None:
        """Find parameter definition for an action."""
        for param in workflow["parameters"]:
            if param["action_index"] == workflow["steps"][0]["actions"].index(action):
                return param
        return None
```

---

## Feature 2.3: Template Marketplace

### Database Schema

```python
# templates_db.py
from dataclasses import dataclass
from typing import List, Dict, Any
import json
import sqlite3
from pathlib import Path

@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    category: str  # e.g., "E-commerce", "Research", "Data Entry"
    author: str
    tags: List[str]
    parameters: List[Dict[str, Any]]
    workflow_data: Dict[str, Any]
    usage_count: int
    rating: float
    created_at: str
    updated_at: str

class TemplateDatabase:
    """SQLite database for workflow templates."""

    def __init__(self, db_path: str = "./tmp/templates.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                author TEXT,
                tags TEXT,  -- JSON array
                parameters TEXT,  -- JSON
                workflow_data TEXT,  -- JSON
                usage_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_id TEXT,
                user_id TEXT,
                executed_at TEXT,
                success BOOLEAN,
                FOREIGN KEY(template_id) REFERENCES templates(id)
            )
        """)

        conn.commit()
        conn.close()

    def save_template(self, template: WorkflowTemplate):
        """Save a workflow template."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO templates VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template.id,
            template.name,
            template.description,
            template.category,
            template.author,
            json.dumps(template.tags),
            json.dumps(template.parameters),
            json.dumps(template.workflow_data),
            template.usage_count,
            template.rating,
            template.created_at,
            template.updated_at
        ))

        conn.commit()
        conn.close()

    def get_templates_by_category(self, category: str) -> List[WorkflowTemplate]:
        """Get all templates in a category."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM templates WHERE category = ? ORDER BY usage_count DESC
        """, (category,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_template(row) for row in rows]

    def search_templates(self, query: str) -> List[WorkflowTemplate]:
        """Search templates by name, description, or tags."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM templates
            WHERE name LIKE ? OR description LIKE ? OR tags LIKE ?
            ORDER BY rating DESC, usage_count DESC
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_template(row) for row in rows]

    def _row_to_template(self, row: sqlite3.Row) -> WorkflowTemplate:
        """Convert database row to WorkflowTemplate."""
        return WorkflowTemplate(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            category=row["category"],
            author=row["author"],
            tags=json.loads(row["tags"]),
            parameters=json.loads(row["parameters"]),
            workflow_data=json.loads(row["workflow_data"]),
            usage_count=row["usage_count"],
            rating=row["rating"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
```

### UI Component

```python
# Template marketplace tab
def create_template_marketplace_tab(ui_manager: WebuiManager):
    """Create template marketplace UI."""

    template_db = TemplateDatabase()

    with gr.Column():
        gr.Markdown("### 📚 Workflow Template Marketplace")

        # Search
        with gr.Row():
            search_input = gr.Textbox(
                placeholder="Search templates...",
                label="Search"
            )
            category_filter = gr.Dropdown(
                choices=["All", "E-commerce", "Research", "Data Entry", "Testing", "Forms"],
                value="All",
                label="Category"
            )

        # Results
        template_gallery = gr.Gallery(
            label="Templates",
            columns=3,
            height="auto"
        )

        # Selected template details
        with gr.Accordion("Template Details", open=False) as details_accordion:
            template_name = gr.Textbox(label="Name", interactive=False)
            template_desc = gr.Textbox(label="Description", interactive=False, lines=3)
            template_params = gr.JSON(label="Parameters")
            use_template_btn = gr.Button("Use This Template", variant="primary")

        # Parameter input (shown when template is selected)
        with gr.Accordion("Configure Parameters", open=False, visible=False) as params_accordion:
            param_inputs = gr.Group()
            run_template_btn = gr.Button("Run Workflow", variant="primary")

        # Event handlers
        def search_templates(query, category):
            if category != "All":
                results = template_db.get_templates_by_category(category)
            else:
                results = template_db.search_templates(query) if query else template_db.get_all_templates()

            # Convert to gallery format (thumbnail images + labels)
            gallery_items = [(t.workflow_data.get("thumbnail", ""), t.name) for t in results]
            return gallery_items

        search_input.change(
            search_templates,
            inputs=[search_input, category_filter],
            outputs=template_gallery
        )

        # ... more event handlers
```

---

## Success Metrics

- [ ] Workflow visualizer renders within 500ms
- [ ] Users can record and replay workflows successfully (90%+ success rate)
- [ ] Template library has 20+ pre-built templates
- [ ] 50%+ of tasks use templates after 2 weeks

---

**Next:** Phase 3 - Observability & Debugging Tools
