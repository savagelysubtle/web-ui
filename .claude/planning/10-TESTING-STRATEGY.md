# Testing Strategy

**Version:** 1.0
**Last Updated:** 2025-10-21

---

## Testing Philosophy

**Principles:**
1. **Test What Matters:** Focus on user-facing functionality and critical paths
2. **Fast Feedback:** Unit tests run in <1s, integration tests in <10s
3. **Real Environments:** Use actual browsers and LLMs (with mocking for CI)
4. **Automated Where Possible:** CI/CD runs all tests on every commit
5. **Manual Where Necessary:** UX testing requires human judgment

---

## Testing Pyramid

```
                  ▲
                 ╱ ╲
                ╱   ╲      Manual/Exploratory (5%)
               ╱─────╲     - UX testing
              ╱       ╲    - Visual regression
             ╱─────────╲
            ╱           ╲  E2E Tests (15%)
           ╱─────────────╲ - Full workflows
          ╱               ╲- Browser automation
         ╱─────────────────╲
        ╱                   ╲ Integration Tests (30%)
       ╱─────────────────────╲ - LLM integration
      ╱                       ╲ - Database operations
     ╱─────────────────────────╲
    ╱                           ╲ Unit Tests (50%)
   ╱═════════════════════════════╲ - Business logic
  ══════════════════════════════════ - Utilities
```

**Target Distribution:**
- 50% Unit Tests (~100 tests)
- 30% Integration Tests (~60 tests)
- 15% E2E Tests (~30 tests)
- 5% Manual Testing

---

## Test Environment Setup

### Dependencies

```bash
# Install test dependencies
uv pip install pytest pytest-asyncio pytest-cov pytest-mock

# Install Playwright for E2E
playwright install --with-deps
```

### Configuration

**pytest.ini:**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests (skip in quick runs)
    llm: Tests that call LLM APIs (skip in CI without keys)

# Coverage settings
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
    -v
```

### Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_llm_provider.py
│   ├── test_cost_calculator.py
│   ├── test_session_manager.py
│   └── test_utils.py
├── integration/                # Integration tests (slower, external deps)
│   ├── test_browser_integration.py
│   ├── test_llm_integration.py
│   ├── test_database_operations.py
│   └── test_event_bus.py
├── e2e/                        # End-to-end tests (slowest, full workflows)
│   ├── test_agent_workflow.py
│   ├── test_template_system.py
│   └── test_ui_interactions.py
└── fixtures/                   # Test data
    ├── sample_workflows.json
    └── mock_responses.json
```

---

## Unit Tests

### Example: LLM Provider Tests

**File:** `tests/unit/test_llm_provider.py`

```python
import pytest
from src.utils.llm_provider import get_llm_model
from unittest.mock import patch, MagicMock

class TestLLMProvider:
    """Tests for LLM provider factory."""

    def test_get_openai_model(self):
        """Test OpenAI model creation."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test'}):
            model = get_llm_model(
                provider='openai',
                model_name='gpt-4o',
                temperature=0.7
            )

            assert model is not None
            assert model.__class__.__name__ == 'ChatOpenAI'

    def test_get_anthropic_model(self):
        """Test Anthropic model creation."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'sk-ant-test'}):
            model = get_llm_model(
                provider='anthropic',
                model_name='claude-3-opus',
                temperature=0.5
            )

            assert model is not None
            assert model.__class__.__name__ == 'ChatAnthropic'

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises appropriate error."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                get_llm_model(provider='openai', model_name='gpt-4o')

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_llm_model(provider='invalid', model_name='test')

    @pytest.mark.parametrize("provider,model,expected_class", [
        ('openai', 'gpt-4o', 'ChatOpenAI'),
        ('anthropic', 'claude-3-sonnet', 'ChatAnthropic'),
        ('google', 'gemini-pro', 'ChatGoogleGenerativeAI'),
        ('ollama', 'llama2', 'ChatOllama'),
    ])
    def test_all_providers(self, provider, model, expected_class):
        """Test all supported providers."""
        # Mock API keys
        api_keys = {
            'OPENAI_API_KEY': 'sk-test',
            'ANTHROPIC_API_KEY': 'sk-ant-test',
            'GOOGLE_API_KEY': 'AIza-test',
            'OLLAMA_ENDPOINT': 'http://localhost:11434',
        }

        with patch.dict('os.environ', api_keys):
            llm = get_llm_model(provider=provider, model_name=model)
            assert llm.__class__.__name__ == expected_class
```

### Example: Cost Calculator Tests

**File:** `tests/unit/test_cost_calculator.py`

