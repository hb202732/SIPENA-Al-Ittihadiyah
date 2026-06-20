import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# 1. INISIALISASI DATABASE & TABEL
# ==========================================
def init_db():
    conn = sqlite3.connect('mts_ittihadiyah.db')
    c = conn.cursor()
    
    # Tabel Pengguna (Users)
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
            jenis TEXT, -- 'Tahfiz' atau 'Tilawah'
            surah_ayat TEXT,
            keterangan TEXT,
            guru TEXT
        )
    ''')
    
    # Tambahkan akun Kepala Madrasah default jika belum ada
    c.execute("SELECT * FROM users WHERE username='kamad'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('kamad', 'admin123', 'Kepala Madrasah', 'Kepala Madrasah')")
        
    conn.commit()
    conn.close()

# Fungsi helper database
def run_query(query, params=(), is_select=True):
    conn = sqlite3.connect('mts_ittihadiyah.db')
    c = conn.cursor()
    c.execute(query, params)
    res = c.fetchall() if is_select else None
    conn.commit()
    conn.close()
    return res

# Jalankan inisialisasi DB
init_db()

# ==========================================
# 2. SISTEM AUTENTIKASI (LOGIN)
# ==========================================
st.set_page_config(page_title="MTs Al-Ittihadiyah - App", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['nama'] = ""
    st.session_state['role'] = ""

def login_user(username, password):
    user = run_query("SELECT username, nama, role FROM users WHERE username=? AND password=?", (username, password))
    if user:
        st.session_state['logged_in'] = True
        st.session_state['username'] = user[0][0]
        st.session_state['nama'] = user[0][1]
        st.session_state['role'] = user[0][2]
        return True
    return False

def logout_user():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['nama'] = ""
    st.session_state['role'] = ""
    st.rerun()

# ==========================================
# INTERFACE HALAMAN LOGIN
# ==========================================
if not st.session_state['logged_in']:
    st.title("🏫 Sistem Informasi & Monitoring MTs Al-Ittihadiyah")
    st.subheader("Buku Penghubung & Capaian Tahfiz/Tilawah")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Masuk")
        
        if submit:
            if login_user(username, password):
                st.success(f"Selamat datang, {st.session_state['nama']}!")
                st.rerun()
            else:
                st.error("Username atau password salah.")
else:
    # Sidebar untuk Navigasi dan Info Login
    st.sidebar.title(f"👤 {st.session_state['nama']}")
    st.sidebar.write(f"Role: **{st.session_state['role']}**")
    if st.sidebar.button("Keluar / Logout"):
        logout_user()
        
    # ==========================================
    # 3. DASHBOARD BERDASARKAN ROLE
    # ==========================================
    role = st.session_state['role']
    
    # ------------------------------------------
    # FITUR KHUSUS: KEPALA MADRASAH (PENGATURAN USER)
    # ------------------------------------------
    if role == "Kepala Madrasah":
        st.title("Dashboard Kepala Madrasah (Top Control)")
        
        menu = st.tabs(["Manajemen Pengguna", "Laporan Buku Penghubung", "Laporan Tahfiz/Tilawah"])
        
        with menu[0]:
            st.header("⚙️ Pengaturan & Manajemen Pengguna")
            
            # Form Tambah Pengguna
            with st.expander("➕ Tambah Pengguna Baru"):
                new_user = st.text_input("Username Baru")
                new_pass = st.text_input("Password Baru", type="password")
                new_nama = st.text_input("Nama Lengkap")
                new_role = st.selectbox("Role", ["Kepala Madrasah", "Wali Kelas", "Guru Qur'an", "Orang Tua"])
                btn_add = st.button("Simpan Pengguna")
                
                if btn_add:
                    if new_user and new_pass and new_nama:
                        try:
                            run_query("INSERT INTO users VALUES (?, ?, ?, ?)", (new_user, new_pass, new_nama, new_role), is_select=False)
                            st.success(f"Pengguna {new_nama} berhasil ditambahkan!")
                            st.rerun()
                        except:
                            st.error("Username sudah digunakan!")
                    else:
                        st.warning("Semua kolom harus diisi.")
            
            # Tampilkan & Aksi Edit/Hapus
            st.subheader("Daftar Pengguna Saat Ini")
            users_data = run_query("SELECT username, nama, role FROM users")
            df_users = pd.DataFrame(users_data, columns=["Username", "Nama Lengkap", "Role"])
            st.dataframe(df_users, use_container_width=True)
            
            # Hapus Pengguna
            with st.expander("🗑️ Hapus Pengguna"):
                user_to_delete = st.selectbox("Pilih Username yang akan dihapus", df_users["Username"].tolist())
                btn_delete = st.button("Hapus", type="primary")
                if btn_delete:
                    if user_to_delete == "kamad":
                        st.error("Akun utama Kamad tidak bisa dihapus!")
                    else:
                        run_query("DELETE FROM users WHERE username=?", (user_to_delete,), is_select=False)
                        st.success(f"User {user_to_delete} berhasil dihapus.")
                        st.rerun()

        with menu[1]:
            st.write("Fitur Laporan Buku Penghubung (Akan dikembangkan di langkah selanjutnya)")
            
        with menu[2]:
            st.write("Fitur Laporan Tahfiz/Tilawah (Akan dikembangkan di langkah selanjutnya)")

    # ------------------------------------------
    # ROLE LAIN (Wali Kelas, Guru Qur'an, Orang Tua)
    # ------------------------------------------
    else:
        st.title(f"Halaman {role}")
        st.write(f"Halo {st.session_state['nama']}, modul untuk halaman Anda sedang disiapkan.")
