using System;
using System.Data.SQLite;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace SporcuTakip
{
    public partial class Form_veri_girisi : Form
    {
        public Form_veri_girisi()
        {
            InitializeComponent();
        }

        // .exe ile aynı klasördeki veritabanı
        string baglantiYolu => Path.Combine(Application.StartupPath, "goruntu_isleme.db");

        private void Form_veri_girisi_Load(object sender, EventArgs e)
        {
            // Şemayı garantiye al (ikisinde de 'aktif' kolonu yoksa ekler ve 1 yapar)
            EnsureAktifColumn("kisiler");
            EnsureAktifColumn("vurus_stilleri");

            // YENİ: spin tablosunu garantiye al + aktif sütunu
            EnsureSpinTable();                 // oluşturmazsa dokunmaz, yoksa oluşturur
            EnsureAktifColumn("spinler");      // aktif sütununu güvenceye al


            // Listeleri doldur
            ListeleKisiler();
            ListeleVurusStilleri();
            ListeleSpinler();                  // YENİ
        }

        private void ListeleSpinler()
        {
            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    string q = "SELECT id, ad FROM spinler WHERE aktif=1 ORDER BY ad;";
                    using (var cmd = new SQLiteCommand(q, conn))
                    using (var r = cmd.ExecuteReader())
                    {
                        comboBox_spinler.Items.Clear();
                        if (kayitli_spinler_txt is TextBox)  // TextBox ise
                            ((TextBox)kayitli_spinler_txt).Clear();


                        while (r.Read())
                        {
                            var item = new ComboBoxItem
                            {
                                Text = r["ad"].ToString(),
                                Value = Convert.ToInt32(r["id"])
                            };
                            comboBox_spinler.Items.Add(item);

                            if (kayitli_spinler_txt is TextBox tb)
                                tb.AppendText(item.Text + Environment.NewLine);

                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Spinler listelenirken hata: " + ex.Message);
            }
        }

        private void EnsureSpinTable()
        {
            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    using (var cmd = new SQLiteCommand(@"
                CREATE TABLE IF NOT EXISTS spinler (
                    id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad     TEXT NOT NULL UNIQUE,
                    aktif  INTEGER NOT NULL DEFAULT 1
                );", conn))
                    {
                        cmd.ExecuteNonQuery();
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("spinler tablosu kontrolünde hata: " + ex.Message);
            }
        }

        // ----------------------------------------------------------------
        // 🧩 Şema güvence: Tabloya 'aktif' kolonu yoksa ekle ve hepsini 1 yap
        // ----------------------------------------------------------------
        private void EnsureAktifColumn(string tabloAdi)
        {
            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();

                    bool aktifVar = false;
                    using (var cmd = new SQLiteCommand($"PRAGMA table_info({tabloAdi});", conn))
                    using (var r = cmd.ExecuteReader())
                    {
                        while (r.Read())
                        {
                            if (r["name"].ToString().Equals("aktif", StringComparison.OrdinalIgnoreCase))
                            {
                                aktifVar = true;
                                break;
                            }
                        }
                    }

                    if (!aktifVar)
                    {
                        using (var cmd = new SQLiteCommand($"ALTER TABLE {tabloAdi} ADD COLUMN aktif INTEGER NOT NULL DEFAULT 1;", conn))
                            cmd.ExecuteNonQuery();
                        using (var cmd = new SQLiteCommand($"UPDATE {tabloAdi} SET aktif = 1 WHERE aktif IS NULL;", conn))
                            cmd.ExecuteNonQuery();
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Şema kontrolü/eklemesi sırasında hata ({tabloAdi}): {ex.Message}");
            }
        }

        // ----------------------------------------------------------------
        // 🧩 Yardımcı: ComboBox Item tipi (ortak)
        // ----------------------------------------------------------------
        private class ComboBoxItem
        {
            public string Text { get; set; }
            public int Value { get; set; }
            public override string ToString() => Text;
        }

        // ----------------------------------------------------------------
        // 👤 Kişiler — Listeleme (yalnız aktif=1)
        // ----------------------------------------------------------------
        private void ListeleKisiler()
        {
            try
            {
                using (var baglanti = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    baglanti.Open();
                    string sorgu = "SELECT id, ad, soyad FROM kisiler WHERE aktif=1 ORDER BY ad, soyad";
                    using (var cmd = new SQLiteCommand(sorgu, baglanti))
                    using (var oku = cmd.ExecuteReader())
                    {
                        comboBox_kisiler.Items.Clear();
                        txt_kayitlikisiler.Clear();

                        while (oku.Read())
                        {
                            string adsoyad = $"{oku["ad"]} {oku["soyad"]}";
                            comboBox_kisiler.Items.Add(new ComboBoxItem
                            {
                                Text = adsoyad,
                                Value = Convert.ToInt32(oku["id"])
                            });
                            txt_kayitlikisiler.AppendText(adsoyad + Environment.NewLine);
                        }
                    }
                }
            }
            catch (SQLiteException ex)
            {
                MessageBox.Show($"Kişi listeleme DB hatası: {ex.Message}");
            }
        }

        // ----------------------------------------------------------------
        // 👤 Kişiler — Ekle (aktif=1)
        // ----------------------------------------------------------------
        private void button_kisi_kaydet_Click(object sender, EventArgs e)
        {
            string ad = txt_isim.Text.Trim();
            string soyad = txt_soyisim.Text.Trim();
            string notlar = txt_notlar.Text.Trim();

            if (string.IsNullOrWhiteSpace(ad) || string.IsNullOrWhiteSpace(soyad))
            {
                MessageBox.Show("Ad ve soyad boş olamaz!", "Uyarı", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    string sorgu = "INSERT INTO kisiler (ad, soyad, notlar, aktif) VALUES (@ad, @soyad, @notlar, 1)";
                    using (var cmd = new SQLiteCommand(sorgu, conn))
                    {
                        cmd.Parameters.AddWithValue("@ad", ad);
                        cmd.Parameters.AddWithValue("@soyad", soyad);
                        cmd.Parameters.AddWithValue("@notlar", notlar);
                        cmd.ExecuteNonQuery();
                    }
                }

                // Form temizle + liste yenile
                txt_isim.Clear();
                txt_soyisim.Clear();
                txt_notlar.Clear();
                ListeleKisiler();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Kişi eklenirken hata: " + ex.Message);
            }
        }

        // ----------------------------------------------------------------
        // 👤 Kişiler — Sil (soft delete: aktif=0)
        // ----------------------------------------------------------------
        private void button_kisi_sil_Click(object sender, EventArgs e)
        {
            if (comboBox_kisiler.SelectedItem == null)
            {
                MessageBox.Show("Lütfen pasif yapılacak kişiyi seçiniz!");
                return;
            }

            var secili = (ComboBoxItem)comboBox_kisiler.SelectedItem;

            var onay = MessageBox.Show(
                $"{secili.Text} adlı kişiyi pasif (silinmiş) yapmak istiyor musunuz?",
                "Onay", MessageBoxButtons.YesNo, MessageBoxIcon.Question);

            if (onay != DialogResult.Yes) return;

            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    string sorgu = "UPDATE kisiler SET aktif=0 WHERE id=@id";
                    using (var cmd = new SQLiteCommand(sorgu, conn))
                    {
                        cmd.Parameters.AddWithValue("@id", secili.Value);
                        cmd.ExecuteNonQuery();
                    }
                }

                MessageBox.Show("Kayıt pasif yapıldı.");
                ListeleKisiler();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Pasif etme hatası: " + ex.Message);
            }
        }

        // ----------------------------------------------------------------
        // 🎾 Vuruş stilleri — Listeleme (yalnız aktif=1)
        // ----------------------------------------------------------------
        private void ListeleVurusStilleri()
        {
            try
            {
                using (var baglanti = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    baglanti.Open();
                    string sorgu = "SELECT id, ad FROM vurus_stilleri WHERE aktif=1 ORDER BY ad";
                    using (var cmd = new SQLiteCommand(sorgu, baglanti))
                    using (var oku = cmd.ExecuteReader())
                    {
                        comboBox_vurus_stilleri.Items.Clear();
                        kayitli_vurus_stilleri_txt.Clear();

                        while (oku.Read())
                        {
                            string ad = oku["ad"].ToString();
                            comboBox_vurus_stilleri.Items.Add(new ComboBoxItem
                            {
                                Text = ad,
                                Value = Convert.ToInt32(oku["id"])
                            });
                            kayitli_vurus_stilleri_txt.AppendText(ad + Environment.NewLine);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Vuruş stilleri listelenirken hata: " + ex.Message);
            }
        }

        // ----------------------------------------------------------------
        // 🎾 Vuruş stilleri — Ekle (aktif=1)
        // ----------------------------------------------------------------
        private void stik_ekle_btn_Click(object sender, EventArgs e)
        {
            string vurusStiliAdi = vurus_stili_adi_txt.Text.Trim();

            if (string.IsNullOrEmpty(vurusStiliAdi))
            {
                MessageBox.Show("Lütfen bir vuruş stili adı giriniz.");
                return;
            }

            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    string sorgu = "INSERT INTO vurus_stilleri (ad, aktif) VALUES (@ad, 1)";
                    using (var cmd = new SQLiteCommand(sorgu, conn))
                    {
                        cmd.Parameters.AddWithValue("@ad", vurusStiliAdi);
                        cmd.ExecuteNonQuery();
                    }
                }

                MessageBox.Show("Vuruş stili eklendi.");
                vurus_stili_adi_txt.Clear();
                ListeleVurusStilleri();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Vuruş stili eklenirken hata: " + ex.Message);
            }
        }

        // ----------------------------------------------------------------
        // 🎾 Vuruş stilleri — Sil (soft delete: aktif=0)
        // ----------------------------------------------------------------
        private void button_vurus_sil_Click(object sender, EventArgs e)
        {
            if (comboBox_vurus_stilleri.SelectedItem == null)
            {
                MessageBox.Show("Lütfen pasif yapılacak vuruş stilini seçiniz!");
                return;
            }

            var secili = (ComboBoxItem)comboBox_vurus_stilleri.SelectedItem;

            var onay = MessageBox.Show(
                $"{secili.Text} adlı vuruş stilini pasif yapmak istiyor musunuz?",
                "Onay", MessageBoxButtons.YesNo, MessageBoxIcon.Question);

            if (onay != DialogResult.Yes) return;

            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    string sorgu = "UPDATE vurus_stilleri SET aktif=0 WHERE id=@id";
                    using (var cmd = new SQLiteCommand(sorgu, conn))
                    {
                        cmd.Parameters.AddWithValue("@id", secili.Value);
                        cmd.ExecuteNonQuery();
                    }
                }

                MessageBox.Show("Vuruş stili pasif yapıldı.");
                ListeleVurusStilleri();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Vuruş stili pasif etme hatası: " + ex.Message);
            }
        }

        // ----------------------------------------------------------------
        // 💾 Veritabanı yedekleme (Online backup)
        // ----------------------------------------------------------------
        private static string GetDesktopFramesDir()
        {
            string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            string oneDrive = Environment.GetEnvironmentVariable("OneDrive");

            var candidates = new[]
            {
                Path.Combine(oneDrive ?? "", "Desktop"),
                Path.Combine(oneDrive ?? "", "Masaüstü"),
                Environment.GetFolderPath(Environment.SpecialFolder.Desktop),
                Path.Combine(home, "Masaüstü")
            };

            foreach (var p in candidates)
                if (!string.IsNullOrWhiteSpace(p) && Directory.Exists(p))
                {
                    string target = Path.Combine(p, "frameler");
                    Directory.CreateDirectory(target);
                    return target;
                }

            string fb = Path.Combine(home, "frameler");
            Directory.CreateDirectory(fb);
            return fb;
        }
        private void button_spin_ekle_Click(object sender, EventArgs e)
        {
            string ad = spin_adi_txt.Text.Trim();
            if (string.IsNullOrEmpty(ad))
            {
                MessageBox.Show("Lütfen bir spin adı giriniz.");
                return;
            }

            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    // SQLite 3.24+ UPSERT: aynı ad varsa aktif=1 yap (re-activate)
                    string q = @"
                INSERT INTO spinler (ad, aktif) VALUES (@ad, 1)
                ON CONFLICT(ad) DO UPDATE SET aktif=1;";
                    using (var cmd = new SQLiteCommand(q, conn))
                    {
                        cmd.Parameters.AddWithValue("@ad", ad);
                        cmd.ExecuteNonQuery();
                    }
                }

                MessageBox.Show("Spin eklendi / aktifleştirildi.");
                spin_adi_txt.Clear();
                ListeleSpinler();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Spin ekleme hatası: " + ex.Message);
            }
        }




        private void button_spin_sil_Click(object sender, EventArgs e)
        {
            if (comboBox_spinler.SelectedItem == null)
            {
                MessageBox.Show("Lütfen pasif yapılacak spini seçiniz!");
                return;
            }

            var secili = (ComboBoxItem)comboBox_spinler.SelectedItem;

            var onay = MessageBox.Show(
                $"{secili.Text} adlı spini pasif yapmak istiyor musunuz?",
                "Onay", MessageBoxButtons.YesNo, MessageBoxIcon.Question);

            if (onay != DialogResult.Yes) return;

            try
            {
                using (var conn = new SQLiteConnection($"Data Source={baglantiYolu};Version=3;"))
                {
                    conn.Open();
                    string q = "UPDATE spinler SET aktif=0 WHERE id=@id;";
                    using (var cmd = new SQLiteCommand(q, conn))
                    {
                        cmd.Parameters.AddWithValue("@id", secili.Value);
                        cmd.ExecuteNonQuery();
                    }
                }

                MessageBox.Show("Spin pasif yapıldı.");
                ListeleSpinler();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Spin pasif etme hatası: " + ex.Message);
            }
        }

        private void button_db_Click(object sender, EventArgs e)
        {
            try
            {
                string srcDb = baglantiYolu;
                if (string.IsNullOrWhiteSpace(srcDb) || !File.Exists(srcDb))
                {
                    MessageBox.Show("Veritabanı bulunamadı:\n" + srcDb, "Uyarı",
                                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }

                string root = GetDesktopFramesDir(); // ...\Masaüstü\frameler
                string stamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
                string destDb = Path.Combine(root, $"goruntu_isleme_{stamp}.db");

                using (var src = new SQLiteConnection($"Data Source={srcDb};Version=3;"))
                using (var dst = new SQLiteConnection($"Data Source={destDb};Version=3;"))
                {
                    src.Open();
                    dst.Open();
                    src.BackupDatabase(dst, "main", "main", -1, null, 0); // tüm sayfalar
                }

                MessageBox.Show($"Yedek alındı:\n{destDb}", "Tamam",
                                MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                try
                {
                    string root = GetDesktopFramesDir();
                    string stamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
                    string destDb = Path.Combine(root, $"goruntu_isleme_{stamp}.db");
                    File.Copy(baglantiYolu, destDb, overwrite: false);

                    MessageBox.Show($"(Fallback) Dosya kopyalama ile yedek alındı:\n{destDb}",
                                    "Bilgi", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex2)
                {
                    MessageBox.Show("Yedekleme başarısız:\n" + ex.Message + "\n\n" + ex2.Message,
                                    "Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        // ---------------------------------------------------------------
        // (İsteğe bağlı) Vuruş stili adı TextChanged — şimdilik boş kalsın
        // ---------------------------------------------------------------
        private void vurus_stili_adi_txt_TextChanged(object sender, EventArgs e) { }
    }
}
