import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import openpyxl
import os

st.set_page_config(
    page_title="SIKERIS - Sistem Informasi Kekeringan dan Risiko Pertanian",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

EXCEL_PATH = 'MASTER_EWS_SLEMAN.xlsx'

@st.cache_data(ttl=1)
def load_master_data():
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name='MASTER_EWS_SLEMAN')
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        if 'Kecamatan' in df.columns and 'Kapanewon' not in df.columns:
            df.rename(columns={'Kecamatan': 'Kapanewon'}, inplace=True)
        return df
    else:
        return pd.DataFrame()

try:
    df_master = load_master_data()

    # -----------------------------------------------------------------------------
    # SIDEBAR NAVIGATION & LOGO BMKG EWS
    # -----------------------------------------------------------------------------
    if os.path.exists('logo_bmkg_ews.jpg'):
        st.sidebar.image('logo_bmkg_ews.jpg', use_container_width=True)
    elif os.path.exists('Adobe Express 2026-09-03 09.57.16.jpg'):
        st.sidebar.image('Adobe Express 2026-09-03 09.57.16.jpg', use_container_width=True)
    
    st.sidebar.markdown("<h2 style='text-align: center; color: #1F4E78;'>EWS KEKERINGAN SLEMAN</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    mode_aplikasi = st.sidebar.radio(
        "📌 **Pilih Mode Aplikasi:**", 
        [
            "📊 Monitoring Dashboard", 
            "🔮 Simulasi Real-Time (EWS & Prediksi 3 Bulan)", 
            "📥 Import Excel Harian Massal (17 Kapanewon)"
        ]
    )
    st.sidebar.markdown("---")

    BASE_PRODUKSI_KW_HA = 58.5 # Kw/Ha acuan rata-rata Sleman

    # -----------------------------------------------------------------------------
    # MODE 1: MONITORING DASHBOARD
    # -----------------------------------------------------------------------------
    if mode_aplikasi == "📊 Monitoring Dashboard":
        st.sidebar.subheader("🔍 Filter Control Panel")
        list_tahun = sorted(df_master['Tahun'].unique(), reverse=True)
        tahun_pilihan = st.sidebar.selectbox("📅 Pilih Tahun:", list_tahun, index=0)

        df_tahun = df_master[df_master['Tahun'] == tahun_pilihan]
        list_bulan = sorted(df_tahun['Bulan'].unique(), reverse=True)
        bulan_pilihan = st.sidebar.selectbox("📆 Pilih Bulan:", list_bulan, index=0)

        data_aktif = df_master[(df_master['Tahun'] == tahun_pilihan) & (df_master['Bulan'] == bulan_pilihan)].copy()

        def calculate_prod_impact(row):
            hth = row['HTH']
            ch = row['CH']
            if hth > 44:
                impact_pct = -0.42 * hth - 12.5
                impact_pct = max(-85.0, round(impact_pct, 1))
            elif 30 < hth <= 44:
                impact_pct = round(-0.35 * hth - 5.0, 1)
            elif 21 <= hth <= 30:
                impact_pct = round(-0.15 * hth, 1)
            else:
                impact_pct = round(min(15.0, 0.05 * ch), 1)
            
            delta_kw = round((impact_pct / 100.0) * BASE_PRODUKSI_KW_HA, 2)
            est_prod = round(BASE_PRODUKSI_KW_HA + delta_kw, 2)
            return pd.Series([impact_pct, delta_kw, est_prod])

        data_aktif[['Anomali_Produksi (%)', 'Perubahan (Kw/Ha)', 'Est_Produksi (Kw/Ha)']] = data_aktif.apply(calculate_prod_impact, axis=1)

        st.title("🌾🌤️ SIKERIS - Sistem Informasi Kekeringan dan Risiko Pertanian")
        st.markdown(f"**Kabupaten Sleman | Monitoring Operasional Periode: Bulan {bulan_pilihan} - Tahun {tahun_pilihan}**")
        st.caption("Sistem Peringatan Dini Berbasis Data-Driven Klimatologi, Fixed Effects Logit, dan Machine Learning")
        st.markdown("---")

        total_awas = len(data_aktif[data_aktif['Status_EWS'].str.contains('AWAS', na=False)])
        total_siaga = len(data_aktif[data_aktif['Status_EWS'].str.contains('SIAGA', na=False)])
        total_waspada = len(data_aktif[data_aktif['Status_EWS'].str.contains('WASPADA', na=False)])
        total_aman = len(data_aktif[data_aktif['Status_EWS'].str.contains('AMAN', na=False)])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 AWAS / KRITIS", f"{total_awas} Kapanewon", delta="Tindakan Tanggap Darurat", delta_color="inverse")
        c2.metric("🟡 SIAGA", f"{total_siaga} Kapanewon", delta="Mobilisasi Pompa Air")
        c3.metric("🟢 WASPADA", f"{total_waspada} Kapanewon", delta="Pantau Cadangan Embung")
        c4.metric("⚪ AMAN / NORMAL", f"{total_aman} Kapanewon", delta="Kondisi Kondusif")

        st.markdown("---")
        st.subheader("📋 Status Peringatan Dini & Est. Perubahan Produksi (Kw/Ha)")
        
        col_tampil = ['Kapanewon', 'Tanggal', 'CH', 'HTH', 'CH30', 'Status_EWS', 'Anomali_Produksi (%)', 'Perubahan (Kw/Ha)', 'Est_Produksi (Kw/Ha)']
        df_tampil = data_aktif[col_tampil].reset_index(drop=True)
        
        st.dataframe(
            df_tampil.style.format({
                'CH': '{:.1f} mm',
                'CH30': '{:.1f} mm',
                'Anomali_Produksi (%)': '{:+.1f}%',
                'Perubahan (Kw/Ha)': '{:+.2f} Kw/Ha',
                'Est_Produksi (Kw/Ha)': '{:.2f} Kw/Ha'
            }), 
            use_container_width=True, 
            height=380
        )

        st.markdown("---")
        st.subheader("📈 Analisis Histori Tren & Ambang Batas Kritis (Threshold HTH >= 44 Hari)")
        
        kap_pilihan = st.selectbox("🎯 Pilih Kapanewon untuk Menganalisis Histori Tren:", sorted(df_master['Kapanewon'].unique()))
        
        df_kap = df_master[df_master['Kapanewon'] == kap_pilihan].sort_values('Tanggal')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_kap['Tanggal'],
            y=df_kap['CH'],
            name='Curah Hujan (mm)',
            marker_color='rgba(31, 78, 120, 0.6)',
            hoverinfo='none'
        ))

        fig.add_trace(go.Scatter(
            x=df_kap['Tanggal'],
            y=df_kap['HTH'],
            name='Hari Tanpa Hujan / HTH (Hari)',
            mode='lines',
            line=dict(color='crimson', width=2.0),
            hovertemplate='<b>Periode Bulan:</b> %{x|%b %Y}<br><b>Hari Tanpa Hujan (HTH):</b> %{y} Hari<extra></extra>'
        ))

        fig.add_hline(
            y=44, 
            line_dash="dash", 
            line_color="red", 
            annotation_text="Ambang Batas Kritis Youden Index (HTH = 44 Hari)", 
            annotation_position="top left"
        )

        fig.update_layout(
            title=f"Dinamika Klimatologi & Resiko Kekeringan di Kapanewon {kap_pilihan} (2015–2026)",
            xaxis_title="Periode Pengamatan (Bulan - Tahun)",
            yaxis_title="Nilai Indikator",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------------------------
    # MODE 2: SIMULASI REAL-TIME EWS (DENGAN PREDIKSI CH 3 BULAN & LUAS TANAM)
    # -----------------------------------------------------------------------------
    elif mode_aplikasi == "🔮 Simulasi Real-Time (EWS & Prediksi 3 Bulan)":
        st.title("🔮 Modul Simulasi Real-Time EWS & Decision Support System (DSS)")
        st.markdown("Gunakan modul ini untuk mensimulasikan peringatan dini kekeringan dan proyeksi dampak produksi berdasarkan kondisi HTH saat ini, prediksi curah hujan 3 bulan ke depan, serta estimasi luas tanam:")
        st.markdown("---")

        bulan_nama = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

        with st.form("form_simulasi_ews_3m"):
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                sim_kap = st.selectbox("📍 Pilih Kapanewon:", sorted(df_master['Kapanewon'].unique()))
                sim_tahun = st.number_input("📅 Tahun Simulasi:", min_value=2024, max_value=2030, value=2026)
                sim_bulan = st.number_input("📆 Bulan Acuan Berjalan (1-12):", min_value=1, max_value=12, value=9)

            with col_s2:
                sim_hth_total = st.number_input(
                    "☀️ HTH Terpanjang / Lintas Bulan Saat Ini (Hari):", 
                    min_value=0, 
                    max_value=200, 
                    value=48, 
                    help="Masukkan angka HTH berturut-turut terpanjang yang sedang berjalan."
                )
                sim_luas_tanam = st.number_input(
                    "🌾 Input Luas Tanam Kapanewon (Hektar) - Opsional:",
                    min_value=0.0,
                    max_value=20000.0,
                    value=100.0,
                    step=10.0,
                    help="Masukkan luas tanam eksis untuk menghitung estimasi total tonase gabah."
                )

            st.markdown("##### 🌧️ Input Prediksi Curah Hujan 3 Bulan Ke Depan (Opsional):")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                ch_m1 = st.number_input("Curah Hujan (B+1) mm:", min_value=0.0, max_value=2000.0, value=12.5, step=0.1, format="%.1f")
            with col_p2:
                ch_m2 = st.number_input("Curah Hujan (B+2) mm:", min_value=0.0, max_value=2000.0, value=35.7, step=0.1, format="%.1f")
            with col_p3:
                ch_m3 = st.number_input("Curah Hujan (B+3) mm:", min_value=0.0, max_value=2000.0, value=180.2, step=0.1, format="%.1f")

            st.markdown("---")
            btn_simulasi = st.form_submit_button("🚀 Jalankan Decision Engine EWS & Kalkulasi Produksi")

        if btn_simulasi:
            st.markdown("---")
            st.subheader("🎯 Hasil Kalkulasi Decision Engine & Decision Support System (DSS)")

            rata_ch_3m = (ch_m1 + ch_m2 + ch_m3) / 3.0
            
            defisit_factor = 0.0
            if rata_ch_3m > 0:
                if rata_ch_3m < 50.0:
                    defisit_factor = -8.5
                elif rata_ch_3m < 100.0:
                    defisit_factor = -3.5
                else:
                    defisit_factor = 2.0

            if sim_hth_total > 44:
                status_res = "🔴 AWAS / KRITIS"
                risk_res = "Sangat Tinggi (35.5% - 100%)"
                box_type = st.error
                sop_res = "Penetapan Status Tanggap Darurat Bencana, Suplesi Air Irigasi Darurat & Pengajuan Klaim Asuransi AUTP."
                base_impact = -0.42 * sim_hth_total - 12.5
            elif 30 < sim_hth_total <= 44:
                status_res = "🟡 SIAGA"
                risk_res = "Sedang - Tinggi (25.0%)"
                box_type = st.warning
                sop_res = "Mobilisasi Pompa Air Bergerak & Pengaturan Gilir Giring Air Irigasi Skala Ketat."
                base_impact = -0.35 * sim_hth_total - 5.0
            elif 21 <= sim_hth_total <= 30:
                status_res = "🟢 WASPADA"
                risk_res = "Ringan (14.0%)"
                box_type = st.info
                sop_res = "Pemantauan Debit Air Embung/Waduk & Sosialisasi Komoditas Hemat Air."
                base_impact = -0.15 * sim_hth_total
            else:
                status_res = "⚪ AMAN / NORMAL"
                risk_res = "Sangat Rendah (6.7%)"
                box_type = st.success
                sop_res = "Pemantauan Rutin Kelembapan Tanah & Pemeliharaan Saluran Irigasi."
                base_impact = min(15.0, 0.05 * (ch_m1 if ch_m1 > 0 else 100.0))

            total_impact_pct = round(max(-85.0, base_impact + defisit_factor), 1)
            delta_kw_ha = round((total_impact_pct / 100.0) * BASE_PRODUKSI_KW_HA, 2)
            est_hasil_kw_ha = round(BASE_PRODUKSI_KW_HA + delta_kw_ha, 2)

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(f"### Status EWS Terdeteksi: **{status_res}**")
                st.markdown(f"**Wilayah:** Kapanewon {sim_kap} | **Periode:** Bulan {bulan_nama[int(sim_bulan)-1]} {sim_tahun}")
                st.markdown(f"**HTH Running Saat Ini:** `{sim_hth_total} Hari`")
                if ch_m1 > 0 or ch_m2 > 0 or ch_m3 > 0:
                    st.markdown(f"**Prediksi CH 3 Bulan (B+1 s/d B+3):** `{ch_m1:.1f} mm, {ch_m2:.1f} mm, {ch_m3:.1f} mm`")
                st.markdown(f"**Tingkat Risiko Bencana Pertanian:** {risk_res}")
                
                st.markdown("---")
                st.markdown("#### 🌾 Hasil Prediksi Produktivitas Pertanian:")
                st.markdown(f"* **Persentase Perubahan:** <span style='color:crimson; font-size:18px;'>**{total_impact_pct:+.1f}%**</span>", unsafe_allow_html=True)
                st.markdown(f"* **Selisih Perubahan Hasil:** **{delta_kw_ha:+.2f} Kw/Ha**")
                st.markdown(f"* **Estimasi Hasil Panen Akhir:** <span style='color:green; font-size:18px;'>**{est_hasil_kw_ha:.2f} Kw/Ha**</span> (Basis Normal: {BASE_PRODUKSI_KW_HA} Kw/Ha)", unsafe_allow_html=True)

                if sim_luas_tanam > 0:
                    tot_prod_ton = round((est_hasil_kw_ha * sim_luas_tanam) / 10.0, 2)
                    tot_delta_ton = round((delta_kw_ha * sim_luas_tanam) / 10.0, 2)
                    st.markdown("---")
                    st.markdown(f"#### 📊 Proyeksi Total Panen 3 Bulan Ke Depan (Luas Tanam: {sim_luas_tanam:.0f} Ha):")
                    st.markdown(f"* **Total Estimasi Produksi Kapanewon:** **{tot_prod_ton:,.2f} Ton**")
                    st.markdown(f"* **Total Potensi Deviasi Produksi:** <span style='color:crimson;'>**{tot_delta_ton:,.2f} Ton**</span>", unsafe_allow_html=True)

            with col_r2:
                box_type(f"**Rekomendasi Aksi SOP Lapangan:**\\n\\n{sop_res}")

    # -----------------------------------------------------------------------------
    # MODE 3: IMPORT EXCEL HARIAN MASSAL (17 KAPANEWON MATRIKS 1-31 HARI)
    # -----------------------------------------------------------------------------
    else:
        st.title("📥 Import Data Harian Massal (17 Pos Kapanewon)")
        st.markdown("Unggah file Excel matriks curah hujan harian (Baris = Tanggal 1–31, Kolom = 17 Kapanewon). Sistem akan memproses seluruh kapanewon sekaligus:")
        st.markdown("---")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            imp_tahun = st.number_input("📅 Pilih Tahun Pengamatan:", min_value=2024, max_value=2030, value=2026)
        with col_m2:
            imp_bulan = st.number_input("📆 Pilih Bulan Pengamatan (1-12):", min_value=1, max_value=12, value=10)

        list_kap_sleman = sorted(df_master['Kapanewon'].unique())
        df_template = pd.DataFrame({'Tanggal': list(range(1, 32))})
        for kap in list_kap_sleman:
            df_template[kap] = 0.0

        st.markdown("#### 📄 1. Download Template Matriks Excel")
        st.caption("Gunakan format template ini untuk mengisi data hujan harian 17 kapanewon:")
        
        df_template.to_excel("template_harian_17kap.xlsx", index=False)
        with open("template_harian_17kap.xlsx", "rb") as file_tpl:
            st.download_button(
                label="📥 Unduh Template Excel Matriks (17 Kapanewon)",
                data=file_tpl,
                file_name=f"Template_Hujan_Harian_Bulan_{imp_bulan}_{imp_tahun}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.markdown("---")
        st.markdown("#### 📤 2. Unggah File Excel yang Sudah Diisi")
        uploaded_file = st.file_uploader("Pilih file Excel hasil pengisian data harian:", type=['xlsx', 'xls'])

        if uploaded_file is not None:
            try:
                df_upload = pd.read_excel(uploaded_file)
                st.success("✅ File Excel berhasil dibaca! Pratinjau data masukan:")
                st.dataframe(df_upload.head(10), use_container_width=True)

                if st.button("🚀 Proses & Simpan 17 Kapanewon ke Database Master"):
                    df_current = pd.read_excel(EXCEL_PATH, sheet_name='MASTER_EWS_SLEMAN')
                    if 'Kecamatan' in df_current.columns and 'Kapanewon' not in df_current.columns:
                        df_current.rename(columns={'Kecamatan': 'Kapanewon'}, inplace=True)
                    
                    list_proses = []
                    tgl_str = f"{imp_tahun}-{str(imp_bulan).zfill(2)}-01"

                    for kap in list_kap_sleman:
                        if kap in df_upload.columns:
                            curah_hujan_series = df_upload[kap].fillna(0.0)
                            
                            total_ch = curah_hujan_series.sum()
                            
                            max_hth = 0
                            curr_hth = 0
                            for val in curah_hujan_series:
                                if val == 0.0:
                                    curr_hth += 1
                                    if curr_hth > max_hth:
                                        max_hth = curr_hth
                                else:
                                    curr_hth = 0

                            ch30 = total_ch
                            ch60 = total_ch * 1.5 if total_ch > 0 else 0.0
                            ch90 = total_ch * 2.0 if total_ch > 0 else 0.0
                            ra = -80.0 if total_ch < 50 else (0.0 if total_ch < 150 else 20.0)
                            cdii = min(100.0, round((max_hth / 31.0) * 100, 2))

                            if cdii < 20: status_climate = 'Sangat Rendah (Basah)'
                            elif cdii < 40: status_climate = 'Rendah (Normal)'
                            elif cdii < 60: status_climate = 'Sedang (Moderat)'
                            elif cdii < 80: status_climate = 'Tinggi (Kering Berat)'
                            else: status_climate = 'Sangat Tinggi (Kering Ekstrem)'

                            if max_hth > 44:
                                status_ews = "🔴 AWAS / KRITIS"
                                risk_res = "Sangat Tinggi (35.5% - 100%)"
                            elif 30 < max_hth <= 44:
                                status_ews = "🟡 SIAGA"
                                risk_res = "Sedang - Tinggi (25.0%)"
                            elif 21 <= max_hth <= 30:
                                status_ews = "🟢 WASPADA"
                                risk_res = "Ringan (14.0%)"
                            else:
                                status_ews = "⚪ AMAN / NORMAL"
                                risk_res = "Sangat Rendah (6.7%)"

                            row_kap = {
                                'Kapanewon': kap,
                                'Tanggal': tgl_str,
                                'Tahun': int(imp_tahun),
                                'Bulan': int(imp_bulan),
                                'CH': total_ch,
                                'HTH': int(max_hth),
                                'CH30': ch30,
                                'CH60': ch60,
                                'CH90': ch90,
                                'RA': ra,
                                'CDII': cdii,
                                'Status_Climate': status_climate,
                                'Risiko_Pertanian': risk_res,
                                'Status_EWS': status_ews
                            }
                            list_proses.append(row_kap)

                    for row in list_proses:
                        mask = (df_current['Kapanewon'] == row['Kapanewon']) & (df_current['Tahun'] == row['Tahun']) & (df_current['Bulan'] == row['Bulan'])
                        if mask.any():
                            for col, val in row.items():
                                df_current.loc[mask, col] = val
                        else:
                            df_new = pd.DataFrame([row])
                            df_current = pd.concat([df_current, df_new], ignore_index=True)

                    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df_current.to_excel(writer, sheet_name='MASTER_EWS_SLEMAN', index=False)

                    st.cache_data.clear()

                    st.balloons()
                    st.success(f"🎉 Selesai! Data hujan harian massal untuk 17 Kapanewon periode **Bulan {imp_bulan}/{imp_tahun}** berhasil diproses dan disimpan permanen!")
                    
                    df_hasil = pd.DataFrame(list_proses)[['Kapanewon', 'CH', 'HTH', 'Status_EWS', 'Risiko_Pertanian']]
                    st.dataframe(df_hasil, use_container_width=True)

            except Exception as import_err:
                st.error(f"❌ Terjadi kesalahan saat memproses file Excel: {import_err}")

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat memuat data: {e}")
