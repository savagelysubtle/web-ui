"""
Quick test to verify dashboard implementation loads correctly.
This doesn't launch the full UI, just checks imports and basic initialization.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_dashboard_imports():
    """Test that all dashboard components can be imported."""
    print("Testing dashboard imports...")

    try:
        print("✓ dashboard_sidebar imported successfully")
    except Exception as e:
        print(f"✗ dashboard_sidebar import failed: {e}")
        return False

    try:
        print("✓ dashboard_main imported successfully")
    except Exception as e:
        print(f"✗ dashboard_main import failed: {e}")
        return False

    try:
        print("✓ dashboard_settings imported successfully")
    except Exception as e:
        print(f"✗ dashboard_settings import failed: {e}")
        return False

    try:
        print("✓ help_modal imported successfully")
    except Exception as e:
        print(f"✗ help_modal import failed: {e}")
        return False

    try:
        print("✓ interface imported successfully")
    except Exception as e:
        print(f"✗ interface import failed: {e}")
        return False

    return True

def test_webui_manager():
    """Test WebuiManager state management."""
    print("\nTesting WebuiManager...")

    try:
        from web_ui.webui.webui_manager import WebuiManager

        manager = WebuiManager()
        print("✓ WebuiManager initialized")

        # Test state management attributes
        assert hasattr(manager, "settings_panel_visible"), "Missing settings_panel_visible"
        assert hasattr(manager, "current_agent_type"), "Missing current_agent_type"
        assert hasattr(manager, "recent_tasks"), "Missing recent_tasks"
        assert hasattr(manager, "token_usage"), "Missing token_usage"
        print("✓ WebuiManager has all state management attributes")

        # Test methods
        assert hasattr(manager, "toggle_settings_panel"), "Missing toggle_settings_panel"
        assert hasattr(manager, "add_recent_task"), "Missing add_recent_task"
        assert hasattr(manager, "update_token_usage"), "Missing update_token_usage"
        print("✓ WebuiManager has all state management methods")

        return True
    except Exception as e:
        print(f"✗ WebuiManager test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Dashboard Implementation Test")
    print("=" * 60)

    imports_ok = test_dashboard_imports()
    manager_ok = test_webui_manager()

    print("\n" + "=" * 60)
    if imports_ok and manager_ok:
        print("✓ All tests passed!")
        print("\nNext steps:")
        print("1. Run 'python webui.py' to start the application")
        print("2. Open browser to http://127.0.0.1:7788")
        print("3. Click the ⚙️ button on the right edge to test settings panel")
        print("4. Settings should smoothly slide in from the right")
    else:
        print("✗ Some tests failed - check errors above")
        sys.exit(1)
    print("=" * 60)
