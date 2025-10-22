# Backend Improvements: LangGraph Memory & State Management

## Current Architecture Analysis

### Strengths

- ✅ **DeepResearchAgent** uses LangGraph with `StateGraph` for workflow orchestration
- ✅ Existing infrastructure: `EventBus`, `AgentTracer`, `CostCalculator`, `WorkflowGraphBuilder`
- ✅ MCP integration for external tool access
- ✅ Observability framework with spans and traces

### Gaps

- ❌ **BrowserUseAgent** doesn't use LangGraph (uses browser-use's internal Agent class)
- ❌ No persistent checkpointing/state management for BrowserUseAgent
- ❌ No conversation memory or summarization
- ❌ Limited streaming support for workflows
- ❌ No retry logic or error recovery patterns

---

## Recommended Improvements

### 1. LangGraph-Based State Management for BrowserUseAgent

**Current:** BrowserUseAgent uses a simple `for step in range(max_steps)` loop

**Proposed:** Refactor to use LangGraph StateGraph with nodes:

- `planning_node` - Analyze task and create plan
- `action_node` - Execute browser actions
- `observation_node` - Process results and extract information
- `decision_node` - Determine next action or completion
- `synthesis_node` - Aggregate results

**Benefits:**

- Better error recovery (can resume from any node)
- Checkpointing support (save/restore state)
- Parallel action execution
- Built-in observability

### 2. Persistent Memory Implementation

#### Short-Term Memory (Conversation Window Management)

```python
from langchain_core.chat_history import InMemoryChatMessageHistory
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.chat_history import BaseChatMessageHistory

class ShortTermMemory:
    """Manages conversation history within context window."""

    def __init__(self, max_history_length: int = 50):
        self.max_history_length = max_history_length
        self.memory = InMemoryChatMessageHistory()

    def add_message(self, message: BaseMessage):
        """Add message and trim if needed."""
        self.memory.add_message(message)
        if len(self.memory.messages) > self.max_history_length:
            self._trim_messages()

    def _trim_messages(self):
        """Remove oldest messages or summarize."""
        # Keep system message + last N messages
        # Or summarize older messages
        pass
```

#### Long-Term Memory (Persistent Storage)

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

class LongTermMemory:
    """Persistent memory across sessions."""

    def __init__(self, persist_directory: str = "./tmp/memory"):
        self.checkpointer = SqliteSaver.from_conn_string("memory.db")
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self._get_embedding_fn()
        )

    async def save_episode(self, session_id: str, state: dict):
        """Save agent execution episode."""
        await self.checkpointer.aput((session_id,), state)

    async def retrieve_similar(self, query: str, k: int = 5):
        """Retrieve similar past experiences."""
        return self.vectorstore.similarity_search(query, k=k)
```

### 3. Enhanced Checkpointing

**Current:** BrowserUseAgent saves final history as JSON/GIF

**Proposed:** LangGraph checkpointing with SqliteSaver

```python
from langgraph.checkpoint.sqlite import SqliteSaver

def build_browser_agent_graph():
    workflow = StateGraph(BrowserAgentState)

    # Setup checkpointing
    checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

    workflow.add_node("plan", planning_node)
    workflow.add_node("act", action_node)
    workflow.add_node("observe", observation_node)

    # Compile with checkpointing
    app = workflow.compile(checkpointer=checkpointer)
    return app

# Usage with checkpointing
thread_config = {"configurable": {"thread_id": task_id}}
final_state = await app.ainvoke(initial_state, config=thread_config)

# Resume from checkpoint
current_state = await app.aget_state(thread_config)
```

### 4. Streaming Support

**Proposed:** Add streaming for real-time updates

```python
from langgraph.graph.message import add_messages

