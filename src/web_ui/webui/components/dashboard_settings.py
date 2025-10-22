"""
Dashboard Settings Panel

Consolidated settings panel with LLM, Browser, MCP, and Advanced configuration.
Collapsible by default with toggle button.
"""

import logging
import os

import gradio as gr

from src.web_ui.utils import config
from src.web_ui.utils.mcp_config import get_mcp_config_path, get_mcp_config_summary, load_mcp_config
from src.web_ui.webui.webui_manager import WebuiManager

logger = logging.getLogger(__name__)


def strtobool(val):
    """Convert a string representation of truth to true (1) or false (0)."""
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    elif val in ("n", "no", "f", "false", "off", "0"):
        return 0
    else:
        raise ValueError(f"invalid truth value {val!r}")


def update_model_dropdown(llm_provider):
    """Update the model name dropdown with predefined models for the selected provider."""
    logger.info(f"Updating model dropdown for provider: {llm_provider}")
    if llm_provider in config.model_names:
        models = config.model_names[llm_provider]
        logger.info(f"Found {len(models)} models for {llm_provider}: {models[:3]}...")
        return gr.update(
            choices=models,
            value=models[0] if models else "",
            interactive=True,
        )
    else:
        logger.warning(f"Provider {llm_provider} not found in config.model_names")
        return gr.update(choices=[], value="", interactive=True)


async def close_browser(webui_manager: WebuiManager):
    """Close browser when browser config changes."""
    if webui_manager.bu_current_task and not webui_manager.bu_current_task.done():
        webui_manager.bu_current_task.cancel()
        webui_manager.bu_current_task = None

    if webui_manager.bu_browser_context:
        logger.info("⚠️ Closing browser context when changing browser config.")
        await webui_manager.bu_browser_context.close()
        webui_manager.bu_browser_context = None

    if webui_manager.bu_browser:
        logger.info("⚠️ Closing browser when changing browser config.")
        await webui_manager.bu_browser.close()
        webui_manager.bu_browser = None


