import streamlit as st
import db_manager as db
import os

# Nhập 3 cái app mình vừa tách ra
import app_me
import app_anh
import app_con

st.set_page_config(page_title="Ren Studio Manager", page_icon="🎬", layout="wide")

# ==========================================
# 🎨 GIAO DIỆN BLITZIT THEME (MA THUẬT CSS)
# ==========================================
def load_blitzit_theme():
    # CHÚ Ý: 3 dấu nháy kép (""") cực kỳ quan trọng ở đây
    st.markdown("""
    <style>
    
    /* 2. Nền App tối sâu (Deep Dark) */
    .stApp {
        background-color: #0F1115;
    }

    /* 3. Bo góc và tạo bóng cho các Khung (Cards) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border: 1px solid #2A2E39 !important;
        background-color: #161923 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        border-color: #7B61FF !important; /* Viền sáng lên màu Tím Neon khi di chuột */
    }

    /* 4. Định dạng Ngăn kéo (Expander) */
    [data-testid="stExpander"] {
        border-radius: 14px !important;
        border: 1px solid #2A2E39 !important;
        background-color: #161923 !important;
    }

    /* 5. Nút Bấm (Button) Phong cách Năng lượng */
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
    
    /* Nút phụ (Secondary Button) như nút Xóa, Hủy */
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

    /* 6. Tiền và Số liệu (Xanh Neon chói lóa) */
    [data-testid="stMetricValue"] {
        color: #00E676 !important; 
        font-weight: 900 !important;
        text-shadow: 0 0 10px rgba(0, 230, 118, 0.3);
    }
    
    /* 7. Định dạng lại Tab cho nổi bật */
    button[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #A0AEC0 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #7B61FF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# GỌI HÀM KÍCH HOẠT GIAO DIỆN TẠI ĐÂY
load_blitzit_theme()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_info"] = None

def show_login_page():
    # CĂN GIỮA LOGO Ở TRANG ĐĂNG NHẬP
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        # Kiểm tra file ảnh
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
                st.rerun()
            else:
                st.error("Sai tên đăng nhập hoặc mật khẩu!")

    # THÊM TÍNH NĂNG QUÊN MẬT KHẨU (GHI CHÚ DƯỚI FORM ĐĂNG NHẬP)
    st.markdown("---")
    st.caption("🔒 **Quên Mật khẩu?** Vui lòng nhắn tin trực tiếp cho Sếp Ren trên Group Zalo/Discord để được cấp lại mật khẩu mới.")

def show_dashboard():
    user = st.session_state["user_info"]
    
    with st.sidebar:
        # CHÈN LOGO VÀO SIDEBAR
        if os.path.exists("logo_studio.png"):
            st.image("logo_studio.png", use_container_width=True) 
        st.markdown("---")
        
        st.title(f"Chào {user['name']} 👋")
        
        # LOGIC ẨN RANK CHO LEADER VÀ BOSS
        if user['role'] == 'User':
            st.write(f"**Vai trò:** Artist | **RANK:** {user.get('rank', 'N/A')}")
        else:
            st.write(f"**Vai trò:** {user['role']}")
        
        # ĐỔI MẬT KHẨU
        with st.expander("🔑 Đổi mật khẩu"):
            pass_moi = st.text_input("Nhập mật khẩu mới:", type="password")
            if st.button("Cập nhật"):
                if pass_moi:
                    db.doi_mat_khau(user["username"], pass_moi)
                    st.session_state["user_info"]["password"] = pass_moi
                    st.success("Đổi thành công!")
                    
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state.clear()
            st.rerun()

    # BỘ ĐỊNH TUYẾN SIÊU GỌN 
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