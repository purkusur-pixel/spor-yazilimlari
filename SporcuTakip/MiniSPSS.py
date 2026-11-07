# -*- coding: utf-8 -*-
"""
MiniSPSS.py
Basit SPSS-benzeri istatistik aracı (Tkinter)

Özellikler:
- CSV/Excel veri yükleme
- Değişken tiplerini (Sayısal/Kategorik) otomatik ayırma
- Önizleme sekmesi
- Tanımlayıcı İstatistikler (mean, std, min, max, quantile, eksik sayısı)
- Frekans Tablosu
- Çapraz Tablo + Ki-Kare testi
- t-Test (bağımsız iki örneklem, isteğe bağlı Welch)
- Tek Yönlü ANOVA
- Korelasyon (Pearson/Spearman)
- Doğrusal Regresyon (OLS, statsmodels özet)
- Grafikler: Histogram, Kutu Grafiği, Sütun, Saçılım (+ en küçük kareler doğrusu)

Kurulum (örn. Windows PowerShell):
  python -m pip install pandas numpy scipy statsmodels matplotlib openpyxl

Çalıştırma:
  python MiniSPSS.py

Notlar:
- Excel için openpyxl gerekir.
- Büyük veri setlerinde arayüz gecikmeleri olabilir; örnekleme seçenekleri ekleyebilirsiniz.
"""

import os
import io
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ----------------------------- Yardımcı Fonksiyonlar -----------------------------

def is_numeric_dtype(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s)

def classify_columns(df: pd.DataFrame, cat_max_unique: int = 20):
    numeric_cols, categorical_cols = [], []
    for c in df.columns:
        s = df[c]
        if is_numeric_dtype(s):
            numeric_cols.append(c)
        else:
            categorical_cols.append(c)
    # numerik olup düşük kardinaliteli olanları kategorik listeye de ekleyelim
    for c in list(numeric_cols):
        s = df[c]
        if s.dropna().nunique() <= cat_max_unique:
            if c not in categorical_cols:
                categorical_cols.append(c)
    return sorted(list(dict.fromkeys(numeric_cols))), sorted(list(dict.fromkeys(categorical_cols)))


def text_from_df(df: pd.DataFrame, max_rows: int = 500) -> str:
    if df is None:
        return ""
    tail_note = ""
    if len(df) > max_rows:
        df = df.head(max_rows)
        tail_note = f"\n... (ilk {max_rows} satır gösterildi)\n"
    buf = io.StringIO()
    df.to_string(buf)
    return buf.getvalue() + tail_note



def ensure_levels(df: pd.DataFrame, col: str, n_levels: int = 2):
    vals = df[col].dropna().unique().tolist()
    if len(vals) < n_levels:
        raise ValueError(f"'{col}' değişkeninde en az {n_levels} farklı seviye olmalı (şu an: {len(vals)}).")
    return vals


