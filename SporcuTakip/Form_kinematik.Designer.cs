using System.Drawing;
using System.Windows.Forms;

namespace SporcuTakip
{
    partial class Form_kinematik
    {
        private System.ComponentModel.IContainer components = null;

        // ---- Alanlar (tek kopya!) ----
        private TableLayoutPanel layoutRoot;
        private GroupBox grpSource, grpOptions, grpRuntime;

        private RadioButton rbCamera, rbVideo, rbImage;
        private NumericUpDown numCameraIndex, numFps;
        private TextBox txtMediaPath, txtOutputPath, txtPythonPath, txtDbPath;
        private Button btnBrowseMedia, btnBrowseOutput, btnBrowsePython, btnBrowseDb;
        private CheckBox chkShow, chkSave;
        private Label lblFps, lblStatus;
        private ProgressBar progress;
        private RichTextBox txtLog;
        private Button btnStart, btnStop;
        private Panel filler; // sağ alt boş panel

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null)) components.Dispose();
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            this.layoutRoot = new System.Windows.Forms.TableLayoutPanel();
            this.grpSource = new System.Windows.Forms.GroupBox();
            this.rbCamera = new System.Windows.Forms.RadioButton();
            this.rbVideo = new System.Windows.Forms.RadioButton();
            this.rbImage = new System.Windows.Forms.RadioButton();
            this.numCameraIndex = new System.Windows.Forms.NumericUpDown();
            this.txtMediaPath = new System.Windows.Forms.TextBox();
            this.btnBrowseMedia = new System.Windows.Forms.Button();
            this.grpOptions = new System.Windows.Forms.GroupBox();
            this.chkShow = new System.Windows.Forms.CheckBox();
            this.chkSave = new System.Windows.Forms.CheckBox();
            this.txtOutputPath = new System.Windows.Forms.TextBox();
            this.btnBrowseOutput = new System.Windows.Forms.Button();
            this.lblFps = new System.Windows.Forms.Label();
            this.numFps = new System.Windows.Forms.NumericUpDown();
            this.txtLog = new System.Windows.Forms.RichTextBox();
            this.grpRuntime = new System.Windows.Forms.GroupBox();
            this.txtPythonPath = new System.Windows.Forms.TextBox();
            this.btnBrowsePython = new System.Windows.Forms.Button();
            this.txtDbPath = new System.Windows.Forms.TextBox();
            this.btnBrowseDb = new System.Windows.Forms.Button();
            this.btnStart = new System.Windows.Forms.Button();
            this.btnStop = new System.Windows.Forms.Button();
            this.progress = new System.Windows.Forms.ProgressBar();
            this.lblStatus = new System.Windows.Forms.Label();
            this.filler = new System.Windows.Forms.Panel();
            this.picPreview = new System.Windows.Forms.PictureBox();
            this.layoutRoot.SuspendLayout();
            this.grpSource.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.numCameraIndex)).BeginInit();
            this.grpOptions.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.numFps)).BeginInit();
            this.grpRuntime.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.picPreview)).BeginInit();
            this.SuspendLayout();
            // 
            // layoutRoot
            // 
            this.layoutRoot.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(245)))), ((int)(((byte)(247)))), ((int)(((byte)(250)))));
            this.layoutRoot.ColumnCount = 2;
            this.layoutRoot.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50F));
            this.layoutRoot.ColumnStyles.Add(new System.Windows.Forms.ColumnStyle(System.Windows.Forms.SizeType.Percent, 50F));
            this.layoutRoot.Controls.Add(this.grpSource, 0, 0);
            this.layoutRoot.Controls.Add(this.grpOptions, 1, 0);
            this.layoutRoot.Controls.Add(this.txtLog, 0, 1);
            this.layoutRoot.Controls.Add(this.picPreview, 1, 1);
            this.layoutRoot.Controls.Add(this.grpRuntime, 0, 2);
            this.layoutRoot.Controls.Add(this.filler, 1, 2);
            this.layoutRoot.Dock = System.Windows.Forms.DockStyle.Fill;
            this.layoutRoot.Location = new System.Drawing.Point(0, 0);
            this.layoutRoot.Name = "layoutRoot";
            this.layoutRoot.RowCount = 3;
            this.layoutRoot.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 165F));
            this.layoutRoot.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Percent, 100F));
            this.layoutRoot.RowStyles.Add(new System.Windows.Forms.RowStyle(System.Windows.Forms.SizeType.Absolute, 170F));
            this.layoutRoot.Size = new System.Drawing.Size(1284, 681);
            this.layoutRoot.TabIndex = 0;
            // 
            // grpSource
            // 
            this.grpSource.Controls.Add(this.rbCamera);
            this.grpSource.Controls.Add(this.rbVideo);
            this.grpSource.Controls.Add(this.rbImage);
            this.grpSource.Controls.Add(this.numCameraIndex);
            this.grpSource.Controls.Add(this.txtMediaPath);
            this.grpSource.Controls.Add(this.btnBrowseMedia);
            this.grpSource.Dock = System.Windows.Forms.DockStyle.Fill;
            this.grpSource.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.grpSource.Location = new System.Drawing.Point(3, 3);
            this.grpSource.Name = "grpSource";
            this.grpSource.Size = new System.Drawing.Size(636, 159);
            this.grpSource.TabIndex = 0;
            this.grpSource.TabStop = false;
            this.grpSource.Text = "Kaynak";
            // 
            // rbCamera
            // 
            this.rbCamera.AutoSize = true;
            this.rbCamera.Checked = true;
            this.rbCamera.Location = new System.Drawing.Point(12, 28);
            this.rbCamera.Name = "rbCamera";
            this.rbCamera.Size = new System.Drawing.Size(79, 23);
            this.rbCamera.TabIndex = 0;
            this.rbCamera.TabStop = true;
            this.rbCamera.Text = "Kamera";
            // 
            // rbVideo
            // 
            this.rbVideo.AutoSize = true;
            this.rbVideo.Location = new System.Drawing.Point(110, 28);
            this.rbVideo.Name = "rbVideo";
            this.rbVideo.Size = new System.Drawing.Size(66, 23);
            this.rbVideo.TabIndex = 1;
            this.rbVideo.Text = "Video";
            // 
            // rbImage
            // 
            this.rbImage.AutoSize = true;
            this.rbImage.Location = new System.Drawing.Point(180, 28);
            this.rbImage.Name = "rbImage";
            this.rbImage.Size = new System.Drawing.Size(85, 23);
            this.rbImage.TabIndex = 2;
            this.rbImage.Text = "Fotoğraf";
            // 
            // numCameraIndex
            // 
            this.numCameraIndex.Location = new System.Drawing.Point(12, 58);
            this.numCameraIndex.Maximum = new decimal(new int[] {
            8,
            0,
            0,
            0});
            this.numCameraIndex.Name = "numCameraIndex";
            this.numCameraIndex.Size = new System.Drawing.Size(80, 25);
            this.numCameraIndex.TabIndex = 3;
            // 
            // txtMediaPath
            // 
            this.txtMediaPath.Location = new System.Drawing.Point(100, 58);
            this.txtMediaPath.Name = "txtMediaPath";
            this.txtMediaPath.Size = new System.Drawing.Size(420, 25);
            this.txtMediaPath.TabIndex = 4;
            // 
            // btnBrowseMedia
            // 
            this.btnBrowseMedia.Location = new System.Drawing.Point(525, 56);
            this.btnBrowseMedia.Name = "btnBrowseMedia";
            this.btnBrowseMedia.Size = new System.Drawing.Size(80, 28);
            this.btnBrowseMedia.TabIndex = 5;
            this.btnBrowseMedia.Text = "Gözat";
            // 
            // grpOptions
            // 
            this.grpOptions.Controls.Add(this.chkShow);
            this.grpOptions.Controls.Add(this.chkSave);
            this.grpOptions.Controls.Add(this.txtOutputPath);
            this.grpOptions.Controls.Add(this.btnBrowseOutput);
            this.grpOptions.Controls.Add(this.lblFps);
            this.grpOptions.Controls.Add(this.numFps);
            this.grpOptions.Dock = System.Windows.Forms.DockStyle.Fill;
            this.grpOptions.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.grpOptions.Location = new System.Drawing.Point(645, 3);
            this.grpOptions.Name = "grpOptions";
            this.grpOptions.Size = new System.Drawing.Size(636, 159);
            this.grpOptions.TabIndex = 1;
            this.grpOptions.TabStop = false;
            this.grpOptions.Text = "Seçenekler";
            // 
            // chkShow
            // 
            this.chkShow.AutoSize = true;
            this.chkShow.Checked = true;
            this.chkShow.CheckState = System.Windows.Forms.CheckState.Checked;
            this.chkShow.Location = new System.Drawing.Point(12, 28);
            this.chkShow.Name = "chkShow";
            this.chkShow.Size = new System.Drawing.Size(184, 23);
            this.chkShow.TabIndex = 0;
            this.chkShow.Text = "İşleneni Ekranda Göster";
            // 
            // chkSave
            // 
            this.chkSave.AutoSize = true;
            this.chkSave.Location = new System.Drawing.Point(220, 28);
            this.chkSave.Name = "chkSave";
            this.chkSave.Size = new System.Drawing.Size(191, 23);
            this.chkSave.TabIndex = 1;
            this.chkSave.Text = "İşlenmiş Videoyu Kaydet";
            // 
            // txtOutputPath
            // 
            this.txtOutputPath.Location = new System.Drawing.Point(12, 58);
            this.txtOutputPath.Name = "txtOutputPath";
            this.txtOutputPath.Size = new System.Drawing.Size(500, 25);
            this.txtOutputPath.TabIndex = 2;
            // 
            // btnBrowseOutput
            // 
            this.btnBrowseOutput.Location = new System.Drawing.Point(525, 56);
            this.btnBrowseOutput.Name = "btnBrowseOutput";
            this.btnBrowseOutput.Size = new System.Drawing.Size(80, 28);
            this.btnBrowseOutput.TabIndex = 3;
            this.btnBrowseOutput.Text = "Gözat";
            // 
            // lblFps
            // 
            this.lblFps.AutoSize = true;
            this.lblFps.Location = new System.Drawing.Point(12, 96);
            this.lblFps.Name = "lblFps";
            this.lblFps.Size = new System.Drawing.Size(82, 19);
            this.lblFps.TabIndex = 4;
            this.lblFps.Text = "Hedef FPS:";
            // 
            // numFps
            // 
            this.numFps.Location = new System.Drawing.Point(88, 92);
            this.numFps.Maximum = new decimal(new int[] {
            60,
            0,
            0,
            0});
            this.numFps.Minimum = new decimal(new int[] {
            5,
            0,
            0,
            0});
            this.numFps.Name = "numFps";
            this.numFps.Size = new System.Drawing.Size(80, 25);
            this.numFps.TabIndex = 5;
            this.numFps.Value = new decimal(new int[] {
            20,
            0,
            0,
            0});
            // 
            // txtLog
            // 
            this.txtLog.BackColor = System.Drawing.Color.White;
            this.txtLog.Dock = System.Windows.Forms.DockStyle.Fill;
            this.txtLog.Font = new System.Drawing.Font("Consolas", 9.5F);
            this.txtLog.Location = new System.Drawing.Point(3, 168);
            this.txtLog.Name = "txtLog";
            this.txtLog.Size = new System.Drawing.Size(636, 340);
            this.txtLog.TabIndex = 2;
            this.txtLog.Text = "";
            // 
            // grpRuntime
            // 
            this.grpRuntime.Controls.Add(this.txtPythonPath);
            this.grpRuntime.Controls.Add(this.btnBrowsePython);
            this.grpRuntime.Controls.Add(this.txtDbPath);
            this.grpRuntime.Controls.Add(this.btnBrowseDb);
            this.grpRuntime.Controls.Add(this.btnStart);
            this.grpRuntime.Controls.Add(this.btnStop);
            this.grpRuntime.Controls.Add(this.progress);
            this.grpRuntime.Controls.Add(this.lblStatus);
            this.grpRuntime.Dock = System.Windows.Forms.DockStyle.Fill;
            this.grpRuntime.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold);
            this.grpRuntime.Location = new System.Drawing.Point(3, 514);
            this.grpRuntime.Name = "grpRuntime";
            this.grpRuntime.Size = new System.Drawing.Size(636, 164);
            this.grpRuntime.TabIndex = 4;
            this.grpRuntime.TabStop = false;
            this.grpRuntime.Text = "Çalıştırma";
            // 
            // txtPythonPath
            // 
            this.txtPythonPath.Location = new System.Drawing.Point(12, 28);
            this.txtPythonPath.Name = "txtPythonPath";
            this.txtPythonPath.Size = new System.Drawing.Size(500, 25);
            this.txtPythonPath.TabIndex = 0;
            // 
            // btnBrowsePython
            // 
            this.btnBrowsePython.Location = new System.Drawing.Point(525, 26);
            this.btnBrowsePython.Name = "btnBrowsePython";
            this.btnBrowsePython.Size = new System.Drawing.Size(80, 28);
            this.btnBrowsePython.TabIndex = 1;
            this.btnBrowsePython.Text = "Gözat";
            // 
            // txtDbPath
            // 
            this.txtDbPath.Location = new System.Drawing.Point(12, 62);
            this.txtDbPath.Name = "txtDbPath";
            this.txtDbPath.Size = new System.Drawing.Size(500, 25);
            this.txtDbPath.TabIndex = 2;
            // 
            // btnBrowseDb
            // 
            this.btnBrowseDb.Location = new System.Drawing.Point(525, 60);
            this.btnBrowseDb.Name = "btnBrowseDb";
            this.btnBrowseDb.Size = new System.Drawing.Size(80, 28);
            this.btnBrowseDb.TabIndex = 3;
            this.btnBrowseDb.Text = "Gözat";
            // 
            // btnStart
            // 
            this.btnStart.Location = new System.Drawing.Point(12, 100);
            this.btnStart.Name = "btnStart";
            this.btnStart.Size = new System.Drawing.Size(120, 36);
            this.btnStart.TabIndex = 4;
            this.btnStart.Text = "Başlat";
            // 
            // btnStop
            // 
            this.btnStop.Enabled = false;
            this.btnStop.Location = new System.Drawing.Point(140, 100);
            this.btnStop.Name = "btnStop";
            this.btnStop.Size = new System.Drawing.Size(120, 36);
            this.btnStop.TabIndex = 5;
            this.btnStop.Text = "Durdur";
            // 
            // progress
            // 
            this.progress.Location = new System.Drawing.Point(270, 106);
            this.progress.MarqueeAnimationSpeed = 0;
            this.progress.Name = "progress";
            this.progress.Size = new System.Drawing.Size(335, 23);
            this.progress.Style = System.Windows.Forms.ProgressBarStyle.Marquee;
            this.progress.TabIndex = 6;
            // 
            // lblStatus
            // 
            this.lblStatus.AutoSize = true;
            this.lblStatus.Location = new System.Drawing.Point(12, 144);
            this.lblStatus.Name = "lblStatus";
            this.lblStatus.Size = new System.Drawing.Size(45, 19);
            this.lblStatus.TabIndex = 7;
            this.lblStatus.Text = "Hazır";
            // 
            // filler
            // 
            this.filler.Dock = System.Windows.Forms.DockStyle.Fill;
            this.filler.Location = new System.Drawing.Point(645, 514);
            this.filler.Name = "filler";
            this.filler.Size = new System.Drawing.Size(636, 164);
            this.filler.TabIndex = 5;
            // 
            // picPreview
            // 
            this.picPreview.BackColor = System.Drawing.Color.Black;
            this.picPreview.Dock = System.Windows.Forms.DockStyle.Fill;
            this.picPreview.Location = new System.Drawing.Point(645, 168);
            this.picPreview.Name = "picPreview";
            this.picPreview.Size = new System.Drawing.Size(636, 340);
            this.picPreview.SizeMode = System.Windows.Forms.PictureBoxSizeMode.Zoom;
            this.picPreview.TabIndex = 3;
            this.picPreview.TabStop = false;
            this.picPreview.Visible = false;
            // 
            // Form_kinematik
            // 
            this.BackColor = System.Drawing.Color.White;
            this.ClientSize = new System.Drawing.Size(1284, 681);
            this.Controls.Add(this.layoutRoot);
            this.Font = new System.Drawing.Font("Segoe UI", 9F);
            this.MinimumSize = new System.Drawing.Size(1100, 720);
            this.Name = "Form_kinematik";
            this.Text = "Kinematik Analiz Paneli";
            this.layoutRoot.ResumeLayout(false);
            this.grpSource.ResumeLayout(false);
            this.grpSource.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.numCameraIndex)).EndInit();
            this.grpOptions.ResumeLayout(false);
            this.grpOptions.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.numFps)).EndInit();
            this.grpRuntime.ResumeLayout(false);
            this.grpRuntime.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.picPreview)).EndInit();
            this.ResumeLayout(false);

        }

        private PictureBox picPreview;
    }
}
