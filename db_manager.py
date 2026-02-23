import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import datetime # Sếp xem trên đầu file có chưa, chưa có thì Sếp thêm dòng này vào nhé
import json

# ==========================================
# PHẦN 1: KẾT NỐI KÉT SẮT FIREBASE (BẢN TÀNG HÌNH)
# ==========================================
if not firebase_admin._apps:
    # Lấy chìa khóa từ Két sắt tàng hình của Streamlit
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

def lay_danh_sach_nhan_su():
    users_ref = db.collection("users").stream()
    return [{**doc.to_dict(), "username": doc.id} for doc in users_ref]

def them_hoac_sua_nhan_su(username, password, name, role, rank):
    db.collection("users").document(username).set({
        "password": password, "name": name, "role": role, "rank": rank
    }, merge=True)
    return True

def xoa_nhan_su(username):
    db.collection("users").document(username).delete()
    return True

def doi_mat_khau(username, pass_moi):
    db.collection("users").document(username).update({"password": pass_moi})
    return True

def thang_rank_nhan_vien(username, rank_moi, loi_nhan):
    db.collection("users").document(username).update({
        "rank": rank_moi,
        "rank_message": loi_nhan
    })
    return True

# ==========================================
# PHẦN 3: QUẢN LÝ TASK & DỰ ÁN
# ==========================================
def lay_danh_sach_task():
    tasks_ref = db.collection("tasks").stream()
    return [{**doc.to_dict(), "id": doc.id} for doc in tasks_ref]

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
    return True

def them_task_moi(project, name, tag, rank, reward, deadline):
    task_moi = {
        "project": project, "name": name, "tag": tag, "rank": rank,
        "reward": int(reward), "status": "Open", "deadline": deadline,
        "assignee": "", "Submission_Link": "", "Leader_Feedback": "",
        "retake_count": 0, # Mới: Bộ đếm số lần sửa
        "completed_at": "" # Mới: Lưu ngày Boss duyệt
    }
    db.collection("tasks").add(task_moi)
    return True

def nhan_task(task_id, user_name):
    db.collection("tasks").document(task_id).update({
        "status": "In_Progress", "assignee": user_name
    })
    return True

def nop_bai(task_id, link_drive):
    db.collection("tasks").document(task_id).update({
        "status": "Pending_Leader", "Submission_Link": link_drive
    })
    return True

def sua_link_nop(task_id, link_moi):
    db.collection("tasks").document(task_id).update({"Submission_Link": link_moi})
    return True

def leader_duyet_pass(task_id):
    db.collection("tasks").document(task_id).update({"status": "Pending_Boss"})
    return True

def leader_yeu_cau_sua(task_id, ly_do):
    db.collection("tasks").document(task_id).update({
        "status": "Revise", 
        "Leader_Feedback": ly_do, 
        "Submission_Link": "",
        "retake_count": firestore.Increment(1) # Tự động cộng 1 lần Retake
    })
    return True

def tra_lai_task(task_id):
    # Hàm này gỡ tên Artist ra và ném task trở lại Chợ (trạng thái Open)
    db.collection("tasks").document(task_id).update({
        "status": "Open",
        "assignee": ""
    })
    return True

def boss_duyet_task(task_id):
    # Lấy ngày hiện tại để làm ngày hoàn thành
    ngay_hoan_thanh = datetime.now().strftime("%d/%m/%Y")
    db.collection("tasks").document(task_id).update({
        "status": "Done",
        "completed_at": ngay_hoan_thanh
    })
    return True

def boss_tra_ve_task(task_id, ly_do):
    db.collection("tasks").document(task_id).update({
        "status": "Revise", 
        "Leader_Feedback": f"[SẾP YÊU CẦU SỬA]: {ly_do}", 
        "Submission_Link": "",
        "retake_count": firestore.Increment(1) # Tự động cộng 1 lần Retake
    })
    return True

# ==========================================
# PHẦN 4: KẾ TOÁN (TÍNH TOÁN DỮ LIỆU)
# ==========================================
def tinh_tien_nhan_vien(user_name):
    t_thuc = 0; t_du = 0
    tasks = lay_danh_sach_task()
    for t in tasks:
        if t.get("assignee") == user_name:
            if t.get("status") == "Done": 
                t_thuc += t.get("reward", 0)
            elif t.get("status") in ["In_Progress", "Revise", "Pending_Leader", "Pending_Boss"]: 
                t_du += t.get("reward", 0)
    return t_thuc, t_du

def tinh_tong_chi_phi_du_an():
    tasks = lay_danh_sach_task()
    return sum([t.get('reward', 0) for t in tasks if t.get('status') == 'Done'])

def xoa_task(task_id):
    db.collection("tasks").document(task_id).delete()
    return True


def tao_thong_bao(tieu_de, noi_dung):
    # Dùng thời gian thực làm ID để thông báo mới luôn xếp lên đầu
    tb_id = str(int(datetime.datetime.now().timestamp()))
    thong_bao = {
        "id": tb_id,
        "title": tieu_de,
        "content": noi_dung,
        "time": datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    db.collection("announcements").document(tb_id).set(thong_bao)
    return True

def lay_danh_sach_thong_bao():
    tb_ref = db.collection("announcements").stream()
    danh_sach = [doc.to_dict() for doc in tb_ref]
    # Sắp xếp để cái nào mới đăng sẽ nằm trên cùng
    danh_sach.sort(key=lambda x: x.get("id", ""), reverse=True)
    return danh_sach

def xoa_thong_bao(tb_id):
    db.collection("announcements").document(tb_id).delete()
    return True