# ----------------------------- Ana Uygulama Sınıfı -----------------------------
class MiniSPSSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MiniSPSS — Temel İstatistik Aracı (Tkinter)")
        self.geometry("1200x750")
        self.minsize(1000, 650)

        self.df: pd.DataFrame | None = None
        self.numeric_cols: list[str] = []
        self.categorical_cols: list[str] = []

        self._build_menu()
        self._build_layout()

    # ------------------------- Menü -------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="CSV Aç...", command=self.open_csv)
        file_menu.add_command(label="Excel Aç...", command=self.open_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.destroy)
        menubar.add_cascade(label="Dosya", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hakkında", command=self.show_about)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        self.config(menu=menubar)

    # ------------------------- Sol/sağ iskelet -------------------------
    def _build_layout(self):
        root = ttk.Frame(self)
        root.pack(fill=tk.BOTH, expand=True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(root, width=260)
        left.pack(side=tk.LEFT, fill=tk.Y)

        right = ttk.Frame(root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Sol panel — Değişken listeleri
        lbl_data = ttk.Label(left, text="Veri Kümesi")
        lbl_data.pack(anchor="w", padx=10, pady=(10, 0))
        self.lbl_dataset = ttk.Label(left, text="(Yüklü değil)")
        self.lbl_dataset.pack(anchor="w", padx=10)

        ttk.Separator(left).pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(left, text="Sayısal Değişkenler").pack(anchor="w", padx=10)
        self.list_num = tk.Listbox(left, selectmode=tk.EXTENDED, height=12, exportselection=False)
        self.list_num.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(left, text="Kategorik Değişkenler").pack(anchor="w", padx=10)
        self.list_cat = tk.Listbox(left, selectmode=tk.EXTENDED, height=12, exportselection=False)
        self.list_cat.pack(fill=tk.X, padx=10, pady=5)

        btn_reclass = ttk.Button(left, text="Yeniden Sınıflandır", command=self.reclassify)
        btn_reclass.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Sağ panel — Sekmeler
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.tab_preview = self._make_tab_preview()
        self.tab_desc = self._make_tab_descriptives()
        self.tab_freq = self._make_tab_frequencies()
        self.tab_xtab = self._make_tab_crosstab()
        self.tab_ttest = self._make_tab_ttest()
        self.tab_anova = self._make_tab_anova()
        self.tab_corr = self._make_tab_corr()
        self.tab_reg = self._make_tab_regression()
        self.tab_plot = self._make_tab_plots()

    def show_about(self):
        messagebox.showinfo(
            "Hakkında",
            "MiniSPSS — Tkinter ile temel istatistik aracı"
            "Yazan: Siz :)  |  Bağımlılıklar: pandas, numpy, scipy, statsmodels, matplotlib"
        )

    # ------------------------- Dosya Aç -------------------------
    def open_csv(self):
        path = filedialog.askopenfilename(
            title="CSV dosyası seçin",
            filetypes=[("CSV", "*.csv"), ("Text", "*.txt"), ("Tümü", "*.*")]
        )
        if not path:
            return
        try:
            df = pd.read_csv(path)
        except Exception as e:
            messagebox.showerror("Hata", f"CSV okunamadı:{e}")
            return
        self._set_df(df, os.path.basename(path))

    def open_excel(self):
        path = filedialog.askopenfilename(
            title="Excel dosyası seçin",
            filetypes=[("Excel", "*.xlsx;*.xlsm;*.xls"), ("Tümü", "*.*")]
        )
        if not path:
            return
        try:
            df = pd.read_excel(path)
        except Exception as e:
            messagebox.showerror("Hata", f"Excel okunamadı:{e}")
            return
        self._set_df(df, os.path.basename(path))

    def _set_df(self, df: pd.DataFrame, name: str):
        self.df = df
        self.lbl_dataset.config(text=f"{name} | {df.shape[0]} satır × {df.shape[1]} sütun")
        self.numeric_cols, self.categorical_cols = classify_columns(df)
        self._refresh_var_lists()
        self.populate_combos()
        self._refresh_preview()

    def _refresh_var_lists(self):
        self.list_num.delete(0, tk.END)
        self.list_cat.delete(0, tk.END)
        for c in self.numeric_cols:
            self.list_num.insert(tk.END, c)
        for c in self.categorical_cols:
            self.list_cat.insert(tk.END, c)

    def reclassify(self):
        if self.df is None:
            return
        self.numeric_cols, self.categorical_cols = classify_columns(self.df)
        self._refresh_var_lists()
        self.populate_combos()

    # ------------------------- Sekme: Önizleme -------------------------
    def _make_tab_preview(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Önizleme")

        self.txt_preview = tk.Text(frame, wrap=tk.NONE)
        self.txt_preview.pack(fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(self.txt_preview, orient=tk.VERTICAL, command=self.txt_preview.yview)
        self.txt_preview.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        return frame

    def _refresh_preview(self):
        if self.df is None:
            return
        self.txt_preview.delete("1.0", tk.END)
        self.txt_preview.insert(tk.END, text_from_df(self.df.head(100)))

    # ------------------------- Sekme: Tanımlayıcı -------------------------
    def _make_tab_descriptives(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Tanımlayıcı")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Sayısal değişken(ler):").pack(side=tk.LEFT)
        self.combo_desc = ttk.Combobox(top, values=[], width=40)
        self.combo_desc.pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Çalıştır", command=self.run_descriptives).pack(side=tk.LEFT)

        self.txt_desc = tk.Text(frame, wrap=tk.NONE)
        self.txt_desc.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_descriptives(self):
        if self.df is None:
            return
        cols = self._get_selected_in_combobox(self.combo_desc, numeric=True, allow_multi=True)
        if not cols:
            messagebox.showwarning("Uyarı", "En az bir sayısal değişken seçin (virgülle ayırabilirsiniz).")
            return
        desc = self.df[cols].describe().T
        desc["missing"] = [self.df[c].isna().sum() for c in cols]
        self._show_df_in_text(desc, self.txt_desc)

    # ------------------------- Sekme: Frekans -------------------------
    def _make_tab_frequencies(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Frekans")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Kategorik değişken:").pack(side=tk.LEFT)
        self.combo_freq = ttk.Combobox(top, values=[], width=40)
        self.combo_freq.pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Çalıştır", command=self.run_frequencies).pack(side=tk.LEFT)

        self.txt_freq = tk.Text(frame, wrap=tk.NONE)
        self.txt_freq.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_frequencies(self):
        if self.df is None:
            return
        col = self._get_selected_in_combobox(self.combo_freq, numeric=False)
        if not col:
            messagebox.showwarning("Uyarı", "Bir kategorik değişken seçin.")
            return
        vc = self.df[col].value_counts(dropna=False)
        pct = vc / vc.sum() * 100
        out = pd.DataFrame({"frekans": vc, "%": pct.round(2)})
        self._show_df_in_text(out, self.txt_freq)

    # ------------------------- Sekme: Çapraz Tablo -------------------------
    def _make_tab_crosstab(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Çapraz Tablo")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Satır (kat):").pack(side=tk.LEFT)
        self.combo_xtab_r = ttk.Combobox(top, values=[], width=25)
        self.combo_xtab_r.pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="Sütun (kat):").pack(side=tk.LEFT)
        self.combo_xtab_c = ttk.Combobox(top, values=[], width=25)
        self.combo_xtab_c.pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Çalıştır", command=self.run_crosstab).pack(side=tk.LEFT)

        self.txt_xtab = tk.Text(frame, wrap=tk.NONE)
        self.txt_xtab.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_crosstab(self):
        if self.df is None:
            return
        r = self._get_selected_in_combobox(self.combo_xtab_r, numeric=False)
        c = self._get_selected_in_combobox(self.combo_xtab_c, numeric=False)
        if not r or not c:
            messagebox.showwarning("Uyarı", "Satır ve sütun için kategorik değişken seçin.")
            return
        ct = pd.crosstab(self.df[r], self.df[c], dropna=False)
        chi2, p, dof, exp = stats.chi2_contingency(ct.fillna(0))
        out = []
        out.append("Contingency Table:" + text_from_df(ct))        
        out.append(f"Ki-Kare: {chi2:.4f}, sd: {dof}, p-değeri: {p:.6f}")
        self._set_text(self.txt_xtab, "".join(out))

    # ------------------------- Sekme: t-Test -------------------------
    def _make_tab_ttest(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="t-Test")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Sürekli değişken (Y):").pack(side=tk.LEFT)
        self.combo_t_y = ttk.Combobox(top, values=[], width=25)
        self.combo_t_y.pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="Grup (2 seviye, kat):").pack(side=tk.LEFT)
        self.combo_t_g = ttk.Combobox(top, values=[], width=25)
        self.combo_t_g.pack(side=tk.LEFT, padx=5)

        self.var_welch = tk.BooleanVar(value=True)
        ttk.Checkbutton(top, text="Welch (eşit varyans varsayma)", variable=self.var_welch).pack(side=tk.LEFT, padx=10)

        ttk.Button(top, text="Çalıştır", command=self.run_ttest).pack(side=tk.LEFT)

        self.txt_t = tk.Text(frame, wrap=tk.NONE)
        self.txt_t.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_ttest(self):
        if self.df is None:
            return
        y = self._get_selected_in_combobox(self.combo_t_y, numeric=True)
        g = self._get_selected_in_combobox(self.combo_t_g, numeric=False)
        if not y or not g:
            messagebox.showwarning("Uyarı", "Sürekli değişken (Y) ve 2 seviyeli grup seçin.")
            return
        levels = ensure_levels(self.df, g, 2)[:2]
        a = self.df[self.df[g] == levels[0]][y].dropna()
        b = self.df[self.df[g] == levels[1]][y].dropna()
        equal_var = not self.var_welch.get()
        t, p = stats.ttest_ind(a, b, equal_var=equal_var)
        out = [
            f"Gruplar: {levels[0]} (n={len(a)}) vs {levels[1]} (n={len(b)})",
            f"Ortalamalar: {a.mean():.4f} vs {b.mean():.4f}",
            f"t = {t:.4f}, p = {p:.6f} (equal_var={equal_var})",
        ]
        self._set_text(self.txt_t, "".join(out))

    # ------------------------- Sekme: ANOVA -------------------------
    def _make_tab_anova(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="ANOVA")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Sürekli değişken (Y):").pack(side=tk.LEFT)
        self.combo_a_y = ttk.Combobox(top, values=[], width=25)
        self.combo_a_y.pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="Faktör (kat):").pack(side=tk.LEFT)
        self.combo_a_g = ttk.Combobox(top, values=[], width=25)
        self.combo_a_g.pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Çalıştır", command=self.run_anova).pack(side=tk.LEFT)

        self.txt_a = tk.Text(frame, wrap=tk.NONE)
        self.txt_a.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_anova(self):
        if self.df is None:
            return
        y = self._get_selected_in_combobox(self.combo_a_y, numeric=True)
        g = self._get_selected_in_combobox(self.combo_a_g, numeric=False)
        if not y or not g:
            messagebox.showwarning("Uyarı", "Y ve faktör (kategorik) seçin.")
            return
        try:
            model = smf.ols(f"Q('{y}') ~ C(Q('{g}'))", data=self.df).fit()
            table = sm.stats.anova_lm(model, typ=2)
            self._show_df_in_text(table, self.txt_a)
        except Exception as e:
            messagebox.showerror("Hata", f"ANOVA hesaplanamadı:{e}")

    # ------------------------- Sekme: Korelasyon -------------------------
    def _make_tab_corr(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Korelasyon")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Sayısal değişken(ler):").pack(side=tk.LEFT)
        self.combo_corr = ttk.Combobox(top, values=[], width=40)
        self.combo_corr.pack(side=tk.LEFT, padx=5)

        self.var_spearman = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Spearman (varsayılan Pearson)", variable=self.var_spearman).pack(side=tk.LEFT, padx=10)

        ttk.Button(top, text="Çalıştır", command=self.run_corr).pack(side=tk.LEFT)

        self.txt_corr = tk.Text(frame, wrap=tk.NONE)
        self.txt_corr.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_corr(self):
        if self.df is None:
            return
        cols = self._get_selected_in_combobox(self.combo_corr, numeric=True, allow_multi=True)
        if not cols or len(cols) < 2:
            messagebox.showwarning("Uyarı", "En az iki sayısal değişken seçin.")
            return
        data = self.df[cols].dropna()
        corr = data.corr(method='spearman') if self.var_spearman.get() else data.corr()
        self._show_df_in_text(corr, self.txt_corr)

    # ------------------------- Sekme: Regresyon -------------------------
    def _make_tab_regression(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Regresyon")

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(top, text="Bağımlı (Y, sayısal):").pack(side=tk.LEFT)
        self.combo_r_y = ttk.Combobox(top, values=[], width=25)
        self.combo_r_y.pack(side=tk.LEFT, padx=5)

        ttk.Label(top, text="Bağımsız(lar) X (virgülle):").pack(side=tk.LEFT)
        self.combo_r_x = ttk.Combobox(top, values=[], width=40)
        self.combo_r_x.pack(side=tk.LEFT, padx=5)

        ttk.Button(top, text="Çalıştır", command=self.run_regression).pack(side=tk.LEFT)

        self.txt_r = tk.Text(frame, wrap=tk.NONE)
        self.txt_r.pack(fill=tk.BOTH, expand=True)
        return frame

    def run_regression(self):
        if self.df is None:
            return
        y = self._get_selected_in_combobox(self.combo_r_y, numeric=True)
        xs = self._get_selected_in_combobox(self.combo_r_x, numeric=True, allow_multi=True)
        if not y or not xs:
            messagebox.showwarning("Uyarı", "Y ve en az bir X seçin.")
            return
        try:
            formula = f"Q('{y}') ~ " + " + ".join([f"Q('{x}')" for x in xs])
            model = smf.ols(formula, data=self.df).fit()
            self._set_text(self.txt_r, model.summary().as_text())
        except Exception as e:
            messagebox.showerror("Hata", f"Regresyon kurulamadı:{e}")

    # ------------------------- Sekme: Grafikler -------------------------
    def _make_tab_plots(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Grafikler")

        ctrl = ttk.Frame(frame)
        ctrl.pack(fill=tk.X, padx=10, pady=10)

        self.plot_kind = tk.StringVar(value="Histogram")
        ttk.Label(ctrl, text="Grafik Türü:").pack(side=tk.LEFT)
        cmb_kind = ttk.Combobox(ctrl, textvariable=self.plot_kind, values=["Histogram", "Kutu", "Sütun", "Saçılım"], width=12)
        cmb_kind.pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl, text="Değişken 1:").pack(side=tk.LEFT)
        self.combo_p_1 = ttk.Combobox(ctrl, values=[], width=20)
        self.combo_p_1.pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl, text="Değişken 2 (opsiyonel):").pack(side=tk.LEFT)
        self.combo_p_2 = ttk.Combobox(ctrl, values=[], width=20)
        self.combo_p_2.pack(side=tk.LEFT, padx=5)

        ttk.Button(ctrl, text="Çiz", command=self.run_plot).pack(side=tk.LEFT, padx=5)

        # Matplotlib Canvas
        self.fig = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        return frame

    def run_plot(self):
        if self.df is None:
            return
        kind = self.plot_kind.get()
        v1 = self.combo_p_1.get().strip()
        v2 = self.combo_p_2.get().strip()
        self.ax.clear()
        try:
            if kind == "Histogram":
                if not v1:
                    raise ValueError("Histogram için sayısal bir değişken seçin.")
                s = pd.to_numeric(self.df[v1], errors='coerce').dropna()
                self.ax.hist(s, bins=20)
                self.ax.set_xlabel(v1); self.ax.set_ylabel("Frekans"); self.ax.set_title("Histogram")

            elif kind == "Kutu":
                if not v1:
                    raise ValueError("Kutu grafiği için sayısal bir değişken seçin.")
                s = pd.to_numeric(self.df[v1], errors='coerce').dropna()
                self.ax.boxplot(s, vert=True)
                self.ax.set_xticks([1]); self.ax.set_xticklabels([v1])
                self.ax.set_title("Kutu Grafiği")

            elif kind == "Sütun":
                if not v1:
                    raise ValueError("Sütun grafiği için kategorik bir değişken seçin.")
                vc = self.df[v1].value_counts(dropna=False)
                self.ax.bar(vc.index.astype(str), vc.values)
                self.ax.set_xlabel(v1); self.ax.set_ylabel("Frekans"); self.ax.set_title("Sütun Grafiği")
                self.ax.tick_params(axis='x', rotation=45)

            elif kind == "Saçılım":
                if not (v1 and v2):
                    raise ValueError("Saçılım için iki sayısal değişken seçin.")
                x = pd.to_numeric(self.df[v1], errors='coerce')
                y = pd.to_numeric(self.df[v2], errors='coerce')
                m = (~x.isna()) & (~y.isna())
                x, y = x[m], y[m]
                self.ax.scatter(x, y)
                # Basit regresyon çizgisi
                if len(x) >= 2:
                    slope, intercept, r, p, se = stats.linregress(x, y)
                    xx = np.linspace(x.min(), x.max(), 100)
                    yy = slope * xx + intercept
                    self.ax.plot(xx, yy)
                    self.ax.legend([f"y = {slope:.3f}x + {intercept:.3f} (R²≈{r**2:.3f})"])
                self.ax.set_xlabel(v1); self.ax.set_ylabel(v2); self.ax.set_title("Saçılım Grafiği")
        except Exception as e:
            messagebox.showerror("Hata", str(e))
        finally:
            self.canvas.draw()

    # ------------------------- Ortak yardımcılar -------------------------
    def _show_df_in_text(self, df: pd.DataFrame, txt: tk.Text):
        txt.delete("1.0", tk.END)
        txt.insert(tk.END, text_from_df(df))

    def _set_text(self, widget: tk.Text, s: str):
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, s)

    def _get_selected_in_combobox(self, combo: ttk.Combobox, numeric: bool = True, allow_multi: bool = False):
        raw = combo.get().strip()
        if not raw:
            return [] if allow_multi else ""
        parts = [p.strip() for p in raw.split(',')] if allow_multi else [raw]
        # yalnızca gerçekten var olan sütunları geçir
        ok = [p for p in parts if p in self.df.columns]
        return ok if allow_multi else (ok[0] if ok else "")

    def populate_combos(self):
        # Tüm analiz sekmelerindeki combobox'lara değişkenleri bas
        num_vals = self.numeric_cols
        cat_vals = self.categorical_cols

        for cb in [self.combo_desc, self.combo_corr, self.combo_r_x]:
            cb.config(values=num_vals)
        for cb in [self.combo_t_y, self.combo_a_y, self.combo_r_y]:
            cb.config(values=num_vals)
        for cb in [self.combo_freq, self.combo_xtab_r, self.combo_xtab_c, self.combo_t_g, self.combo_a_g]:
            cb.config(values=cat_vals)
        # plot
        self.combo_p_1.config(values=list(self.df.columns))
        self.combo_p_2.config(values=list(self.df.columns))


if __name__ == "__main__":
    app = MiniSPSSApp()
    app.mainloop()

# =========================  Meta-Analiz Eklentisi  =========================
# Bu bölüm, çalışmalardan alınan etki büyüklüklerini (yi) ve varyanslarını (vi) birleştirir.
# Modlar:
#  1) Hazır yi/vi sütunları
#  2) SMD (Hedges g): m1, sd1, n1, m2, sd2, n2 -> yi, vi
#  3) Log OR: 2x2 tablo a,b,c,d -> yi, vi

from math import sqrt

class MiniSPSSApp(MiniSPSSApp):  # mevcut sınıfı genişletiyoruz
    def _make_tab_meta(self):
        frame = ttk.Frame(self.tabs)
        self.tabs.add(frame, text="Meta-Analiz")

        # Üst kontrol şeridi
        ctrl = ttk.Frame(frame)
        ctrl.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(ctrl, text="Mod:").pack(side=tk.LEFT)
        self.meta_mode = tk.StringVar(value="yi/vi")
        cmb_mode = ttk.Combobox(ctrl, textvariable=self.meta_mode, values=["yi/vi", "SMD (Hedges g)", "Log OR"], width=18)
        cmb_mode.pack(side=tk.LEFT, padx=5)

        ttk.Button(ctrl, text="Hesapla", command=self.meta_calculate).pack(side=tk.LEFT, padx=(10,5))
        ttk.Button(ctrl, text="Forest", command=self.meta_forest).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="Funnel", command=self.meta_funnel).pack(side=tk.LEFT, padx=5)

        # Alan eşleştirme paneli
        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X, padx=10, pady=(0,10))

        # Satır 1: Çalışma etiketi
        ttk.Label(grid, text="Çalışma Adı (opsiyonel):").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.meta_study = ttk.Combobox(grid, values=[], width=25)
        self.meta_study.grid(row=0, column=1, sticky="w", padx=5)

        # Satır 2: yi/vi
        ttk.Label(grid, text="yi (etki)").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.meta_yi = ttk.Combobox(grid, values=[], width=25)
        self.meta_yi.grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(grid, text="vi (varyans)").grid(row=1, column=2, sticky="w", padx=5, pady=3)
        self.meta_vi = ttk.Combobox(grid, values=[], width=25)
        self.meta_vi.grid(row=1, column=3, sticky="w", padx=5)

        # Satır 3: SMD alanları
        ttk.Label(grid, text="m1, sd1, n1").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.meta_m1 = ttk.Combobox(grid, values=[], width=25); self.meta_m1.grid(row=2, column=1, sticky="w", padx=5)
        self.meta_sd1 = ttk.Combobox(grid, values=[], width=25); self.meta_sd1.grid(row=2, column=2, sticky="w", padx=5)
        self.meta_n1 = ttk.Combobox(grid, values=[], width=25); self.meta_n1.grid(row=2, column=3, sticky="w", padx=5)

        ttk.Label(grid, text="m2, sd2, n2").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.meta_m2 = ttk.Combobox(grid, values=[], width=25); self.meta_m2.grid(row=3, column=1, sticky="w", padx=5)
        self.meta_sd2 = ttk.Combobox(grid, values=[], width=25); self.meta_sd2.grid(row=3, column=2, sticky="w", padx=5)
        self.meta_n2 = ttk.Combobox(grid, values=[], width=25); self.meta_n2.grid(row=3, column=3, sticky="w", padx=5)

        # Satır 4: 2x2 tablo alanları
        ttk.Label(grid, text="a (olay1)").grid(row=4, column=0, sticky="w", padx=5, pady=3)
        self.meta_a = ttk.Combobox(grid, values=[], width=25); self.meta_a.grid(row=4, column=1, sticky="w", padx=5)
        ttk.Label(grid, text="b (olaysız1)").grid(row=4, column=2, sticky="w", padx=5)
        self.meta_b = ttk.Combobox(grid, values=[], width=25); self.meta_b.grid(row=4, column=3, sticky="w", padx=5)

        ttk.Label(grid, text="c (olay2)").grid(row=5, column=0, sticky="w", padx=5, pady=3)
        self.meta_c = ttk.Combobox(grid, values=[], width=25); self.meta_c.grid(row=5, column=1, sticky="w", padx=5)
        ttk.Label(grid, text="d (olaysız2)").grid(row=5, column=2, sticky="w", padx=5)
        self.meta_d = ttk.Combobox(grid, values=[], width=25); self.meta_d.grid(row=5, column=3, sticky="w", padx=5)

        # Sonuç metni + şekil alanı
        self.txt_meta = tk.Text(frame, wrap=tk.NONE, height=14)
        self.txt_meta.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Şekil alanı
        self.fig_meta = plt.Figure(figsize=(6.5, 3.8), dpi=100)
        self.ax_meta = self.fig_meta.add_subplot(111)
        self.canvas_meta = FigureCanvasTkAgg(self.fig_meta, master=frame)
        self.canvas_meta.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        return frame

    # populate
    def populate_combos(self):
        super().populate_combos()
        if self.df is None:
            return
        cols = list(self.df.columns)
        for cb in [self.meta_study, self.meta_yi, self.meta_vi, self.meta_m1, self.meta_sd1, self.meta_n1,
                   self.meta_m2, self.meta_sd2, self.meta_n2, self.meta_a, self.meta_b, self.meta_c, self.meta_d]:
            try:
                cb.config(values=cols)
            except Exception:
                pass

    # Hesaplama akışı
    def meta_calculate(self):
        if self.df is None:
            messagebox.showwarning("Uyarı", "Önce bir veri dosyası yükleyin.")
            return
        mode = self.meta_mode.get()
        try:
            if mode == "yi/vi":
                yi = pd.to_numeric(self.df[self.meta_yi.get()], errors='coerce')
                vi = pd.to_numeric(self.df[self.meta_vi.get()], errors='coerce')
            elif mode == "SMD (Hedges g)":
                yi, vi = self._meta_from_smd()
            else:  # Log OR
                yi, vi = self._meta_from_log_or()
            mask = (~yi.isna()) & (~vi.isna()) & (vi > 0)
            yi, vi = yi[mask], vi[mask]
            if len(yi) < 2:
                raise ValueError("En az iki çalışmanın geçerli yi/vi değeri olmalı.")
            fixed = self._fixed_effect(yi, vi)
            random = self._random_effect(yi, vi)
            egger = self._egger_test(yi, vi)

            out = []
            out.append(f"Kayıt sayısı: {len(yi)}")
            out.append("\n[Fixed-Effect]")
            out.append(self._fmt_pool(fixed))
            out.append("\n[Random-Effects (DerSimonian-Laird)]")
            out.append(self._fmt_pool(random))
            out.append("\n[Egger Publication Bias Test]")
            out.append(f"Intercept t={egger['t']:.3f}, p={egger['p']:.4f}")
            self._set_text(self.txt_meta, "\n".join(out))

            # Son hesaplamaları tut
            self._meta_cache = {
                'yi': yi, 'vi': vi,
                'fixed': fixed, 'random': random, 'egger': egger,
                'study': self.df[self.meta_study.get()] if self.meta_study.get() in self.df.columns else pd.Series([f"Study {i+1}" for i in range(len(yi))], index=yi.index)
            }
        except Exception as e:
            messagebox.showerror("Meta-Analiz Hatası", str(e))

    def _fmt_pool(self, d):
        return (f"Etki = {d['theta']:.4f}  (SE={d['se']:.4f})  95% CI: [{d['lcl']:.4f}, {d['ucl']:.4f}]\n"
                f"Heterojenlik: Q={d['Q']:.3f}, df={d['df']}, p={d['Q_p']:.4f}, I²={d['I2']:.1f}%")

    # Forest plot
    def meta_forest(self):
        if not hasattr(self, '_meta_cache'):
            messagebox.showinfo("Bilgi", "Önce 'Hesapla' deyin.")
            return
        yi = self._meta_cache['yi']; vi = self._meta_cache['vi']
        study = self._meta_cache['study']
        re = self._meta_cache['random']
        se = np.sqrt(vi)
        lcl = yi - 1.96*se
        ucl = yi + 1.96*se

        self.ax_meta.clear()
        order = np.arange(len(yi))[::-1]
        self.ax_meta.errorbar(yi.values, order, xerr=1.96*se.values, fmt='o')
        self.ax_meta.axvline(re['theta'], linestyle='--')
        self.ax_meta.set_yticks(order)
        labels = [str(study.iloc[i]) for i in order]
        self.ax_meta.set_yticklabels(labels)
        self.ax_meta.set_xlabel('Etki (yi)')
        self.ax_meta.set_title('Forest Plot (RE)')
        self.canvas_meta.draw()

    # Funnel plot
    def meta_funnel(self):
        if not hasattr(self, '_meta_cache'):
            messagebox.showinfo("Bilgi", "Önce 'Hesapla' deyin.")
            return
        yi = self._meta_cache['yi']; vi = self._meta_cache['vi']
        se = np.sqrt(vi)
        self.ax_meta.clear()
        self.ax_meta.scatter(yi, se)
        self.ax_meta.invert_yaxis()
        self.ax_meta.set_xlabel('Etki (yi)')
        self.ax_meta.set_ylabel('SE')
        self.ax_meta.set_title('Funnel Plot')
        self.canvas_meta.draw()

    # --- Yardımcı hesaplar ---
    def _fixed_effect(self, yi, vi):
        w = 1.0/vi
        theta = np.sum(w*yi)/np.sum(w)
        se = sqrt(1.0/np.sum(w))
        lcl, ucl = theta - 1.96*se, theta + 1.96*se
        Q = np.sum(w*(yi-theta)**2)
        df = len(yi)-1
        Q_p = 1 - stats.chi2.cdf(Q, df)
        I2 = max(0.0, (Q-df)/Q)*100 if Q>0 else 0.0
        return dict(theta=theta, se=se, lcl=lcl, ucl=ucl, Q=Q, df=df, Q_p=Q_p, I2=I2, tau2=0.0)

    def _random_effect(self, yi, vi):
        w = 1.0/vi
        theta_fixed = np.sum(w*yi)/np.sum(w)
        Q = np.sum(w*(yi-theta_fixed)**2)
        df = len(yi)-1
        c = np.sum(w) - np.sum(w**2)/np.sum(w)
        tau2 = max(0.0, (Q-df)/c)
        w_star = 1.0/(vi + tau2)
        theta = np.sum(w_star*yi)/np.sum(w_star)
        se = sqrt(1.0/np.sum(w_star))
        lcl, ucl = theta - 1.96*se, theta + 1.96*se
        Q_p = 1 - stats.chi2.cdf(Q, df)
        I2 = max(0.0, (Q-df)/Q)*100 if Q>0 else 0.0
        return dict(theta=theta, se=se, lcl=lcl, ucl=ucl, Q=Q, df=df, Q_p=Q_p, I2=I2, tau2=tau2)

    def _egger_test(self, yi, vi):
        se = np.sqrt(vi)
        precision = 1.0/se
        sn = yi/se  # standard normal deviate
        X = sm.add_constant(precision)
        model = sm.OLS(sn, X).fit()
        t_val = model.tvalues[0]
        p_val = model.pvalues[0]
        return {'t': float(t_val), 'p': float(p_val)}

    # --- Dönüşümler ---
    def _meta_from_smd(self):
        req = [self.meta_m1.get(), self.meta_sd1.get(), self.meta_n1.get(),
               self.meta_m2.get(), self.meta_sd2.get(), self.meta_n2.get()]
        if any(r not in self.df.columns for r in req):
            raise ValueError("SMD için m1, sd1, n1, m2, sd2, n2 sütunlarını seçin.")
        m1 = pd.to_numeric(self.df[self.meta_m1.get()], errors='coerce')
        sd1 = pd.to_numeric(self.df[self.meta_sd1.get()], errors='coerce')
        n1 = pd.to_numeric(self.df[self.meta_n1.get()], errors='coerce')
        m2 = pd.to_numeric(self.df[self.meta_m2.get()], errors='coerce')
        sd2 = pd.to_numeric(self.df[self.meta_sd2.get()], errors='coerce')
        n2 = pd.to_numeric(self.df[self.meta_n2.get()], errors='coerce')
        sp = np.sqrt(((n1-1)*sd1**2 + (n2-1)*sd2**2) / (n1+n2-2))
        d = (m1 - m2) / sp
        J = 1 - (3/(4*(n1+n2)-9))
        g = J * d
        vi = ((n1+n2)/(n1*n2)) + (g**2/(2*(n1+n2-2)))
        return g, vi

    def _meta_from_log_or(self):
        req = [self.meta_a.get(), self.meta_b.get(), self.meta_c.get(), self.meta_d.get()]
        if any(r not in self.df.columns for r in req):
            raise ValueError("Log OR için a, b, c, d sütunlarını seçin.")
        a = pd.to_numeric(self.df[self.meta_a.get()], errors='coerce')
        b = pd.to_numeric(self.df[self.meta_b.get()], errors='coerce')
        c = pd.to_numeric(self.df[self.meta_c.get()], errors='coerce')
        d = pd.to_numeric(self.df[self.meta_d.get()], errors='coerce')
        # H continuity correction (0 hücreler için 0.5 ekleme)
        a = a.replace(0, 0.5); b = b.replace(0, 0.5); c = c.replace(0, 0.5); d = d.replace(0, 0.5)
        yi = np.log((a*d)/(b*c))
        vi = (1/a) + (1/b) + (1/c) + (1/d)
        return yi, vi