async def stream_agent_execution(app, initial_state, thread_id):
    """Stream agent execution updates."""
    config = {"configurable": {"thread_id": thread_id}}

    async for event in app.astream(initial_state, config=config):
        # Yield events for UI updates
        if event:
            yield {
                "node": list(event.keys())[0],
                "state": event[list(event.keys())[0]],
                "timestamp": time.time()
            }
```

### 5. Error Recovery & Retry Logic

```python
from langgraph.graph import StateGraph
from typing import Literal

class BrowserAgentState(TypedDict):
    messages: list[BaseMessage]
    task: str
    actions_taken: list[dict]
    failures: int
    max_retries: int
    current_page: str
    browser_state: dict

def should_retry(state: BrowserAgentState) -> Literal["retry", "continue", "fail"]:
    """Determine if we should retry failed action."""
    if state["failures"] < state["max_retries"]:
        return "retry"
    elif state["failures"] >= state["max_retries"]:
        return "fail"
    return "continue"

# Add retry node
async def retry_node(state: BrowserAgentState) -> dict:
    """Retry last failed action with different strategy."""
    last_action = state["actions_taken"][-1]

    # Adjust strategy (e.g., wait longer, try different selector)
    return {
        "failures": state["failures"] + 1,
        "current_strategy": _get_next_strategy(state["failures"])
    }
```

### 6. Conversation Summarization

```python
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import PromptTemplate

class ConversationSummarizer:
    """Summarize long conversations to save tokens."""

    def __init__(self, llm):
        self.llm = llm
        self.summary_prompt = PromptTemplate(
            input_variables=["text"],
            template="Summarize the following conversation, focusing on: "
                     "1. Task objective 2. Key actions taken 3. Results found\n\n{text}"
        )

    async def summarize_history(self, messages: list[BaseMessage]) -> str:
        """Condense conversation history."""
        # Convert messages to text
        conversation_text = "\n".join([msg.content for msg in messages])

        # Create chain
        chain = load_summarize_chain(self.llm, chain_type="stuff")

        # Summarize
        summary = await chain.ainvoke({"input_documents": [Document(page_content=conversation_text)]})
        return summary["output_text"]
```

### 7. Integration with Existing Observability

**Proposed:** Enhance tracer to work with LangGraph

```python
from src.web_ui.observability.tracer import AgentTracer

class LangGraphTracer:
    """Tracer for LangGraph workflows."""

    def __init__(self, tracer: AgentTracer):
        self.tracer = tracer

    async def trace_node(self, node_name: str, inputs: dict):
        """Trace a LangGraph node execution."""
        async with self.tracer.span(
            name=f"node:{node_name}",
            span_type=SpanType.AGENT_NODE,
            inputs=inputs
        ) as span:
            # Node execution
            yield span
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

1. ✅ Add LangGraph to BrowserUseAgent
2. ✅ Implement SqliteSaver checkpointing
3. ✅ Create BrowserAgentState TypedDict
4. ✅ Add basic workflow nodes (plan, act, observe)

### Phase 2: Memory (Week 3-4)

1. ✅ Implement ShortTermMemory for message trimming
2. ✅ Add LongTermMemory with vector store
3. ✅ Integrate conversation summarization
4. ✅ Add memory retrieval to planning node

### Phase 3: Reliability (Week 5-6)

1. ✅ Add retry logic and error recovery
2. ✅ Implement streaming support
3. ✅ Enhance observability integration
4. ✅ Add progress persistence

### Phase 4: Optimization (Week 7-8)

1. ✅ Optimize checkpoint frequency
2. ✅ Add parallel action execution
3. ✅ Implement result caching
4. ✅ Performance tuning

---

## Code Structure

```
src/web_ui/agent/browser_use/
├── browser_use_agent.py        # Current (to be refactored)
├── langgraph_agent.py          # NEW: LangGraph-based agent
├── state.py                    # NEW: State definitions
├── nodes.py                    # NEW: Workflow nodes
├── memory/
│   ├── __init__.py
│   ├── short_term.py          # NEW: Conversation memory
│   ├── long_term.py           # NEW: Persistent memory
│   └── summarizer.py          # NEW: Conversation summarization
└── checkpoints/
    ├── __init__.py
    └── sqlite_checkpointer.py  # NEW: Checkpoint management
```

