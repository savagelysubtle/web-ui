# Phase 1: Real-time UX Improvements

**Timeline:** Weeks 1-2
**Priority:** Critical
**Complexity:** Medium

## Overview

Transform the static batch-update interface into a real-time, streaming experience that provides immediate feedback and professional polish.

## Feature 1.1: Token-by-Token Streaming

### Current Behavior
```python
# Current: Batch updates after LLM completes
async def run_agent():
    result = await agent.run()
    chatbot.append({"role": "assistant", "content": result})
    yield chatbot
```

### Target Behavior
```python
# Target: Stream tokens as they arrive
async def run_agent_streaming():
    async for token in agent.stream():
        chatbot[-1]["content"] += token
        yield chatbot
```

### Implementation Details

#### Backend Changes
**File:** `src/web_ui/agent/browser_use/browser_use_agent.py`

```python
class BrowserUseAgent(Agent):
    async def stream_execution(self) -> AsyncGenerator[AgentStreamEvent, None]:
        """Stream agent execution events in real-time."""
        for step in range(max_steps):
            # Stream step start
            yield AgentStreamEvent(
                type="STEP_START",
                data={"step": step, "max_steps": max_steps}
            )

            # Stream LLM thinking
            async for token in self.llm.astream(messages):
                yield AgentStreamEvent(
                    type="LLM_TOKEN",
                    data={"token": token}
                )

            # Stream action execution
            yield AgentStreamEvent(
                type="ACTION_START",
                data={"action": action_name, "params": params}
            )

            # Execute action
            result = await self.execute_action(action)

            yield AgentStreamEvent(
                type="ACTION_END",
                data={"action": action_name, "result": result}
            )
```

**File:** `src/web_ui/webui/components/browser_use_agent_tab.py`

```python
async def run_agent_with_streaming(
    task: str,
    chatbot: list,
    webui_manager: WebuiManager
) -> AsyncGenerator:
    """Run agent with real-time streaming updates."""

    # Add initial message
    chatbot.append({
        "role": "assistant",
        "content": "",
        "metadata": {"status": "thinking"}
    })

    async for event in webui_manager.bu_agent.stream_execution():
        if event.type == "LLM_TOKEN":
            # Append token to current message
            chatbot[-1]["content"] += event.data["token"]
            yield chatbot

        elif event.type == "ACTION_START":
            # Show action indicator
            chatbot[-1]["metadata"]["current_action"] = event.data["action"]
            yield chatbot

        elif event.type == "ACTION_END":
            # Update with result
            chatbot[-1]["metadata"]["last_action"] = event.data["action"]
            chatbot[-1]["metadata"]["status"] = "completed"
            yield chatbot
```

#### Frontend Changes
**File:** `src/web_ui/webui/components/browser_use_agent_tab.py`

```python
# Custom CSS for streaming indicators
streaming_css = """
.streaming-indicator {
    display: inline-block;
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
}

.action-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.85em;
    font-weight: 500;
    margin-right: 8px;
}

.action-badge.thinking { background: #FFA500; color: white; }
.action-badge.clicking { background: #4CAF50; color: white; }
.action-badge.typing { background: #2196F3; color: white; }
.action-badge.extracting { background: #9C27B0; color: white; }
.action-badge.navigating { background: #FF5722; color: white; }
.action-badge.completed { background: #4CAF50; color: white; }
.action-badge.error { background: #F44336; color: white; }
```

### Testing Plan
- [ ] Test with fast LLM (GPT-4o) - tokens should appear smoothly
- [ ] Test with slow LLM (local Ollama) - UI should remain responsive
- [ ] Test network interruption - graceful degradation
- [ ] Test with very long responses - memory management

### Success Criteria
- Tokens appear within 100ms of LLM generation
- No UI freezing during streaming
- Smooth animation (60fps)
- Proper error handling for stream interruption

---

## Feature 1.2: Enhanced Visual Status Display