def create_dashboard_settings(webui_manager: WebuiManager):
    """
    Create the collapsible settings panel with consolidated configuration.

    Args:
        webui_manager: WebUI manager instance
    """
    settings_components = {}

    gr.Markdown("## ⚙️ Settings")

    # Save/Load Config at Top
    with gr.Row():
        save_config_button = gr.Button("💾 Save", variant="primary", scale=1, size="sm")
        load_config_button = gr.Button("📂 Load", variant="secondary", scale=1, size="sm")

    config_file = gr.File(
        label="Configuration File",
        file_types=[".json"],
        interactive=True,
        visible=False,
    )
    config_status = gr.Textbox(label="Status", lines=1, interactive=False, visible=False)

    gr.Markdown("---")

    # 🤖 LLM Configuration
    with gr.Accordion("🤖 LLM Configuration", open=True):
        gr.Markdown("**Primary language model** for agent reasoning")

        with gr.Row():
            llm_provider = gr.Dropdown(
                choices=[provider for provider, model in config.model_names.items()],
                label="Provider",
                value=os.getenv("DEFAULT_LLM", "openai"),
                interactive=True,
            )
            default_provider = os.getenv("DEFAULT_LLM", "openai")
            default_models = config.model_names.get(default_provider, [])
            llm_model_name = gr.Dropdown(
                label="Model",
                choices=default_models,
                value=default_models[0] if default_models else "",
                interactive=True,
                allow_custom_value=True,
            )

        with gr.Row():
            llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.6,
                step=0.1,
                label="Temperature",
                info="0=deterministic, 2=creative",
                interactive=True,
            )
            use_vision = gr.Checkbox(
                label="Enable Vision",
                value=True,
                info="Use screenshots for context",
                interactive=True,
            )

        # API Credentials (collapsed)
        with gr.Accordion("🔑 API Credentials", open=False):
            with gr.Row():
                llm_base_url = gr.Textbox(
                    label="Base URL",
                    value="",
                    placeholder="https://api.example.com/v1",
                    info="Leave blank for default",
                )
                llm_api_key = gr.Textbox(
                    label="API Key",
                    type="password",
                    value="",
                    placeholder="sk-...",
                    info="Leave blank to use .env",
                )

        # Ollama-specific setting
        ollama_num_ctx = gr.Slider(
            minimum=2**8,
            maximum=2**16,
            value=16000,
            step=1,
            label="Ollama Context Length",
            visible=False,
            interactive=True,
        )

        # Planner LLM (collapsed by default)
        use_planner = gr.Checkbox(
            label="Use separate planner model",
            value=False,
            info="Enable for complex multi-step reasoning",
            interactive=True,
        )

        with gr.Group(visible=False) as planner_group:
            gr.Markdown("**Planner Model Configuration**")

            with gr.Row():
                planner_llm_provider = gr.Dropdown(
                    choices=[provider for provider, model in config.model_names.items()],
                    label="Planner Provider",
                    value=None,
                    interactive=True,
                )
                planner_llm_model_name = gr.Dropdown(
                    label="Planner Model",
                    interactive=True,
                    allow_custom_value=True,
                )

            planner_llm_temperature = gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.6,
                step=0.1,
                label="Temperature",
                interactive=True,
            )

            planner_use_vision = gr.Checkbox(
                label="Enable Vision",
                value=False,
                interactive=True,
            )

            planner_ollama_num_ctx = gr.Slider(
                minimum=2**8,
                maximum=2**16,
                value=16000,
                step=1,
                label="Ollama Context",
                visible=False,
                interactive=True,
            )

            with gr.Accordion("🔑 Planner API Credentials", open=False):
                with gr.Row():
                    planner_llm_base_url = gr.Textbox(
                        label="Base URL",
                        value="",
                        placeholder="https://api.example.com/v1",
                    )
                    planner_llm_api_key = gr.Textbox(
                        label="API Key",
                        type="password",
                        value="",
                        placeholder="sk-...",
                    )

    # 🌐 Browser Configuration
    with gr.Accordion("🌐 Browser Configuration", open=False):
        gr.Markdown("**Browser behavior and connection settings**")

        # Custom Browser
        use_own_browser = gr.Checkbox(
            label="Use Own Browser",
            value=bool(strtobool(os.getenv("USE_OWN_BROWSER", "false"))),
            info="Connect to your Chrome instance",
            interactive=True,
        )

        with gr.Group(visible=False) as custom_browser_group:
            browser_binary_path = gr.Textbox(
                label="Browser Binary Path",
                placeholder="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                info="Path to Chrome/Chromium",
            )
            browser_user_data_dir = gr.Textbox(
                label="User Data Directory",
                placeholder="Leave empty for default profile",
                info="Custom profile directory",
            )

        # Browser Behavior
        gr.Markdown("**Behavior Settings**")
        with gr.Row():
            headless = gr.Checkbox(
                label="Headless Mode",
                value=False,
                info="Run without visible GUI",
                interactive=True,
            )
            keep_browser_open = gr.Checkbox(
                label="Keep Open",
                value=bool(strtobool(os.getenv("KEEP_BROWSER_OPEN", "true"))),
                info="Persist between tasks",
                interactive=True,
            )
            disable_security = gr.Checkbox(
                label="Disable Security",
                value=False,
                info="⚠️ Use with caution",
                interactive=True,
            )

        with gr.Row():
            window_w = gr.Number(
                label="Window Width",
                value=1280,
                interactive=True,
            )
            window_h = gr.Number(
                label="Window Height",
                value=1100,
                interactive=True,
            )

        # Advanced Browser Settings (collapsed)
        with gr.Accordion("🔗 Advanced Browser Settings", open=False):
            gr.Markdown("**Remote debugging and storage paths**")

            with gr.Row():
                cdp_url = gr.Textbox(
                    label="CDP URL",
                    value=os.getenv("BROWSER_CDP", None),
                    placeholder="http://localhost:9222",
                )
                wss_url = gr.Textbox(
                    label="WSS URL",
                    placeholder="wss://localhost:9222/devtools/browser/...",
                )

            gr.Markdown("**Storage Paths**")
            with gr.Row():
                save_recording_path = gr.Textbox(
                    label="📹 Recording Path",
                    placeholder="./tmp/record_videos",
                )
                save_trace_path = gr.Textbox(
                    label="📊 Trace Path",
                    placeholder="./tmp/traces",
                )

            with gr.Row():
                save_agent_history_path = gr.Textbox(
                    label="📜 History Path",
                    value="./tmp/agent_history",
                )
                save_download_path = gr.Textbox(
                    label="⬇️ Downloads Path",
                    value="./tmp/downloads",
                )

    # 🔌 MCP Servers
    with gr.Accordion("🔌 MCP Servers", open=False):
        gr.Markdown("**Model Context Protocol server configuration**")

        # MCP Status Display
        mcp_config_path = get_mcp_config_path()
        mcp_config = load_mcp_config()

        if mcp_config and "mcpServers" in mcp_config:
            summary = get_mcp_config_summary(mcp_config)
            mcp_status_md = f"""
✅ **MCP Configuration Active**

{summary}

Configuration file: `{mcp_config_path}`
"""
        else:
            mcp_status_md = f"""
ℹ️ **No MCP Configuration**

No MCP servers configured. You can add servers via the MCP Settings editor.

Expected file: `{mcp_config_path}`
"""

        mcp_status_display = gr.Markdown(mcp_status_md)

        # Button to open MCP settings (will be handled in interface.py)
        edit_mcp_button = gr.Button(
            "📝 Edit MCP Configuration",
            variant="secondary",
            size="sm",
        )

        # Hidden MCP file upload (for compatibility with old agent_settings)
        mcp_json_file = gr.File(
            label="Upload MCP Config (Temporary)",
            interactive=True,
            file_types=[".json"],
            visible=False,
        )
        mcp_server_config = gr.Textbox(
            label="MCP Configuration",
            lines=6,
            interactive=True,
            visible=False,
        )

    # ⚡ Advanced Settings
    with gr.Accordion("⚡ Advanced Settings", open=False):
        gr.Markdown("**System prompts and agent parameters**")

        # System Prompts
        with gr.Accordion("📝 System Prompts", open=False):
            override_system_prompt = gr.Textbox(
                label="Override System Prompt",
                lines=4,
                placeholder="Replace the entire system prompt...",
                interactive=True,
            )
            extend_system_prompt = gr.Textbox(
                label="Extend System Prompt",
                lines=4,
                placeholder="Add additional instructions...",
                interactive=True,
            )

        # Agent Parameters
        gr.Markdown("**Agent Limits**")
        with gr.Row():
            max_steps = gr.Slider(
                minimum=1,
                maximum=1000,
                value=100,
                step=1,
                label="Max Steps",
                interactive=True,
            )
            max_actions = gr.Slider(
                minimum=1,
                maximum=100,
                value=10,
                step=1,
                label="Max Actions/Step",
                interactive=True,
            )

        with gr.Row():
            max_input_tokens = gr.Number(
                label="Max Input Tokens",
                value=128000,
                precision=0,
                interactive=True,
            )
            tool_calling_method = gr.Dropdown(
                label="Tool Calling Method",
                value="auto",
                choices=["function_calling", "json_mode", "raw", "auto", "tools", "None"],
                interactive=True,
                allow_custom_value=True,
            )

    gr.Markdown("---")

    # Save/Load Config at Bottom (repeated for convenience)
    with gr.Row():
        save_config_button_bottom = gr.Button("💾 Save Configuration", variant="primary")
        load_config_button_bottom = gr.Button("📂 Load Configuration", variant="secondary")

    # Register agent settings components with old-style IDs for compatibility
    agent_settings_components = {
        "override_system_prompt": override_system_prompt,
        "extend_system_prompt": extend_system_prompt,
        "llm_provider": llm_provider,
        "llm_model_name": llm_model_name,
        "llm_temperature": llm_temperature,
        "use_vision": use_vision,
        "llm_base_url": llm_base_url,
        "llm_api_key": llm_api_key,
        "ollama_num_ctx": ollama_num_ctx,
        "planner_llm_provider": planner_llm_provider,
        "planner_llm_model_name": planner_llm_model_name,
        "planner_llm_temperature": planner_llm_temperature,
        "planner_use_vision": planner_use_vision,
        "planner_ollama_num_ctx": planner_ollama_num_ctx,
        "planner_llm_base_url": planner_llm_base_url,
        "planner_llm_api_key": planner_llm_api_key,
        "max_steps": max_steps,
        "max_actions": max_actions,
        "max_input_tokens": max_input_tokens,
        "tool_calling_method": tool_calling_method,
        "mcp_json_file": mcp_json_file,
        "mcp_server_config": mcp_server_config,
    }
    webui_manager.add_components("agent_settings", agent_settings_components)

    # Register browser settings components with old-style IDs for compatibility
    browser_settings_components = {
        "browser_binary_path": browser_binary_path,
        "browser_user_data_dir": browser_user_data_dir,
        "use_own_browser": use_own_browser,
        "keep_browser_open": keep_browser_open,
        "headless": headless,
        "disable_security": disable_security,
        "window_w": window_w,
        "window_h": window_h,
        "cdp_url": cdp_url,
        "wss_url": wss_url,
        "save_recording_path": save_recording_path,
        "save_trace_path": save_trace_path,
        "save_agent_history_path": save_agent_history_path,
        "save_download_path": save_download_path,
    }
    webui_manager.add_components("browser_settings", browser_settings_components)

    # Register dashboard settings components
    settings_components.update(
        {
            "save_config_button": save_config_button,
            "load_config_button": load_config_button,
            "config_file": config_file,
            "config_status": config_status,
            "llm_provider": llm_provider,
            "llm_model_name": llm_model_name,
            "llm_temperature": llm_temperature,
            "use_vision": use_vision,
            "llm_base_url": llm_base_url,
            "llm_api_key": llm_api_key,
            "ollama_num_ctx": ollama_num_ctx,
            "use_planner": use_planner,
            "planner_group": planner_group,
            "planner_llm_provider": planner_llm_provider,
            "planner_llm_model_name": planner_llm_model_name,
            "planner_llm_temperature": planner_llm_temperature,
            "planner_use_vision": planner_use_vision,
            "planner_ollama_num_ctx": planner_ollama_num_ctx,
            "planner_llm_base_url": planner_llm_base_url,
            "planner_llm_api_key": planner_llm_api_key,
            "use_own_browser": use_own_browser,
            "custom_browser_group": custom_browser_group,
            "browser_binary_path": browser_binary_path,
            "browser_user_data_dir": browser_user_data_dir,
            "headless": headless,
            "keep_browser_open": keep_browser_open,
            "disable_security": disable_security,
            "window_w": window_w,
            "window_h": window_h,
            "cdp_url": cdp_url,
            "wss_url": wss_url,
            "save_recording_path": save_recording_path,
            "save_trace_path": save_trace_path,
            "save_agent_history_path": save_agent_history_path,
            "save_download_path": save_download_path,
            "mcp_status_display": mcp_status_display,
            "edit_mcp_button": edit_mcp_button,
            "mcp_json_file": mcp_json_file,
            "mcp_server_config": mcp_server_config,
            "override_system_prompt": override_system_prompt,
            "extend_system_prompt": extend_system_prompt,
            "max_steps": max_steps,
            "max_actions": max_actions,
            "max_input_tokens": max_input_tokens,
            "tool_calling_method": tool_calling_method,
            "save_config_button_bottom": save_config_button_bottom,
            "load_config_button_bottom": load_config_button_bottom,
        }
    )

    webui_manager.add_components("dashboard_settings", settings_components)

    # Wire up event handlers

    # LLM Provider change -> Update model dropdown and show/hide Ollama context
    def update_llm_settings(provider):
        """Update both model dropdown and Ollama context visibility."""
        models_update = update_model_dropdown(provider)
        ollama_visible = gr.update(visible=provider == "ollama")
        return models_update, ollama_visible

    llm_provider.change(
        fn=update_llm_settings,
        inputs=[llm_provider],
        outputs=[llm_model_name, ollama_num_ctx],
    )

    # Planner checkbox -> Show/hide planner group
    use_planner.change(
        fn=lambda checked: gr.update(visible=checked),
        inputs=[use_planner],
        outputs=[planner_group],
    )

    # Planner provider change
    def update_planner_settings(provider):
        """Update both planner model dropdown and Ollama context visibility."""
        models_update = update_model_dropdown(provider)
        ollama_visible = gr.update(visible=provider == "ollama")
        return models_update, ollama_visible

    planner_llm_provider.change(
        fn=update_planner_settings,
        inputs=[planner_llm_provider],
        outputs=[planner_llm_model_name, planner_ollama_num_ctx],
    )

    # Use Own Browser checkbox -> Show/hide custom browser fields
    use_own_browser.change(
        fn=lambda checked: gr.update(visible=checked),
        inputs=[use_own_browser],
        outputs=[custom_browser_group],
    )

    # Browser config changes -> Close browser
    async def close_wrapper():
        """Wrapper for closing browser."""
        await close_browser(webui_manager)

    headless.change(close_wrapper)
    keep_browser_open.change(close_wrapper)
    disable_security.change(close_wrapper)
    use_own_browser.change(close_wrapper)

    # Note: Save/Load config handlers will be wired up in interface.py
    # to ensure all components are registered first

    return settings_components
