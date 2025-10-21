# Phase 3: Observability & Debugging

**Timeline:** Weeks 7-12
**Priority:** High (Professional Tool Requirement)
**Complexity:** Very High

## Overview

Build comprehensive observability and debugging tools to make the agent's decision-making process transparent, traceable, and debuggable - inspired by LangSmith, Chrome DevTools, and Playwright Inspector.

---

## Feature 3.1: Agent Observability Dashboard

### Goal
Provide LangSmith-level insights into agent execution: traces, metrics, costs, and performance analytics.

### Architecture

```
src/web_ui/observability/
├── __init__.py
├── tracer.py                 # Core tracing logic
├── metrics_collector.py      # Metrics aggregation
├── cost_calculator.py        # Token usage & cost tracking
├── trace_visualizer.py       # Trace UI component
└── analytics_dashboard.py    # Analytics & insights
```

### Implementation

#### Trace Data Structure

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class SpanType(Enum):
    """Types of execution spans."""
    AGENT_RUN = "agent_run"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    BROWSER_ACTION = "browser_action"
    RETRIEVAL = "retrieval"

@dataclass
class TraceSpan:
    """A single span in the execution trace."""
    span_id: str
    parent_id: Optional[str]
    span_type: SpanType
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None

    # Inputs & Outputs
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # LLM-specific
    model_name: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost_usd: Optional[float] = None

    # Status
    status: str = "running"  # running, completed, error
    error: Optional[str] = None

    def complete(self, outputs: Dict[str, Any] = None):
        """Mark span as completed."""
        self.end_time = datetime.now().timestamp()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = "completed"
        if outputs:
            self.outputs = outputs

    def error_out(self, error: Exception):
        """Mark span as error."""
        self.end_time = datetime.now().timestamp()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = "error"
        self.error = str(error)

@dataclass
class ExecutionTrace:
    """Complete execution trace with all spans."""
    trace_id: str
    session_id: str
    task: str
    start_time: float
    end_time: Optional[float] = None

    spans: List[TraceSpan] = field(default_factory=list)

    # Aggregated metrics
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    llm_calls: int = 0
    actions_executed: int = 0

    # Outcome
    success: bool = False
    final_output: Optional[Any] = None
    error: Optional[str] = None

    def add_span(self, span: TraceSpan):
        """Add a span to the trace."""
        self.spans.append(span)

        # Update aggregated metrics
        if span.tokens_input:
            self.total_tokens += span.tokens_input
        if span.tokens_output:
            self.total_tokens += span.tokens_output
        if span.cost_usd:
            self.total_cost_usd += span.cost_usd
        if span.span_type == SpanType.LLM_CALL:
            self.llm_calls += 1
        if span.span_type == SpanType.BROWSER_ACTION:
            self.actions_executed += 1

    def get_duration_ms(self) -> float:
        """Get total trace duration."""
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (datetime.now().timestamp() - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "task": self.task,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.get_duration_ms(),
            "spans": [asdict(span) for span in self.spans],
            "total_tokens": self.total_tokens,
            "total_cost_usd": self.total_cost_usd,
            "llm_calls": self.llm_calls,
            "actions_executed": self.actions_executed,
            "success": self.success,
            "final_output": self.final_output,
            "error": self.error
        }
```

#### Tracer Implementation

```python
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging

logger = logging.getLogger(__name__)