```python
import pytest
from src.observability.cost_calculator import calculate_llm_cost

class TestCostCalculator:
    """Tests for LLM cost calculation."""

    def test_gpt4o_cost(self):
        """Test GPT-4o cost calculation."""
        cost = calculate_llm_cost(
            model='gpt-4o',
            input_tokens=1000,
            output_tokens=500
        )

        # Expected: (1000/1M * $2.50) + (500/1M * $10.00)
        expected = 0.0025 + 0.005
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_claude_sonnet_cost(self):
        """Test Claude 3.5 Sonnet cost calculation."""
        cost = calculate_llm_cost(
            model='claude-3.5-sonnet',
            input_tokens=2000,
            output_tokens=1000
        )

        # Expected: (2000/1M * $3.00) + (1000/1M * $15.00)
        expected = 0.006 + 0.015
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_unknown_model_returns_zero(self):
        """Test that unknown models return 0 cost."""
        cost = calculate_llm_cost(
            model='unknown-model',
            input_tokens=1000,
            output_tokens=500
        )
        assert cost == 0.0

    def test_zero_tokens(self):
        """Test with zero tokens."""
        cost = calculate_llm_cost(
            model='gpt-4o',
            input_tokens=0,
            output_tokens=0
        )
        assert cost == 0.0

    @pytest.mark.parametrize("input_tokens,output_tokens", [
        (1000, 500),
        (5000, 2500),
        (10000, 5000),
        (100000, 50000),
    ])
    def test_cost_scales_linearly(self, input_tokens, output_tokens):
        """Test that cost scales linearly with token count."""
        cost1 = calculate_llm_cost('gpt-4o', input_tokens, output_tokens)
        cost2 = calculate_llm_cost('gpt-4o', input_tokens * 2, output_tokens * 2)

        assert cost2 == pytest.approx(cost1 * 2, rel=1e-6)
```

---

## Integration Tests

### Example: Browser Integration

**File:** `tests/integration/test_browser_integration.py`

```python
import pytest
from playwright.async_api import async_playwright
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext

@pytest.mark.integration
@pytest.mark.asyncio
class TestBrowserIntegration:
    """Integration tests for browser operations."""

    @pytest.fixture
    async def browser(self):
        """Fixture to provide browser instance."""
        browser = CustomBrowser(headless=True)
        await browser.initialize()
        yield browser
        await browser.close()

    @pytest.fixture
    async def context(self, browser):
        """Fixture to provide browser context."""
        context = await browser.new_context()
        yield context
        await context.close()

    async def test_navigate_to_page(self, context):
        """Test basic navigation."""
        page = await context.get_current_page()
        response = await page.goto('https://example.com')

        assert response.status == 200
        assert 'example.com' in page.url

    async def test_click_element(self, context):
        """Test clicking an element."""
        page = await context.get_current_page()
        await page.goto('https://example.com')

        # Click the "More information..." link
        await page.click('text=More information')

        # Verify navigation occurred
        await page.wait_for_load_state('networkidle')
        assert page.url != 'https://example.com'

    async def test_extract_text(self, context):
        """Test text extraction."""
        page = await context.get_current_page()
        await page.goto('https://example.com')

        # Extract heading text
        heading = await page.locator('h1').inner_text()
        assert heading == 'Example Domain'

    async def test_screenshot_capture(self, context, tmp_path):
        """Test screenshot capture."""
        page = await context.get_current_page()
        await page.goto('https://example.com')

        screenshot_path = tmp_path / "screenshot.png"
        await page.screenshot(path=str(screenshot_path))

        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0

    @pytest.mark.slow
    async def test_persistent_context(self):
        """Test persistent browser context."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Create persistent context
            browser = CustomBrowser(
                headless=True,
                user_data_dir=temp_dir
            )
            await browser.initialize()

            page = await browser.get_current_page()
            await page.goto('https://example.com')

            # Set local storage
            await page.evaluate('localStorage.setItem("test", "value")')

            await browser.close()

            # Reopen with same context
            browser2 = CustomBrowser(
                headless=True,
                user_data_dir=temp_dir
            )
            await browser2.initialize()

            page2 = await browser2.get_current_page()
            await page2.goto('https://example.com')

            # Verify local storage persisted
            value = await page2.evaluate('localStorage.getItem("test")')
            assert value == "value"

            await browser2.close()

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
```

### Example: LLM Integration

**File:** `tests/integration/test_llm_integration.py`

