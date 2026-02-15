import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dompet Mhs Pro",
    page_icon="💳",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. DATABASE & AUTH ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds)
    return None

def get_database():
    client = get_gspread_client()
    return client.open("database_keuangan") if client else None

def cek_login(username, password):
    sh = get_database()
    if not sh: return None
    try:
        ws = sh.worksheet("users")
        df = pd.DataFrame(ws.get_all_records())
        user = df[(df['username'].astype(str) == str(username)) & (df['password'].astype(str) == str(password))]
        return user.iloc[0]['nama_lengkap'] if not user.empty else None
    except: return None

def register_user(username, password, nama):
    sh = get_database()
    if not sh: return False
    try:
        ws = sh.worksheet("users")
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty and username in df['username'].values: return False
        ws.append_row([username, password, nama])
        return True
    except: return False

def tambah_transaksi(username, tgl, tipe, kat, nom, cat):
    sh = get_database()
    if sh:
        ws = sh.worksheet("transaksi")
        ws.append_row([username, tgl.strftime("%Y-%m-%d"), tipe, kat, nom, cat])

def ambil_data(username):
    sh = get_database()
    if not sh: return pd.DataFrame()
    ws = sh.worksheet("transaksi")
    df = pd.DataFrame(ws.get_all_records())
    if df.empty: return df
    df_user = df[df['username'] == username].copy()
    if not df_user.empty:
        df_user['tanggal'] = pd.to_datetime(df_user['tanggal'], errors='coerce')
    return df_user

def ambil_celengan(username):
    sh = get_database()
    if not sh: return pd.DataFrame()
    ws = sh.worksheet("celengan")
    df = pd.DataFrame(ws.get_all_records())
    return df[df['username'] == username].copy() if not df.empty else df

def tambah_target(username, nama_target, target, deadline):
    sh = get_database()
    if sh:
        ws = sh.worksheet("celengan")
        ws.append_row([username, nama_target, target, 0, deadline.strftime("%Y-%m-%d")])

def ambil_hutang(username):
    sh = get_database()
    if not sh: return pd.DataFrame()
    ws = sh.worksheet("hutang")
    df = pd.DataFrame(ws.get_all_records())
    return df[df['username'] == username].copy() if not df.empty else df

def tambah_hutang(username, tgl, nama_org, jenis, nom, status, cat, tgl_tempo):
    sh = get_database()
    if sh:
        ws = sh.worksheet("hutang")
        ws.append_row([username, tgl.strftime("%Y-%m-%d"), nama_org, jenis, nom, status, cat, tgl_tempo.strftime("%Y-%m-%d")])

def update_status_hutang(username, nama_org, nominal, status_baru):
    sh = get_database()
    ws = sh.worksheet("hutang")
    data = ws.get_all_values()
    for i, row in enumerate(data):
        if i == 0: continue 
        if row[0] == username and row[2] == nama_org and str(row[4]) == str(nominal):
            ws.update_cell(i + 1, 6, status_baru)
            return True
    return False

