import streamlit as st
from streamlit_cookies_controller import CookieController
import db_manager as db
import os

import app_me
import app_anh
import app_con

st.set_page_config(page_title="Ren Studio Manager", page_icon="🎬", layout="wide")

# Khởi tạo bộ quản lý Cookie (Phép thuật chống văng tài khoản)
controller = CookieController()

# ==========================================
# 🎨 GIAO DIỆN BLITZIT THEME (MA THUẬT CSS)
# ==========================================
def load_blitzit_theme():
    st.markdown("""
    <style>
    .stApp { background-color: #0F1115; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border: 1px solid #2A2E39 !important;
        background-color: #161923 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        border-color: #7B61FF !important; 
    }
    [data-testid="stExpander"] {
        border-radius: 14px !important;
        border: 1px solid #2A2E39 !important;
        background-color: #161923 !important;
    }
    div.stButton > button {
        border-radius: 24px !important;
        font-weight: 800 !important;
        border: none !important;
        background: linear-gradient(135deg, #7B61FF 0%, #00D4FF 100%) !important;
        color: white !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(123, 97, 255, 0.4) !important;
    }
    div.stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 6px 18px rgba(123, 97, 255, 0.7) !important;
    }
    div.stButton > button[kind="secondary"] {
        background: #2A2E39 !important;
        box-shadow: none !important;
        border: 1px solid #4A5568 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        border-color: #FF4B4B !important;
        color: #FF4B4B !important;
        background: #161923 !important;
    }
    [data-testid="stMetricValue"] {
        color: #00E676 !important; 
        font-weight: 900 !important;
        text-shadow: 0 0 10px rgba(0, 230, 118, 0.3);
    }
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #A0AEC0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #7B61FF !important;
    }
    /* TẮT HIỆU ỨNG MỜ MÀN HÌNH CHỐNG LAG */
    .stApp [data-testid="stMainBlockContainer"] {
        opacity: 1 !important;
        transition: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

load_blitzit_theme()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

# TỰ ĐỘNG ĐĂNG NHẬP BẰNG COOKIE TRÌNH DUYỆT
if not st.session_state["logged_in"]:
    saved_user = controller.get('ren_user')
    saved_pass = controller.get('ren_pass')
    if saved_user and saved_pass:
        user = db.kiem_tra_dang_nhap(saved_user, saved_pass)
        if user:
            st.session_state["logged_in"] = True
            st.session_state["user_info"] = user
            st.rerun()

def show_login_page():
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        if os.path.exists("logo_studio.png"):
            st.image("logo_studio.png", use_container_width=True)
        else:
            st.warning("⚠️ Sếp nhớ bỏ file 'logo_studio.png' vào thư mục nhé!")
            
    st.title("🎬 Ren Animation Studio")
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.form_submit_button("Đăng nhập"):
            user = db.kiem_tra_dang_nhap(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = user
                # LƯU THẺ COOKIE TRONG 30 NGÀY
                controller.set('ren_user', username, max_age=2592000)
                controller.set('ren_pass', password, max_age=2592000)
                st.rerun()
            else:
                st.error("Sai tên đăng nhập hoặc mật khẩu!")

    st.markdown("---")
    st.caption("🔒 **Quên Mật khẩu?** Vui lòng nhắn tin trực tiếp cho Sếp Ren trên Group Zalo/Discord để được cấp lại mật khẩu mới.")

def show_dashboard():
    user = st.session_state["user_info"]
    
    with st.sidebar:
        if os.path.exists("logo_studio.png"):
            st.image("logo_studio.png", use_container_width=True) 
        st.markdown("---")
        
        st.title(f"Chào {user['name']} 👋")
        
        if user['role'] == 'User':
            st.write(f"**Vai trò:** Artist | **RANK:** {user.get('rank', 'N/A')}")
        else:
            st.write(f"**Vai trò:** {user['role']}")
            
        # NÚT LÀM MỚI DỮ LIỆU DÀNH CHO TẤT CẢ MỌI NGƯỜI
        if st.button("🔄 Cập nhật dữ liệu", type="primary", use_container_width=True):
            st.toast("✅ Đã kéo dữ liệu mới nhất từ Sếp!")
            st.rerun()
            
        with st.expander("🔑 Đổi mật khẩu"):
            pass_moi = st.text_input("Nhập mật khẩu mới:", type="password")
            if st.button("Cập nhật"):
                if pass_moi:
                    db.doi_mat_khau(user["username"], pass_moi)
                    st.session_state["user_info"]["password"] = pass_moi
                    controller.set('ren_pass', pass_moi, max_age=2592000) # Cập nhật luôn cookie
                    st.success("Đổi thành công!")
                    
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            controller.remove('ren_user')
            controller.remove('ren_pass')
            st.session_state.clear()
            st.rerun()

    if user["role"] == "Boss":
        app_me.hien_thi()
    elif user["role"] == "Leader":
        app_anh.hien_thi()
    elif user["role"] == "User":
        app_con.hien_thi()

if not st.session_state.get("logged_in", False):
    show_login_page()
else:
    show_dashboard()