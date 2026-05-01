import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import datetime
import json
import requests  # <-- Thư viện mới để gửi tin nhắn Discord

# ==========================================
# CẤU HÌNH BOT DISCORD (TRỢ LÝ BÁO CÁO)
# ==========================================
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1480332244039241751/dGrWgL0ZWDZ-NDqYHOdxYtC0m7zWJhTrQ98B1s4tVwXoI2VXrwdtAxBe4eNHNuvWZ7Uu"

def gui_thong_bao_discord(tin_nhan):
    if not DISCORD_WEBHOOK_URL:
        return
    data = {
        "content": tin_nhan,
        "username": "Trợ Lý Ren Studio", 
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/4712/4712010.png" # Icon con Bot cho đẹp
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn Discord: {e}")

# ==========================================
# PHẦN 1: KẾT NỐI KÉT SẮT FIREBASE
# ==========================================
if not firebase_admin._apps:
    try:
        key_dict = json.loads(st.secrets["FIREBASE_JSON"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Lỗi kết nối Secrets: {e}")

db = firestore.client()

# ==========================================
# PHẦN 2: QUẢN LÝ TÀI KHOẢN & NHÂN SỰ
# ==========================================
def kiem_tra_dang_nhap(username, password):
    user_ref = db.collection("users").document(username).get()
    if user_ref.exists:
        u = user_ref.to_dict()
        if u.get("password") == password:
            u["username"] = username
            return u
    return None

@st.cache_data(ttl=60)
def lay_danh_sach_nhan_su():
    users_ref = db.collection("users").stream()
    return [{**doc.to_dict(), "username": doc.id} for doc in users_ref]

def them_hoac_sua_nhan_su(username, password, name, role, rank, tags=None):
    if tags is None: tags = ["All"]
    db.collection("users").document(username).set({
        "password": password, "name": name, "role": role, 
        "rank": rank, "tags": tags
    }, merge=True)
    st.cache_data.clear()
    return True

def cap_nhat_ten_hien_thi(username, ten_cu, ten_moi):
    db.collection("users").document(username).update({"name": ten_moi})
    tasks_ref = db.collection("tasks").where("assignee", "==", ten_cu).stream()
    for doc in tasks_ref:
        doc.reference.update({"assignee": ten_moi})
    st.cache_data.clear()
    return True

def xoa_nhan_su(username):
    db.collection("users").document(username).delete()
    st.cache_data.clear()
    return True

def doi_mat_khau(username, pass_moi):
    db.collection("users").document(username).update({"password": pass_moi})
    st.cache_data.clear()
    return True

def thang_rank_nhan_vien(username, rank_moi, loi_nhan):
    db.collection("users").document(username).update({
        "rank": rank_moi, "rank_message": loi_nhan
    })
    st.cache_data.clear()
    return True

def cap_nhat_tai_chinh_studio(username, da_thanh_toan, studio_no):
    db.collection("users").document(username).update({
        "paid_amount": int(da_thanh_toan), "studio_debt": int(studio_no)
    })
    st.cache_data.clear()
    return True

# ==========================================
# PHẦN 3: QUẢN LÝ TASK & DỰ ÁN
# ==========================================
@st.cache_data(ttl=60)
def lay_danh_sach_task():
    tasks_ref = db.collection("tasks").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in tasks_ref]

@st.cache_data(ttl=60)
def lay_danh_sach_du_an():
    p_ref = db.collection("projects").stream()
    projects = [doc.id for doc in p_ref]
    if not projects:
        projects = ["7.1.111", "XQSH"]
        for p in projects:
            db.collection("projects").document(p).set({"name": p})
    return projects

def them_du_an(ten_du_an):
    db.collection("projects").document(ten_du_an).set({"name": ten_du_an})
    st.cache_data.clear()
    return True

def them_task_moi(project, name, tag, rank, reward, deadline):
    task_moi = {
        "project": project, "name": name, "tag": tag, "rank": rank,
        "reward": int(reward), "status": "Open", "deadline": deadline,
        "assignee": "", "Submission_Link": "", "Leader_Feedback": "",
        "retake_count": 0, "completed_at": "" 
    }
    db.collection("tasks").add(task_moi)
    st.cache_data.clear()
    
    # Báo Discord
    gui_thong_bao_discord(f"🎬 **SẾP TUNG TASK MỚI:** `[{project}] {name}`\n🏷️ Khâu: **{tag}** | 💰 Thù lao: **{reward:,} đ**\n👉 Anh em lên Chợ nhận việc ngay nhé!")
    return True

def nhan_task(task_id, user_name):
    # Lấy thông tin task để báo cáo
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    db.collection("tasks").document(task_id).update({
        "status": "In_Progress", "assignee": user_name
    })
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"🚀 **{user_name}** vừa xí phần Task: `[{t_data.get('project')}] {t_data.get('name')}`")
    return True

def nop_bai(task_id, link_drive):
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    db.collection("tasks").document(task_id).update({
        "status": "Pending_Leader", "Submission_Link": link_drive
    })
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"📤 **{t_data.get('assignee')}** vừa nộp bài cho Task: `[{t_data.get('project')}] {t_data.get('name')}`\n🔗 Leader vào check file nhé: {link_drive}")
    return True

def sua_link_nop(task_id, link_moi):
    db.collection("tasks").document(task_id).update({"Submission_Link": link_moi})
    st.cache_data.clear()
    return True

def leader_duyet_pass(task_id):
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    db.collection("tasks").document(task_id).update({"status": "Pending_Boss"})
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"✅ **Leader đã duyệt** Task: `[{t_data.get('project')}] {t_data.get('name')}`.\n👑 Chờ Sếp Ren vào chốt tiền!")
    return True

