import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import plotly.graph_objects as go

# Setup Path Modular
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from function.kalkulator import hitung_produksi, hitung_opex, hitung_depresiasi, hitung_cashflow_makro
from utils.exporter import convert_df_to_excel

# Konfigurasi Halaman Web Sesuai Standar Streamlit Terbaru
st.set_page_config(page_title="Simulasi Keekonomian Lapangan", layout="wide")

# Custom CSS Layout
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        border-left: 5px solid #1F4E78;
        margin-bottom: 15px;
    }
    .metric-title { color: #6c757d; font-size: 13px; font-weight: bold; margin-bottom: 4px; }
    .metric-value { color: #1F4E78; font-size: 22px; font-weight: 900; }
    </style>
""", unsafe_allow_html=True)

st.title("Aplikasi Optimasi Keekonomian Lapangan Migas")
st.markdown("---")

# --- INISIALISASI SESSION STATE
if "hitung_aktif" not in st.session_state:
    st.session_state.hitung_aktif = False

# --- IDENTITAS ---
st.sidebar.subheader("Mada Soneta")
st.sidebar.subheader("123230184")
st.sidebar.markdown("---")

# --- PANEL SIDEBAR KIRI ---
st.sidebar.header("⚙️ 1. Parameter Reservoir")
cadangan = st.sidebar.number_input("Total Cadangan Minyak (Mbbl)", value=4320.0, step=100.0)
jangka_waktu = st.sidebar.number_input("Jangka Waktu Proyek (Tahun)", min_value=1, max_value=30, value=10)

st.sidebar.subheader("Data Produksi Dinamis")
num_manual = st.sidebar.number_input("Berapa Tahun Input Manual?", min_value=1, max_value=10, value=4)
manual_prods = []
default_prods = [175.0, 201.0, 217.0, 198.0]

for i in range(num_manual):
    def_val = default_prods[i] if i < len(default_prods) else 100.0
    val = st.sidebar.number_input(f"Produksi Tahun ke-{i+1} (Mbbl)", value=def_val)
    manual_prods.append(val)
    
decline_rate = st.sidebar.number_input("Decline Rate mulai Tahun berikutnya (%)", value=3.0, step=0.5) / 100

st.sidebar.header("💰 2. Parameter Finansial")
harga_minyak = st.sidebar.number_input("Harga Minyak ($/bbl)", value=32.0, step=1.0)
capital = st.sidebar.number_input("Investasi Capital ($M)", value=13000.0, step=1000.0)
non_capital = st.sidebar.number_input("Investasi Non-Capital ($M)", value=8000.0, step=1000.0)

st.sidebar.subheader("Pengaturan Opex")
opex_dasar = st.sidebar.number_input("Opex Dasar ($M)", value=180.0, step=10.0)
durasi_flat = st.sidebar.number_input("Durasi Opex Flat (Tahun)", min_value=0, max_value=10, value=3)
eskalasi = st.sidebar.number_input("Kenaikan Opex per Tahun (%)", value=2.5, step=0.1) / 100

st.sidebar.subheader("Pajak & Depresiasi")
metode_dep = st.sidebar.selectbox("Metode Depresiasi", ["Straight Line", "Double Declining Balance"])
umur_depresiasi = st.sidebar.number_input("Umur Depresiasi (Tahun)", min_value=1, value=10)
pajak_persen = st.sidebar.number_input("Pajak (%)", value=51.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("📝 Administrasi Laporan")
input_studi_kasus = st.sidebar.text_input("Nama Lapangan / Studi Kasus:", value=" ")

# Pemicu Kalkulasi
if st.sidebar.button("Hitung NCF Sekarang", type="primary"):
    st.session_state.hitung_aktif = True

# --- PROSES DAN TAMPILKAN DASHBOARD UTAMA ---
if st.session_state.hitung_aktif:
    # Eksekusi kalkulasi melalui modul kalkulator
    arr_produksi, warning_cadangan, kumulatif_prod = hitung_produksi(cadangan, manual_prods, decline_rate, jangka_waktu)
    arr_opex = hitung_opex(opex_dasar, durasi_flat, eskalasi, jangka_waktu)
    arr_depresiasi = hitung_depresiasi(metode_dep, capital, umur_depresiasi, jangka_waktu)
    df_cashflow = hitung_cashflow_makro(jangka_waktu, arr_produksi, harga_minyak, capital, non_capital, arr_opex, arr_depresiasi, pajak_persen)

    if warning_cadangan:
        st.warning(f"⚠️ **Peringatan Reservoir:** Capaian kumulatif produksi menyentuh batas maksimum cadangan reservoir ({cadangan:,.2f} Mbbl).")
    else:
        st.success(f"✅ Kumulatif produksi ({kumulatif_prod:,.2f} Mbbl) masih dalam batas aman cadangan ({cadangan:,.2f} Mbbl)")

    # Siapkan data untuk kartu ringkasan metrik
    tot_income = df_cashflow["Income ($M)"].sum()
    tot_tax = df_cashflow["Tax ($M)"].sum()
    tot_ncf_tahunan = df_cashflow[df_cashflow.index > 0]["NCF ($M)"].sum()
    kumulatif_ncf_akhir = df_cashflow["NCF Undiscounted ($M)"].iloc[-1]

    # Presentasi 4 Kartu Metrik
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="metric-card"><div class="metric-title">Total Income</div><div class="metric-value">${tot_income:,.2f} M</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-card"><div class="metric-title">Total Tax</div><div class="metric-value">${tot_tax:,.2f} M</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-card"><div class="metric-title">Total NCF Tahunan</div><div class="metric-value">${tot_ncf_tahunan:,.2f} M</div></div>', unsafe_allow_html=True)
    
    judul_kartu_4 = f"Kumulatif NCF (Thn ke-{jangka_waktu})"
    c4.markdown(f'<div class="metric-card" style="border-left: 5px solid #28a745;"><div class="metric-title">{judul_kartu_4}</div><div class="metric-value" style="color: #28a745;">${kumulatif_ncf_akhir:,.2f} M</div></div>', unsafe_allow_html=True)

    # --- GRAFIK Aliran ---
    tab1, tab2 = st.tabs(["📈 Profil Produksi Lapangan", "💰 Aliran Arus Kas (NCF Tahunan)"])
    df_active_plot = df_cashflow[df_cashflow.index > 0]
    
    with tab1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df_active_plot.index, y=df_active_plot["Produksi (Mbbl)"], mode='lines+markers', name='Produksi (Mbbl)', line=dict(color='#E11D48', width=3)))
        fig1.update_layout(xaxis_title="Tahun", yaxis_title="Volume Produksi (Mbbl)", plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
        fig1.update_xaxes(showgrid=True, gridcolor='LightGray')
        fig1.update_yaxes(showgrid=True, gridcolor='LightGray')
        st.plotly_chart(fig1, width='stretch')
        
    with tab2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_active_plot.index, y=df_active_plot["NCF ($M)"], mode='lines+markers', name='NCF Bersih', line=dict(color='#1E40AF', width=3)))
        fig2.update_layout(xaxis_title="Tahun", yaxis_title="Nilai Arus Kas Bersih ($M)", plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
        fig2.update_xaxes(showgrid=True, gridcolor='LightGray')
        fig2.update_yaxes(showgrid=True, gridcolor='LightGray')
        st.plotly_chart(fig2, width='stretch')

    # --- TABEL KEEKONOMIAN PSC
    st.subheader("📑 Tabel Aplikasi Perhitungan Keekonomian Lapangan Migas")
    
    df_display = df_cashflow.reset_index()
    df_display["Tahun"] = df_display["Tahun"].astype(str)
    
    row_total = {
        "Tahun": "Total",
        "Produksi (Mbbl)": df_display["Produksi (Mbbl)"].sum(),
        "Income ($M)": df_display["Income ($M)"].sum(),
        "Capital ($M)": df_display["Capital ($M)"].sum(),
        "Investasi Non Capital ($M)": df_display["Investasi Non Capital ($M)"].sum(),
        "Opex ($M)": df_display[df_display["Tahun"] != "0"]["Opex ($M)"].sum(),
        "Di ($M)": df_display["Di ($M)"].sum(),
        "Taxable Income ($M)": df_display["Taxable Income ($M)"].sum(),
        "Tax ($M)": df_display["Tax ($M)"].sum(),
        "NCF ($M)": tot_ncf_tahunan,
        "NCF Undiscounted ($M)": np.nan
    }
    
    df_display = pd.concat([df_display, pd.DataFrame([row_total])], ignore_index=True)
    df_display.set_index("Tahun", inplace=True)
    
    st.dataframe(df_display.style.format("{:,.2f}", na_rep="-"), width='stretch')

    # --- UNDUH LAPORAN EXCEL ---
    st.markdown("---")
    st.subheader("Laporan Keekonomian Lapangan Migas")
    st.info(f" Laporan *{input_studi_kasus}* telah diproses dan siap untuk di unduh")
    
    excel_data = convert_df_to_excel(df_cashflow, input_studi_kasus)
    st.download_button(
        label=f"📥 Unduh Berkas Excel {input_studi_kasus} (.xlsx)",
        data=excel_data,
        file_name=f"Laporan PSC {input_studi_kasus.replace(' ', ' ')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("Silakan sesuaikan parameter terlebih dahulu untuk melihat hasil analisis")