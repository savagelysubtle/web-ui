import gradio as gr

from src.web_ui.webui.components.agent_settings_tab import create_agent_settings_tab
from src.web_ui.webui.components.browser_settings_tab import create_browser_settings_tab
from src.web_ui.webui.components.browser_use_agent_tab import create_browser_use_agent_tab
from src.web_ui.webui.components.deep_research_agent_tab import create_deep_research_agent_tab
from src.web_ui.webui.components.load_save_config_tab import create_load_save_config_tab
from src.web_ui.webui.components.mcp_settings_tab import create_mcp_settings_tab
from src.web_ui.webui.components.quick_start_tab import create_quick_start_tab
from src.web_ui.webui.webui_manager import WebuiManager

theme_map = {
    "Default": gr.themes.Default(),
    "Soft": gr.themes.Soft(),
    "Monochrome": gr.themes.Monochrome(),
    "Glass": gr.themes.Glass(),
    "Origin": gr.themes.Origin(),
    "Citrus": gr.themes.Citrus(),
    "Ocean": gr.themes.Ocean(),
    "Base": gr.themes.Base(),
}


def create_ui(theme_name="Ocean"):
    css = """
    .gradio-container {
        width: 85vw !important;
        max-width: 85% !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
    }

    /* Enhanced Header Styles */
    .header-container {
        text-align: center;
        padding: 25px 20px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(168, 85, 247, 0.12));
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .header-main {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 8px;
    }
    .header-icon {
        font-size: 32px;
    }
    .header-title {
        margin: 0;
        font-size: 2em;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .header-tagline {
        font-size: 1.1em;
        margin: 8px 0 16px 0;
        opacity: 0.9;
    }
    .header-features {
        display: flex;
        gap: 12px;
        justify-content: center;
        flex-wrap: wrap;
    }
    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 500;
    }
    .badge-icon {
        font-size: 1.1em;
    }

    /* Loading States */
    .loading-spinner {
        border: 4px solid rgba(99, 102, 241, 0.1);
        border-top: 4px solid #6366f1;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: rgba(128, 128, 128, 0.8);
    }
    .empty-state-icon {
        font-size: 48px;
        margin-bottom: 16px;
    }

    /* Existing Styles */
    .header-text {
        text-align: center;
        margin-bottom: 15px;
        padding: 20px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
        border-radius: 12px;
    }
    .tab-header-text {
        text-align: center;
        font-size: 1.1em;
        margin-bottom: 15px;
    }
    .settings-card {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background: rgba(0, 0, 0, 0.02);
    }
    .main-tabs > .tab-nav > button {
        font-size: 1.05em;
        font-weight: 500;
        padding: 12px 20px;
    }
    .secondary-tabs > .tab-nav > button {
        font-size: 0.95em;
        padding: 8px 16px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 500;
        margin-left: 8px;
    }
    .preset-description {
        font-size: 0.9em;
        color: rgba(128, 128, 128, 0.9);
        margin-top: -8px;
        margin-bottom: 12px;
    }
    .preset-status {
        padding: 12px;
        border-radius: 8px;
        background: rgba(99, 102, 241, 0.1);
        margin-top: 15px;
    }
    .status-display {
        padding: 15px;
        border-radius: 10px;
        background: rgba(0, 0, 0, 0.02);
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    .gr-group {
        margin-bottom: 12px;
    }
    .primary-button {
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        border: none !important;
        font-weight: 500;
    }
    .secondary-button {
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
    }

    /* Notification System */
    #notification-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 400px;
    }
    .notification {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s forwards;
    }
    .notification-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: bold;
        flex-shrink: 0;
    }
    .notification-success .notification-icon {
        background: #10b981;
        color: white;
    }
    .notification-error .notification-icon {
        background: #ef4444;
        color: white;
    }
    .notification-warning .notification-icon {
        background: #f59e0b;
        color: white;
    }
    .notification-info .notification-icon {
        background: #3b82f6;
        color: white;
    }
    .notification-content {
        flex: 1;
    }
    .notification-content strong {
        display: block;
        margin-bottom: 4px;
    }
    .notification-content p {
        margin: 0;
        font-size: 0.9em;
        opacity: 0.8;
    }
    .notification-close {
        background: none;
        border: none;
        font-size: 24px;
        cursor: pointer;
        opacity: 0.5;
        transition: opacity 0.2s;
    }
    .notification-close:hover {
        opacity: 1;
    }
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    /* Keyboard Shortcuts Modal */
    .shortcuts-modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    }
    .shortcuts-content {
        background: var(--body-background-fill);
        padding: 30px;
        border-radius: 12px;
        max-width: 500px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    }
    .shortcut-list {
        margin: 20px 0;
    }
    .shortcut-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.1);
    }
    .shortcut-item:last-child {
        border-bottom: none;
    }
    kbd {
        display: inline-block;
        padding: 3px 6px;
        font-family: monospace;
        font-size: 0.85em;
        background: rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-radius: 3px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    /* Focus Indicators */
    *:focus-visible {
        outline: 2px solid #6366f1;
        outline-offset: 2px;
        border-radius: 4px;
    }

    /* Mobile Responsiveness */
    @media (max-width: 768px) {
        .gradio-container {
            width: 95vw !important;
            max-width: 95% !important;
            padding: 5px !important;
        }
        .header-container {
            padding: 15px;
            font-size: 0.9em;
        }
        .header-title {
            font-size: 1.5em !important;
        }
        .header-features {
            flex-direction: column;
        }
        .main-tabs > .tab-nav {
            overflow-x: auto;
            white-space: nowrap;
        }
        .main-tabs > .tab-nav > button {
            min-width: auto;
            padding: 10px 15px;
            font-size: 0.9em;
        }
        button, .gr-button {
            min-height: 44px;
            min-width: 44px;
        }
        .gr-form {
            flex-direction: column !important;
        }
    }
    @media (max-width: 480px) {
        .feature-badge {
            font-size: 0.8em;
            padding: 4px 10px;
        }
    }
    """

    # Enhanced JavaScript features - loaded safely after page ready
    js_func = """
    function refresh() {
        const url = new URL(window.location);
        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }

    // Initialize features after a short delay to ensure Gradio is ready
    setTimeout(function() {
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + Enter to submit (when in textarea)
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && e.target.matches('textarea')) {
                const runButton = document.querySelector('button[id*="run"]');
                if (runButton) runButton.click();
            }

            // Escape to stop
            if (e.key === 'Escape' && !e.target.matches('input, textarea')) {
                const stopButton = document.querySelector('button[id*="stop"]');
                if (stopButton) stopButton.click();
            }

            // Show shortcuts with ?
            if (e.key === '?' && !e.target.matches('input, textarea')) {
                showKeyboardShortcuts();
            }
        });

        window.showKeyboardShortcuts = function() {
            // Remove existing modal if any
            const existing = document.querySelector('.shortcuts-modal');
            if (existing) {
                existing.remove();
                return;
            }

            const modal = document.createElement('div');
            modal.className = 'shortcuts-modal';
            modal.innerHTML = `
                <div class="shortcuts-content">
                    <h3 style="margin-top: 0;">⌨️ Keyboard Shortcuts</h3>
                    <div class="shortcut-list">
                        <div class="shortcut-item">
                            <div>
                                <kbd>Ctrl</kbd> + <kbd>Enter</kbd>
                            </div>
                            <span>Submit task (when in text area)</span>
                        </div>
                        <div class="shortcut-item">
                            <div><kbd>Esc</kbd></div>
                            <span>Stop agent</span>
                        </div>
                        <div class="shortcut-item">
                            <div><kbd>?</kbd></div>
                            <span>Show this help</span>
                        </div>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" style="margin-top: 20px; padding: 8px 16px; cursor: pointer;">Close</button>
                </div>
            `;
            modal.onclick = function(e) {
                if (e.target === modal) {
                    modal.remove();
                }
            };
            document.body.appendChild(modal);
        };

        // Notification system
        window.showNotification = function(type, title, message, duration) {
            duration = duration || 5000;
            let container = document.getElementById('notification-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'notification-container';
                document.body.appendChild(container);
            }

            const notification = document.createElement('div');
            notification.className = 'notification notification-' + type;

            const icons = {
                success: '✓',
                info: 'ℹ',
                warning: '⚠',
                error: '✕'
            };

            notification.innerHTML = `
                <div class="notification-icon">${icons[type] || 'ℹ'}</div>
                <div class="notification-content">
                    <strong>${title}</strong>
                    <p>${message}</p>
                </div>
                <button class="notification-close" onclick="this.parentElement.remove()">×</button>
            `;
            container.appendChild(notification);

            setTimeout(function() {
                notification.style.animation = 'slideOut 0.3s forwards';
                setTimeout(function() {
                    if (notification.parentNode) notification.remove();
                }, 300);
            }, duration);
        };
    }, 100);
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
        title="Browser Use WebUI",
        theme=theme_map[theme_name],
        css=css,
        # Temporarily disabled to debug empty tabs issue
        # js=js_func,
    ) as demo:
        # Enhanced Header with visual badges
        with gr.Row():
            gr.HTML("""
            <div class="header-container">
                <div class="header-main">
                    <span class="header-icon">🌐</span>
                    <h1 class="header-title">Browser Use WebUI</h1>
                </div>
                <p class="header-tagline">AI-Powered Browser Automation Platform</p>
                <div class="header-features">
                    <span class="feature-badge"><span class="badge-icon">🤖</span> Multi-LLM</span>
                    <span class="feature-badge"><span class="badge-icon">🌐</span> Custom Browser</span>
                    <span class="feature-badge"><span class="badge-icon">🔌</span> MCP Compatible</span>
                    <span class="feature-badge"><span class="badge-icon">🔬</span> Deep Research</span>
                </div>
            </div>
            """)

        # Main navigation with improved organization
        # Note: Settings tab created first so components are registered before Quick Start references them
        with gr.Tabs(elem_classes=["main-tabs"], selected="🚀 Quick Start") as main_tabs:
            # ⚙️ SETTINGS TAB (CONSOLIDATED) - Create first so components exist
            with gr.TabItem("⚙️ Settings"):
                gr.Markdown(
                    """
                    ### Configure Your AI Agent
                    Set up LLM providers, browser options, and MCP servers. All settings are organized in collapsible sections below.
                    """,
                    elem_classes=["tab-header-text"],
                )

                with gr.Tabs(elem_classes=["secondary-tabs"]):
                    with gr.TabItem("🤖 Agent Settings"):
                        create_agent_settings_tab(ui_manager)

                    with gr.TabItem("🌐 Browser Settings"):
                        create_browser_settings_tab(ui_manager)

                    with gr.TabItem("🔌 MCP Settings"):
                        create_mcp_settings_tab(ui_manager)

            # 🚀 QUICK START TAB - Create after settings so we can reference components
            with gr.TabItem("🚀 Quick Start"):
                create_quick_start_tab(ui_manager)

            # 🤖 RUN AGENT TAB
            with gr.TabItem("🤖 Run Agent"):
                gr.Markdown(
                    """
                    ### Execute Browser Automation Tasks
                    Enter your task below and let the AI agent control the browser for you.
                    """,
                    elem_classes=["tab-header-text"],
                )
                create_browser_use_agent_tab(ui_manager)

            # 🎁 AGENT MARKETPLACE TAB
            with gr.TabItem("🎁 Agent Marketplace"):
                gr.Markdown(
                    """
                    ### Specialized Agents
                    Pre-built agents optimized for specific tasks. Choose an agent that matches your use case.
                    """,
                    elem_classes=["tab-header-text"],
                )
                with gr.Tabs(elem_classes=["secondary-tabs"]):
                    with gr.TabItem("🔬 Deep Research"):
                        gr.Markdown("""
                        **Deep Research Agent** performs comprehensive multi-source research with automatic verification and synthesis.

                        **Best for:** Academic research, market analysis, competitive intelligence
                        """)
                        create_deep_research_agent_tab(ui_manager)

            # 💾 CONFIG MANAGEMENT TAB
            with gr.TabItem("💾 Config Management"):
                gr.Markdown(
                    """
                    ### Save & Load Configurations
                    Save your current settings or load previously saved configurations.
                    """,
                    elem_classes=["tab-header-text"],
                )
                create_load_save_config_tab(ui_manager)

    return demo