### Current Behavior
Plain text showing action progress

### Target Behavior
Rich status cards with:
- Step counter with progress bar
- Current action with icon
- Execution time
- Token/cost counter (optional)
- Screenshot thumbnail

### Implementation

#### Status Card Component
**File:** `src/web_ui/webui/components/status_card.py` (new)

```python
import gradio as gr
from typing import Optional

def create_status_card() -> gr.HTML:
    """Create a live status card component."""

    initial_html = """
    <div class="status-card">
        <div class="status-header">
            <span class="status-title">Agent Status</span>
            <span class="status-time">0:00</span>
        </div>

        <div class="progress-container">
            <div class="progress-label">
                <span>Step <span id="current-step">0</span>/<span id="max-steps">100</span></span>
                <span id="progress-percent">0%</span>
            </div>
            <div class="progress-bar">
                <div id="progress-fill" class="progress-fill" style="width: 0%"></div>
            </div>
        </div>

        <div class="current-action">
            <div class="action-icon" id="action-icon">🤔</div>
            <div class="action-details">
                <div class="action-name" id="action-name">Thinking...</div>
                <div class="action-description" id="action-desc">Analyzing task</div>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric">
                <span class="metric-label">Actions</span>
                <span class="metric-value" id="action-count">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Tokens</span>
                <span class="metric-value" id="token-count">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Cost</span>
                <span class="metric-value" id="cost">$0.00</span>
            </div>
        </div>

        <div class="screenshot-preview" id="screenshot-preview">
            <!-- Mini screenshot will go here -->
        </div>
    </div>

    <style>
        .status-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 10px 0;
        }

        .status-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .status-title {
            font-size: 1.1em;
            font-weight: 600;
        }

        .status-time {
            font-family: monospace;
            font-size: 0.95em;
            opacity: 0.9;
        }

        .progress-container {
            margin-bottom: 20px;
        }

        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            margin-bottom: 6px;
            opacity: 0.95;
        }

        .progress-bar {
            background: rgba(255,255,255,0.2);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-fill {
            background: white;
            height: 100%;
            transition: width 0.3s ease;
        }

        .current-action {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(255,255,255,0.1);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
        }

        .action-icon {
            font-size: 2em;
            animation: bounce 2s ease-in-out infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }

        .action-details {
            flex: 1;
        }

        .action-name {
            font-weight: 600;
            font-size: 1.05em;
            margin-bottom: 2px;
        }

        .action-description {
            font-size: 0.85em;
            opacity: 0.85;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 16px;
        }

        .metric {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 6px;
            text-align: center;
        }

        .metric-label {
            display: block;
            font-size: 0.75em;
            opacity: 0.8;
            margin-bottom: 4px;
        }

        .metric-value {
            display: block;
            font-size: 1.2em;
            font-weight: 600;
        }

        .screenshot-preview {
            border-radius: 6px;
            overflow: hidden;
            background: rgba(255,255,255,0.1);
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .screenshot-preview img {
            width: 100%;
            height: auto;
            display: block;
        }
    </style>
    """

    return gr.HTML(value=initial_html, elem_id="status-card")

def update_status_card(
    step: int,
    max_steps: int,
    action_name: str,
    action_desc: str,
    action_icon: str,
    action_count: int,
    token_count: int,
    cost: float,
    elapsed_time: str,
    screenshot_b64: Optional[str] = None
) -> str:
    """Generate updated HTML for status card."""

    progress_percent = int((step / max_steps) * 100)

    screenshot_html = ""
    if screenshot_b64:
        screenshot_html = f'<img src="data:image/png;base64,{screenshot_b64}" alt="Current view">'

    return f"""
    <div class="status-card">
        <div class="status-header">
            <span class="status-title">Agent Status</span>
            <span class="status-time">{elapsed_time}</span>
        </div>

        <div class="progress-container">
            <div class="progress-label">
                <span>Step {step}/{max_steps}</span>
                <span>{progress_percent}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress_percent}%"></div>
            </div>
        </div>

        <div class="current-action">
            <div class="action-icon">{action_icon}</div>
            <div class="action-details">
                <div class="action-name">{action_name}</div>
                <div class="action-description">{action_desc}</div>
            </div>
        </div>

        <div class="metrics-grid">
            <div class="metric">
                <span class="metric-label">Actions</span>
                <span class="metric-value">{action_count}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Tokens</span>
                <span class="metric-value">{token_count:,}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Cost</span>
                <span class="metric-value">${cost:.3f}</span>
            </div>
        </div>

        <div class="screenshot-preview">
            {screenshot_html}
        </div>
    </div>
    """

# Action icon mapping
ACTION_ICONS = {
    "thinking": "🤔",
    "navigate": "🧭",
    "click": "🖱️",
    "type": "⌨️",
    "extract": "📊",
    "search": "🔍",
    "scroll": "📜",
    "wait": "⏱️",
    "done": "✅",
    "error": "❌"
}
```

