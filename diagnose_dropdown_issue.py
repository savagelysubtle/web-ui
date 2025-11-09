#!/usr/bin/env python3
"""
Advanced diagnostic tool for LLM provider dropdown issue.
This will help identify exactly where the problem is.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("LLM PROVIDER DROPDOWN DIAGNOSTIC TOOL")
print("=" * 80)

# Step 1: Check Gradio version
print("\n[STEP 1] Checking Gradio version...")
try:
    import gradio as gr
    print(f"✅ Gradio version: {gr.__version__}")
    
    # Check if it's recent enough
    major, minor, patch = gr.__version__.split('.')[:3]
    if int(major) < 4:
        print(f"⚠️  WARNING: Gradio {gr.__version__} is old. Recommend upgrading to 4.x or 5.x")
        print(f"   Run: pip install --upgrade gradio")
except Exception as e:
    print(f"❌ ERROR: Could not import Gradio: {e}")
    sys.exit(1)

# Step 2: Test update_model_dropdown function
print("\n[STEP 2] Testing update_model_dropdown() function...")
try:
    from src.web_ui.webui.components.dashboard_settings import update_model_dropdown
    
    result = update_model_dropdown("anthropic")
    print(f"✅ Function works correctly")
    print(f"   Choices: {result.get('choices', [])}")
    print(f"   Value: {result.get('value', '')}")
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Check component registration
print("\n[STEP 3] Checking component registration...")
try:
    from src.web_ui.webui.webui_manager import WebuiManager
    
    manager = WebuiManager()
    print(f"✅ WebuiManager created")
    print(f"   Total components: {len(manager.id_to_component)}")
    
    # Check for key components
    key_components = [
        "dashboard_settings.llm_provider",
        "dashboard_settings.llm_model_name",
        "dashboard_settings.ollama_num_ctx",
    ]
    
    for comp_id in key_components:
        if comp_id in manager.id_to_component:
            print(f"   ✅ {comp_id} registered")
        else:
            print(f"   ❌ {comp_id} NOT FOUND")
            
except Exception as e:
    print(f"❌ ERROR: {e}")

# Step 4: Check if dashboard_settings.py has event handlers removed
print("\n[STEP 4] Verifying event handlers are in interface.py (not dashboard_settings.py)...")
try:
    with open("src/web_ui/webui/components/dashboard_settings.py") as f:
        content = f.read()
        
    if "llm_provider.change(" in content:
        print("⚠️  WARNING: Event handler still in dashboard_settings.py!")
        print("   This should have been moved to interface.py")
    else:
        print("✅ Event handlers removed from dashboard_settings.py")
        
    with open("src/web_ui/webui/interface.py") as f:
        content = f.read()
        
    if "llm_provider_comp.change(" in content:
        print("✅ Event handler found in interface.py")
    else:
        print("❌ Event handler NOT in interface.py!")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# Step 5: Test gr.update() format
print("\n[STEP 5] Testing gr.update() return format...")
try:
    update = gr.update(choices=["model1", "model2"], value="model1")
    print(f"✅ gr.update() creates dict: {type(update)}")
    print(f"   Keys: {list(update.keys())}")
    print(f"   Choices key exists: {'choices' in update}")
    print(f"   Value key exists: {'value' in update}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Step 6: Provide troubleshooting steps
print("\n" + "=" * 80)
print("TROUBLESHOOTING STEPS")
print("=" * 80)

print("""
If the issue persists, try these steps IN ORDER:

1. 🔄 RESTART THE WEBUI
   - Stop the current WebUI (Ctrl+C)
   - Run: python webui.py
   - The fixes won't apply until you restart!

2. 🧹 CLEAR BROWSER CACHE
   - In browser, press Ctrl+Shift+Delete
   - Clear "Cached images and files"
   - OR: Open WebUI in Incognito/Private mode

3. 🔍 CHECK CONSOLE OUTPUT
   When you start the WebUI, you should see:
   - "[SETUP] Attaching .change() handler to llm_provider_comp..."
   - "[SETUP] ✅ Change handler attached: ..."
   
   When you CHANGE the provider dropdown, you should see:
   - "[DEBUG] ⚡ update_llm_settings CALLED with provider: ..."
   - "[DEBUG] ✅ Model update: ..."

4. 🌐 CHECK BROWSER DEVELOPER TOOLS
   - Press F12 in browser
   - Go to "Console" tab
   - Look for any JavaScript errors (red text)
   - Change provider and watch for activity

5. 🔬 TEST MANUALLY IN PYTHON
   Run this in Python to verify the function works:
   
   >>> from src.web_ui.webui.components.dashboard_settings import update_model_dropdown
   >>> result = update_model_dropdown("anthropic")
   >>> print(result)
   
   Should show: {'choices': ['claude-3-5-sonnet-20241022', ...], 'value': '...'}

6. 📊 UPGRADE GRADIO (if version < 4.0)
   - Run: pip install --upgrade gradio
   - Then restart the WebUI

7. 🐛 ENABLE VERBOSE LOGGING
   Add this to the top of webui.py:
   
   import logging
   logging.basicConfig(level=logging.DEBUG)

8. 🆘 IF NOTHING WORKS
   - Share the COMPLETE console output when starting WebUI
   - Share the COMPLETE console output when changing provider
   - Share any browser console errors (F12 → Console tab)
""")

print("=" * 80)
print("✅ DIAGNOSTIC COMPLETE")
print("=" * 80)
