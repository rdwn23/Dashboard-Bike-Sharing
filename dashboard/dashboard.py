from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Dashboard Bike Sharing", layout="wide")

BASE = Path(__file__).parent
SEASON_ORDER = ["Summer", "Spring", "Fall", "Winter"]
SUHU_ORDER = ["Dingin", "Sedang", "Panas"]
WAKTU_ORDER = ["Dini hari", "Pagi", "Siang", "Sore", "Malam"]
WAKTU_LABEL = {
    "Dini hari": "Dini hari\n(jam 0-5)",
    "Pagi": "Pagi\n(jam 6-9)",
    "Siang": "Siang\n(jam 10-15)",
    "Sore": "Sore\n(jam 16-19)",
    "Malam": "Malam\n(jam 20-23)",
}
SUHU_LABEL = {
    "Dingin": "Dingin\n(< 15 °C)",
    "Sedang": "Sedang\n(15-25 °C)",
    "Panas": "Panas\n(> 25 °C)",
}
HARI_LABEL = {"Working Day": "Hari kerja", "Non-Working Day": "Hari libur"}
HARI_COLOR = {"Working Day": "#1f77b4", "Non-Working Day": "#ff7f0e"}


@st.cache_data
def load_data():
    return pd.read_csv(BASE / "main_data.csv", parse_dates=["dteday"])


main_df = load_data()