### Integration with Agent Tab

```python
# In browser_use_agent_tab.py

def create_browser_use_agent_tab(ui_manager: WebuiManager):
    """Create the browser use agent tab with status card."""

    with gr.Column():
        # Status card at the top
        status_card = create_status_card()

        # Existing chatbot
        chatbot = gr.Chatbot(...)

        # Update function
        async def run_with_status_updates(task, *args):
            start_time = time.time()
            action_count = 0
            token_count = 0
            cost = 0.0

            async for event in agent.stream_execution():
                elapsed = time.time() - start_time
                elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"

                if event.type == "STEP_START":
                    step = event.data["step"]
                    max_steps = event.data["max_steps"]

                    # Update status card
                    new_html = update_status_card(
                        step=step,
                        max_steps=max_steps,
                        action_name="Thinking...",
                        action_desc="Planning next action",
                        action_icon=ACTION_ICONS["thinking"],
                        action_count=action_count,
                        token_count=token_count,
                        cost=cost,
                        elapsed_time=elapsed_str
                    )
                    yield status_card.update(value=new_html), chatbot

                elif event.type == "ACTION_START":
                    action_name = event.data["action"]
                    action_count += 1

                    new_html = update_status_card(
                        step=step,
                        max_steps=max_steps,
                        action_name=action_name.title(),
                        action_desc=f"Executing {action_name}...",
                        action_icon=ACTION_ICONS.get(action_name, "⚡"),
                        action_count=action_count,
                        token_count=token_count,
                        cost=cost,
                        elapsed_time=elapsed_str
                    )
                    yield status_card.update(value=new_html), chatbot
```

---

## Feature 1.3: Interactive Chat Components

### Collapsible Output Sections

```python
def create_collapsible_output(title: str, content: str, collapsed: bool = True) -> str:
    """Create collapsible section for verbose output."""

    collapsed_class = "collapsed" if collapsed else ""

    return f"""
    <div class="collapsible-section {collapsed_class}">
        <div class="collapsible-header" onclick="this.parentElement.classList.toggle('collapsed')">
            <span class="collapse-icon">▶</span>
            <span class="collapsible-title">{title}</span>
        </div>
        <div class="collapsible-content">
            <pre><code>{content}</code></pre>
        </div>
    </div>

    <style>
        .collapsible-section {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin: 8px 0;
            overflow: hidden;
        }

        .collapsible-header {
            background: #f5f5f5;
            padding: 10px 14px;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .collapsible-header:hover {
            background: #eeeeee;
        }

        .collapse-icon {
            transition: transform 0.2s ease;
        }

        .collapsible-section:not(.collapsed) .collapse-icon {
            transform: rotate(90deg);
        }

        .collapsible-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }

        .collapsible-section:not(.collapsed) .collapsible-content {
            max-height: 500px;
            overflow-y: auto;
        }

        .collapsible-content pre {
            margin: 0;
            padding: 14px;
            background: #fafafa;
        }

        .collapsible-content code {
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
    </style>
    """
```