def leader_yeu_cau_sua(task_id, ly_do):
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    db.collection("tasks").document(task_id).update({
        "status": "Revise", "Leader_Feedback": ly_do, 
        "Submission_Link": "", "retake_count": firestore.Increment(1) 
    })
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"🚨 Task `[{t_data.get('project')}] {t_data.get('name')}` vừa bị Leader yêu cầu SỬA LẠI!\n💬 Lý do: {ly_do}")
    return True

def tra_lai_task(task_id):
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    db.collection("tasks").document(task_id).update({
        "status": "Open", "assignee": ""
    })
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"⚠️ **{t_data.get('assignee')}** vừa bỏ nhận Task `[{t_data.get('project')}] {t_data.get('name')}`. Task đã được ném lại lên Chợ!")
    return True

def boss_duyet_task(task_id):
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    ngay_hoan_thanh = datetime.datetime.now().strftime("%d/%m/%Y")
    db.collection("tasks").document(task_id).update({
        "status": "Done", "completed_at": ngay_hoan_thanh
    })
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"💸 **SẾP ĐÃ DUYỆT FINAL** Task `[{t_data.get('project')}] {t_data.get('name')}` của **{t_data.get('assignee')}**! Ting ting!")
    return True

def boss_tra_ve_task(task_id, ly_do):
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    
    db.collection("tasks").document(task_id).update({
        "status": "Revise", "Leader_Feedback": f"[SẾP YÊU CẦU SỬA]: {ly_do}", 
        "Submission_Link": "", "retake_count": firestore.Increment(1)
    })
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"🚨 **SẾP QUACK** 🦆: Task `[{t_data.get('project')}] {t_data.get('name')}` làm chưa đạt!\n💬 Sếp dặn: {ly_do}")
    return True

def xoa_task(task_id):
    # 1. Chụp lại thông tin task trước khi nó "bay màu" để làm bằng chứng
    t_doc = db.collection("tasks").document(task_id).get()
    t_data = t_doc.to_dict() if t_doc.exists else {}
    ten_task = f"[{t_data.get('project', 'N/A')}] {t_data.get('name', 'N/A')}"
    nguoi_nhan = t_data.get('assignee', 'Chưa có ai nhận')

    # 2. Tiến hành xóa sổ khỏi Firebase
    db.collection("tasks").document(task_id).delete()
    st.cache_data.clear()
    
    # 3. Bắn tin nhắn báo động đỏ lên Discord
    gui_thong_bao_discord(f"🚨 **CẢNH BÁO XÓA DỮ LIỆU:** Task `{ten_task}` (Artist đang giữ: **{nguoi_nhan}**) vừa bị **XÓA VĨNH VIỄN** khỏi hệ thống Két sắt!")
    
    return True

def sua_thong_tin_task(task_id, deadline_moi, gia_tien_moi):
    db.collection("tasks").document(task_id).update({
        "deadline": deadline_moi,
        "reward": int(gia_tien_moi)
    })
    st.cache_data.clear()
    return True

# ==========================================
# PHẦN 4: KẾ TOÁN
# ==========================================
def tinh_tien_nhan_vien(username_id):
    user_doc = db.collection("users").document(username_id).get()
    if not user_doc.exists: return 0, 0, 0, 0, 0
    u = user_doc.to_dict()
    
    ten_nhan_su = u.get("name", "")
    da_thanh_toan = u.get("paid_amount", 0) 
    tien_no = u.get("studio_debt", 0)

    t_thuc = 0
    t_du = 0
    tasks = lay_danh_sach_task()
    
    for t in tasks:
        if t.get("assignee") == ten_nhan_su:
            if t.get("status") == "Done": 
                t_thuc += t.get("reward", 0)
                t_du += t.get("reward", 0)
            elif t.get("status") not in ["Open", "Paid"]:  # <--- CHỈ TÍNH TIỀN CHO CÁC TASK CHƯA NHẬN LƯƠNG
                t_du += t.get("reward", 0)
                
    # Công thức chốt số tiền phải chuyển khoản
    cho_thanh_toan = t_thuc + tien_no
    if cho_thanh_toan < 0: cho_thanh_toan = 0

    return t_thuc, t_du, cho_thanh_toan, da_thanh_toan, tien_no

def tinh_tong_chi_phi_du_an():
    tasks = lay_danh_sach_task()
    return sum([t.get('reward', 0) for t in tasks if t.get('status') == 'Done'])

# ==========================================
# PHẦN 5: THÔNG BÁO
# ==========================================
def tao_thong_bao(tieu_de, noi_dung):
    tb_id = str(int(datetime.datetime.now().timestamp()))
    thong_bao = {"id": tb_id, "title": tieu_de, "content": noi_dung, "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}
    db.collection("announcements").document(tb_id).set(thong_bao)
    st.cache_data.clear()
    
    gui_thong_bao_discord(f"📢 **LOA LOA LOA! THÔNG BÁO TỪ SẾP:**\n**{tieu_de}**\n{noi_dung}")
    return True

@st.cache_data(ttl=60)
def lay_danh_sach_thong_bao():
    tb_ref = db.collection("announcements").stream()
    danh_sach = [doc.to_dict() for doc in tb_ref]
    danh_sach.sort(key=lambda x: x.get("id", ""), reverse=True)
    return danh_sach

def xoa_thong_bao(tb_id):
    db.collection("announcements").document(tb_id).delete()
    st.cache_data.clear()
    return True