class AgentTracer:
    """Tracer for agent execution."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_trace: Optional[ExecutionTrace] = None
        self.span_stack: List[TraceSpan] = []  # Stack for nested spans

    def start_trace(self, task: str) -> ExecutionTrace:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())
        self.current_trace = ExecutionTrace(
            trace_id=trace_id,
            session_id=self.session_id,
            task=task,
            start_time=datetime.now().timestamp()
        )
        return self.current_trace

    def end_trace(self, success: bool, final_output: Any = None, error: str = None):
        """End the current trace."""
        if self.current_trace:
            self.current_trace.end_time = datetime.now().timestamp()
            self.current_trace.success = success
            self.current_trace.final_output = final_output
            self.current_trace.error = error

    @asynccontextmanager
    async def span(
        self,
        name: str,
        span_type: SpanType,
        inputs: Dict[str, Any] = None,
        **metadata
    ) -> AsyncGenerator[TraceSpan, None]:
        """Context manager for creating spans."""

        # Create span
        span_id = str(uuid.uuid4())
        parent_id = self.span_stack[-1].span_id if self.span_stack else None

        span = TraceSpan(
            span_id=span_id,
            parent_id=parent_id,
            span_type=span_type,
            name=name,
            start_time=datetime.now().timestamp(),
            inputs=inputs or {},
            metadata=metadata
        )

        # Push to stack
        self.span_stack.append(span)

        # Add to trace
        if self.current_trace:
            self.current_trace.add_span(span)

        try:
            yield span
            span.complete()
        except Exception as e:
            span.error_out(e)
            raise
        finally:
            # Pop from stack
            if self.span_stack and self.span_stack[-1].span_id == span_id:
                self.span_stack.pop()

    def get_current_trace(self) -> Optional[ExecutionTrace]:
        """Get the current trace."""
        return self.current_trace
```

#### Integration with BrowserUseAgent

```python
# In browser_use_agent.py

from src.observability.tracer import AgentTracer, SpanType
from src.observability.cost_calculator import calculate_llm_cost

class BrowserUseAgent(Agent):
    """Agent with observability built-in."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracer = AgentTracer(session_id=str(uuid.uuid4()))

    async def run(self, max_steps: int = 100) -> AgentHistoryList:
        """Run agent with full tracing."""

        # Start trace
        trace = self.tracer.start_trace(task=self.task)

        try:
            async with self.tracer.span("agent_execution", SpanType.AGENT_RUN, inputs={"task": self.task}):
                for step in range(max_steps):

                    # LLM call span
                    async with self.tracer.span(
                        f"llm_call_step_{step}",
                        SpanType.LLM_CALL,
                        inputs={"messages": self.message_manager.get_messages()},
                        model=self.model_name
                    ) as llm_span:

                        # Get LLM response
                        model_output = await self.get_next_action()

                        # Calculate cost
                        llm_span.model_name = self.model_name
                        llm_span.tokens_input = model_output.metadata.get("input_tokens", 0)
                        llm_span.tokens_output = model_output.metadata.get("output_tokens", 0)
                        llm_span.cost_usd = calculate_llm_cost(
                            model=self.model_name,
                            input_tokens=llm_span.tokens_input,
                            output_tokens=llm_span.tokens_output
                        )

                        llm_span.outputs = {"actions": model_output.actions}

                    # Execute actions
                    for action in model_output.actions:
                        async with self.tracer.span(
                            action.name,
                            SpanType.BROWSER_ACTION,
                            inputs=action.params
                        ) as action_span:

                            result = await self.execute_action(action)
                            action_span.outputs = {"result": result}

                    # Check if done
                    if model_output.done:
                        self.tracer.end_trace(success=True, final_output=model_output.output)
                        break

            return self.state.history

        except Exception as e:
            self.tracer.end_trace(success=False, error=str(e))
            raise
        finally:
            # Save trace to database
            await self._save_trace(trace)

    async def _save_trace(self, trace: ExecutionTrace):
        """Save trace to database for later analysis."""
        # Save to SQLite or send to observability backend
        from src.observability.trace_storage import TraceStorage

        storage = TraceStorage()
        await storage.save_trace(trace)
```

#### Cost Calculator

```python
# cost_calculator.py

# Pricing as of Jan 2025 (USD per 1M tokens)
LLM_PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "claude-3.7-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-opus": {"input": 15.00, "output": 75.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "gemini-pro": {"input": 0.50, "output": 1.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "deepseek-v3": {"input": 0.14, "output": 0.28},
}

def calculate_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int
) -> float:
    """Calculate cost in USD for an LLM call."""

    # Normalize model name
    model_key = model.lower()
    for known_model in LLM_PRICING:
        if known_model in model_key:
            model_key = known_model
            break

    if model_key not in LLM_PRICING:
        logger.warning(f"Unknown model for cost calculation: {model}")
        return 0.0

    pricing = LLM_PRICING[model_key]

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]

    return input_cost + output_cost
```

---

## Feature 3.2: Trace Visualizer UI

### Waterfall Chart Component

```python
# trace_visualizer.py

