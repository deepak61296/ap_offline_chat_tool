namespace MissionPlanner.GCSViews
{
    partial class ChatAssistant
    {
        /// <summary> 
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary> 
        /// Required method for Designer support - do not modify 
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.chatHistoryBox = new System.Windows.Forms.RichTextBox();
            this.inputTextBox = new System.Windows.Forms.TextBox();
            this.sendButton = new MissionPlanner.Controls.MyButton();
            this.bottomToolbar = new System.Windows.Forms.Panel();
            this.connectionButton = new System.Windows.Forms.Button();
            this.modeLabel = new System.Windows.Forms.Label();
            this.modeComboBox = new System.Windows.Forms.ComboBox();
            this.modelLabel = new System.Windows.Forms.Label();
            this.modelComboBox = new System.Windows.Forms.ComboBox();
            this.debugToggleButton = new System.Windows.Forms.Button();
            this.debugSplitter = new System.Windows.Forms.Splitter();
            this.cancelButton = new System.Windows.Forms.Button();
            this.flashScriptButton = new System.Windows.Forms.Button();
            this.bottomToolbar.SuspendLayout();
            this.SuspendLayout();
            //
            // chatHistoryBox - anchored to Top, Left, Right only (not Bottom) to allow dynamic height
            //
            this.chatHistoryBox.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left)
            | System.Windows.Forms.AnchorStyles.Right)));
            this.chatHistoryBox.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(30)))), ((int)(((byte)(30)))), ((int)(((byte)(30)))));
            this.chatHistoryBox.BorderStyle = System.Windows.Forms.BorderStyle.None;
            this.chatHistoryBox.Font = new System.Drawing.Font("Segoe UI", 11F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.chatHistoryBox.ForeColor = System.Drawing.Color.White;
            this.chatHistoryBox.Location = new System.Drawing.Point(0, 0);
            this.chatHistoryBox.Name = "chatHistoryBox";
            this.chatHistoryBox.ReadOnly = true;
            this.chatHistoryBox.Size = new System.Drawing.Size(800, 490);
            this.chatHistoryBox.TabIndex = 0;
            this.chatHistoryBox.Text = "";
            // 
            // bottomToolbar
            // 
            this.bottomToolbar.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.bottomToolbar.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(40)))), ((int)(((byte)(40)))), ((int)(((byte)(40)))));
            this.bottomToolbar.Controls.Add(this.connectionButton);
            this.bottomToolbar.Controls.Add(this.modeLabel);
            this.bottomToolbar.Controls.Add(this.modeComboBox);
            this.bottomToolbar.Controls.Add(this.modelLabel);
            this.bottomToolbar.Controls.Add(this.modelComboBox);
            this.bottomToolbar.Controls.Add(this.inputTextBox);
            this.bottomToolbar.Controls.Add(this.sendButton);
            this.bottomToolbar.Controls.Add(this.cancelButton);
            this.bottomToolbar.Controls.Add(this.flashScriptButton);
            this.bottomToolbar.Location = new System.Drawing.Point(0, 490);
            this.bottomToolbar.Name = "bottomToolbar";
            this.bottomToolbar.Size = new System.Drawing.Size(800, 110);
            this.bottomToolbar.TabIndex = 1;
            // 
            // connectionButton
            // 
            this.connectionButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.connectionButton.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(60)))), ((int)(((byte)(60)))));
            this.connectionButton.FlatAppearance.BorderSize = 0;
            this.connectionButton.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.connectionButton.Font = new System.Drawing.Font("Segoe UI", 14F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.connectionButton.ForeColor = System.Drawing.Color.Red;
            this.connectionButton.Location = new System.Drawing.Point(750, 75);
            this.connectionButton.Name = "connectionButton";
            this.connectionButton.Size = new System.Drawing.Size(40, 30);
            this.connectionButton.TabIndex = 6;
            this.connectionButton.Text = "🔌";
            this.connectionButton.UseVisualStyleBackColor = false;
            this.connectionButton.Click += new System.EventHandler(this.connectionButton_Click);
            this.connectionButton.MouseUp += new System.Windows.Forms.MouseEventHandler(this.connectionButton_MouseUp);
            // 
            // modeLabel
            // 
            this.modeLabel.AutoSize = true;
            this.modeLabel.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.modeLabel.ForeColor = System.Drawing.Color.LightGray;
            this.modeLabel.Location = new System.Drawing.Point(10, 82);
            this.modeLabel.Name = "modeLabel";
            this.modeLabel.Size = new System.Drawing.Size(40, 15);
            this.modeLabel.TabIndex = 2;
            this.modeLabel.Text = "Mode:";
            // 
            // modeComboBox
            // 
            this.modeComboBox.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(50)))), ((int)(((byte)(50)))), ((int)(((byte)(50)))));
            this.modeComboBox.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.modeComboBox.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.modeComboBox.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.modeComboBox.ForeColor = System.Drawing.Color.White;
            this.modeComboBox.FormattingEnabled = true;
            this.modeComboBox.Items.AddRange(new object[] {"Agent", "Ask", "Script"});
            this.modeComboBox.Location = new System.Drawing.Point(55, 79);
            this.modeComboBox.Name = "modeComboBox";
            this.modeComboBox.Size = new System.Drawing.Size(100, 23);
            this.modeComboBox.TabIndex = 3;
            // 
            // modelLabel
            // 
            this.modelLabel.AutoSize = true;
            this.modelLabel.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.modelLabel.ForeColor = System.Drawing.Color.LightGray;
            this.modelLabel.Location = new System.Drawing.Point(175, 82);
            this.modelLabel.Name = "modelLabel";
            this.modelLabel.Size = new System.Drawing.Size(44, 15);
            this.modelLabel.TabIndex = 4;
            this.modelLabel.Text = "Model:";
            // 
            // modelComboBox
            // 
            this.modelComboBox.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(50)))), ((int)(((byte)(50)))), ((int)(((byte)(50)))));
            this.modelComboBox.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.modelComboBox.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.modelComboBox.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.modelComboBox.ForeColor = System.Drawing.Color.White;
            this.modelComboBox.FormattingEnabled = true;
            this.modelComboBox.Location = new System.Drawing.Point(225, 79);
            this.modelComboBox.Name = "modelComboBox";
            this.modelComboBox.Size = new System.Drawing.Size(150, 23);
            this.modelComboBox.TabIndex = 5;
            //
            // debugToggleButton - floating button between debug console and toolbar (RIGHT side)
            //
            this.debugToggleButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.debugToggleButton.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(60)))), ((int)(((byte)(60)))));
            this.debugToggleButton.FlatAppearance.BorderColor = System.Drawing.Color.Cyan;
            this.debugToggleButton.FlatAppearance.BorderSize = 2;
            this.debugToggleButton.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.debugToggleButton.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.debugToggleButton.ForeColor = System.Drawing.Color.Cyan;
            this.debugToggleButton.Location = new System.Drawing.Point(640, 455);
            this.debugToggleButton.Name = "debugToggleButton";
            this.debugToggleButton.Size = new System.Drawing.Size(150, 30);
            this.debugToggleButton.TabIndex = 9;
            this.debugToggleButton.Text = "▼ Debug Console";
            this.debugToggleButton.UseVisualStyleBackColor = false;
            this.debugToggleButton.Cursor = System.Windows.Forms.Cursors.Hand;
            //
            // debugSplitter - horizontal splitter to resize debug console
            //
            this.debugSplitter.Dock = System.Windows.Forms.DockStyle.Bottom;
            this.debugSplitter.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(80)))), ((int)(((byte)(80)))), ((int)(((byte)(80)))));
            this.debugSplitter.Location = new System.Drawing.Point(0, 487);
            this.debugSplitter.Name = "debugSplitter";
            this.debugSplitter.Size = new System.Drawing.Size(800, 3);
            this.debugSplitter.TabIndex = 10;
            this.debugSplitter.TabStop = false;
            this.debugSplitter.Visible = false;
            //
            // inputTextBox - spans from left, leaves room for Flash and Send buttons
            //
            this.inputTextBox.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left)
            | System.Windows.Forms.AnchorStyles.Right)));
            this.inputTextBox.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(50)))), ((int)(((byte)(50)))), ((int)(((byte)(50)))));
            this.inputTextBox.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.inputTextBox.Font = new System.Drawing.Font("Segoe UI", 11F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.inputTextBox.ForeColor = System.Drawing.Color.White;
            this.inputTextBox.Location = new System.Drawing.Point(10, 10);
            this.inputTextBox.Multiline = true;
            this.inputTextBox.Name = "inputTextBox";
            this.inputTextBox.Size = new System.Drawing.Size(565, 60);
            this.inputTextBox.TabIndex = 0;
            this.inputTextBox.KeyDown += new System.Windows.Forms.KeyEventHandler(this.inputTextBox_KeyDown);
            //
            // sendButton - rightmost button
            //
            this.sendButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.sendButton.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(0)))), ((int)(((byte)(120)))), ((int)(((byte)(215)))));
            this.sendButton.FlatAppearance.BorderSize = 0;
            this.sendButton.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.sendButton.Font = new System.Drawing.Font("Segoe UI", 11F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.sendButton.ForeColor = System.Drawing.Color.White;
            this.sendButton.Location = new System.Drawing.Point(695, 10);
            this.sendButton.Name = "sendButton";
            this.sendButton.Size = new System.Drawing.Size(95, 60);
            this.sendButton.TabIndex = 1;
            this.sendButton.Text = "Send";
            this.sendButton.UseVisualStyleBackColor = false;
            this.sendButton.Click += new System.EventHandler(this.sendButton_Click);
            //
            // cancelButton - same position as Send, shown during processing
            //
            this.cancelButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.cancelButton.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(220)))), ((int)(((byte)(53)))), ((int)(((byte)(69)))));
            this.cancelButton.FlatAppearance.BorderSize = 0;
            this.cancelButton.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.cancelButton.Font = new System.Drawing.Font("Segoe UI", 11F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.cancelButton.ForeColor = System.Drawing.Color.White;
            this.cancelButton.Location = new System.Drawing.Point(695, 10);
            this.cancelButton.Name = "cancelButton";
            this.cancelButton.Size = new System.Drawing.Size(95, 60);
            this.cancelButton.TabIndex = 7;
            this.cancelButton.Text = "Cancel";
            this.cancelButton.UseVisualStyleBackColor = false;
            this.cancelButton.Visible = false;
            this.cancelButton.Click += new System.EventHandler(this.cancelButton_Click);
            //
            // flashScriptButton - between input and Send button
            //
            this.flashScriptButton.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.flashScriptButton.BackColor = System.Drawing.Color.FromArgb(100, 149, 237);
            this.flashScriptButton.FlatAppearance.BorderSize = 0;
            this.flashScriptButton.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.flashScriptButton.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.flashScriptButton.ForeColor = System.Drawing.Color.White;
            this.flashScriptButton.Location = new System.Drawing.Point(585, 10);
            this.flashScriptButton.Name = "flashScriptButton";
            this.flashScriptButton.Size = new System.Drawing.Size(100, 60);
            this.flashScriptButton.TabIndex = 8;
            this.flashScriptButton.Text = "⚡ Flash FC";
            this.flashScriptButton.UseVisualStyleBackColor = false;
            this.flashScriptButton.Visible = false;
            this.flashScriptButton.Click += new System.EventHandler(this.flashScriptButton_Click);
            // 
            // ChatAssistant
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(30)))), ((int)(((byte)(30)))), ((int)(((byte)(30)))));
            this.Controls.Add(this.debugToggleButton);
            this.Controls.Add(this.debugSplitter);
            this.Controls.Add(this.bottomToolbar);
            this.Controls.Add(this.chatHistoryBox);
            this.Name = "ChatAssistant";
            this.Size = new System.Drawing.Size(800, 600);
            this.Load += new System.EventHandler(this.ChatAssistant_Load);
            this.bottomToolbar.ResumeLayout(false);
            this.bottomToolbar.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.RichTextBox chatHistoryBox;
        private System.Windows.Forms.TextBox inputTextBox;
        private Controls.MyButton sendButton;
        private System.Windows.Forms.Panel bottomToolbar;
        private System.Windows.Forms.Label modeLabel;
        private System.Windows.Forms.ComboBox modeComboBox;
        private System.Windows.Forms.Label modelLabel;
        private System.Windows.Forms.ComboBox modelComboBox;
        private System.Windows.Forms.Button debugToggleButton;
        private System.Windows.Forms.Splitter debugSplitter;
        private System.Windows.Forms.Button connectionButton;
        private System.Windows.Forms.Button cancelButton;
        private System.Windows.Forms.Button flashScriptButton;
    }
}