---

## Example: New LangGraph-Based BrowserUseAgent

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict

class BrowserAgentState(TypedDict):
    task: str
    messages: list[BaseMessage]
    browser_context: BrowserContext
    actions_taken: list[dict]
    current_url: str
    page_html: str
    failures: int
    max_steps: int
    current_step: int

class LangGraphBrowserAgent:
    def __init__(self, llm, browser, controller):
        self.llm = llm
        self.browser = browser
        self.controller = controller
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(BrowserAgentState)

        # Add nodes
        workflow.add_node("plan", self.planning_node)
        workflow.add_node("act", self.action_node)
        workflow.add_node("observe", self.observation_node)
        workflow.add_node("decide", self.decision_node)

        # Setup edges
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "act")
        workflow.add_edge("act", "observe")
        workflow.add_edge("observe", "decide")

        # Conditional edge
        workflow.add_conditional_edges(
            "decide",
            self.should_continue,
            {
                "act": "act",
                "synthesize": "synthesize_node",
                "end": "end_node"
            }
        )

        # Compile with checkpointing
        checkpointer = SqliteSaver.from_conn_string("browser_agent.db")
        return workflow.compile(checkpointer=checkpointer)

    async def run(self, task: str, config: dict = None):
        """Run agent with checkpointing support."""
        initial_state = {
            "task": task,
            "messages": [HumanMessage(content=task)],
            "browser_context": self.browser,
            "actions_taken": [],
            "current_url": "",
            "page_html": "",
            "failures": 0,
            "max_steps": 100,
            "current_step": 0
        }

        # Use thread_id for checkpointing
        if config is None:
            config = {"configurable": {"thread_id": str(uuid.uuid4())}}

        # Stream execution for real-time updates
        async for event in self.graph.astream(initial_state, config=config):
            yield event

        # Get final state
        final_state = await self.graph.aget_state(config)
        return final_state
```

---

## Migration Strategy

### Option 1: Gradual Migration (Recommended)

1. Keep existing `BrowserUseAgent` as-is
2. Create new `LangGraphBrowserAgent` in parallel
3. Add feature flag to switch between implementations
4. Test thoroughly before full migration

### Option 2: Full Refactor

1. Refactor `BrowserUseAgent` to use LangGraph internally
2. Maintain same public API
3. Add checkpointing/memory as optional features

---

## Dependencies to Add

```toml
[dependencies]
langgraph = ">=0.3.34"              # Already added
langchain-community = ">=0.3.0"     # Already added
chromadb = ">=0.5.0"                # NEW: Vector store
tiktoken = ">=0.7.0"                # NEW: Token counting
sqlalchemy = ">=2.0.0"              # NEW: For SqliteSaver
```

---

## Benefits Summary

| Feature | Current | With Improvements |
|---------|---------|-------------------|
| State Persistence | ❌ None | ✅ Sqlite checkpointing |
| Resume Execution | ❌ Not possible | ✅ Resume from any checkpoint |
| Memory Management | ❌ None | ✅ Short + long-term memory |
| Error Recovery | ❌ Basic retry | ✅ Advanced retry logic |
| Streaming | ❌ Limited | ✅ Full streaming support |
| Observability | ⚠️ Partial | ✅ Full integration |
| Performance | ⚠️ Good | ✅ Optimized with caching |

---

## Next Steps

1. **Review** this document with the team
2. **Prioritize** features based on use cases
3. **Create** implementation tickets
4. **Start** with Phase 1 (foundation)
5. **Iterate** based on feedback

---

## Questions?

- Which features are highest priority?
- Should we implement gradual migration or full refactor?
- What's the target timeline?
- Any specific use cases we should prioritize?
