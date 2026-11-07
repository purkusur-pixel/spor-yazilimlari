using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace SporcuTakip
{
    /// <summary>
    /// WebView2 preview -> Bitmap -> BGRA -> MemoryMappedFile
    /// Shared memory layout:
    /// 0..63   : header (fixed 64 bytes)
    /// 64..    : BGRA bytes (stride * height)
    /// Header (little-endian):
    /// [0]   uint32 magic = 0x46524D45
    /// [4]   uint32 version = 1
    /// [8]   int32  width
    /// [12]  int32  height
    /// [16]  int32  strideBytes
    /// [20]  int32  channels (=4)
    /// [24]  int32  format (=1 => BGRA)
    /// [28]  int32  frameId
    /// [32]  int64  ticksUtc
    /// [40]  int32  dataBytes
    /// [44]  int32  ready (0/1)
    /// [48..63] reserved
    /// </summary>
    public sealed class SharedFrameWriter : IDisposable
    {
        public const string DefaultMapName = "Global\\SPORCU_FRAME_MMF_V1";
        public const string DefaultMutexName = "Global\\SPORCU_FRAME_MMF_MUTEX_V1";

        private const int HEADER_SIZE = 64;
        private const uint MAGIC = 0x46524D45; // 'EMRF'
        private const int VERSION = 1;

        private readonly WebView2 _webView;
        private readonly int _maxW;
        private readonly int _maxH;
        private readonly int _maxBytes;
        private readonly string _mapName;
        private readonly string _mutexName;

        private MemoryMappedFile _mmf;
        private MemoryMappedViewAccessor _acc;
        private Mutex _mtx;

        private System.Windows.Forms.Timer _uiTimer;   // ✅ UI thread timer
        private int _frameId = 0;
        private volatile bool _busy = false;

        public bool IsRunning { get; private set; }

        public SharedFrameWriter(
            WebView2 webView,
            int maxWidth = 1920,
            int maxHeight = 1080,
            string mapName = DefaultMapName,
            string mutexName = DefaultMutexName)
        {
            _webView = webView ?? throw new ArgumentNullException(nameof(webView));
            _maxW = Math.Max(320, maxWidth);
            _maxH = Math.Max(240, maxHeight);
            _maxBytes = _maxW * _maxH * 4; // BGRA
            _mapName = mapName;
            _mutexName = mutexName;

            long capacity = HEADER_SIZE + (long)_maxBytes;

            _mmf = MemoryMappedFile.CreateOrOpen(_mapName, capacity, MemoryMappedFileAccess.ReadWrite);
            _acc = _mmf.CreateViewAccessor(0, capacity, MemoryMappedFileAccess.ReadWrite);

            bool createdNew;
            _mtx = new Mutex(false, _mutexName, out createdNew);

            // initial header
            WriteHeader(0, 0, 0, 4, 1, 0, DateTime.UtcNow.Ticks, 0, 0);
        }

        public void Start(int intervalMs = 33) // ~30 FPS
        {
            if (IsRunning) return;
            IsRunning = true;

            // ✅ UI thread timer
            _uiTimer = new System.Windows.Forms.Timer();
            _uiTimer.Interval = Math.Max(15, intervalMs);
            _uiTimer.Tick += async (s, e) =>
            {
                if (!IsRunning) return;
                if (_busy) return;
                if (_webView == null) return;
                if (_webView.CoreWebView2 == null) return;

                _busy = true;
                try
                {
                    await CaptureAndWriteOnce_UIThread();
                }
                catch (Exception ex)
                {
                    Debug.WriteLine("SharedFrameWriter tick error: " + ex.Message);
                }
                finally
                {
                    _busy = false;
                }
            };
            _uiTimer.Start();
        }

        public void Stop()
        {
            IsRunning = false;
            try { _uiTimer?.Stop(); } catch { }
            try { _uiTimer?.Dispose(); } catch { }
            _uiTimer = null;

            // ready=0
            try { _acc?.Write(44, 0); } catch { }
        }

        private async System.Threading.Tasks.Task CaptureAndWriteOnce_UIThread()
        {
            // ✅ Bu fonksiyon UI thread'de çalışır (WinForms Timer tick)
            using (var ms = new MemoryStream())
            {
                await _webView.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, ms);
                ms.Position = 0;

                using (var bmp = new Bitmap(ms))
                using (var conv = Ensure32bppPArgb(bmp))
                {
                    WriteBitmapToMmf(conv);
                }
            }
        }

        private static Bitmap Ensure32bppPArgb(Bitmap src)
        {
            if (src.PixelFormat == PixelFormat.Format32bppPArgb)
                return (Bitmap)src.Clone();

            var dst = new Bitmap(src.Width, src.Height, PixelFormat.Format32bppPArgb);
            using (var g = Graphics.FromImage(dst))
                g.DrawImage(src, 0, 0, src.Width, src.Height);
            return dst;
        }

        private void WriteBitmapToMmf(Bitmap bmp)
        {
            int w = bmp.Width;
            int h = bmp.Height;

            // max sınır
            if (w > _maxW || h > _maxH)
            {
                int nw = _maxW;
                int nh = (int)Math.Round(h * (nw / (double)w));
                if (nh > _maxH)
                {
                    nh = _maxH;
                    nw = (int)Math.Round(w * (nh / (double)h));
                }

                using (var resized = new Bitmap(bmp, new Size(nw, nh)))
                using (var conv = Ensure32bppPArgb(resized))
                {
                    WriteBitmapToMmf(conv);
                    return;
                }
            }

            var rect = new Rectangle(0, 0, w, h);
            BitmapData bd = null;

            try
            {
                bd = bmp.LockBits(rect, ImageLockMode.ReadOnly, PixelFormat.Format32bppPArgb);
                int stride = bd.Stride;
                int bytes = Math.Abs(stride) * h;
                if (bytes <= 0 || bytes > _maxBytes) return;

                // mutex ile yaz (çok kısa)
                if (!_mtx.WaitOne(10)) return;

                int fid = Interlocked.Increment(ref _frameId);
                long ticks = DateTime.UtcNow.Ticks;

                // ready=0
                WriteHeader(w, h, stride, 4, 1, fid, ticks, bytes, 0);

                // kopyala
                byte[] buf = new byte[bytes];
                Marshal.Copy(bd.Scan0, buf, 0, bytes);
                _acc.WriteArray(HEADER_SIZE, buf, 0, bytes);

                // ready=1
                _acc.Write(44, 1);

                _mtx.ReleaseMutex();
            }
            catch
            {
                try { _mtx.ReleaseMutex(); } catch { }
            }
            finally
            {
                if (bd != null) bmp.UnlockBits(bd);
            }
        }

        private void WriteHeader(int w, int h, int stride, int channels, int format, int frameId, long ticksUtc, int dataBytes, int ready)
        {
            _acc.Write(0, (UInt32)MAGIC);
            _acc.Write(4, (UInt32)VERSION);

            _acc.Write(8, w);
            _acc.Write(12, h);
            _acc.Write(16, stride);
            _acc.Write(20, channels);
            _acc.Write(24, format);
            _acc.Write(28, frameId);
            _acc.Write(32, ticksUtc);
            _acc.Write(40, dataBytes);
            _acc.Write(44, ready);
        }

        public void Dispose()
        {
            Stop();
            try { _acc?.Dispose(); } catch { }
            try { _mmf?.Dispose(); } catch { }
            try { _mtx?.Dispose(); } catch { }
            _acc = null;
            _mmf = null;
            _mtx = null;
        }
    }
}