```python
import pytest
from src.utils.llm_provider import get_llm_model

@pytest.mark.integration
@pytest.mark.llm
class TestLLMIntegration:
    """Integration tests with real LLM APIs."""

    @pytest.fixture
    def skip_if_no_api_key(self):
        """Skip test if API keys not available."""
        import os
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set")

    @pytest.mark.asyncio
    async def test_openai_completion(self, skip_if_no_api_key):
        """Test actual OpenAI API call."""
        llm = get_llm_model(provider='openai', model_name='gpt-4o-mini')

        response = await llm.ainvoke("Say 'hello world'")

        assert response.content
        assert 'hello' in response.content.lower()

    @pytest.mark.asyncio
    async def test_streaming_response(self, skip_if_no_api_key):
        """Test streaming LLM response."""
        llm = get_llm_model(provider='openai', model_name='gpt-4o-mini')

        tokens = []
        async for token in llm.astream("Count from 1 to 3"):
            tokens.append(token.content)

        full_response = ''.join(tokens)
        assert '1' in full_response
        assert '2' in full_response
        assert '3' in full_response

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_multiple_providers(self):
        """Test multiple LLM providers work correctly."""
        providers_to_test = []

        # Only test providers with API keys set
        if os.getenv('OPENAI_API_KEY'):
            providers_to_test.append(('openai', 'gpt-4o-mini'))
        if os.getenv('ANTHROPIC_API_KEY'):
            providers_to_test.append(('anthropic', 'claude-3-haiku'))
        if os.getenv('GOOGLE_API_KEY'):
            providers_to_test.append(('google', 'gemini-pro'))

        for provider, model in providers_to_test:
            llm = get_llm_model(provider=provider, model_name=model)
            response = await llm.ainvoke("Say hello")
            assert response.content
```

---

## End-to-End Tests

### Example: Agent Workflow

**File:** `tests/e2e/test_agent_workflow.py`

```python
import pytest
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController

@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.slow
class TestAgentWorkflow:
    """End-to-end tests for complete agent workflows."""

    @pytest.fixture
    async def agent(self):
        """Create agent instance for testing."""
        browser = CustomBrowser(headless=True)
        await browser.initialize()

        controller = CustomController()

        agent = BrowserUseAgent(
            task="Search Google for 'testing'",
            llm=get_llm_model('openai', 'gpt-4o-mini'),
            browser=browser,
            controller=controller
        )

        yield agent

        await browser.close()

    async def test_simple_search_workflow(self, agent):
        """Test a complete search workflow."""
        # Run agent
        history = await agent.run(max_steps=10)

        # Verify agent completed successfully
        assert history.is_done()
        assert len(history.history) > 0

        # Verify search was performed
        final_state = history.history[-1].state
        assert 'google.com' in final_state.url.lower() or 'search' in final_state.url.lower()

    async def test_agent_with_error_handling(self, agent):
        """Test agent handles errors gracefully."""
        # Give agent an impossible task
        agent.task = "Navigate to http://this-domain-does-not-exist-12345.com"

        history = await agent.run(max_steps=5)

        # Agent should report error but not crash
        assert len(history.history) > 0
        final_history = history.history[-1]
        assert final_history.result[0].error is not None

    async def test_multi_step_workflow(self, agent):
        """Test workflow with multiple steps."""
        agent.task = """
        1. Go to example.com
        2. Find the heading text
        3. Click the 'More information' link
        """

        history = await agent.run(max_steps=20)

        # Verify multiple actions were taken
        assert len(history.history) >= 3

        # Verify final success
        assert history.is_done()
```

### Example: UI Interaction Tests

**File:** `tests/e2e/test_ui_interactions.py`

```python
import pytest
from gradio_client import Client
import time

@pytest.mark.e2e
@pytest.mark.slow
class TestUIInteractions:
    """End-to-end tests for UI interactions."""

    @pytest.fixture(scope="class")
    def gradio_client(self):
        """Start Gradio app and return client."""
        # Start the app in background
        import subprocess
        import time

        proc = subprocess.Popen(['python', 'webui.py', '--port', '7789'])
        time.sleep(5)  # Wait for app to start

        client = Client("http://127.0.0.1:7789")

        yield client

        proc.terminate()
        proc.wait()

    def test_submit_task(self, gradio_client):
        """Test submitting a task through UI."""
        result = gradio_client.predict(
            "Search Google for testing",
            api_name="/run_agent"
        )

        assert result is not None
        # Check that we got some output
        assert len(result) > 0

    def test_template_selection(self, gradio_client):
        """Test selecting and using a template."""
        # Get available templates
        templates = gradio_client.predict(api_name="/get_templates")

        assert len(templates) > 0

        # Select first template
        task = gradio_client.predict(
            templates[0]["id"],
            api_name="/load_template"
        )

        assert task == templates[0]["task"]

    def test_session_save_load(self, gradio_client):
        """Test saving and loading sessions."""
        # Run agent
        result = gradio_client.predict(
            "Test task",
            api_name="/run_agent"
        )

        # Save session
        session_id = gradio_client.predict(api_name="/save_session")

        assert session_id is not None

        # Load session
        loaded = gradio_client.predict(
            session_id,
            api_name="/load_session"
        )

        assert loaded is not None
```

