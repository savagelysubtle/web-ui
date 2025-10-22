# Testing Sequential Thinking MCP

## Quick Test Tasks

### For BrowserUseAgent

**Task:** "Visit GitHub, find the browser-use repository, and summarize its README using sequential thinking to plan your approach first."

The agent should:

1. Think through the navigation steps
2. Plan how to locate the repo
3. Strategy for extracting README
4. Approach to summarizing

### For DeepResearchAgent

**Task:** "Research 'MCP tools for AI agents' using sequential thinking to create a research strategy first."

The agent should:

1. Break down research question into sub-topics
2. Plan which sources to check (docs, GitHub, blogs)
3. Organize search queries
4. Structure findings synthesis

## Expected Behavior

You'll see log entries like:

```
✓ MCP Tool: sequential-thinking.create_thought_sequence
✓ MCP Tool: sequential-thinking.add_thought_step
✓ MCP Tool: sequential-thinking.get_thought_chain
```

## How to Run Test

1. Start the Web UI:

   ```bash
   python webui.py
   ```

2. Go to "🤖 Run Agent" tab

3. Enter one of the test tasks above

4. Check the logs for sequential thinking tool usage

5. Review the agent's reasoning process in the output