# ---------------- Sidebar ----------------
st.sidebar.header("Filter")
min_date = main_df["dteday"].min().date()
max_date = main_df["dteday"].max().date()
date_range = st.sidebar.date_input(
    "Rentang tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if len(date_range) != 2:
    st.info("Pilih tanggal awal dan tanggal akhir pada filter di sidebar.")
    st.stop()

start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
hour_f = main_df[(main_df["dteday"] >= start) & (main_df["dteday"] <= end)]

if hour_f.empty:
    st.warning("Tidak ada data pada rentang tanggal tersebut.")
    st.stop()

# Data harian: satu baris per tanggal (cnt_day berulang di setiap jam)
day_f = hour_f.drop_duplicates("dteday")

# ---------------- Header ----------------
st.title("Dashboard Analisis Penyewaan Sepeda (Bike Sharing)")
st.caption("Data penyewaan sepeda 2011-2012. Satuan: jumlah penyewaan.")

c1, c2, c3 = st.columns(3)
c1.metric("Total Penyewaan", f"{day_f['cnt_day'].sum():,}")
c2.metric("Jumlah Hari", f"{day_f.shape[0]:,}")
c3.metric("Rata-rata Penyewaan per Hari", f"{day_f['cnt_day'].mean():,.0f}")

# ---------------- Pertanyaan 1 ----------------
st.header("Pertanyaan 1: Rata-rata Penyewaan Harian per Musim")
st.write(
    "Pada musim apa rata-rata jumlah penyewaan sepeda harian paling tinggi dan paling rendah, "
    "dan berapa selisih rata-ratanya?"
)

season_df = (
    day_f.groupby("season")["cnt_day"].mean().reindex(SEASON_ORDER).dropna().sort_values(ascending=False)
)
colors = [
    "#1f77b4" if s == season_df.idxmax() else "#d62728" if s == season_df.idxmin() else "#c7c7c7"
    for s in season_df.index
]

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(season_df.index, season_df.values, color=colors)
for i, v in enumerate(season_df.values):
    ax.text(i, v + season_df.max() * 0.01, f"{v:,.0f}", ha="center", fontsize=10)
ax.set_title("Rata-rata Penyewaan Sepeda Harian per Musim (2011-2012)")
ax.set_xlabel("Musim")
ax.set_ylabel("Rata-rata Jumlah Penyewaan per Hari")
ax.set_ylim(0, season_df.max() * 1.15)
st.pyplot(fig)

if len(season_df) > 1:
    st.write(
        f"Musim tertinggi: **{season_df.idxmax()}** ({season_df.max():,.0f}), "
        f"terendah: **{season_df.idxmin()}** ({season_df.min():,.0f}), "
        f"selisih: **{season_df.max() - season_df.min():,.0f}** penyewaan per hari."
    )

# ---------------- Pertanyaan 2 ----------------
st.header("Pertanyaan 2: Rata-rata Penyewaan per Jam, Hari Kerja vs Hari Libur")
st.write(
    "Pada jam berapa rata-rata jumlah penyewaan sepeda per jam paling tinggi pada hari kerja "
    "dibandingkan hari libur, dan berapa selisih rata-ratanya?"
)

hourly_df = hour_f.pivot_table(index="hr", columns="workingday", values="cnt", aggfunc="mean")

fig, ax = plt.subplots(figsize=(12, 4.5))

for col in hourly_df.columns:
    ax.plot(hourly_df.index, hourly_df[col], marker="o", color=HARI_COLOR[col], label=HARI_LABEL[col])

for col in hourly_df.columns:
    peak_hr = hourly_df[col].idxmax()
    peak_val = hourly_df[col].max()
    if col == "Working Day":
        text_pos = (peak_hr + 1.5, peak_val + 15)
        ha = "left"
    else:
        text_pos = (peak_hr, peak_val + 90)
        ha = "center"
    ax.annotate(
        f"Puncak {HARI_LABEL[col].lower()}\njam {peak_hr} ({peak_val:,.0f})",
        xy=(peak_hr, peak_val),
        xytext=text_pos,
        ha=ha,
        arrowprops=dict(arrowstyle="->"),
        fontsize=9,
    )

ax.set_title("Rata-rata Penyewaan Sepeda per Jam: Hari Kerja vs Hari Libur (2011-2012)")
ax.set_xlabel("Jam (0-23)")
ax.set_ylabel("Rata-rata Jumlah Penyewaan per Jam")
ax.set_xticks(range(0, 24))
ax.set_ylim(0, hourly_df.max().max() * 1.25)
ax.legend()
st.pyplot(fig)

peaks = [f"{HARI_LABEL[c]}: jam **{hourly_df[c].idxmax()}** ({hourly_df[c].max():,.0f})" for c in hourly_df.columns]
st.write("Puncak penyewaan per jam. " + "; ".join(peaks) + ".")

# ---------------- Analisis lanjutan ----------------
st.header("Analisis Lanjutan: Binning Suhu dan Pengelompokan Jam")
col_a, col_b = st.columns(2)

with col_a:
    suhu_df = day_f.groupby("kategori_suhu")["cnt_day"].mean().reindex(SUHU_ORDER).dropna()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar([SUHU_LABEL[k] for k in suhu_df.index], suhu_df.values, color="#1f77b4")
    for i, v in enumerate(suhu_df.values):
        ax.text(i, v + suhu_df.max() * 0.01, f"{v:,.0f}", ha="center", fontsize=10)
    ax.set_title("Rata-rata Penyewaan Harian per Kategori Suhu (2011-2012)")
    ax.set_xlabel("Kategori suhu")
    ax.set_ylabel("Rata-rata Jumlah Penyewaan per Hari")
    ax.set_ylim(0, suhu_df.max() * 1.15)
    st.pyplot(fig)

with col_b:
    waktu_df = (
        hour_f.pivot_table(index="kelompok_waktu", columns="workingday", values="cnt", aggfunc="mean")
        .reindex(WAKTU_ORDER)
        .dropna(how="all")
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    waktu_df.plot(kind="bar", ax=ax, color=[HARI_COLOR[c] for c in waktu_df.columns])
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", padding=3, fontsize=8)
    ax.set_xticklabels([WAKTU_LABEL[k] for k in waktu_df.index], rotation=0, fontsize=8)
    ax.set_title("Rata-rata Penyewaan per Jam pada Tiap Kelompok Waktu (2011-2012)")
    ax.set_xlabel("Kelompok waktu")
    ax.set_ylabel("Rata-rata Jumlah Penyewaan per Jam")
    ax.set_ylim(0, waktu_df.max().max() * 1.15)
    ax.legend([HARI_LABEL[c] for c in waktu_df.columns])
    st.pyplot(fig)