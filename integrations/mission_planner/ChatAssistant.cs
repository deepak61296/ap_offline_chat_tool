using MissionPlanner.Controls;
using MissionPlanner.Utilities;
using MissionPlanner.ArduPilot.Mavlink;
using System;
using System.Drawing;
using System.Windows.Forms;
using System.Threading.Tasks;
using System.Threading;
using System.Linq;

namespace MissionPlanner.GCSViews
{
    /// <summary>
    /// AI Chat Assistant form for Mission Planner
    /// </summary>
    public partial class ChatAssistant : MyUserControl, IActivate
    {
        private AIBackendService aiService;
        private DroneCommandExecutor commandExecutor;
        private TelemetryCollector telemetryCollector;
        private bool isProcessing = false;
        private bool isConnected = false;
        private CancellationTokenSource cancellationTokenSource;
        private string lastSavedScriptPath = null;
        private string lastScriptDescription = null;

        // Debug console components
        private RichTextBox debugConsole;
        // debugToggleButton is declared in Designer.cs
        private bool debugConsoleVisible = false;

        /// <summary>
        /// Constructor for ChatAssistant form
        /// </summary>
        public ChatAssistant()
        {
            InitializeComponent();
            
            // Ensure Flash button has correct positioning (left of Send button)
            if (flashScriptButton != null)
            {
                flashScriptButton.Location = new System.Drawing.Point(585, 10);
                flashScriptButton.Size = new System.Drawing.Size(100, 60);
                flashScriptButton.Text = "⚡ Flash FC";
                flashScriptButton.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right;
                flashScriptButton.Visible = false;
                flashScriptButton.Enabled = false;
            }
            
            // Initialize Debug Console
            InitializeDebugConsole();

            // Get backend URL from settings (default: http://localhost:5000)
            string backendUrl = Settings.Instance.GetString("ai_backend_url", "http://localhost:5000");

            // Initialize AI backend service (90 second timeout for cold start LLM queries)
            aiService = new AIBackendService(backendUrl, 90);
            
            // Initialize command executor with Mission Planner's MAVLink connection
            commandExecutor = new DroneCommandExecutor(MainV2.comPort);
            
            // Initialize telemetry collector
            telemetryCollector = new TelemetryCollector(MainV2.comPort);
            
            // Set default mode to Ask (read-only) for safety
            modeComboBox.SelectedIndex = 1;  // Ask mode (read-only)
            
            // Add mode change event handler
            modeComboBox.SelectedIndexChanged += ModeComboBox_SelectedIndexChanged;
            
            // Load available models from Ollama
            LoadAvailableModels();
        }

        /// <summary>
        /// Handles mode selection changes and shows warning for Agent mode
        /// </summary>
        private void ModeComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
            // Mode indices: 0 = Agent, 1 = Ask, 2 = Script
            if (modeComboBox.SelectedIndex == 0) // Agent mode
            {
                flashScriptButton.Visible = false;
                AppendMessage("[System] WARNING: Agent Mode enabled. AI can now control drone functions including ARM, TAKEOFF, LAND, and movement commands. Use with caution!", Color.FromArgb(255, 165, 0));
            }
            else if (modeComboBox.SelectedIndex == 1) // Ask mode
            {
                flashScriptButton.Visible = false;
                AppendMessage("[System] Ask Mode enabled. AI is in read-only mode and cannot execute commands.", Color.FromArgb(0, 200, 83));
            }
            else if (modeComboBox.SelectedIndex == 2) // Script mode
            {
                flashScriptButton.Visible = true;
                flashScriptButton.Enabled = (lastSavedScriptPath != null);
                AppendMessage("[System] Script Mode enabled. AI will generate ArduPilot Lua scripts from your requests.", Color.FromArgb(100, 149, 237));
            }
        }

        /// <summary>
        /// Called when the form is activated
        /// </summary>
        public void Activate()
        {
            // Apply theme to controls
            ThemeManager.ApplyThemeTo(this);
        }

        /// <summary>
        /// Handles the Send button click event
        /// </summary>
        private void sendButton_Click(object sender, EventArgs e)
        {
            SendMessage();
        }