def create_trace_visualizer() -> gr.Component:
    """Create interactive trace visualizer component."""

    # HTML/CSS for waterfall chart
    waterfall_html = """
    <div id="trace-waterfall" class="trace-waterfall">
        <div class="waterfall-header">
            <div class="waterfall-label">Span</div>
            <div class="waterfall-timeline">Timeline</div>
            <div class="waterfall-duration">Duration</div>
        </div>
        <div class="waterfall-body" id="waterfall-body">
            <!-- Spans will be inserted here -->
        </div>
    </div>

    <style>
        .trace-waterfall {
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }

        .waterfall-header {
            display: grid;
            grid-template-columns: 300px 1fr 120px;
            background: #f5f5f5;
            padding: 12px;
            font-weight: 600;
            border-bottom: 2px solid #e0e0e0;
        }

        .waterfall-body {
            max-height: 600px;
            overflow-y: auto;
        }

        .waterfall-row {
            display: grid;
            grid-template-columns: 300px 1fr 120px;
            padding: 8px 12px;
            border-bottom: 1px solid #f0f0f0;
            cursor: pointer;
            transition: background 0.2s;
        }

        .waterfall-row:hover {
            background: #f9f9f9;
        }

        .span-label {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .span-icon {
            font-size: 1.1em;
        }

        .span-name {
            font-weight: 500;
        }

        .span-timeline {
            position: relative;
            padding: 4px 0;
        }

        .span-bar {
            position: absolute;
            height: 24px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            padding: 0 8px;
            color: white;
            font-size: 0.85em;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }

        .span-bar.llm-call { background: #2196F3; }
        .span-bar.browser-action { background: #4CAF50; }
        .span-bar.tool-call { background: #FF9800; }
        .span-bar.agent-run { background: #9C27B0; }

        .span-duration {
            font-family: monospace;
            color: #666;
        }

        .span-details {
            grid-column: 1 / -1;
            background: #fafafa;
            padding: 16px;
            border-top: 1px solid #e0e0e0;
            display: none;
        }

        .waterfall-row.expanded .span-details {
            display: block;
        }
    </style>

    <script>
        function renderWaterfall(trace) {
            const body = document.getElementById('waterfall-body');
            body.innerHTML = '';

            const totalDuration = trace.duration_ms;

            trace.spans.forEach(span => {
                const row = document.createElement('div');
                row.className = 'waterfall-row';
                row.onclick = () => row.classList.toggle('expanded');

                // Calculate bar position and width
                const startPercent = ((span.start_time - trace.start_time) * 1000 / totalDuration) * 100;
                const widthPercent = (span.duration_ms / totalDuration) * 100;

                row.innerHTML = `
                    <div class="span-label">
                        <span class="span-icon">${getSpanIcon(span.span_type)}</span>
                        <span class="span-name">${span.name}</span>
                    </div>
                    <div class="span-timeline">
                        <div class="span-bar ${span.span_type}"
                             style="left: ${startPercent}%; width: ${widthPercent}%;">
                            ${span.duration_ms.toFixed(0)}ms
                        </div>
                    </div>
                    <div class="span-duration">${span.duration_ms.toFixed(0)}ms</div>
                    <div class="span-details">
                        <pre>${JSON.stringify(span, null, 2)}</pre>
                    </div>
                `;

                body.appendChild(row);
            });
        }

        function getSpanIcon(spanType) {
            const icons = {
                'agent_run': '🤖',
                'llm_call': '🧠',
                'browser_action': '🌐',
                'tool_call': '🔧',
                'retrieval': '📚'
            };
            return icons[spanType] || '⚙️';
        }
    </script>
    """

    return gr.HTML(value=waterfall_html)
```

### Analytics Dashboard

```python
def create_observability_dashboard(ui_manager: WebuiManager):
    """Create comprehensive observability dashboard."""

    with gr.Tab("📊 Observability"):
        with gr.Row():
            # Metrics cards
            with gr.Column(scale=1):
                total_cost = gr.Number(label="Total Cost (USD)", value=0.0, interactive=False)
                total_tokens = gr.Number(label="Total Tokens", value=0, interactive=False)
                avg_duration = gr.Number(label="Avg Duration (s)", value=0.0, interactive=False)
                success_rate = gr.Number(label="Success Rate (%)", value=0.0, interactive=False)

        with gr.Tabs():
            with gr.TabItem("Trace Timeline"):
                trace_waterfall = create_trace_visualizer()

            with gr.TabItem("LLM Calls"):
                llm_calls_table = gr.Dataframe(
                    headers=["Timestamp", "Model", "Input Tokens", "Output Tokens", "Cost", "Duration"],
                    label="LLM Call History"
                )

            with gr.TabItem("Actions"):
                actions_table = gr.Dataframe(
                    headers=["Timestamp", "Action", "Status", "Duration", "Result"],
                    label="Browser Actions"
                )

            with gr.TabItem("Cost Analysis"):
                with gr.Row():
                    cost_over_time = gr.Plot(label="Cost Over Time")
                    tokens_by_model = gr.Plot(label="Tokens by Model")

        # Update functions
        def update_dashboard(trace: ExecutionTrace):
            """Update all dashboard components with trace data."""

            # Aggregate metrics
            metrics = {
                "total_cost": trace.total_cost_usd,
                "total_tokens": trace.total_tokens,
                "avg_duration": trace.get_duration_ms() / 1000,
                "success_rate": 100.0 if trace.success else 0.0
            }

            # Extract LLM calls
            llm_calls = [
                [
                    datetime.fromtimestamp(span.start_time).strftime("%H:%M:%S"),
                    span.model_name,
                    span.tokens_input,
                    span.tokens_output,
                    f"${span.cost_usd:.4f}",
                    f"{span.duration_ms:.0f}ms"
                ]
                for span in trace.spans if span.span_type == SpanType.LLM_CALL
            ]

            # Extract actions
            actions = [
                [
                    datetime.fromtimestamp(span.start_time).strftime("%H:%M:%S"),
                    span.name,
                    span.status,
                    f"{span.duration_ms:.0f}ms",
                    str(span.outputs)[:50]
                ]
                for span in trace.spans if span.span_type == SpanType.BROWSER_ACTION
            ]

            return {
                total_cost: metrics["total_cost"],
                total_tokens: metrics["total_tokens"],
                avg_duration: metrics["avg_duration"],
                success_rate: metrics["success_rate"],
                llm_calls_table: llm_calls,
                actions_table: actions
            }