# --- 3. CSS REVOLUTION (VERSION: ULTRA TIGHT & JINAK) ---
def apply_custom_design():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* 1. MENGHILANGKAN HEADER & DEKORASI */
        header, [data-testid="stHeader"], [data-testid="stDecoration"], [data-testid="stToolbar"] {
            display: none !important;
            height: 0px !important;
        }

        /* 2. BACKGROUND & FONT */
        .stApp { background-color: #f8fafc; font-family: 'Plus Jakarta Sans', sans-serif; }

        /* 3. PAKSA KONTEN MENEMPEL KE ATAS */
        .main .block-container {
            padding-top: 0rem !important;
            margin-top: -7rem !important; 
            max-width: 1000px;
        }

        /* 4. RESET GAP */
        [data-testid="stVerticalBlock"] { gap: 0px !important; }

        /* 5. GAYA KARTU MODERN */
        .wallet-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 2rem;
            border-radius: 25px;
            color: white;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            margin-top: 10px;
            margin-bottom: 1.5rem;
        }

        .section-title {
            font-size: 1.4rem;
            font-weight: 800;
            color: #1e293b;
            margin-top: 0px !important;
            margin-bottom: 0.5rem;
        }

        /* 6. SIDEBAR & BUTTON */
        section[data-testid="stSidebar"] { background-color: white !important; border-right: 1px solid #e2e8f0; }
        .stButton>button { border-radius: 12px !important; font-weight: 700 !important; }
        div[data-testid="stButton"] button[kind="primary"] { background: #10b981 !important; color: white !important; }

        /* 7. METRIC BOX */
        div[data-testid="stMetric"] {
            background: white;
            padding: 15px !important;
            border-radius: 15px;
            border: 1px solid #f1f5f9;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 4. MAIN APP ---
def main():
    apply_custom_design()
    if 'status_login' not in st.session_state:
        st.session_state.update({'status_login': False, 'user': None, 'nama': None})

    if not st.session_state['status_login']:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<div style='text-align: center; margin-top: 100px;'>", unsafe_allow_html=True)
            st.markdown("<h1 style='color: #0f172a; font-weight: 800;'>💳 Wallet Mhs Pro</h1>", unsafe_allow_html=True)
            t_log, t_reg = st.tabs(["🔐 Masuk", "✨ Daftar"])
            with t_log:
                u = st.text_input("Username", key="u_log")
                p = st.text_input("Password", type="password", key="p_log")
                if st.button("Masuk 🚀", use_container_width=True, type="primary"):
                    nama = cek_login(u, p)
                    if nama:
                        st.session_state.update({'status_login': True, 'user': u, 'nama': nama})
                        st.rerun()
                    else: st.error("Akses Ditolak.")
            with t_reg:
                new_u = st.text_input("Username Baru")
                new_p = st.text_input("Password Baru", type="password")
                new_n = st.text_input("Nama Lengkap")
                if st.button("Daftar Sekarang ✨", use_container_width=True):
                    if register_user(new_u, new_p, new_n):
                        st.success("Berhasil! Silakan Masuk.")
                    else: st.error("Username sudah ada.")
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        with st.sidebar:
            st.markdown(f"### 💰 DompetKu")
            st.write(f"Halo, **{st.session_state['nama']}**!")
            st.divider()
            selected = st.radio("MENU", ["🏠 Dashboard", "📝 Catat Baru", "📂 Riwayat Data", "🎯 Celengan", "🤝 Hutang"], label_visibility="collapsed")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state['status_login'] = False
                st.rerun()

        # --- LOGIKA RENDER MENU (DENGAN CSS JINAK) ---
        if selected == "🏠 Dashboard":
            st.markdown('<div class="section-title">📊 Dashboard</div>', unsafe_allow_html=True)
            df = ambil_data(st.session_state['user'])
            masuk = df[df['tipe'] == 'Pemasukan']['nominal'].sum() if not df.empty else 0
            keluar = df[df['tipe'] == 'Pengeluaran']['nominal'].sum() if not df.empty else 0
            saldo = masuk - keluar

            st.markdown(f"""<div class="wallet-card">
                <small style="opacity:0.7;">SALDO AKTIF</small>
                <h1 style="margin:0; font-size:3rem;">Rp {saldo:,.0f}</h1>
            </div>""", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            c1.metric("Pemasukan", f"Rp {masuk:,.0f}")
            c2.metric("Pengeluaran", f"Rp {keluar:,.0f}", delta_color="inverse")
            
            if not df.empty:
                st.divider()
                st.bar_chart(df[df['tipe'] == 'Pengeluaran'].groupby('kategori')['nominal'].sum(), color="#10b981")
            else: st.info("Data kosong.")

        elif selected == "📝 Catat Baru":
            st.markdown('<div class="section-title">📝 Tambah Transaksi</div>', unsafe_allow_html=True)
            with st.container():
                tgl = st.date_input("Tanggal", datetime.now())
                tipe = st.radio("Jenis", ["Pengeluaran 📤", "Pemasukan 📥"], horizontal=True)
                kat = st.selectbox("Kategori", ["Makan", "Transport", "Kuota", "Tugas", "Belanja", "Lainnya"])
                nom = st.number_input("Nominal", min_value=0)
                cat = st.text_input("Keterangan")
                if st.button("SIMPAN 💾", type="primary", use_container_width=True):
                    tambah_transaksi(st.session_state['user'], tgl, tipe.split()[0], kat, nom, cat)
                    st.success("Berhasil!"); time.sleep(0.5); st.rerun()

        elif selected == "📂 Riwayat Data":
            st.markdown('<div class="section-title">📂 Riwayat Transaksi</div>', unsafe_allow_html=True)
            df = ambil_data(st.session_state['user'])
            if not df.empty:
                st.dataframe(df.sort_values('tanggal', ascending=False), use_container_width=True, hide_index=True)
            else: st.info("Belum ada data.")

        elif selected == "🎯 Celengan":
            st.markdown('<div class="section-title">🎯 Celengan / Target</div>', unsafe_allow_html=True)
            with st.form("form_celengan", clear_on_submit=True):
                t_nama = st.text_input("Nama Target")
                t_nom = st.number_input("Nominal Target", min_value=0)
                t_dl = st.date_input("Deadline", datetime.now())
                if st.form_submit_button("Tambah Target 🎯"):
                    tambah_target(st.session_state['user'], t_nama, t_nom, t_dl)
                    st.success("Tersimpan!"); st.rerun()
            
            df_c = ambil_celengan(st.session_state['user'])
            if not df_c.empty:
                st.divider()
                st.dataframe(df_c, use_container_width=True, hide_index=True)

        elif selected == "🤝 Hutang":
            st.markdown('<div class="section-title">🤝 Hutang & Piutang</div>', unsafe_allow_html=True)
            tab_in, tab_lis = st.tabs(["📝 Catat Baru", "📜 Riwayat & Ubah Status"])
            with tab_in:
                col1, col2 = st.columns(2)
                ht, h_tm = col1.date_input("Tgl Pinjam", datetime.now()), col2.date_input("Jatuh Tempo")
                hn = st.text_input("Nama Orang")
                hj = st.radio("Jenis", ["Saya Pinjam", "Dia Pinjam"], horizontal=True)
                hs = st.selectbox("Status", ["Belum Lunas ❌", "Lunas ✅"])
                hm = st.number_input("Nominal", min_value=0)
                hc = st.text_input("Catatan")
                if st.button("Simpan Hutang 📌", type="primary", use_container_width=True):
                    tambah_hutang(st.session_state['user'], ht, hn, hj, hm, hs, hc, h_tm)
                    st.success("Tersimpan!"); st.rerun()

            with tab_lis:
                df_h = ambil_hutang(st.session_state['user'])
                if not df_h.empty:
                    st.subheader("⚠️ Status Hutang")
                    for i, r in df_h.iterrows():
                        with st.container():
                            c_a, c_b = st.columns([0.7, 0.3])
                            c_a.write(f"**{r['nama_orang']}** | Rp {r['nominal']:,.0f} ({r['status']})")
                            if "Belum" in r['status'] and c_b.button("Lunas ✅", key=f"h_lns_{i}"):
                                update_status_hutang(st.session_state['user'], r['nama_orang'], r['nominal'], "Lunas ✅")
                                st.rerun()
                else: st.info("Kosong.")

if __name__ == "__main__":
    main()