---

## Test Fixtures

**File:** `tests/conftest.py`

```python
import pytest
import asyncio
from pathlib import Path

# Make event loop available for all async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    from langchain_core.messages import AIMessage

    return AIMessage(content="This is a test response")

@pytest.fixture
def sample_workflow():
    """Load sample workflow for testing."""
    workflow_file = Path(__file__).parent / "fixtures" / "sample_workflows.json"
    import json

    with open(workflow_file) as f:
        return json.load(f)

@pytest.fixture
async def test_database(tmp_path):
    """Create temporary test database."""
    from src.storage.database import Database

    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    await db.initialize()

    yield db

    await db.close()

@pytest.fixture
def mock_browser():
    """Mock browser for unit tests."""
    from unittest.mock import AsyncMock, MagicMock

    browser = AsyncMock()
    browser.get_current_page = AsyncMock()
    browser.new_page = AsyncMock()
    browser.close = AsyncMock()

    return browser
```

---

## Running Tests

### Quick Test Run (Unit Tests Only)

```bash
# Run only unit tests (fast)
pytest tests/unit -v

# With coverage
pytest tests/unit --cov=src --cov-report=html
```

### Full Test Suite

```bash
# Run all tests
pytest

# Skip slow tests
pytest -m "not slow"

# Skip LLM tests (if no API keys)
pytest -m "not llm"

# Run specific test file
pytest tests/unit/test_llm_provider.py -v

# Run specific test
pytest tests/unit/test_llm_provider.py::TestLLMProvider::test_get_openai_model -v
```

### CI/CD Pipeline

**GitHub Actions:** `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.14'

    - name: Install UV
      run: pip install uv

    - name: Install dependencies
      run: uv sync

    - name: Install Playwright
      run: playwright install --with-deps chromium

    - name: Run unit tests
      run: pytest tests/unit -v --cov=src --cov-report=xml

    - name: Run integration tests (no LLM)
      run: pytest tests/integration -m "not llm" -v

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

---

## Test Coverage Goals

### Minimum Coverage

```yaml
Overall: 70%
Critical Paths:
  - Agent execution: 90%
  - LLM integration: 85%
  - Browser operations: 80%
  - Controller actions: 85%
  - Database operations: 75%
  - API endpoints: 80%
```

### Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html
```

---

## Manual Testing Checklist

### Before Each Release

- [ ] Test on all supported LLM providers (OpenAI, Anthropic, Google, etc.)
- [ ] Test on Chrome, Firefox, Safari (if supported)
- [ ] Test light and dark themes
- [ ] Test mobile responsive design (Phase 5)
- [ ] Test with slow network conditions
- [ ] Test with high concurrency (10+ simultaneous agents)
- [ ] Accessibility testing (screen reader, keyboard navigation)
- [ ] Visual regression testing (screenshot comparison)

### User Acceptance Testing

Recruit 5-10 beta users for:
- [ ] Usability testing (can they complete tasks easily?)
- [ ] Feature feedback (which features are most/least valuable?)
- [ ] Bug discovery (edge cases we didn't think of)
- [ ] Performance testing (real-world usage patterns)

---

## Performance Testing

### Load Testing

```python
# tests/performance/test_load.py

import pytest
import asyncio
from locust import HttpUser, task, between

class BrowserUseUser(HttpUser):
    """Locust user for load testing."""
    wait_time = between(1, 5)

    @task
    def run_agent(self):
        """Simulate running an agent."""
        self.client.post("/api/sessions", json={
            "task": "Search Google for testing"
        })

    @task(2)
    def list_templates(self):
        """Simulate browsing templates."""
        self.client.get("/api/templates")

# Run with: locust -f tests/performance/test_load.py --host=http://localhost:8000
```

### Benchmarking

```python
# tests/performance/benchmark.py

import time
import asyncio

async def benchmark_agent_execution():
    """Benchmark agent execution time."""
    from src.agent.browser_use.browser_use_agent import BrowserUseAgent

    agent = BrowserUseAgent(task="Test task", ...)

    start = time.time()
    await agent.run(max_steps=10)
    duration = time.time() - start

    print(f"Agent execution: {duration:.2f}s")

    assert duration < 30, "Agent execution too slow"

# Run: python tests/performance/benchmark.py
```

---

**Last Updated:** 2025-10-21
**Status:** Testing framework ready for implementation