```

---

## Feature 3.3: Step-by-Step Debugger

### Debugger UI

```python
def create_debugger_panel():
    """Create interactive debugger panel."""

    with gr.Accordion("🐛 Debugger", open=False) as debugger_panel:
        gr.Markdown("### Execution Debugger")

        with gr.Row():
            # Controls
            pause_btn = gr.Button("⏸️ Pause", size="sm")
            step_btn = gr.Button("⏭️ Step", size="sm", interactive=False)
            resume_btn = gr.Button("▶️ Resume", size="sm", interactive=False)
            stop_btn = gr.Button("⏹️ Stop", size="sm")

        # Breakpoints
        with gr.Group():
            gr.Markdown("**Breakpoints**")
            breakpoint_action = gr.Dropdown(
                choices=["click", "type", "navigate", "extract"],
                label="Break on action type"
            )
            add_breakpoint_btn = gr.Button("Add Breakpoint", size="sm")
            breakpoints_list = gr.Dataframe(
                headers=["ID", "Type", "Condition", "Enabled"],
                label="Active Breakpoints"
            )

        # State inspection
        with gr.Group():
            gr.Markdown("**Current State**")
            current_url = gr.Textbox(label="URL", interactive=False)
            current_action = gr.Textbox(label="Current Action", interactive=False)
            browser_state_json = gr.JSON(label="Browser State")

        # Variables
        with gr.Group():
            gr.Markdown("**Variables**")
            variables_json = gr.JSON(label="Agent Variables")

    return {
        "pause_btn": pause_btn,
        "step_btn": step_btn,
        "resume_btn": resume_btn,
        "breakpoints_list": breakpoints_list,
        # ... other components
    }
```

### Debugger Integration

```python
class DebuggableAgent(BrowserUseAgent):
    """Agent with debugging capabilities."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.debug_mode = False
        self.breakpoints: List[Breakpoint] = []
        self.paused = False
        self.step_mode = False

    async def run_with_debugging(self, max_steps: int = 100):
        """Run agent with debugging support."""

        for step in range(max_steps):
            # Check breakpoints
            if self._should_break(step):
                self.paused = True
                yield {"status": "breakpoint", "step": step}

                # Wait for user to resume or step
                while self.paused and not self.step_mode:
                    await asyncio.sleep(0.1)

            # Execute step
            await self.step(step)

            if self.step_mode:
                self.paused = True
                self.step_mode = False

    def _should_break(self, step: int) -> bool:
        """Check if execution should pause at this step."""
        for bp in self.breakpoints:
            if bp.enabled and bp.matches(step, self.state):
                return True
        return False

    def add_breakpoint(self, breakpoint: Breakpoint):
        """Add a breakpoint."""
        self.breakpoints.append(breakpoint)

    def resume(self):
        """Resume execution."""
        self.paused = False

    def step(self):
        """Execute one step."""
        self.step_mode = True
        self.paused = False
```

---

## Success Metrics

- [ ] Trace data captured for 100% of executions
- [ ] Cost calculation accurate within 1%
- [ ] Waterfall chart renders in <300ms
- [ ] Debugger allows step-through execution
- [ ] User rating >4.5/5 for debugging experience

---

**Status:** Detailed specification complete
**Dependencies:** Phase 1 & 2 completion
**Estimated effort:** 4-5 weeks
