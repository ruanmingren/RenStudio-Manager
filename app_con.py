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
    
    # === GẮN BẢNG THÔNG BÁO VÀO CỘT TRÁI (SIDEBAR) - ĐÃ CHUYỂN VÀO ĐÂY ===
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

    # 1. KIỂM TRA THÔNG BÁO THĂNG RANK & BÓNG BAY (10 giây)
    all_users = db.lay_danh_sach_nhan_su()
    u_data = next((u for u in all_users if u['username'] == username_id), None)
    
    if u_data and u_data.get("rank_message"):
        st.balloons()
        st.toast(f"🔔 Bạn có thông báo mới từ Sếp Ren!")
        st.success(f"### 🎉 CHÚC MỪNG BẠN ĐÃ LÊN HẠNG: {u_data.get('rank')} \n\n **Lời nhắn từ Sếp:** {u_data.get('rank_message')}")
        placeholder = st.empty()
        for i in range(10, 0, -1):
            placeholder.write(f"✨ Thông báo này sẽ đóng sau {i} giây...")
            time.sleep(1)
        placeholder.empty()
        db.db.collection("users").document(username_id).update({"rank_message": ""})
        st.rerun()

    st.header(f"👶 Chào {ten_nhan_su} - Không gian làm việc")
    st.markdown("---")
    
    # 2. KHU VỰC THÔNG TIN TÀI CHÍNH & ĐỔI PASS
    col_info, col_pass = st.columns(2)
    with col_info:
        tien_thuc_te, tien_du_kien = db.tinh_tien_nhan_vien(ten_nhan_su)
        st.metric(label="💰 Thu nhập thực tế (Đã chốt)", value=f"{tien_thuc_te:,} đ")
        st.metric(label="⏳ Thu nhập dự kiến (Đang làm)", value=f"{tien_du_kien:,} đ")
        
    with col_pass:
        with st.expander("🔐 Tài khoản & Bảo mật"):
            st.write(f"**Hạng hiện tại:** {u_data.get('rank', 'N/A') if u_data else 'N/A'}")
            st.caption("Chỉ Sếp mới có quyền thay đổi Rank.")
            new_pass = st.text_input("Đổi mật khẩu mới:", type="password")
            if st.button("Xác nhận đổi mật khẩu"):
                if new_pass:
                    db.doi_mat_khau(username_id, new_pass)
                    st.success("Đã cập nhật mật khẩu mới!")
                else:
                    st.warning("Vui lòng nhập mật khẩu.")

    st.markdown("---")
    tasks = db.lay_danh_sach_task()
    
# 3. VIỆC ĐANG LÀM & CẦN SỬA
    st.subheader("📝 Việc đang làm & Cần sửa")
    task_dang_lam = [t for t in tasks if t.get("assignee") == ten_nhan_su and t.get("status") in ["In_Progress", "Revise"]]
    
    if not task_dang_lam:
        st.info("Chưa có task nào đang làm.")
    for t in task_dang_lam:
        thong_bao_han, mau_sac = tinh_ngay_con_lai(t.get('deadline', ''))
        with st.expander(f"🔥 [{t.get('project')}] {t.get('name')}", expanded=True):
            st.markdown(f"**Deadline:** {t.get('deadline')} | <span style='color:{mau_sac}; font-weight:bold'>{thong_bao_han}</span>", unsafe_allow_html=True)
            st.write(f"💵 Thù lao: **{t.get('reward', 0):,} đ**")
            
            if t.get("status") == "Revise":
                st.error(f"🚨 YÊU CẦU SỬA: {t.get('Leader_Feedback', '')}")
            
            link_nop = st.text_input("🔗 Dán link Google Drive nộp bài:", key=f"link_{t.get('id')}")
            
            # --- TUI CHIA 2 CỘT CHO NÚT NỘP VÀ TRẢ TASK ĐẸP MẮT ---
            col_nop, col_tra = st.columns(2)
            with col_nop:
                if st.button("📤 Gửi bài cho Leader", key=f"nop_{t.get('id')}", type="primary", use_container_width=True):
                    if link_nop:
                        db.nop_bai(t.get("id"), link_nop)
                        st.success("Đã nộp bài!"); st.rerun()
            with col_tra:
                # ---> NÚT TRẢ TASK NẰM Ở ĐÂY MỚI CHUẨN <---
                if st.button(f"⚠️ Bỏ nhận (Trả về Chợ)", key=f"tra_{t['id']}", type="secondary", use_container_width=True):
                    db.tra_lai_task(t['id'])
                    st.warning(f"Đã trả task '{t['name']}' về Chợ thành công!")
                    st.rerun()

    # 4. BÀI ĐÃ NỘP (DẠNG NGĂN KÉO GỌN GÀNG)
    st.subheader("⏳ Bài đã nộp (Đang chờ duyệt)")
    task_cho = [t for t in tasks if t.get("assignee") == ten_nhan_su and t.get("status") in ["Pending_Leader", "Pending_Boss"]]
    
    if not task_cho:
        st.caption("Hiện không có bài nào đang chờ duyệt.")
    for t in task_cho:
        icon_status = "⏳" if t.get("status") == "Pending_Leader" else "🏛️"
        trang_thai_text = "Chờ Leader" if t.get("status") == "Pending_Leader" else "Chờ Sếp duyệt"
        
        with st.expander(f"{icon_status} **[{t.get('project')}] {t.get('name')}** — *{trang_thai_text}*"):
            st.markdown(f"🔗 **Link hiện tại:** [Xem file nộp]({t.get('Submission_Link', '')})")
            new_link = st.text_input("Cập nhật lại link Drive mới (nếu nhầm):", key=f"uplink_{t['id']}")
            if st.button("🔄 Cập nhật Link", key=f"btn_up_{t['id']}"):
                if new_link:
                    db.sua_link_nop(t["id"], new_link)
                    st.success("Đã cập nhật link mới!"); st.rerun()
    

    st.markdown("---")
    
    # 5. CHỢ TASK (CÓ BỘ LỌC)
    st.subheader("🛒 Chợ Task Studio")
    task_tren_cho = [t for t in tasks if t.get("status") == "Open"]
    
    col_loc1, col_loc2 = st.columns(2)
    du_an_loc = col_loc1.selectbox("📌 Lọc theo Dự án", ["Tất cả"] + db.lay_danh_sach_du_an())
    tag_loc = col_loc2.selectbox("🏷️ Lọc theo Khâu (Tag)", ["Tất cả", "LO", "Sakkan", "Nigen", "Douga", "Shiage", "Concept", "Background", "Illustration"])
    
    if du_an_loc != "Tất cả": task_tren_cho = [t for t in task_tren_cho if t.get("project") == du_an_loc]
    if tag_loc != "Tất cả": task_tren_cho = [t for t in task_tren_cho if t.get("tag") == tag_loc]
        
    if not task_tren_cho:
        st.info("Chợ đang trống hoặc không có task phù hợp. Chờ Sếp tung việc nhé!")
        
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