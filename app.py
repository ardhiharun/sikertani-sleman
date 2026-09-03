import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import openpyxl
import os

st.set_page_config(
    page_title="SIKERTANI - Sistem Informasi Peringatan Dini Kekeringan Pertanian Berbasis Iklim",
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
        ["📊 Monitoring Dashboard", "🔮 Simulasi Real-Time (EWS)", "➕ Input & Simpan Data Baru (Harian)"]
    )
    st.sidebar.markdown("---")

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

        st.title("🌾🌤️ SIKERTANI - Sistem Informasi Peringatan Dini Kekeringan Pertanian Berbasis Iklim")
        st.markdown(f"**Kabupaten Sleman | Monitoring Operasional Periode: Bulan {bulan_pilihan} - Tahun {tahun_pilihan}**")
        st.caption("Sistem Peringatan Dini Berbasis Data-Driven Klimatologi, Fixed Effects Logit, dan Machine Learning")
        st.markdown("---")

        total_awas = len(data_aktif[data_aktif['Status_EWS'].str.contains('AWAS', na=False)])
        total_siaga = len(data_aktif[data_aktif['Status_EWS'].str.contains('SIAGA', na=False)])
        total_waspada = len(data_aktif[data_aktif['Status_EWS'].str.contains('WASPADA', na=False)])
        total_aman = len(data_aktif[data_aktif['Status_EWS'].str.contains('AMAN', na=False)])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔴 AWAS / KRITIS", f"{total_awas} Kecamatan", delta="Tindakan Tanggap Darurat", delta_color="inverse")
        c2.metric("🟡 SIAGA", f"{total_siaga} Kecamatan", delta="Mobilisasi Pompa Air")
        c3.metric("🟢 WASPADA", f"{total_waspada} Kecamatan", delta="Pantau Cadangan Embung")
        c4.metric("⚪ AMAN / NORMAL", f"{total_aman} Kecamatan", delta="Kondisi Kondusif")

        st.markdown("---")
        st.subheader("📋 Status Peringatan Dini per Kecamatan")
        
        col_tampil = ['Kecamatan', 'Tanggal', 'CH', 'HTH', 'CH30', 'CH60', 'CH90', 'RA', 'Status_Climate', 'Risiko_Pertanian', 'Status_EWS']
        df_tampil = data_aktif[col_tampil].reset_index(drop=True)
        
        st.dataframe(df_tampil, use_container_width=True, height=380)

        st.markdown("---")
        st.subheader("📈 Analisis Histori Tren & Ambang Batas Kritis (Threshold HTH >= 44 Hari)")
        
        kec_pilihan = st.selectbox("🎯 Pilih Kecamatan untuk Menganalisis Histori Tren:", sorted(df_master['Kecamatan'].unique()))
        
        df_kec = df_master[df_master['Kecamatan'] == kec_pilihan].sort_values('Tanggal')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df_kec['Tanggal'],
            y=df_kec['CH'],
            name='Curah Hujan (mm)',
            marker_color='rgba(31, 78, 120, 0.6)'
        ))

        fig.add_trace(go.Scatter(
            x=df_kec['Tanggal'],
            y=df_kec['HTH'],
            name='Hari Tanpa Hujan / HTH (Hari)',
            mode='lines+markers',
            line=dict(color='crimson', width=2.5)
        ))

        fig.add_hline(
            y=44, 
            line_dash="dash", 
            line_color="red", 
            annotation_text="Ambang Batas Kritis Youden Index (HTH = 44 Hari)", 
            annotation_position="top left"
        )

        fig.update_layout(
            title=f"Dinamika Klimatologi & Resiko Kekeringan di Kecamatan {kec_pilihan} (2015–2026)",
            xaxis_title="Periode Waktu (Tanggal)",
            yaxis_title="Nilai Indikator",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
            template="plotly_white"
        )

        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------------------------
    # MODE 2: SIMULASI REAL-TIME EWS (INPUT HTH LINTAS BULAN / TERPANJANG)
    # -----------------------------------------------------------------------------
    elif mode_aplikasi == "🔮 Simulasi Real-Time (EWS)":
        st.title("🔮 Modul Simulasi Real-Time EWS Kekeringan")
        st.markdown("Gunakan modul ini untuk menguji skenario dampak kekeringan secara cepat tanpa mengubah data di database master:")
        st.markdown("---")

        with st.form("form_simulasi_ews"):
            col1, col2 = st.columns(2)
            
            with col1:
                sim_kec = st.selectbox("📍 Pilih Kecamatan:", sorted(df_master['Kecamatan'].unique()))
                sim_tahun = st.number_input("📅 Tahun Simulasi:", min_value=2024, max_value=2030, value=2026)
                sim_bulan = st.number_input("📆 Bulan Simulasi (1-12):", min_value=1, max_value=12, value=10)

            with col2:
                sim_ch = st.number_input("🌧️ Estimasi Curah Hujan Bulanan (mm):", min_value=0.0, max_value=2000.0, value=15.0)
                sim_hth_total = st.number_input(
                    "☀️ HTH Terpanjang / Lintas Bulan (Hari):", 
                    min_value=0, 
                    max_value=200, 
                    value=48, 
                    help="Masukkan angka HTH berturut-turut terpanjang yang sedang berjalan (bisa menyeberang dari bulan sebelumnya, historis Sleman pernah 170 hari)."
                )

            btn_simulasi = st.form_submit_button("🚀 Jalankan Simulasi EWS")

        if btn_simulasi:
            st.markdown("---")
            st.subheader("🎯 Hasil Simulasi Decision Engine EWS")

            # Decision Engine Rules
            if sim_hth_total > 44:
                status_res = "🔴 AWAS / KRITIS"
                risk_res = "Sangat Tinggi (35.5% - 100%)"
                box_type = st.error
                sop_res = "Penetapan Status Tanggap Darurat Bencana, Suplesi Air Irigasi Darurat & Pengajuan Klaim Asuransi AUTP."
            elif 30 < sim_hth_total <= 44:
                status_res = "🟡 SIAGA"
                risk_res = "Sedang - Tinggi (25.0%)"
                box_type = st.warning
                sop_res = "Mobilisasi Pompa Air Bergerak & Pengaturan Gilir Giring Air Irigasi Skala Ketat."
            elif 21 <= sim_hth_total <= 30:
                status_res = "🟢 WASPADA"
                risk_res = "Ringan (14.0%)"
                box_type = st.info
                sop_res = "Pemantauan Debit Air Embung/Waduk & Sosialisasi Komoditas Hemat Air."
            else:
                status_res = "⚪ AMAN / NORMAL"
                risk_res = "Sangat Rendah (6.7%)"
                box_type = st.success
                sop_res = "Pemantauan Rutin Kelembapan Tanah & Pemeliharaan Saluran Irigasi."

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown(f"### Status Terdeteksi: **{status_res}**")
                st.markdown(f"**Wilayah:** Kecamatan {sim_kec} | **Periode:** Bulan {sim_bulan}/{sim_tahun}")
                st.markdown(f"**Total HTH Terpanjang Lintas Bulan:** `{sim_hth_total} Hari`")
                st.markdown(f"**Tingkat Risiko Bencana Pertanian:** {risk_res}")

            with col_r2:
                box_type(f"**Rekomendasi Aksi SOP Lapangan:**\n\n{sop_res}")

    # -----------------------------------------------------------------------------
    # MODE 3: INPUT DATA HARIAN & OTOMATIS HITUNG UNTUK MASTER
    # -----------------------------------------------------------------------------
    else:
        st.title("➕ Input Data Harian Stasiun Hujan (Tanggal 1–30/31)")
        st.markdown("Masukkan data curah hujan harian dari stasiun hujan. Sistem akan **otomatis mendeteksi pola HTH berturut-turut**, menghitung **Total Curah Hujan Bulanan**, dan memperbarui database master:")
        st.markdown("---")

        col_h1, col_h2, col_h3 = st.columns(3)
        with col_h1:
            inp_kec = st.selectbox("📍 Pilih Kecamatan:", sorted(df_master['Kecamatan'].unique()))
        with col_h2:
            inp_tahun = st.number_input("📅 Tahun:", min_value=2024, max_value=2030, value=2026)
        with col_h3:
            inp_bulan = st.number_input("📆 Bulan (1-12):", min_value=1, max_value=12, value=10)

        # Hitung jumlah hari dalam bulan terpilih (28/29/30/31)
        if inp_bulan in [1, 3, 5, 7, 8, 10, 12]:
            max_days = 31
        elif inp_bulan in [4, 6, 9, 11]:
            max_days = 30
        else:
            # Februari
            max_days = 29 if (inp_tahun % 4 == 0 and (inp_tahun % 100 != 0 or inp_tahun % 400 == 0)) else 28

        st.subheader(f"🌧️ Form Input Curah Hujan Harian ({max_days} Hari - Bulan {inp_bulan}/{inp_tahun})")
        st.caption("Isi nilai curah hujan harian dalam (mm). Masukkan 0 jika tidak ada hujan.")

        with st.form("form_harian_ews"):
            # Buat grid input 7 kolom x 5 baris
            daily_vals = []
            cols_per_row = 7
            
            for d in range(1, max_days + 1):
                if (d - 1) % cols_per_row == 0:
                    cols = st.columns(cols_per_row)
                val = cols[(d - 1) % cols_per_row].number_input(f"Tgl {d}:", min_value=0.0, max_value=500.0, value=0.0, step=1.0)
                daily_vals.append(val)

            st.markdown("---")
            btn_proses_harian = st.form_submit_button("💾 Hitung Otomatis & Simpan ke Database Master")

        if btn_proses_harian:
            # 1. Hitung Total CH Bulanan Otomatis
            total_ch_bulanan = sum(daily_vals)
            
            # 2. Hitung HTH Maksimum Berturut-turut
            max_hth_consecutive = 0
            curr_hth = 0
            for v in daily_vals:
                if v == 0.0:
                    curr_hth += 1
                    if curr_hth > max_hth_consecutive:
                        max_hth_consecutive = curr_hth
                else:
                    curr_hth = 0

            # 3. Hitung Indikator Turunan
            tgl_str = f"{inp_tahun}-{str(inp_bulan).zfill(2)}-01"
            ch30 = total_ch_bulanan
            ch60 = total_ch_bulanan * 1.5 if total_ch_bulanan > 0 else 0.0
            ch90 = total_ch_bulanan * 2.0 if total_ch_bulanan > 0 else 0.0
            ra = -80.0 if total_ch_bulanan < 50 else (0.0 if total_ch_bulanan < 150 else 20.0)
            cdii = min(100.0, round((max_hth_consecutive / 31.0) * 100, 2))

            if cdii < 20: status_climate = 'Sangat Rendah (Basah)'
            elif cdii < 40: status_climate = 'Rendah (Normal)'
            elif cdii < 60: status_climate = 'Sedang (Moderat)'
            elif cdii < 80: status_climate = 'Tinggi (Kering Berat)'
            else: status_climate = 'Sangat Tinggi (Kering Ekstrem)'

            if max_hth_consecutive > 44:
                status_ews = "🔴 AWAS / KRITIS"
                risk_res = "Sangat Tinggi (35.5% - 100%)"
            elif 30 < max_hth_consecutive <= 44:
                status_ews = "🟡 SIAGA"
                risk_res = "Sedang - Tinggi (25.0%)"
            elif 21 <= max_hth_consecutive <= 30:
                status_ews = "🟢 WASPADA"
                risk_res = "Ringan (14.0%)"
            else:
                status_ews = "⚪ AMAN / NORMAL"
                risk_res = "Sangat Rendah (6.7%)"

            row_baru = {
                'Kecamatan': inp_kec,
                'Tanggal': tgl_str,
                'Tahun': int(inp_tahun),
                'Bulan': int(inp_bulan),
                'CH': total_ch_bulanan,
                'HTH': int(max_hth_consecutive),
                'CH30': ch30,
                'CH60': ch60,
                'CH90': ch90,
                'RA': ra,
                'CDII': cdii,
                'Status_Climate': status_climate,
                'Risiko_Pertanian': risk_res,
                'Status_EWS': status_ews
            }

            try:
                df_current = pd.read_excel(EXCEL_PATH, sheet_name='MASTER_EWS_SLEMAN')
                mask = (df_current['Kecamatan'] == inp_kec) & (df_current['Tahun'] == inp_tahun) & (df_current['Bulan'] == inp_bulan)
                
                if mask.any():
                    for col, val in row_baru.items():
                        df_current.loc[mask, col] = val
                    st.info(f"🔄 Data untuk **Kecamatan {inp_kec} ({inp_bulan}/{inp_tahun})** berhasil **DIPERBARUI**!")
                else:
                    df_new_row = pd.DataFrame([row_baru])
                    df_current = pd.concat([df_current, df_new_row], ignore_index=True)
                    st.success(f"✅ Data baru untuk **Kecamatan {inp_kec} ({inp_bulan}/{inp_tahun})** berhasil **DITAMBAHKAN**!")

                with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df_current.to_excel(writer, sheet_name='MASTER_EWS_SLEMAN', index=False)

                st.cache_data.clear()

                st.markdown("---")
                st.subheader("🎯 Hasil Kalkulasi Otomatis Sistem:")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("🌧️ Total CH Bulanan", f"{total_ch_bulanan:.1f} mm")
                col_m2.metric("☀️ HTH Maks Berturut-turut", f"{max_hth_consecutive} Hari")
                col_m3.metric("📊 Status EWS", status_ews)
                col_m4.metric("🚨 Risiko Bencana", risk_res)

            except Exception as save_err:
                st.error(f"❌ Gagal menyimpan ke Excel: {save_err}")

except Exception as e:
    st.error(f"❌ Terjadi kesalahan saat memuat data: {e}")
