import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==========================================
# 1. INISIALISASI DATABASE & TABEL
# ==========================================
def init_db():
    conn = sqlite3.connect('mts_ittihadiyah.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabel Pengguna
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            nama TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # Tabel Buku Penghubung
    c.execute('''
        CREATE TABLE IF NOT EXISTS buku_penghubung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            nama_siswa TEXT,
            catatan TEXT,
            wali_kelas TEXT
        )
    ''')
    
    # Tabel Capaian Tahfiz & Tilawah
    c.execute('''
        CREATE TABLE IF NOT EXISTS capaian_quran (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            nama_siswa TEXT,
            jenis TEXT,
            surah_ayat TEXT,
            keterangan TEXT,
            guru TEXT
        )
    ''')
    
    # Akun default Kepala Madrasah
    c.execute("SELECT * FROM users WHERE username='kamad'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('kamad', 'admin123', 'Kepala Madrasah', 'Kepala Madrasah')")
        
    conn.commit()
    conn.close()

def run_query(query, params=(), is_select=True):
    try:
        conn = sqlite3.connect('mts_ittihadiyah.db', check_same_thread=False)
        c = conn.cursor()
        c.execute(query, params)
        res = c.fetchall() if is_select else None
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        st.error(f"Database Error: {e}")
        return []

# Jalankan DB
init_db()

# ==========================================
# 2. SISTEM LOGIN & SESSION STATE
# ==========================================
st.set_page_config(page_title="MTs Al-Ittihadiyah", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['nama'] = ""
    st.session_state['role'] = ""

# Tampilan Utama jika Belum Login
if not st.session_state['logged_in']:
    st.title("🏫 MTs Al-Ittihadiyah")
    st.subheader("Buku Penghubung & Monitoring Tahfiz/Tilawah")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Masuk")
        
        if submit:
            user = run_query("SELECT username, nama, role FROM users WHERE username=? AND password=?", (username, password))
            if user:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user[0][0]
                st.session_state['nama'] = user[0][1]
                st.session_state['role'] = user[0][2]
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username atau password salah.")
else:
    # SIDEBAR CONTROL
    st.sidebar.title(f"👤 {st.session_state['nama']}")
    st.sidebar.info(f"Role: **{st.session_state['role']}**")
    if st.sidebar.button("Keluar / Logout", type="primary"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    role = st.session_state['role']
    hari_ini = datetime.now().strftime("%Y-%m-%d")

    # ==========================================
    # INTERFACE 1: KEPALA MADRASAH (TOP CONTROL)
    # ==========================================
    if role == "Kepala Madrasah":
        st.title("Dashboard Kepala Madrasah")
        t_user, t_buku, t_quran = st.tabs(["⚙️ Pengaturan Pengguna", "📋 Laporan Buku Penghubung", "📖 Laporan Tahfiz/Tilawah"])
        
        with t_user:
            st.subheader("Manajemen Akun Pengguna")
            with st.expander("➕ Tambah Pengguna Baru"):
                u_baru = st.text_input("Username Baru")
                p_baru = st.text_input("Password Baru", type="password")
                n_baru = st.text_input("Nama Lengkap")
                r_baru = st.selectbox("Role", ["Kepala Madrasah", "Wali Kelas", "Guru Qur'an", "Orang Tua"])
                if st.button("Simpan Akun"):
                    if u_baru and p_baru and n_baru:
                        run_query("INSERT INTO users VALUES (?, ?, ?, ?)", (u_baru, p_baru, n_baru, r_baru), is_select=False)
                        st.success("User berhasil ditambahkan!")
                        st.rerun()
            
            data_u = run_query("SELECT username, nama, role FROM users")
            df_u = pd.DataFrame(data_u, columns=["Username", "Nama", "Role"])
            st.dataframe(df_u, use_container_width=True)
            
            with st.expander("🗑️ Hapus Pengguna"):
                u_hapus = st.selectbox("Pilih User", df_u["Username"].tolist())
                if st.button("Hapus Akun", type="primary"):
                    if u_hapus != "kamad":
                        run_query("DELETE FROM users WHERE username=?", (u_hapus,), is_select=False)
                        st.success("Terhapus!")
                        st.rerun()
                    else:
                        st.error("Akun utama 'kamad' tidak bisa dihapus.")

        with t_buku:
            st.subheader("Semua Catatan Buku Penghubung")
            data_b = run_query("SELECT tanggal, nama_siswa, catatan, wali_kelas FROM buku_penghubung")
            st.dataframe(pd.DataFrame(data_b, columns=["Tanggal", "Siswa", "Catatan", "Wali Kelas"]), use_container_width=True)

        with t_quran:
            st.subheader("Semua Capaian Tahfiz & Tilawah")
            data_q = run_query("SELECT tanggal, nama_siswa, jenis, surah_ayat, keterangan, guru FROM capaian_quran")
            st.dataframe(pd.DataFrame(data_q, columns=["Tanggal", "Siswa", "Jenis", "Surah/Ayat", "Keterangan", "Guru"]), use_container_width=True)

    # ==========================================
    # INTERFACE 2: WALI KELAS
    # ==========================================
    elif role == "Wali Kelas":
        st.title("Menu Utama Wali Kelas")
        with st.form("form_buku"):
            st.subheader("📝 Input Catatan Perkembangan Siswa")
            siswa = st.text_input("Nama Siswa")
            catatan = st.text_area("Catatan Perkembangan / Pengumuman ke Orang Tua")
            if st.form_submit_button("Kirim ke Orang Tua"):
                if siswa and catatan:
                    run_query("INSERT INTO buku_penghubung (tanggal, nama_siswa, catatan, wali_kelas) VALUES (?,?,?,?)", 
                              (hari_ini, siswa, catatan, st.session_state['nama']), is_select=False)
                    st.success("Catatan berhasil disimpan!")
                else:
                    st.warning("Mohon isi nama siswa dan catatan.")
                    
        st.subheader("Riwayat Catatan Anda")
        riwayat = run_query("SELECT tanggal, nama_siswa, catatan FROM buku_penghubung WHERE wali_kelas=?", (st.session_state['nama'],))
        st.dataframe(pd.DataFrame(riwayat, columns=["Tanggal", "Siswa", "Catatan"]), use_container_width=True)

    # ==========================================
    # INTERFACE 3: GURU QUR'AN
    # ==========================================
    elif role == "Guru Qur'an":
        st.title("Menu Setoran Hafalan & Tilawah")
        with st.form("form_quran"):
            siswa = st.text_input("Nama Siswa")
            jenis = st.radio("Jenis Setoran", ["Tahfiz (Hafalan)", "Tilawah (Bacaan)"])
            progres = st.text_input("Surah dan Ayat (Contoh: An-Naba' 1-10)")
            ket = st.text_input("Keterangan Tambahan (Contoh: Lancar, Perlu Diulang)")
            if st.form_submit_button("Simpan Setoran"):
                if siswa and progres:
                    run_query("INSERT INTO capaian_quran (tanggal, nama_siswa, jenis, surah_ayat, keterangan, guru) VALUES (?,?,?,?,?,?)",
                              (hari_ini, siswa, jenis, progres, ket, st.session_state['nama']), is_select=False)
                    st.success("Data setoran berhasil direkam!")
                else:
                    st.warning("Nama siswa dan Surah/Ayat harus diisi.")
                    
        st.subheader("Riwayat Input Setoran Anda")
        riwayat_q = run_query("SELECT tanggal, nama_siswa, jenis, surah_ayat, keterangan FROM capaian_quran WHERE guru=?", (st.session_state['nama'],))
        st.dataframe(pd.DataFrame(riwayat_q, columns=["Tanggal", "Siswa", "Jenis", "Surah/Ayat", "Keterangan"]), use_container_width=True)

    # ==========================================
    # INTERFACE 4: ORANG TUA
    # ==========================================
    elif role == "Orang Tua":
        st.title("Portal Informasi Orang Tua Siswa")
        st.info("Silakan cari nama anak Anda untuk melihat laporan perkembangan harian.")
        
        cari_nama = st.text_input("Ketik Nama Lengkap Anak Anda:")
        if cari_nama:
            st.subheader(f"📊 Laporan untuk: {cari_nama}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 📋 Buku Penghubung (Wali Kelas)")
                buku_ortu = run_query("SELECT tanggal, catatan, wali_kelas FROM buku_penghubung WHERE nama_siswa LIKE ?", (f"%{cari_nama}%",))
                if buku_ortu:
                    st.dataframe(pd.DataFrame(buku_ortu, columns=["Tanggal", "Catatan/Pesan", "Wali Kelas"]), use_container_width=True)
                else:
                    st.write("Belum ada catatan dari Wali Kelas.")
                    
            with col2:
                st.markdown("### 📖 Capaian Hafalan Qur'an")
                quran_ortu = run_query("SELECT tanggal, jenis, surah_ayat, keterangan, guru FROM capaian_quran WHERE nama_siswa LIKE ?", (f"%{cari_nama}%",))
                if quran_ortu:
                    st.dataframe(pd.DataFrame(quran_ortu, columns=["Tanggal", "Jenis", "Surah/Ayat", "Keterangan", "Guru"]), use_container_width=True)
                else:
                    st.write("Belum ada riwayat setoran hafalan.")