        /// <summary>
        /// Handles the Enter key press in the input text box
        /// </summary>
        private void inputTextBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                e.Handled = true;
                e.SuppressKeyPress = true;
                SendMessage();
            }
        }

        /// <summary>
        /// Sends the user message and displays the response
        /// </summary>
        private async void SendMessage()
        {
            try
            {
                // Prevent multiple simultaneous requests
                if (isProcessing)
                {
                    return;
                }

                string userMessage = inputTextBox.Text.Trim();

                if (string.IsNullOrEmpty(userMessage))
                {
                    return;
                }

                // Mark as processing - hide send, show cancel
                isProcessing = true;
                sendButton.Visible = false;
                
                // Create cancellation token and show cancel button
                cancellationTokenSource = new CancellationTokenSource();
                cancelButton.Visible = true;

                // Display user message in modern blue
                AppendMessage("You: " + userMessage, Color.FromArgb(0, 120, 215));

                // Clear input box
                inputTextBox.Clear();

                // Show loading indicator
                AppendMessage("Assistant: Thinking...", Color.Gray);

                // Auto-scroll to bottom
                chatHistoryBox.SelectionStart = chatHistoryBox.Text.Length;
                chatHistoryBox.ScrollToCaret();

                // Get mode and model from UI
                string mode = modeComboBox.SelectedItem?.ToString().ToLower() ?? "agent";
                string model = modelComboBox.SelectedItem?.ToString() ?? "qwen2.5:3b";
                
                // Collect telemetry data
                var telemetry = telemetryCollector.CollectAll();

                // Get AI response with mode, model, telemetry, and cancellation token
                AIResponse aiResponse = await aiService.SendMessageAsync(
                    userMessage, 
                    mode, 
                    model, 
                    telemetry,
                    cancellationTokenSource.Token
                );

                // Remove "Thinking..." message
                RemoveLastMessage();

                // Check if request was successful
                if (!aiResponse.Success)
                {
                    AppendMessage($"Assistant: [Error: {aiResponse.Error}]", Color.Red);
                    chatHistoryBox.SelectionStart = chatHistoryBox.Text.Length;
                    chatHistoryBox.ScrollToCaret();
                    return;
                }

                // Display AI response
                AppendMessage("Assistant: " + aiResponse.Response, Color.Black);

                // Execute command if present
                if (aiResponse.Command != null)
                {
                    AppendMessage($"[Executing: {aiResponse.Command.Type}...]", Color.Blue);
                    
                    string result = await commandExecutor.ExecuteCommand(aiResponse.Command);
                    
                    // Track last saved script for flash button
                    if (aiResponse.Command.Type == "LUA_SCRIPT" && result.StartsWith("✓"))
                    {
                        var lines = result.Split('\n');

                        // Parse the result to extract full path
                        // Format: Line 0: ✓ Lua script saved: {filename}
                        //         Line 1: 📁 Location: {directory}
                        //         Line 2: 💾 Full path: {full_path}
                        //         Line 3: 📊 Size: {size}
                        //         Line 4: 📝 {description}

                        string fullPath = null;
                        string description = "Lua script";

                        foreach (var line in lines)
                        {
                            if (line.Contains("💾 Full path:"))
                            {
                                fullPath = line.Replace("💾 Full path:", "").Trim();
                            }
                            else if (line.Contains("📝 "))
                            {
                                description = line.Replace("📝 ", "").Trim();
                            }
                        }

                        // If full path is found, use it
                        if (!string.IsNullOrEmpty(fullPath))
                        {
                            lastSavedScriptPath = fullPath;
                            lastScriptDescription = description;
                            flashScriptButton.Enabled = true;
                            AppendMessage($"[Script ready to flash: {System.IO.Path.GetFileName(fullPath)}]", Color.FromArgb(100, 149, 237));
                        }
                        else
                        {
                            // Fallback to old method (combine location + filename)
                            if (lines.Length >= 2)
                            {
                                string filename = lines[0].Replace("✓ Lua script saved: ", "").Trim();
                                string location = lines[1].Replace("📁 Location: ", "").Trim();
                                lastSavedScriptPath = System.IO.Path.Combine(location, filename);
                                lastScriptDescription = lines.Length >= 3 ? lines[2].Replace("📝 ", "").Trim() : "Lua script";
                                flashScriptButton.Enabled = true;
                            }
                        }
                    }
                    
                    // Color code the result (green for success, red for error)
                    Color resultColor = result.StartsWith("✓") ? Color.Green : Color.Red;
                    AppendMessage(result, resultColor);
                }

                // Auto-scroll to bottom
                chatHistoryBox.SelectionStart = chatHistoryBox.Text.Length;
                chatHistoryBox.ScrollToCaret();
            }
            catch (Exception ex)
            {
                CustomMessageBox.Show("Error sending message: " + ex.Message, Strings.ERROR);
            }
            finally
            {
                // Re-enable send button and hide cancel button
                isProcessing = false;
                sendButton.Visible = true;
                cancelButton.Visible = false;
                cancellationTokenSource?.Dispose();
                cancellationTokenSource = null;
            }
        }

        /// <summary>
        /// Handles cancel button click to stop AI processing
        /// </summary>
        private void cancelButton_Click(object sender, EventArgs e)
        {
            try
            {
                // Cancel the ongoing request
                cancellationTokenSource?.Cancel();
                
                // Remove "Thinking..." message
                RemoveLastMessage();
                
                // Show cancellation message
                AppendMessage("Assistant: [Request cancelled by user]", Color.Orange);
                
                // Auto-scroll to bottom
                chatHistoryBox.SelectionStart = chatHistoryBox.Text.Length;
                chatHistoryBox.ScrollToCaret();
            }
            catch (Exception ex)
            {
                CustomMessageBox.Show("Error cancelling request: " + ex.Message, Strings.ERROR);
            }
        }

        /// <summary>
        /// Appends a message to the chat history with the specified color
        /// </summary>
        /// <param name="message">The message to append</param>
        /// <param name="color">The color of the message text</param>
        private void AppendMessage(string message, Color color)
        {
            chatHistoryBox.SelectionStart = chatHistoryBox.Text.Length;
            chatHistoryBox.SelectionLength = 0;
            
            // Adjust colors for dark background readability
            Color displayColor = color;
            if (color == Color.Black)
                displayColor = Color.FromArgb(230, 230, 230);
            else if (color == Color.Gray)
                displayColor = Color.FromArgb(150, 150, 150);
            else if (color == Color.Blue)
                displayColor = Color.FromArgb(100, 180, 255);
            else if (color == Color.Green)
                displayColor = Color.FromArgb(100, 255, 100);
            else if (color == Color.Red || color == Color.OrangeRed)
                displayColor = Color.FromArgb(255, 120, 120);
            else if (color == Color.FromArgb(0, 120, 215))
                displayColor = Color.FromArgb(100, 200, 255);
            
            chatHistoryBox.SelectionColor = displayColor;
            chatHistoryBox.SelectionFont = new Font(chatHistoryBox.Font.FontFamily, 12, FontStyle.Regular);
            chatHistoryBox.AppendText(message + Environment.NewLine + Environment.NewLine);
            chatHistoryBox.SelectionColor = chatHistoryBox.ForeColor;
        }

        /// <summary>
        /// Removes the last message from the chat history (used to remove loading indicator)
        /// </summary>
        private void RemoveLastMessage()
        {
            try
            {
                string text = chatHistoryBox.Text;
                int lastDoubleNewline = text.LastIndexOf(Environment.NewLine + Environment.NewLine);
                
                if (lastDoubleNewline > 0)
                {
                    // Find the previous double newline to get the start of the last message
                    int previousDoubleNewline = text.LastIndexOf(Environment.NewLine + Environment.NewLine, lastDoubleNewline - 1);
                    int startPos = previousDoubleNewline >= 0 ? previousDoubleNewline + (Environment.NewLine + Environment.NewLine).Length : 0;
                    
                    chatHistoryBox.Select(startPos, chatHistoryBox.Text.Length - startPos);
                    chatHistoryBox.SelectedText = "";
                }
            }
            catch
            {
                // Ignore errors in removing message
            }
        }

        /// <summary>
        /// Initialize the debug console UI
        /// </summary>
        private int debugConsoleHeight = 150;
        private const int BUTTON_RESERVED_AREA = 40; // Reserved space for debug button above toolbar
        private Panel debugPanel;
        private Label debugLabel;

        private void InitializeDebugConsole()
        {
            // Wire up click event for debug toggle button (already created in Designer)
            debugToggleButton.Click += DebugToggleButton_Click;

            // Create debug panel container with header
            debugPanel = new Panel();
            debugPanel.Name = "debugPanel";
            debugPanel.BackColor = Color.Black;
            debugPanel.Visible = false;
            debugPanel.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            debugPanel.Location = new Point(0, bottomToolbar.Top - debugConsoleHeight);
            debugPanel.Size = new Size(this.Width, debugConsoleHeight);

            // Debug header label
            debugLabel = new Label();
            debugLabel.Text = " DEBUG CONSOLE";
            debugLabel.BackColor = Color.FromArgb(30, 30, 30);
            debugLabel.ForeColor = Color.Cyan;
            debugLabel.Font = new Font("Consolas", 9F, FontStyle.Bold);
            debugLabel.Dock = DockStyle.Top;
            debugLabel.Height = 20;
            debugLabel.TextAlign = ContentAlignment.MiddleLeft;
            debugPanel.Controls.Add(debugLabel);

            // Create debug console RichTextBox inside panel
            debugConsole = new RichTextBox();
            debugConsole.Name = "debugConsole";
            debugConsole.BackColor = Color.Black;
            debugConsole.ForeColor = Color.LightGreen;
            debugConsole.Font = new Font("Consolas", 9F);
            debugConsole.ReadOnly = true;
            debugConsole.BorderStyle = BorderStyle.None;
            debugConsole.ScrollBars = RichTextBoxScrollBars.Vertical;
            debugConsole.Dock = DockStyle.Fill;
            debugPanel.Controls.Add(debugConsole);

            // Add panel to form
            this.Controls.Add(debugPanel);
        }

        /// <summary>
        /// Toggle debug console visibility
        /// </summary>
        private void DebugToggleButton_Click(object sender, EventArgs e)
        {
            debugConsoleVisible = !debugConsoleVisible;

            if (debugConsoleVisible)
            {
                // Update button appearance - active state (green)
                debugToggleButton.BackColor = Color.FromArgb(0, 100, 0);
                debugToggleButton.Text = "▲ Debug Console";
                debugToggleButton.ForeColor = Color.LimeGreen;
                debugToggleButton.FlatAppearance.BorderColor = Color.LimeGreen;

                // Calculate positions - NEVER cover the button area
                // Debug panel must end ABOVE the reserved button area
                int maxDebugBottom = bottomToolbar.Top - BUTTON_RESERVED_AREA;
                int panelTop = maxDebugBottom - debugConsoleHeight;

                // If panel would go too high, adjust
                if (panelTop < 0) panelTop = 0;

                int actualPanelHeight = maxDebugBottom - panelTop;

                debugPanel.Location = new Point(0, panelTop);
                debugPanel.Size = new Size(this.Width, actualPanelHeight);

                // Shrink chat history to make room for debug panel
                chatHistoryBox.Height = panelTop;

                // Show debug panel, splitter, and bring to front
                debugPanel.Visible = true;
                debugSplitter.Visible = true;
                debugSplitter.Location = new Point(0, panelTop - 3);
                debugPanel.BringToFront();
                debugSplitter.BringToFront();

                // Button should stay visible - bring it to front
                debugToggleButton.BringToFront();

                DebugLog("=== Debug Console Ready ===");
            }
            else
            {
                // Update button appearance - inactive state (gray)
                debugToggleButton.BackColor = Color.FromArgb(60, 60, 60);
                debugToggleButton.Text = "▼ Debug Console";
                debugToggleButton.ForeColor = Color.Cyan;
                debugToggleButton.FlatAppearance.BorderColor = Color.Cyan;

                // Hide debug panel and splitter
                debugPanel.Visible = false;
                debugSplitter.Visible = false;

                // Restore chat height to fill space above bottomToolbar
                chatHistoryBox.Height = bottomToolbar.Top;
            }
        }

        /// <summary>
        /// Log a message to the debug console with auto-color based on content
        /// </summary>
        private void DebugLog(string message)
        {
            if (debugConsole == null) return;

            try
            {
                if (debugConsole.InvokeRequired)
                {
                    debugConsole.BeginInvoke(new Action(() => DebugLog(message)));
                    return;
                }

                // Determine color based on message content
                Color logColor = Color.LightGreen;  // Default
                if (message.Contains("ERROR") || message.Contains("FAILED") || message.Contains("MISMATCH"))
                    logColor = Color.Red;
                else if (message.Contains("WARNING") || message.Contains("⚠"))
                    logColor = Color.Orange;
                else if (message.Contains("SUCCESS") || message.Contains("✓") || message.Contains("OK"))
                    logColor = Color.LimeGreen;
                else if (message.Contains("==="))
                    logColor = Color.Cyan;

                string timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
                int startPos = debugConsole.TextLength;
                debugConsole.AppendText($"[{timestamp}] {message}\n");
                debugConsole.Select(startPos, debugConsole.TextLength - startPos);
                debugConsole.SelectionColor = logColor;
                debugConsole.SelectionLength = 0;
                debugConsole.ScrollToCaret();
            }
            catch
            {
                // Ignore errors
            }
        }

        /// <summary>
        /// Clear the debug console
        /// </summary>
        private void ClearDebugLog()
        {
            if (debugConsole != null)
            {
                debugConsole.Clear();
            }
        }

        /// <summary>
        /// Handles the form load event
        /// </summary>
        private async void ChatAssistant_Load(object sender, EventArgs e)
        {
            // Apply theme
            ThemeManager.ApplyThemeTo(this);

            // Hook up resize handler to maintain layout
            this.Resize += ChatAssistant_Resize;

            // Set initial chat height
            chatHistoryBox.Height = bottomToolbar.Top;

            // Display welcome message
            AppendMessage("Assistant: Welcome to the ArduPilot AI Assistant! How can I help you today?", Color.Black);

            // Check AI backend connection
            await CheckBackendConnectionAsync();
        }

        /// <summary>
        /// Handle resize to maintain layout
        /// </summary>
        private void ChatAssistant_Resize(object sender, EventArgs e)
        {
            // Update chat height based on debug panel visibility
            if (debugConsoleVisible && debugPanel != null)
            {
                // Respect the reserved button area - debug panel must stay ABOVE it
                int maxDebugBottom = bottomToolbar.Top - BUTTON_RESERVED_AREA;
                int panelTop = maxDebugBottom - debugConsoleHeight;
                if (panelTop < 0) panelTop = 0;

                int actualPanelHeight = maxDebugBottom - panelTop;

                debugPanel.Location = new Point(0, panelTop);
                debugPanel.Size = new Size(this.Width, actualPanelHeight);
                chatHistoryBox.Height = panelTop;

                // Keep button visible
                debugToggleButton.BringToFront();
            }
            else
            {
                chatHistoryBox.Height = bottomToolbar.Top;
            }
        }

        /// <summary>
        /// Load available models from Ollama
        /// </summary>
        private async void LoadAvailableModels()
        {
            try
            {
                using (var client = new System.Net.Http.HttpClient())
                {
                    client.Timeout = TimeSpan.FromSeconds(5);
                    var response = await client.GetAsync("http://localhost:11434/api/tags");
                    
                    if (response.IsSuccessStatusCode)
                    {
                        var json = await response.Content.ReadAsStringAsync();
                        var data = Newtonsoft.Json.JsonConvert.DeserializeObject<dynamic>(json);
                        
                        modelComboBox.Items.Clear();
                        
                        foreach (var model in data.models)
                        {
                            string modelName = model.name.ToString();
                            modelComboBox.Items.Add(modelName);
                        }

                        // Set default to qwen2.5:3b if available, otherwise first item
                        int defaultIndex = modelComboBox.Items.IndexOf("qwen2.5:3b");
                        if (defaultIndex >= 0)
                        {
                            modelComboBox.SelectedIndex = defaultIndex;
                        }
                        else if (modelComboBox.Items.Count > 0)
                        {
                            modelComboBox.SelectedIndex = 0;
                        }
                        
                        UpdateConnectionStatus(true);
                    }
                    else
                    {
                        // Fallback to default models
                        modelComboBox.Items.AddRange(new object[] { "qwen2.5:3b", "qwen2.5-coder:7b" });
                        modelComboBox.SelectedIndex = 0;
                        UpdateConnectionStatus(false);
                    }
                }
            }
            catch
            {
                // Fallback to default models if Ollama is not running
                modelComboBox.Items.AddRange(new object[] { "qwen2.5:3b", "qwen2.5-coder:7b" });
                modelComboBox.SelectedIndex = 0;
                UpdateConnectionStatus(false);
            }
        }

        /// <summary>
        /// Update connection status indicator
        /// </summary>
        private void UpdateConnectionStatus(bool connected)
        {
            isConnected = connected;
            
            if (connected)
            {
                connectionButton.ForeColor = Color.FromArgb(0, 200, 0); // Green
                connectionButton.Text = "🔌";
            }
            else
            {
                connectionButton.ForeColor = Color.Red;
                connectionButton.Text = "🔌";
            }
        }

        /// <summary>
        /// Handle connection button click
        /// </summary>
        private async void connectionButton_Click(object sender, EventArgs e)
        {
            if (isConnected)
            {
                // Disconnect - just update status
                UpdateConnectionStatus(false);
                AppendMessage("[System: Disconnected from AI Backend]", Color.Gray);
            }
            else
            {
                // Try to connect
                AppendMessage("[System: Connecting to AI Backend...]", Color.Gray);

                try
                {
                    bool isHealthy = await aiService.CheckHealthAsync();

                    if (isHealthy)
                    {
                        LoadAvailableModels();
                        AppendMessage("[System: AI Backend connected ✓]", Color.Green);
                    }
                    else
                    {
                        UpdateConnectionStatus(false);
                        AppendMessage("[System: AI Backend not available. Please start the backend server.]", Color.OrangeRed);
                    }
                }
                catch
                {
                    UpdateConnectionStatus(false);
                    AppendMessage("[System: Could not connect to AI Backend]", Color.Red);
                }
            }
        }

        /// <summary>
        /// Handle right-click on connection button to configure backend URL
        /// </summary>
        private void connectionButton_MouseUp(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Right)
            {
                // Show context menu for backend configuration
                var contextMenu = new ContextMenuStrip();

                var configureItem = new ToolStripMenuItem("Configure Backend URL...");
                configureItem.Click += (s, args) => ConfigureBackendUrl();
                contextMenu.Items.Add(configureItem);

                var currentUrlItem = new ToolStripMenuItem($"Current: {Settings.Instance.GetString("ai_backend_url", "http://localhost:5000")}");
                currentUrlItem.Enabled = false;
                contextMenu.Items.Add(currentUrlItem);

                contextMenu.Show(connectionButton, e.Location);
            }
        }

        /// <summary>
        /// Show dialog to configure backend URL
        /// </summary>
        private void ConfigureBackendUrl()
        {
            string currentUrl = Settings.Instance.GetString("ai_backend_url", "http://localhost:5000");
            string newUrl = currentUrl;

            var result = MissionPlanner.Controls.InputBox.Show("Configure AI Backend", "Enter backend URL:", ref newUrl);

            if (result == DialogResult.OK && !string.IsNullOrEmpty(newUrl) && newUrl != currentUrl)
            {
                Settings.Instance["ai_backend_url"] = newUrl;

                // Recreate AI service with new URL
                aiService = new AIBackendService(newUrl, 90);

                AppendMessage($"[System] Backend URL changed to: {newUrl}", Color.Cyan);
                AppendMessage("[System] Click connect button to test connection.", Color.Gray);

                UpdateConnectionStatus(false);
            }
        }

        /// <summary>
        /// Check if AI backend is connected and display status
        /// </summary>
        private async Task CheckBackendConnectionAsync()
        {
            try
            {
                bool isHealthy = await aiService.CheckHealthAsync();
                
                if (isHealthy)
                {
                    UpdateConnectionStatus(true);
                    AppendMessage("[System: AI Backend connected ✓]", Color.Green);
                }
                else
                {
                    UpdateConnectionStatus(false);
                    AppendMessage("[System: AI Backend not available. Please start the backend server.]", Color.OrangeRed);
                }
            }
            catch (Exception ex)
            {
                UpdateConnectionStatus(false);
                AppendMessage("[System: Could not check AI backend status]", Color.Gray);
            }
        }


        /// <summary>
        /// Handle flash script button click - uploads last saved script to flight controller
        /// </summary>
        /// <summary>
        /// Check if scripting is enabled (SCR_ENABLE = 1) and offer to enable it if not
        /// </summary>
        private async Task<bool> CheckAndEnableScripting()
        {
            try
            {
                AppendMessage("[Checking if Lua scripting is enabled...]", Color.Blue);

                double scrEnable = MainV2.comPort.MAV.param["SCR_ENABLE"].Value;

                if (scrEnable == 0)
                {
                    AppendMessage("[WARNING: SCR_ENABLE = 0, Lua scripting is DISABLED]", Color.Orange);

                    var result = CustomMessageBox.Show(
                        "Lua Scripting is DISABLED on the flight controller.\n\n" +
                        "Current: SCR_ENABLE = 0\n" +
                        "Required: SCR_ENABLE = 1\n\n" +
                        "Would you like to enable scripting and reboot the FC now?\n\n" +
                        "This process will:\n" +
                        "1. Set SCR_ENABLE = 1\n" +
                        "2. Wait 2 seconds for EEPROM write\n" +
                        "3. Reboot the flight controller\n" +
                        "4. Wait for reconnection\n" +
                        "5. Continue with script upload",
                        "Enable Lua Scripting?",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Question
                    );

                    if (result != (int)DialogResult.Yes)
                    {
                        AppendMessage("[Flash cancelled - scripting not enabled]", Color.Orange);
                        return false;
                    }

                    AppendMessage("[Enabling Lua scripting...]", Color.Blue);

                    // Set SCR_ENABLE = 1
                    bool paramSet = MainV2.comPort.setParam("SCR_ENABLE", 1);

                    if (!paramSet)
                    {
                        AppendMessage("[Error: Failed to set SCR_ENABLE parameter]", Color.Red);
                        CustomMessageBox.Show(
                            "Failed to set SCR_ENABLE parameter.\n\n" +
                            "Please set it manually:\n" +
                            "1. Go to CONFIG > Full Parameter Tree\n" +
                            "2. Find SCR_ENABLE\n" +
                            "3. Set value to 1\n" +
                            "4. Click 'Write Params'\n" +
                            "5. Reboot the flight controller",
                            "Parameter Set Failed",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        );
                        return false;
                    }

                    AppendMessage("✓ SCR_ENABLE set to 1", Color.Green);
                    DebugLog("SCR_ENABLE set to 1");

                    // Also set SCR_HEAP_SIZE if it's too small (scripts won't load without enough memory)
                    try
                    {
                        float currentHeap = MainV2.comPort.MAV.param.ContainsKey("SCR_HEAP_SIZE")
                            ? (float)MainV2.comPort.MAV.param["SCR_HEAP_SIZE"]
                            : 0;

                        DebugLog($"Current SCR_HEAP_SIZE: {currentHeap}");

                        if (currentHeap < 65536)
                        {
                            AppendMessage($"[Setting SCR_HEAP_SIZE from {currentHeap} to 131072...]", Color.Blue);
                            DebugLog("SCR_HEAP_SIZE too small, setting to 131072");
                            bool heapSet = MainV2.comPort.setParam("SCR_HEAP_SIZE", 131072);
                            if (heapSet)
                            {
                                AppendMessage("✓ SCR_HEAP_SIZE set to 131072", Color.Green);
                                DebugLog("SCR_HEAP_SIZE set to 131072");
                            }
                            else
                            {
                                AppendMessage("⚠ Could not set SCR_HEAP_SIZE (scripts may not load)", Color.Orange);
                                DebugLog("WARNING: Failed to set SCR_HEAP_SIZE");
                            }
                        }
                        else
                        {
                            AppendMessage($"✓ SCR_HEAP_SIZE is already {currentHeap} (OK)", Color.Green);
                            DebugLog($"SCR_HEAP_SIZE already adequate: {currentHeap}");
                        }
                    }
                    catch (Exception heapEx)
                    {
                        DebugLog($"Error checking SCR_HEAP_SIZE: {heapEx.Message}");
                        AppendMessage("[Could not check SCR_HEAP_SIZE - continuing anyway]", Color.Gray);
                    }

                    AppendMessage("[Waiting 2 seconds for EEPROM write...]", Color.Gray);

                    // IMPORTANT: Wait for parameter to be written to EEPROM
                    await Task.Delay(2000);

                    AppendMessage("[Rebooting flight controller...]", Color.Blue);
                    DebugLog("Sending reboot command...");

                    // Send reboot command
                    if (!MainV2.comPort.doReboot(false, true))
                    {
                        AppendMessage("[Error: Failed to send reboot command]", Color.Red);
                        AppendMessage("[Please reboot manually and try again]", Color.Orange);
                        return false;
                    }

                    AppendMessage("✓ Reboot command sent", Color.Green);
                    AppendMessage("[Waiting for flight controller to reboot and reconnect...]", Color.Gray);
                    AppendMessage("[This may take 10-15 seconds...]", Color.Gray);

                    // Wait for FC to reboot and reconnect (typical reboot takes 5-10 seconds)
                    await Task.Delay(8000);

                    // Check if still connected (with proper null checks)
                    int retries = 0;
                    while ((MainV2.comPort == null || MainV2.comPort.BaseStream == null || !MainV2.comPort.BaseStream.IsOpen) && retries < 15)
                    {
                        AppendMessage($"[Waiting for reconnection... ({retries + 1}/15)]", Color.Gray);
                        await Task.Delay(1000);
                        retries++;
                    }

                    // Check if reconnected (with null checks)
                    bool reconnected = MainV2.comPort != null &&
                                      MainV2.comPort.BaseStream != null &&
                                      MainV2.comPort.BaseStream.IsOpen;

                    if (!reconnected)
                    {
                        AppendMessage("[Warning: FC not reconnected yet. Please wait and try flash again.]", Color.Orange);
                        CustomMessageBox.Show(
                            "Flight controller has not reconnected yet.\n\n" +
                            "Please wait for the FC to finish rebooting, then try flashing again.\n\n" +
                            "If the FC doesn't reconnect automatically, you may need to:\n" +
                            "1. Manually reconnect using the CONNECT button\n" +
                            "2. Verify SCR_ENABLE = 1 in Full Parameter Tree\n" +
                            "3. Try flashing the script again",
                            "Reconnection Timeout",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Warning
                        );
                        return false;
                    }

                    AppendMessage("✓ Flight controller reconnected", Color.Green);
                    AppendMessage("[Waiting for parameters to load...]", Color.Gray);

                    // Wait for parameters to be fully loaded after reboot
                    await Task.Delay(2000);

                    // Verify parameters are accessible
                    int paramRetries = 0;
                    while ((MainV2.comPort.MAV.param == null || MainV2.comPort.MAV.param.Count == 0) && paramRetries < 10)
                    {
                        AppendMessage($"[Waiting for parameters... ({paramRetries + 1}/10)]", Color.Gray);
                        await Task.Delay(1000);
                        paramRetries++;
                    }

                    if (MainV2.comPort.MAV.param == null || MainV2.comPort.MAV.param.Count == 0)
                    {
                        AppendMessage("[Warning: Parameters not loaded. Please wait and try flash again.]", Color.Orange);
                        CustomMessageBox.Show(
                            "Parameters have not loaded yet.\n\n" +
                            "Please wait a few more seconds for the flight controller to fully initialize, then try flashing again.",
                            "Parameters Not Ready",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Warning
                        );
                        return false;
                    }

                    AppendMessage("✓ Parameters loaded successfully", Color.Green);
                    AppendMessage("[Scripting is now enabled! Continuing with upload...]", Color.Green);
                }
                else
                {
                    AppendMessage("✓ SCR_ENABLE = 1 (scripting already enabled)", Color.Green);
                }

                return true;
            }
            catch (Exception ex)
            {
                AppendMessage($"[Error checking SCR_ENABLE: {ex.Message}]", Color.Red);
                AppendMessage("[Cannot verify scripting status. Please check parameters manually.]", Color.Orange);

                // Ask user if they want to continue anyway
                var continueResult = CustomMessageBox.Show(
                    $"Could not verify SCR_ENABLE status:\n{ex.Message}\n\n" +
                    "Do you want to continue with the upload anyway?\n\n" +
                    "(Only do this if you know scripting is already enabled)",
                    "Parameter Check Failed",
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Warning
                );

                return continueResult == (int)DialogResult.Yes;
            }
        }

        private async void flashScriptButton_Click(object sender, EventArgs e)
        {
            try
            {
                // Validate script path exists
                if (string.IsNullOrEmpty(lastSavedScriptPath))
                {
                    AppendMessage("[Error: No script has been generated yet]", Color.Red);
                    return;
                }

                // Check if file actually exists on disk
                if (!System.IO.File.Exists(lastSavedScriptPath))
                {
                    AppendMessage($"[Error: Script file not found at: {lastSavedScriptPath}]", Color.Red);
                    AppendMessage("[The file may have been moved or deleted. Generate a new script to continue.]", Color.Red);
                    lastSavedScriptPath = null;
                    flashScriptButton.Enabled = false;
                    return;
                }

                // Check if MAVLink is connected
                if (MainV2.comPort == null || !MainV2.comPort.BaseStream.IsOpen)
                {
                    AppendMessage("[Error: Flight controller not connected. Please connect to a vehicle first.]", Color.Red);
                    CustomMessageBox.Show(
                        "Cannot upload script - no vehicle connected.\n\n" +
                        "Please connect to a flight controller first.",
                        Strings.ERROR
                    );
                    return;
                }

                // === AUTO-ENABLE SCRIPTING IF DISABLED ===
                bool scriptingEnabled = await CheckAndEnableScripting();
                if (!scriptingEnabled)
                {
                    return; // User cancelled or error occurred
                }

                // Get file info for display
                var fileInfo = new System.IO.FileInfo(lastSavedScriptPath);
                string fileName = System.IO.Path.GetFileName(lastSavedScriptPath);

                // === PARAMETER VERIFICATION ===
                AppendMessage("[Checking scripting parameters...]", Color.Blue);

                double scrEnable = 0;
                double scrHeapSize = 0;
                bool paramsOk = true;
                string paramWarnings = "";

                try
                {
                    // Verify comPort and params are valid before accessing
                    if (MainV2.comPort == null || MainV2.comPort.MAV == null || MainV2.comPort.MAV.param == null)
                    {
                        throw new Exception("MAVLink connection or parameters not available");
                    }

                    // Check SCR_ENABLE
                    if (!MainV2.comPort.MAV.param.ContainsKey("SCR_ENABLE"))
                    {
                        throw new Exception("SCR_ENABLE parameter not found");
                    }

                    scrEnable = MainV2.comPort.MAV.param["SCR_ENABLE"].Value;
                    if (scrEnable != 1)
                    {
                        paramsOk = false;
                        paramWarnings += $"⚠ SCR_ENABLE is {scrEnable} (should be 1)\n";
                        AppendMessage($"[WARNING: SCR_ENABLE = {scrEnable}, scripting is DISABLED]", Color.Orange);
                    }
                    else
                    {
                        AppendMessage("✓ SCR_ENABLE = 1 (scripting enabled)", Color.Green);
                    }

                    // Check SCR_HEAP_SIZE
                    if (MainV2.comPort.MAV.param.ContainsKey("SCR_HEAP_SIZE"))
                    {
                        scrHeapSize = MainV2.comPort.MAV.param["SCR_HEAP_SIZE"].Value;
                        AppendMessage($"✓ SCR_HEAP_SIZE = {scrHeapSize} bytes", Color.Gray);

                        if (scrHeapSize < 65536)
                        {
                            paramWarnings += $"⚠ SCR_HEAP_SIZE is {scrHeapSize} bytes (recommended >= 65536)\n";
                            AppendMessage($"[NOTE: SCR_HEAP_SIZE = {scrHeapSize}, may be too small for complex scripts]", Color.Gray);
                        }
                    }
                }
                catch (Exception paramEx)
                {
                    AppendMessage($"[WARNING: Could not verify parameters: {paramEx.Message}]", Color.Orange);
                    paramWarnings += "⚠ Could not verify scripting parameters\n";
                }

                // === LUA SYNTAX VALIDATION ===
                AppendMessage("[Validating Lua script syntax...]", Color.Blue);
                string syntaxWarnings = "";

                try
                {
                    string scriptContent = System.IO.File.ReadAllText(lastSavedScriptPath);

                    // Check for Python-style string formatting (common AI mistake)
                    if (scriptContent.Contains("\"") && scriptContent.Contains("%") && scriptContent.Contains(") %"))
                    {
                        syntaxWarnings += "⚠ SYNTAX ERROR: Python-style % formatting detected!\n";
                        syntaxWarnings += "  Found: '... \" % variable'\n";
                        syntaxWarnings += "  Should be: string.format(\"...\", variable)\n\n";
                        AppendMessage("[ERROR: Script contains Python-style % string formatting]", Color.Red);
                        AppendMessage("[Lua uses string.format(), not % operator]", Color.Red);
                        paramsOk = false;
                    }

                    // Check for required script structure
                    if (!scriptContent.Contains("function update()"))
                    {
                        syntaxWarnings += "⚠ Script may be missing update() function\n";
                        AppendMessage("[WARNING: Script may not have proper update() function]", Color.Orange);
                    }

                    if (!scriptContent.Contains("return update"))
                    {
                        syntaxWarnings += "⚠ Script may not return update() function\n";
                        AppendMessage("[WARNING: Script may not return update() function]", Color.Orange);
                    }

                    if (string.IsNullOrEmpty(syntaxWarnings))
                    {
                        AppendMessage("✓ Basic Lua syntax checks passed", Color.Green);
                    }
                }
                catch (Exception syntaxEx)
                {
                    AppendMessage($"[WARNING: Could not validate syntax: {syntaxEx.Message}]", Color.Orange);
                }

                // Show errors if syntax is bad
                if (!string.IsNullOrEmpty(syntaxWarnings))
                {
                    var fixResult = CustomMessageBox.Show(
                        "Lua Syntax Errors Detected!\n\n" + syntaxWarnings +
                        "\nThis script will likely FAIL to load on the flight controller.\n\n" +
                        "Do you want to:\n" +
                        "• Cancel and regenerate the script (Recommended)\n" +
                        "• Upload anyway (Advanced users only)",
                        "Script Syntax Error",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Warning
                    );

                    if (fixResult != (int)DialogResult.Yes)
                    {
                        AppendMessage("[Upload cancelled - please regenerate the script]", Color.Orange);
                        AppendMessage("[Tip: Ask AI to regenerate using correct Lua syntax]", Color.Gray);
                        return;
                    }
                }

                // Step 1: Ask if user wants to flash the script
                string confirmMessage = $"Flash Lua script to flight controller?\n\n" +
                    $"File: {fileName}\n" +
                    $"Size: {fileInfo.Length} bytes\n" +
                    $"Description: {lastScriptDescription}\n\n" +
                    $"Target: /APM/scripts/{fileName}\n\n";

                if (!string.IsNullOrEmpty(paramWarnings))
                {
                    confirmMessage += "⚠ PARAMETER WARNINGS:\n" + paramWarnings + "\n";
                }

                confirmMessage += $"Requirements:\n" +
                    $"• SD card inserted and formatted\n" +
                    $"• SCR_ENABLE = 1 (currently {scrEnable})\n" +
                    $"• Enough free space for the script\n\n" +
                    $"Do you want to proceed with flashing?";

                var result = CustomMessageBox.Show(
                    confirmMessage,
                    "Flash Script to FC",
                    CustomMessageBox.MessageBoxButtons.YesNo,
                    paramsOk ? CustomMessageBox.MessageBoxIcon.Question : CustomMessageBox.MessageBoxIcon.Warning
                );

                if (result != CustomMessageBox.DialogResult.Yes)
                {
                    AppendMessage("[Flash cancelled by user]", Color.Gray);
                    return;
                }

                // Step 2: Ask if user wants to clear old scripts first
                string clearMessage = "How would you like to handle existing scripts?\n\n" +
                    "CLEAR & FLASH (Recommended):\n" +
                    "• Delete ALL existing .lua scripts from /APM/scripts/\n" +
                    "• Upload this new script\n" +
                    "• Only this script will run after reboot\n" +
                    "• Clean state, no conflicts\n\n" +
                    "FLASH ONLY (Advanced):\n" +
                    "• Keep all existing scripts\n" +
                    "• Add this new script\n" +
                    "• ALL scripts will run simultaneously after reboot\n" +
                    "• Use only if you want multiple scripts running together\n\n" +
                    "Click YES to Clear & Flash (recommended)\n" +
                    "Click NO to Flash Only (keep existing scripts)";

                var clearResult = CustomMessageBox.Show(
                    clearMessage,
                    "Script Management",
                    CustomMessageBox.MessageBoxButtons.YesNo,
                    CustomMessageBox.MessageBoxIcon.Question,
                    "Clear & Flash",
                    "Flash Only"
                );

                bool clearOldScripts = (clearResult == CustomMessageBox.DialogResult.Yes);

                if (clearOldScripts)
                {
                    AppendMessage("[User selected: Clear all scripts and flash new one]", Color.Blue);
                }
                else
                {
                    AppendMessage("[User selected: Flash without clearing existing scripts]", Color.Blue);
                    AppendMessage("[NOTE: Multiple scripts will run simultaneously after reboot]", Color.Orange);
                }

                AppendMessage($"[Preparing to flash {fileName} ({fileInfo.Length} bytes)...]", Color.Blue);
                AppendMessage($"[Local path: {lastSavedScriptPath}]", Color.Gray);
                AppendMessage("[Creating /APM/scripts/ directory on SD card if needed...]", Color.Gray);

                if (clearOldScripts)
                {
                    AppendMessage("[Will delete all old scripts before upload]", Color.Orange);
                }
                else
                {
                    AppendMessage("[Will keep existing scripts]", Color.Gray);
                }

                AppendMessage("[Uploading script...]", Color.Blue);

                string targetDir = "/APM/scripts";
                string targetPath = targetDir + "/" + fileName;

                // Capture flag for use in Task
                bool shouldClearOldScripts = clearOldScripts;

                // Log to debug console
                DebugLog("=== STARTING UPLOAD ===");
                DebugLog($"Local file: {lastSavedScriptPath}");
                DebugLog($"Target path: {targetPath}");
                DebugLog($"Clear old scripts: {shouldClearOldScripts}");

                string uploadResult = await Task.Run(() =>
                {
                    try
                    {
                        // Verify file exists one more time before reading
                        DebugLog("Checking local file exists...");
                        if (!System.IO.File.Exists(lastSavedScriptPath))
                        {
                            DebugLog("ERROR: Local file not found!");
                            throw new Exception($"File disappeared: {lastSavedScriptPath}");
                        }
                        DebugLog("Local file exists OK");

                        // Read file bytes
                        DebugLog("Reading file bytes...");
                        var fileBytes = System.IO.File.ReadAllBytes(lastSavedScriptPath);
                        DebugLog($"Read {fileBytes.Length} bytes");

                        if (fileBytes == null || fileBytes.Length == 0)
                        {
                            DebugLog("ERROR: File is empty!");
                            throw new Exception("File is empty or could not be read");
                        }

                        // Create MAVFTP instance
                        DebugLog("Creating MAVFTP instance...");
                        var ftp = new MAVFtp(MainV2.comPort, MainV2.comPort.MAV.sysid, MainV2.comPort.MAV.compid);
                        DebugLog($"MAVFTP: sysid={MainV2.comPort.MAV.sysid}, compid={MainV2.comPort.MAV.compid}");

                        // Create a CancellationTokenSource for all FTP operations (like MavFTPUI does)
                        var ftpCancel = new System.Threading.CancellationTokenSource();

                        // Try to list root directory first to verify MAVFTP is working
                        string debugInfo = "";
                        try
                        {
                            DebugLog("Listing root directory...");
                            var rootList = ftp.kCmdListDirectory("/", ftpCancel);
                            DebugLog($"Root dir: Found {rootList.Count} items");
                            debugInfo += $"✓ MAVFTP working - Found {rootList.Count} items in root\n";

                            // Check if APM directory exists
                            bool apmExists = rootList.Any(f => f.Name == "APM");
                            DebugLog($"/APM exists: {apmExists}");
                            if (apmExists)
                            {
                                debugInfo += "✓ /APM directory exists\n";

                                // Check if scripts directory exists
                                DebugLog("Listing /APM directory...");
                                var apmList = ftp.kCmdListDirectory("/APM", ftpCancel);
                                bool scriptsExists = apmList.Any(f => f.Name == "scripts");
                                DebugLog($"/APM/scripts exists: {scriptsExists}");
                                if (scriptsExists)
                                {
                                    debugInfo += "✓ /APM/scripts directory already exists\n";
                                }
                                else
                                {
                                    debugInfo += "⚠ /APM/scripts directory does NOT exist - will create it\n";
                                }
                            }
                            else
                            {
                                debugInfo += "⚠ /APM directory does NOT exist (common in SITL) - will create it\n";
                            }
                        }
                        catch (Exception listEx)
                        {
                            DebugLog($"ERROR listing directories: {listEx.Message}");
                            debugInfo += $"✗ MAVFTP directory listing failed: {listEx.Message}\n";
                            return "ERROR: Cannot list directories via MAVFTP. This means:\n" +
                                   "• SD card might not be inserted or not formatted\n" +
                                   "• MAVFTP not supported by your firmware\n" +
                                   "• Flight controller communication issue\n\n" + debugInfo;
                        }

                        // Create /APM directory if it doesn't exist (needed for SITL)
                        try
                        {
                            bool apmCreated = ftp.kCmdCreateDirectory("/APM", ftpCancel);
                            if (apmCreated)
                            {
                                debugInfo += "✓ Created /APM directory\n";
                            }
                        }
                        catch (Exception dirEx)
                        {
                            // Directory might already exist, that's OK
                            if (dirEx.Message.Contains("EEXIST"))
                            {
                                debugInfo += "✓ /APM directory confirmed\n";
                            }
                            else
                            {
                                throw new Exception($"Failed to create /APM directory: {dirEx.Message}");
                            }
                        }

                        // Now create /APM/scripts directory
                        DebugLog("Creating /APM/scripts directory...");
                        try
                        {
                            bool scriptsCreated = ftp.kCmdCreateDirectory(targetDir, ftpCancel);
                            DebugLog($"/APM/scripts created: {scriptsCreated}");
                            if (scriptsCreated)
                            {
                                debugInfo += $"✓ Created {targetDir} directory\n";
                            }
                        }
                        catch (Exception dirEx)
                        {
                            DebugLog($"/APM/scripts create exception: {dirEx.Message}");
                            // Directory might already exist, that's OK
                            if (dirEx.Message.Contains("EEXIST"))
                            {
                                debugInfo += $"✓ {targetDir} directory confirmed\n";
                            }
                            else
                            {
                                throw new Exception($"Failed to create directory {targetDir}: {dirEx.Message}");
                            }
                        }

                        // Delete all old Lua scripts from /APM/scripts/ (if user requested)
                        if (shouldClearOldScripts)
                        {
                            DebugLog("=== DELETING OLD SCRIPTS ===");
                            try
                            {
                                debugInfo += "Checking for old scripts to delete...\n";
                                DebugLog("Listing /APM/scripts for deletion...");
                                var scriptsList = ftp.kCmdListDirectory(targetDir, ftpCancel);

                                if (scriptsList != null && scriptsList.Count > 0)
                                {
                                    DebugLog($"Found {scriptsList.Count} items in scripts dir");
                                    int deletedCount = 0;
                                    foreach (var file in scriptsList)
                                    {
                                        DebugLog($"  Item: {file.Name} (size: {file.Size})");
                                        if (file.Name.EndsWith(".lua", StringComparison.OrdinalIgnoreCase))
                                        {
                                            try
                                            {
                                                string oldScriptPath = targetDir + "/" + file.Name;
                                                DebugLog($"  Deleting: {oldScriptPath}");
                                                ftp.kCmdRemoveFile(oldScriptPath, ftpCancel);
                                                DebugLog($"  Deleted: {file.Name}");
                                                debugInfo += $"✓ Deleted old script: {file.Name}\n";
                                                deletedCount++;
                                            }
                                            catch (Exception delEx)
                                            {
                                                DebugLog($"  ERROR deleting {file.Name}: {delEx.Message}");
                                                debugInfo += $"⚠ Could not delete {file.Name}: {delEx.Message}\n";
                                            }
                                        }
                                    }

                                    DebugLog($"Deleted {deletedCount} old scripts");
                                    if (deletedCount > 0)
                                    {
                                        debugInfo += $"✓ Deleted {deletedCount} old script(s)\n";
                                    }
                                    else
                                    {
                                        debugInfo += "✓ No old scripts found\n";
                                    }
                                }
                                else
                                {
                                    DebugLog("Scripts directory is empty");
                                    debugInfo += "✓ Scripts directory is empty\n";
                                }
                            }
                            catch (Exception cleanEx)
                            {
                                DebugLog($"ERROR cleaning scripts: {cleanEx.Message}");
                                // Non-fatal - continue with upload even if cleanup fails
                                debugInfo += $"⚠ Could not clean old scripts: {cleanEx.Message}\n";
                            }
                        }
                        else
                        {
                            DebugLog("Keeping existing scripts (user choice)");
                            debugInfo += "Keeping existing scripts (user choice)\n";
                        }

                        // Upload new file via MAVFTP
                        DebugLog("=== UPLOADING NEW FILE ===");
                        DebugLog($"Target path: {targetPath}");
                        DebugLog($"File size: {fileBytes.Length} bytes");
                        DebugLog($"Local file: {lastSavedScriptPath}");
                        debugInfo += $"Target path: {targetPath}\n";
                        debugInfo += $"File size: {fileBytes.Length} bytes\n";

                        try
                        {
                            // Add progress handler for diagnostics
                            ftp.Progress += (msg, pct) => {
                                DebugLog($"FTP Progress: {msg} - {pct}%");
                            };

                            DebugLog("Calling ftp.UploadFile() with file path...");
                            debugInfo += "Starting MAVFTP upload...\n";

                            // Use file-path based UploadFile (like MavFTPUI does) instead of Stream-based
                            // This is more reliable as it handles the file reading internally
                            ftp.UploadFile(targetPath, lastSavedScriptPath, ftpCancel);

                            DebugLog("UploadFile() returned without exception");
                            debugInfo += "Upload command completed\n";

                            // Verify with CRC32 (like MavFTPUI does)
                            DebugLog("=== VERIFYING WITH CRC32 ===");
                            debugInfo += "Verifying upload with CRC32...\n";
                            uint remoteCrc = 0;
                            ftp.kCmdCalcFileCRC32(targetPath, ref remoteCrc, ftpCancel);
                            var localCrc = MAVFtp.crc_crc32(0, fileBytes);
                            DebugLog($"Local CRC32: {localCrc:X8}");
                            DebugLog($"Remote CRC32: {remoteCrc:X8}");
                            debugInfo += $"Local CRC32: {localCrc:X8}\n";
                            debugInfo += $"Remote CRC32: {remoteCrc:X8}\n";

                            if (localCrc != remoteCrc)
                            {
                                DebugLog("CRC32 MISMATCH! Upload failed.");
                                throw new Exception($"CRC32 mismatch! Local: {localCrc:X8}, Remote: {remoteCrc:X8}. Upload may have failed.");
                            }

                            DebugLog("CRC32 match - upload verified!");
                            debugInfo += $"✓ CRC32 verified - upload successful!\n";

                            // Also verify by listing directory
                            DebugLog("=== VERIFYING BY DIRECTORY LISTING ===");
                            DebugLog($"Listing {targetDir}...");
                            debugInfo += $"Verifying in {targetDir}...\n";
                            var verifyList = ftp.kCmdListDirectory(targetDir, ftpCancel);
                            bool uploadVerified = false;

                            if (verifyList != null)
                            {
                                DebugLog($"Found {verifyList.Count} files:");
                                debugInfo += $"Found {verifyList.Count} files in {targetDir}:\n";
                                foreach (var f in verifyList)
                                {
                                    DebugLog($"  [{f.Name}] size={f.Size}");
                                    debugInfo += $"  - {f.Name} ({f.Size} bytes)\n";
                                }

                                DebugLog($"Looking for: {fileName}");
                                var uploadedFile = verifyList.FirstOrDefault(f => f.Name == fileName);
                                if (uploadedFile != null)
                                {
                                    uploadVerified = true;
                                    DebugLog($"SUCCESS! Found {fileName} ({uploadedFile.Size} bytes)");
                                    debugInfo += $"✓ Upload verified: {fileName} ({uploadedFile.Size} bytes)\n";
                                }
                                else
                                {
                                    DebugLog($"WARNING: {fileName} NOT FOUND in directory listing (but CRC passed)");
                                    debugInfo += $"⚠ File {fileName} not in listing (CRC passed anyway)\n";
                                    // Don't fail if CRC passed - directory listing can be cached
                                    uploadVerified = true;
                                }
                            }
                            else
                            {
                                debugInfo += "⚠ Directory listing returned null (CRC passed anyway)\n";
                                uploadVerified = true; // Trust CRC if it passed
                            }
                        }
                        catch (Exception uploadEx)
                        {
                            debugInfo += $"Exception: {uploadEx.GetType().Name}: {uploadEx.Message}\n";
                            if (uploadEx.InnerException != null)
                            {
                                debugInfo += $"Inner: {uploadEx.InnerException.Message}\n";
                            }
                            throw new Exception($"{uploadEx.Message}\n\nDebug info:\n{debugInfo}");
                        }

                        return "SUCCESS\n" + debugInfo;
                    }
                    catch (Exception uploadEx)
                    {
                        return $"ERROR: {uploadEx.Message}";
                    }
                });

                // Check result
                if (uploadResult.StartsWith("SUCCESS"))
                {
                    AppendMessage($"✓ Script uploaded successfully to {targetPath}", Color.Green);
                    AppendMessage("[Debug info:\n" + uploadResult.Replace("SUCCESS\n", "") + "]", Color.Gray);

                    if (shouldClearOldScripts)
                    {
                        AppendMessage("[⚠ IMPORTANT: Old scripts deleted from SD card but still running in memory!]", Color.Orange);
                        AppendMessage("[⚠ You MUST reboot to stop old scripts and load only the new script]", Color.Orange);
                    }
                    else
                    {
                        AppendMessage("[The flight controller needs to be rebooted to load the script]", Color.FromArgb(100, 149, 237));
                    }

                    // Show success message and offer to reboot
                    string rebootMessage;
                    if (shouldClearOldScripts)
                    {
                        rebootMessage = $"✓ Lua script uploaded successfully!\n\n" +
                            $"File: {fileName}\n" +
                            $"Target: {targetPath}\n\n" +
                            $"⚠ IMPORTANT - REBOOT REQUIRED:\n" +
                            $"Old scripts were deleted from SD card but are STILL RUNNING in memory.\n" +
                            $"You MUST reboot now to:\n" +
                            $"  • Stop all old scripts from running\n" +
                            $"  • Load only the new script from SD card\n\n" +
                            $"Without reboot, old scripts will continue running alongside the new one!\n\n" +
                            $"Reboot the flight controller now?";
                    }
                    else
                    {
                        rebootMessage = $"✓ Lua script uploaded successfully!\n\n" +
                            $"File: {fileName}\n" +
                            $"Target: {targetPath}\n\n" +
                            $"The flight controller needs to reboot to load the script.\n" +
                            $"After reboot, watch the Messages tab for:\n" +
                            $"  \"Scripting: loaded X scripts\"\n\n" +
                            $"Reboot the flight controller now?";
                    }

                    var rebootResult = CustomMessageBox.Show(
                        rebootMessage,
                        shouldClearOldScripts ? "⚠ REBOOT REQUIRED" : "Script Upload Successful",
                        CustomMessageBox.MessageBoxButtons.YesNo,
                        shouldClearOldScripts ? CustomMessageBox.MessageBoxIcon.Warning : CustomMessageBox.MessageBoxIcon.Information
                    );

                    if (rebootResult == CustomMessageBox.DialogResult.Yes)
                    {
                        AppendMessage("[Preparing to reboot...]", Color.Blue);

                        // Small delay to ensure any pending operations complete
                        await Task.Delay(500);

                        AppendMessage("[Rebooting flight controller...]", Color.Blue);

                        // Send reboot command (false = normal reboot, true = current vehicle only)
                        if (MainV2.comPort.doReboot(false, true))
                        {
                            AppendMessage("✓ Reboot command sent successfully", Color.Green);
                            AppendMessage("[Flight controller is rebooting...]", Color.Gray);
                            AppendMessage("[Waiting for reconnection to verify script loading...]", Color.Blue);
                            DebugLog("Waiting for FC to reconnect after final reboot...");

                            // Wait for reconnection after reboot (to verify script loading)
                            bool reconnected = false;
                            for (int i = 0; i < 20; i++)
                            {
                                await Task.Delay(1000);
                                AppendMessage($"[Reconnecting... ({i + 1}/20)]", Color.Gray);
                                DebugLog($"Reconnection attempt {i + 1}/20");

                                if (MainV2.comPort.BaseStream != null && MainV2.comPort.BaseStream.IsOpen)
                                {
                                    reconnected = true;
                                    break;
                                }
                            }

                            if (reconnected)
                            {
                                AppendMessage("✓ Flight controller reconnected", Color.Green);
                                DebugLog("FC reconnected - checking scripting parameters");

                                // Wait for parameters to load
                                await Task.Delay(2000);

                                // Verify scripting parameters after reboot
                                try
                                {
                                    float verifyScrEnable = (float)MainV2.comPort.MAV.param["SCR_ENABLE"];
                                    float verifyScrHeap = MainV2.comPort.MAV.param.ContainsKey("SCR_HEAP_SIZE")
                                        ? (float)MainV2.comPort.MAV.param["SCR_HEAP_SIZE"]
                                        : 0;

                                    DebugLog($"SCR_ENABLE = {verifyScrEnable}");
                                    DebugLog($"SCR_HEAP_SIZE = {verifyScrHeap}");

                                    AppendMessage($"[Scripting parameters: SCR_ENABLE={verifyScrEnable}, SCR_HEAP_SIZE={verifyScrHeap}]", Color.Gray);

                                    if (verifyScrEnable != 1)
                                    {
                                        AppendMessage("⚠ WARNING: SCR_ENABLE is NOT 1! Scripting is disabled.", Color.Red);
                                        AppendMessage("[Scripts will NOT load. Please enable SCR_ENABLE manually.]", Color.Red);
                                        DebugLog("ERROR: SCR_ENABLE != 1 after reboot!");
                                    }
                                    else if (verifyScrHeap < 65536)
                                    {
                                        AppendMessage($"⚠ WARNING: SCR_HEAP_SIZE={verifyScrHeap} is too small!", Color.Orange);
                                        AppendMessage("[Recommended: SCR_HEAP_SIZE >= 65536. Scripts may fail to load.]", Color.Orange);
                                        DebugLog($"WARNING: SCR_HEAP_SIZE too small: {verifyScrHeap}");
                                    }
                                    else
                                    {
                                        AppendMessage("✓ Scripting is enabled and configured correctly", Color.Green);
                                        AppendMessage("[Watch the Messages tab for 'Scripting: loaded X scripts']", Color.FromArgb(100, 149, 237));
                                        DebugLog("Scripting parameters OK");
                                    }
                                }
                                catch (Exception verifyEx)
                                {
                                    AppendMessage($"[Could not verify parameters: {verifyEx.Message}]", Color.Orange);
                                    DebugLog($"Parameter check error: {verifyEx.Message}");
                                }

                                AppendMessage("[Check Messages tab for script loading status]", Color.FromArgb(100, 149, 237));
                            }
                            else
                            {
                                AppendMessage("⚠ Flight controller did not reconnect in time", Color.Orange);
                                AppendMessage("[Please reconnect manually and check Messages tab for script status]", Color.Orange);
                                DebugLog("FC did not reconnect in 20 seconds");
                            }
                        }
                        else
                        {
                            AppendMessage("✗ Failed to send reboot command", Color.Red);
                            AppendMessage("[Please reboot manually via CONFIG > Full Parameter Tree > Reboot]", Color.FromArgb(255, 165, 0));
                            DebugLog("Failed to send reboot command");
                        }
                    }
                    else
                    {
                        AppendMessage("[Remember to reboot the flight controller to load the script]", Color.FromArgb(255, 165, 0));
                        AppendMessage("[After reboot, watch Messages tab for 'Scripting: loaded X scripts']", Color.Gray);
                    }
                }
                else
                {
                    throw new Exception(uploadResult);
                }
            }
            catch (Exception ex)
            {
                AppendMessage($"[✗ Upload failed: {ex.Message}]", Color.Red);

                string errorDetails = ex.Message;
                if (ex.InnerException != null)
                {
                    errorDetails += $"\n\nDetails: {ex.InnerException.Message}";
                }

                CustomMessageBox.Show(
                    $"Failed to upload script:\n\n{errorDetails}\n\n" +
                    $"Troubleshooting:\n" +
                    $"• Ensure flight controller is connected\n" +
                    $"• Check SD card is inserted and working\n" +
                    $"• Verify SCR_ENABLE parameter is set to 1\n" +
                    $"• Try rebooting the flight controller\n" +
                    $"• Check that MAVFTP is supported by your firmware",
                    Strings.ERROR
                );
            }
        }

    }
}