### Copy Button for Outputs

```python
def add_copy_button(content: str, label: str = "Copy") -> str:
    """Add a copy button to content."""

    import uuid
    content_id = f"copy-content-{uuid.uuid4().hex[:8]}"

    return f"""
    <div class="copy-container">
        <div class="copy-content" id="{content_id}">{content}</div>
        <button class="copy-button" onclick="copyToClipboard('{content_id}')">
            {label}
        </button>
    </div>

    <script>
    function copyToClipboard(elementId) {{
        const element = document.getElementById(elementId);
        const text = element.innerText;
        navigator.clipboard.writeText(text).then(() => {{
            // Visual feedback
            const btn = event.target;
            const originalText = btn.innerText;
            btn.innerText = 'Copied!';
            btn.classList.add('copied');
            setTimeout(() => {{
                btn.innerText = originalText;
                btn.classList.remove('copied');
            }}, 2000);
        }});
    }}
    </script>

    <style>
        .copy-container {
            position: relative;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
        }

        .copy-button {
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 6px 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            transition: background 0.2s;
        }

        .copy-button:hover {
            background: #0056b3;
        }

        .copy-button.copied {
            background: #28a745;
        }

        .copy-content {
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-break: break-word;
            padding-right: 80px;
        }
    </style>
    """
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_streaming.py

import pytest
from src.agent.browser_use.browser_use_agent import BrowserUseAgent

@pytest.mark.asyncio
async def test_stream_execution():
    """Test that streaming yields correct event types."""
    agent = BrowserUseAgent(...)

    events = []
    async for event in agent.stream_execution():
        events.append(event.type)
        if len(events) > 10:
            break

    assert "STEP_START" in events
    assert "LLM_TOKEN" in events
    assert "ACTION_START" in events

@pytest.mark.asyncio
async def test_streaming_interruption():
    """Test graceful handling of stream interruption."""
    agent = BrowserUseAgent(...)

    async for event in agent.stream_execution():
        if event.type == "STEP_START":
            break  # Simulate interruption

    # Should not raise exception
    await agent.close()
```

### Integration Tests
```python
# tests/test_ui_streaming.py

import pytest
from gradio_client import Client

def test_real_time_updates():
    """Test that UI receives real-time updates."""
    client = Client("http://localhost:7788")

    updates = []
    for update in client.predict("Test task", api_name="/run_agent"):
        updates.append(update)
        if len(updates) >= 5:
            break

    # Should receive multiple updates before completion
    assert len(updates) >= 3
```

---

## Performance Targets

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time to first token | N/A | <100ms | Frontend timing |
| UI update frequency | 1/min | 10/sec | Event count |
| Memory overhead | N/A | <50MB | Process monitoring |
| Streaming latency | N/A | <50ms | Network timing |

---

## Rollout Plan

### Week 1
- [ ] Day 1-2: Implement streaming backend
- [ ] Day 3: Add status card component
- [ ] Day 4: Integrate with agent tab
- [ ] Day 5: Testing & bug fixes

### Week 2
- [ ] Day 1-2: Add collapsible sections
- [ ] Day 3: Add copy buttons
- [ ] Day 4: Polish animations
- [ ] Day 5: User testing & feedback

---

## Dependencies

### Libraries
- `gradio>=5.27.0` (current)
- No new dependencies required

### Breaking Changes
- None - backward compatible

---

## Success Metrics

- [ ] 90% of users see real-time updates
- [ ] Average latency <100ms
- [ ] Zero UI freezes during streaming
- [ ] Positive user feedback (>4/5 rating)

---

**Status:** Ready for implementation
**Assigned to:** TBD
**Review date:** End of Week 1
