import streamlit as st
import db_manager as db
import time
from datetime import datetime

def tinh_ngay_con_lai(deadline_str):
    try:
        if not deadline_str: return "Chưa có hạn", "gray"
        nam_hien_tai = datetime.now().year
        deadline_dt = datetime.strptime(f"{deadline_str}/{nam_hien_tai}", "%d/%m/%Y")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        gap = (deadline_dt - today).days
        if gap < 0: return f"⚠️ Quá hạn {-gap} ngày", "red"
        elif gap == 0: return "🔥 Hạn cuối hôm nay!", "#FF4B4B"
        else: return f"⏳ Còn {gap} ngày", "#00FF00"
    except: return f"📅 Hạn: {deadline_str}", "gray"

def hien_thi():
    user_info = st.session_state["user_info"]
    username_id = user_info["username"]
    ten_nhan_su = user_info["name"]
    
    # 0. LẤY DATA NGAY TỪ ĐẦU
    all_users = db.lay_danh_sach_nhan_su()
    u_data = next((u for u in all_users if u['username'] == username_id), None)
    user_tags = u_data.get("tags", ["All"]) if u_data else ["All"]

    # === GẮN BẢNG THÔNG BÁO VÀO CỘT TRÁI ===
    with st.sidebar:
        st.markdown("---")
        st.subheader("📢 Bảng Tin Studio")
        ds_tb = db.lay_danh_sach_thong_bao()
        if ds_tb:
            for tb in ds_tb:
                with st.container(border=True):
                    st.markdown(f"**{tb['title']}**")
                    st.caption(f"🕒 {tb['time']}")
                    st.write(tb['content'])
        else:
            st.info("Hiện không có thông báo nào mới.")

    # 1. THÔNG BÁO THĂNG RANK
    if u_data and u_data.get("rank_message"):
        st.balloons()
        st.success(f"### 🎉 CHÚC MỪNG BẠN ĐÃ LÊN HẠNG: {u_data.get('rank')} \n\n **Sếp nhắn:** {u_data.get('rank_message')}")
        db.db.collection("users").document(username_id).update({"rank_message": ""})

    st.header(f"👶 Không gian của {ten_nhan_su}")
    st.markdown("---")
    
    # 2. KHU VỰC THÔNG TIN TÀI CHÍNH (4 CỘT) & BẢO MẬT
    col_info, col_pass = st.columns([2, 1])
    with col_info:
        st.subheader("💵 Báo cáo Thu nhập")
        t_thuc, t_du, t_cho, t_chinh, t_no = db.tinh_tien_nhan_vien(username_id)
        
        c1, c2 = st.columns(2)
        c1.metric(label="💰 Thực tế (Đã duyệt)", value=f"{t_thuc:,} đ")
        c2.metric(label="⏳ Dự kiến (Tổng task)", value=f"{t_du:,} đ")
        
        c3, c4 = st.columns(2)
        c3.metric(label="🔥 Chờ thanh toán (+Nợ)", value=f"{t_cho:,} đ", help="Tiền chờ Sếp chuyển khoản (Đã cộng tiền Sếp thưởng thêm)")
        c4.metric(label="✅ Chính thức (Đã nhận)", value=f"{t_chinh:,} đ", help="Tiền Sếp đã chuyển khoản thành công")

    with col_pass:
        st.subheader("🔐 Cá nhân")
        with st.expander("Thông tin & Bảo mật", expanded=True):
            st.write(f"**Hạng:** {u_data.get('rank', 'N/A') if u_data else 'N/A'}")
            st.write(f"**Tag chuyên môn:** {', '.join(user_tags)}")
            
            # Tính năng tự đổi tên
            new_name = st.text_input("Đổi tên hiển thị (Nickname):", value=ten_nhan_su)
            if st.button("Lưu Tên Mới", type="primary"):
                if new_name and new_name != ten_nhan_su:
                    db.cap_nhat_ten_hien_thi(username_id, ten_nhan_su, new_name)
                    st.session_state["user_info"]["name"] = new_name
                    st.success("Đổi tên thành công!"); st.rerun()

            # Đổi mật khẩu
            new_pass = st.text_input("Đổi mật khẩu mới:", type="password")
            if st.button("Xác nhận đổi MK"):
                if new_pass:
                    db.doi_mat_khau(username_id, new_pass)
                    st.success("Đã cập nhật mật khẩu mới!")

    st.markdown("---")
    tasks = db.lay_danh_sach_task()
    
    # 3. VIỆC ĐANG LÀM & CẦN SỬA
    st.subheader("📝 Việc đang làm & Cần sửa")
    task_dang_lam = [t for t in tasks if t.get("assignee") == ten_nhan_su and t.get("status") in ["In_Progress", "Revise"]]
    
    if not task_dang_lam: st.info("Chưa có task nào đang làm.")
    for t in task_dang_lam:
        thong_bao_han, mau_sac = tinh_ngay_con_lai(t.get('deadline', ''))
        with st.expander(f"🔥 [{t.get('project')}] {t.get('name')}", expanded=True):
            st.markdown(f"**Deadline:** {t.get('deadline')} | <span style='color:{mau_sac}; font-weight:bold'>{thong_bao_han}</span>", unsafe_allow_html=True)
            st.write(f"💵 Thù lao: **{t.get('reward', 0):,} đ**")
            
            if t.get("status") == "Revise":
                st.error(f"🚨 YÊU CẦU SỬA: {t.get('Leader_Feedback', '')}")
            
            link_nop = st.text_input("🔗 Dán link Google Drive nộp bài:", key=f"link_{t.get('id')}")
            col_nop, col_tra = st.columns(2)
            with col_nop:
                if st.button("📤 Gửi bài cho Leader", key=f"nop_{t.get('id')}", type="primary", use_container_width=True):
                    if link_nop:
                        db.nop_bai(t.get("id"), link_nop)
                        st.success("Đã nộp bài!"); st.rerun()
            with col_tra:
                if st.button(f"⚠️ Hủy Task (Trả về Chợ)", key=f"tra_{t['id']}", type="secondary", use_container_width=True):
                    db.tra_lai_task(t['id'])
                    st.warning("Đã hủy và trả task về chợ!"); st.rerun()

    # 4. BÀI ĐÃ NỘP (ĐANG CHỜ DUYỆT)
    st.subheader("⏳ Bài đã nộp (Đang chờ duyệt)")
    # BỘ LỌC BẤT TỬ: Lấy tất cả task KHÁC Open, Done, In_Progress, Revise
    task_cho = [t for t in tasks if t.get("assignee") == ten_nhan_su and t.get("status") not in ["Open", "Done", "In_Progress", "Revise"]]
    
    if not task_cho: st.caption("Hiện không có bài nào đang chờ duyệt.")
    for t in task_cho:
        tt_hien_tai = t.get("status")
        if tt_hien_tai == "Pending_Leader": tt_text = "Chờ Leader"
        elif tt_hien_tai == "Pending_Boss": tt_text = "Chờ Sếp duyệt"
        else: tt_text = f"Đang chờ ({tt_hien_tai})" # Hiển thị luôn lỗi sai chữ của Leader để Sếp dễ bắt giò
        
        with st.expander(f"⏳ **[{t.get('project')}] {t.get('name')}** — *{tt_text}*"):
            st.markdown(f"🔗 **Link hiện tại:** [Xem file nộp]({t.get('Submission_Link', '')})")
            new_link = st.text_input("Cập nhật lại link Drive mới:", key=f"uplink_{t['id']}")
            if st.button("🔄 Cập nhật Link", key=f"btn_up_{t['id']}"):
                if new_link:
                    db.sua_link_nop(t["id"], new_link)
                    st.success("Đã cập nhật!"); st.rerun()

    st.markdown("---")
    
    # 5. CHỢ TASK (SMART FILTER BẰNG TAG)
    st.subheader("🛒 Chợ Task Studio")
    task_tren_cho = [t for t in tasks if t.get("status") == "Open"]
    
    # LỌC THEO TAG CỦA USER
    if "All" not in user_tags:
        task_tren_cho = [t for t in task_tren_cho if t.get("tag") in user_tags or t.get("tag") == "All"]
    
    col_loc1, col_loc2 = st.columns(2)
    du_an_loc = col_loc1.selectbox("📌 Lọc theo Dự án", ["Tất cả"] + db.lay_danh_sach_du_an())
    
    # Dropdown tag lọc chỉ hiển thị những tag user có (hoặc All)
    luachon_tag = ["Tất cả"] + user_tags if "All" not in user_tags else ["Tất cả", "All", "LO", "Sakkan", "Nigen", "Douga", "Shiage", "Concept", "Background", "Illustration"]
    tag_loc = col_loc2.selectbox("🏷️ Lọc theo Khâu", luachon_tag)
    
    if du_an_loc != "Tất cả": task_tren_cho = [t for t in task_tren_cho if t.get("project") == du_an_loc]
    if tag_loc != "Tất cả": task_tren_cho = [t for t in task_tren_cho if t.get("tag") == tag_loc]
        
    if not task_tren_cho:
        st.info("Chợ đang trống hoặc Sếp chưa giao Task thuộc chuyên môn (Tag) của bạn.")
        
    for t in task_tren_cho:
        thong_bao_han, mau_sac = tinh_ngay_con_lai(t.get('deadline', ''))
        with st.container(border=True):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.markdown(f"**[{t.get('project')}] {t.get('name')}**")
                st.markdown(f"Khâu: `{t.get('tag')}` | Giá: **{t.get('reward', 0):,} đ**")
                st.markdown(f"<span style='color:{mau_sac}'>{thong_bao_han}</span> (Hạn: {t.get('deadline')})", unsafe_allow_html=True)
            with col_b:
                if st.button("🚀 Đăng ký", key=f"nhan_{t.get('id')}", use_container_width=True):
                    db.nhan_task(t.get("id"), ten_nhan_su)
                    st.rerun()