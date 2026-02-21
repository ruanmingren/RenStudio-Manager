import streamlit as st
import pandas as pd
import db_manager as db
from datetime import datetime

# Hàm lấy chính xác số ngày khoảng cách để lọc (Trễ hạn, Cận hạn)
def get_khoang_cach_ngay(deadline_str):
    if not deadline_str: return 9999 # Coi như an toàn nếu chưa set hạn
    try:
        nam_hien_tai = datetime.now().year
        deadline_dt = datetime.strptime(f"{deadline_str}/{nam_hien_tai}", "%d/%m/%Y")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return (deadline_dt - today).days
    except:
        return 9999

def hien_thi():
    st.header("👑 Trụ sở chính - Bảng Điều Khiển")
    st.markdown("---")
    tasks = db.lay_danh_sach_task()
    
    tab_tongquan, tab_taichinh, tab_duyet, tab_sanxuat, tab_nhansu, tab_chotluong = st.tabs([
        "📊 Tiến độ", "💰 Kế toán", "✅ Kho Duyệt", "🎬 Sản Xuất", "👥 Nhân sự", "🧾 Chốt Lương"
    ])
    
    # ==========================================
    # TAB 1: GIÁM SÁT TIẾN ĐỘ THÔNG MINH
    # ==========================================
    with tab_tongquan:
        st.subheader("🎯 Giám sát Tiến độ & Deadline")
        if tasks:
            # Phân loại task theo nhóm
            task_open = [t for t in tasks if t.get("status") == "Open"]
            task_dang_lam = [t for t in tasks if t.get("status") in ['In_Progress', 'Revise', 'Pending_Leader', 'Pending_Boss']]
            task_done = [t for t in tasks if t.get("status") == 'Done']
            
            task_tre_han = []
            task_can_han = []
            
            # Lọc riêng các task có vấn đề về thời gian (chỉ xét task chưa hoàn thành)
            for t in tasks:
                if t.get("status") != 'Done':
                    kc = get_khoang_cach_ngay(t.get('deadline', ''))
                    if kc < 0:
                        task_tre_han.append(t)
                    elif kc in [0, 1]: # Còn 0 ngày (hôm nay) hoặc 1 ngày (ngày mai)
                        task_can_han.append(t)

            # 1. Các task có nguy cơ cao (Show lên đầu)
            with st.expander(f"🚨 TRỄ DEADLINE ({len(task_tre_han)} task)", expanded=True if task_tre_han else False):
                if not task_tre_han: st.success("Tuyệt vời! Không có task nào trễ hạn.")
                for t in task_tre_han:
                    kc = get_khoang_cach_ngay(t.get('deadline'))
                    st.error(f"**[{t.get('project')}] {t.get('name')}** | Artist: {t.get('assignee', 'Chưa có')} | Quá hạn {-kc} ngày!")

            with st.expander(f"⚠️ CẬN DEADLINE (Còn <= 1 ngày) ({len(task_can_han)} task)", expanded=True if task_can_han else False):
                if not task_can_han: st.info("Chưa có task nào rớt vào vòng nguy hiểm.")
                for t in task_can_han:
                    kc = get_khoang_cach_ngay(t.get('deadline'))
                    chu_thich = "Hôm nay!" if kc == 0 else "Còn 1 ngày!"
                    st.warning(f"**[{t.get('project')}] {t.get('name')}** | Artist: {t.get('assignee', 'Chưa có')} | {chu_thich}")

            st.markdown("---")
            
            # 2. Tổng quan trạng thái các task
            with st.expander(f"🛒 Chưa ai nhận ({len(task_open)} task)"):
                for t in task_open:
                    st.write(f"- **[{t.get('project')}] {t.get('name')}** | Hạn: {t.get('deadline', 'Chưa có')}")
                    
            with st.expander(f"🔥 Đang làm ({len(task_dang_lam)} task)"):
                for t in task_dang_lam:
                    # Ghi rõ đang kẹt ở khâu nào
                    tt = t.get('status')
                    if tt == 'In_Progress': tt_vn = "Đang vẽ"
                    elif tt == 'Revise': tt_vn = "Đang sửa"
                    elif tt == 'Pending_Leader': tt_vn = "Chờ Leader"
                    else: tt_vn = "Chờ Sếp duyệt"
                    
                    st.write(f"- **[{t.get('project')}] {t.get('name')}** | Artist: {t.get('assignee')} | Trạng thái: **{tt_vn}**")
                    
            with st.expander(f"🌟 Đã hoàn thành ({len(task_done)} task)"):
                for t in task_done:
                    st.write(f"- **[{t.get('project')}] {t.get('name')}** | Thực hiện bởi: {t.get('assignee')}")
        else:
            st.info("Chưa có dữ liệu task trong hệ thống.")

    # ==========================================
    # TAB 2: KẾ TOÁN & TÀI CHÍNH CHI TIẾT
    # ==========================================
    with tab_taichinh:
        st.subheader("🏦 Quản lý Ngân sách Studio")
        
        # TÍNH TOÁN CÁC QUỸ
        tong_ngan_sach = sum(t.get('reward', 0) for t in tasks) # Bao gồm tất cả task
        tong_chi = sum(t.get('reward', 0) for t in tasks if t.get('status') == 'Done')
        tong_treo = sum(t.get('reward', 0) for t in tasks if t.get('status') in ['In_Progress', 'Revise', 'Pending_Leader', 'Pending_Boss'])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 TỔNG QUỸ DỰ KIẾN", f"{tong_ngan_sach:,} đ", help="Tổng ngân sách cần chuẩn bị cho tất cả task đã giao")
        col2.metric("💸 Đã chốt (Phải trả)", f"{tong_chi:,} đ")
        col3.metric("⏳ Đang thực hiện", f"{tong_treo:,} đ", help="Tiền task đang chạy, sắp phải thanh toán")
        
        st.markdown("---")
        st.subheader("💵 Bảng lương chi tiết nhân sự")
        users = db.lay_danh_sach_nhan_su()
        luong_data = []
        for u in users:
            thuc, du = db.tinh_tien_nhan_vien(u['name'])
            # SHOW TẤT CẢ NHÂN SỰ kể cả chưa có lương
            luong_data.append({
                "Tên nhân sự": u['name'], 
                "Vai trò": u.get('role', 'User'),
                "Đã chốt (VNĐ)": thuc, 
                "Đang làm (VNĐ)": du
            })
            
        if luong_data:
            # Sắp xếp để Boss và Leader lên đầu cho dễ nhìn
            df_luong = pd.DataFrame(luong_data)
            st.dataframe(df_luong, use_container_width=True, hide_index=True)

    # ==========================================
    # CÁC TAB CÒN LẠI (GIỮ NGUYÊN)
    # ==========================================
    with tab_duyet:
        st.subheader("✅ Duyệt bài Final (Chốt tiền)")
        cho_duyet = [t for t in tasks if t.get("status") == "Pending_Boss"]
        if not cho_duyet:
            st.success("Bàn làm việc trống trải, Sếp có thể đi cà phê!")
        for t in cho_duyet:
            with st.container(border=True):
                st.info(f"**[{t.get('project')}] {t.get('name')}** | Tác giả: {t.get('assignee')} | Giá: {t.get('reward', 0):,} đ")
                st.markdown(f"🔗 [Bấm để kiểm tra bài]({t.get('Submission_Link', '#')})")
                ly_do = st.text_input("Ghi chú trả về:", key=f"note_{t['id']}")
                col1, col2 = st.columns(2)
                if col1.button("💸 Đạt! Duyệt & Chốt Tiền", key=f"ok_{t['id']}", type="primary"):
                    db.boss_duyet_task(t['id']); st.rerun()
                if col2.button("❌ Trả về bắt sửa", key=f"no_{t['id']}"):
                    if ly_do: db.boss_tra_ve_task(t['id'], ly_do); st.rerun()
                    else: st.warning("Hãy ghi lý do để Artist biết đường sửa bài.")

    with tab_sanxuat:
        col_da, col_t = st.columns([1, 2])
        with col_da:
            st.subheader("📁 Thêm Dự án")
            ten_da = st.text_input("Tên dự án mới")
            if st.button("Tạo Dự án") and ten_da: 
                db.them_du_an(ten_da); st.success("Đã thêm!"); st.rerun()
        
        with col_t.container():
            st.subheader("➕ Tung Task Lên Chợ")
            p_moi = st.selectbox("Thuộc dự án", db.lay_danh_sach_du_an())
            n_moi = st.text_input("Tên việc (VD: Cut 05 - Genga)")
            c_tag, c_tien = st.columns(2)
            tag_moi = c_tag.selectbox("Khâu (Tag)", ["LO", "Sakkan", "Nigen", "Douga", "Shiage", "Concept", "Background", "Illustration"])
            r_moi = c_tien.number_input("Thù lao (VNĐ)", min_value=0, step=50000)
            d_moi = st.text_input("Hạn nộp (Ghi đúng định dạng DD/MM, VD: 26/02)")
            
            if st.button("🚀 Tung lên Chợ", type="primary") and n_moi:
                db.them_task_moi(p_moi, n_moi, tag_moi, "B", r_moi, d_moi)
                st.success("Task đã bay lên chợ!"); st.rerun()
        st.markdown("---")
        st.subheader("🗑️ Xóa Task (Dọn dẹp rác)")
        st.warning("⚠️ LƯU Ý KẾ TOÁN: Xóa task đang có trạng thái 'Done' sẽ làm TỤT LƯƠNG của Artist trong bảng tính!")
        
        # Lấy danh sách task để Sếp chọn (kèm theo trạng thái để Sếp biết đường né)
        if tasks:
            danh_sach_xoa = {f"[{t.get('status')}] {t.get('project')} - {t.get('name')} (Artist: {t.get('assignee', 'Trống')})": t['id'] for t in tasks}
            task_can_xoa = st.selectbox("📌 Chọn task muốn xóa vĩnh viễn khỏi hệ thống:", list(danh_sach_xoa.keys()))
            
            if st.button("❌ Bấm để Xóa Vĩnh Viễn", type="secondary"):
                task_id_xoa = danh_sach_xoa[task_can_xoa]
                db.xoa_task(task_id_xoa)
                st.success("Đã ném task vào lò đốt rác thành công!")
                st.rerun()
        else:
            st.info("Hiện không có task nào trong hệ thống để xóa.")

    # ==========================================
    # TAB 5: QUẢN LÝ NHÂN SỰ (FULL CHỨC NĂNG)
    # ==========================================
    with tab_nhansu:
        st.subheader("📋 Danh sách Nhân sự")
        ns = db.lay_danh_sach_nhan_su()
        if ns:
            st.dataframe(pd.DataFrame(ns)[['username', 'name', 'role', 'rank']], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có nhân sự nào.")
        
        st.markdown("---")
        
        # 1. TÍNH NĂNG THÊM NHÂN SỰ MỚI
        st.subheader("➕ Thêm Nhân Sự Mới (Cấp Tài Khoản)")
        with st.expander("Bấm để mở biểu mẫu tạo tài khoản", expanded=False):
            col_id, col_pass = st.columns(2)
            new_user = col_id.text_input("Tên đăng nhập (ID viết liền, vd: hoang_artist)")
            new_pass = col_pass.text_input("Mật khẩu tạm (Nhân viên có thể tự đổi sau)")
            
            col_name, col_role = st.columns(2)
            new_name = col_name.text_input("Tên hiển thị (VD: Animator Hoàng)")
            new_role = col_role.selectbox("Vai trò", ["User", "Leader", "Boss"])
            
            new_rank = st.selectbox("Đánh giá Hạng (Rank ban đầu)", ["Thực tập", "C", "B", "A", "S"])
            
            if st.button("✅ Khởi tạo Tài Khoản", type="primary"):
                if new_user and new_pass and new_name:
                    db.them_hoac_sua_nhan_su(new_user, new_pass, new_name, new_role, new_rank)
                    st.success(f"Đã cấp thẻ nhân viên thành công cho: {new_name}!")
                    st.rerun()
                else:
                    st.warning("⚠️ Sếp điền thiếu Tên đăng nhập, Mật khẩu hoặc Tên hiển thị kìa!")

        st.markdown("---")
        
        # 2. TÍNH NĂNG THĂNG HẠNG
        st.subheader("🎖️ Thăng Hạng & Ghi Nhận")
        with st.expander("Bấm để thăng hạng cho nhân viên"):
            if ns:
                target = st.selectbox("Chọn nhân sự", [u['username'] for u in ns if u['role'] != 'Boss'])
                rank_moi = st.selectbox("Hạng mới", ["S", "A", "B", "C", "Thực tập"])
                loi_nhan = st.text_area("Lời nhắn chúc mừng từ Sếp (VD: Làm tốt lắm em!)")
                if st.button("🌟 Xác nhận Thăng Hạng"):
                    db.thang_rank_nhan_vien(target, rank_moi, loi_nhan)
                    st.success(f"Đã thăng hạng {target}!"); st.rerun()

        st.markdown("---")
        
        # 3. TÍNH NĂNG XÓA/SA THẢI NHÂN SỰ
        st.subheader("🗑️ Sa thải / Xóa nhân sự")
        if ns:
            id_xoa = st.selectbox("Chọn tài khoản xóa", [u['username'] for u in ns if u['role'] != 'Boss'])
            if st.button("❌ Xóa vĩnh viễn", type="secondary"):
                db.xoa_nhan_su(id_xoa)
                st.success(f"Đã xóa tài khoản {id_xoa} khỏi Studio!")
                st.rerun()

    # ==========================================
    # TAB 6: CHỐT LƯƠNG TỪNG CÁ NHÂN (TÍNH NĂNG MỚI)
    # ==========================================
    with tab_chotluong:
        st.subheader("🧾 Bảng Tính Lương Chi Tiết Từng Nhân Sự")
        st.write("Dùng để soi chi tiết chất lượng công việc, tính thưởng và trừ tiền trễ hạn.")
        
        ns_artist = [u['name'] for u in ns if u['role'] != 'Boss']
        if not ns_artist:
            st.info("Chưa có nhân sự nào trong hệ thống.")
        else:
            # 1. Bảng điều khiển chọn người và chọn ngày
            col_chon_nguoi, col_chon_ngay = st.columns([1, 1])
            nv_chon = col_chon_nguoi.selectbox("👤 Chọn nhân sự cần tính lương:", ns_artist)
            
            # Chọn khoảng thời gian
            ngay_loc = col_chon_ngay.date_input(
                "📅 Khoảng thời gian duyệt bài (Từ ngày - Đến ngày):", 
                value=(datetime.today(), datetime.today())
            )

            st.markdown("---")
            
            # 2. Xử lý Logic lọc Task Đã Hoàn Thành
            if len(ngay_loc) == 2:
                ngay_bat_dau, ngay_ket_thuc = ngay_loc
                
                # Lọc task của nhân viên này VÀ đã Done
                task_da_xong = [t for t in tasks if t.get("assignee") == nv_chon and t.get("status") == "Done"]
                
                # Lọc tiếp theo khoảng thời gian Boss chọn
                task_hop_le = []
                for t in task_da_xong:
                    completed_str = t.get("completed_at", "")
                    if completed_str:
                        try:
                            # Đổi chuỗi DD/MM/YYYY thành định dạng Date để so sánh
                            d = datetime.strptime(completed_str, "%d/%m/%Y").date()
                            if ngay_bat_dau <= d <= ngay_ket_thuc:
                                task_hop_le.append(t)
                        except:
                            pass # Bỏ qua nếu lỗi định dạng ngày cũ
                    else:
                        # Nếu task cũ chưa có ngày hoàn thành, tạm thời cho vào luôn để Boss tự quyết
                        task_hop_le.append(t)
                
                # 3. Hiển thị chi tiết từng Task để Boss soi
                st.subheader(f"Các task đã hoàn thành trong đợt ({len(task_hop_le)} task)")
                tong_luong_co_ban = 0
                
                if not task_hop_le:
                    st.info("Nhân sự này không hoàn thành task nào trong khoảng thời gian trên.")
                else:
                    for t in task_hop_le:
                        tong_luong_co_ban += t.get("reward", 0)
                        
                        # Soi chất lượng: Retake và Deadline
                        so_lan_retake = t.get("retake_count", 0)
                        canh_bao_retake = f"⚠️ Bị trả về sửa {so_lan_retake} lần" if so_lan_retake > 0 else "✅ 1 Phát Ăn Ngay"
                        
                        # Tạm tính xem có trễ hạn không (So sánh deadline và ngày nộp)
                        ghi_chu_tre = "*(Cần kiểm tra lại hạn)*"
                        
                        with st.expander(f"📁 [{t.get('project')}] {t.get('name')} - {t.get('reward', 0):,} đ | {canh_bao_retake}"):
                            st.write(f"- **Khâu (Tag):** {t.get('tag')}")
                            st.write(f"- **Hạn chót (Deadline):** {t.get('deadline', 'Chưa có')}")
                            st.write(f"- **Ngày Sếp duyệt xong:** {t.get('completed_at', 'Chưa ghi nhận')}")
                            st.write(f"- **Số lần bắt sửa (Retake):** {so_lan_retake} lần")
                            st.markdown(f"🔗 [Link file lưu trữ]({t.get('Submission_Link', '#')})")

                # 4. Bảng Chốt Lương Cuối Cùng
                st.markdown("---")
                st.subheader("🧮 TỔNG KẾT & CHỐT LƯƠNG")
                st.write(f"**Lương cơ bản (Theo task):** {tong_luong_co_ban:,} đ")
                
                col_thuong, col_phat = st.columns(2)
                tien_thuong = col_thuong.number_input("➕ Lương Thưởng (Năng suất cao, vv...)", min_value=0, step=50000, value=0)
                tien_phat = col_phat.number_input("➖ Trừ Lương (Trễ hạn, Retake nhiều...)", min_value=0, step=50000, value=0)
                
                luong_thuc_lanh = tong_luong_co_ban + tien_thuong - tien_phat
                
                # Hiển thị số tiền to rõ ràng
                st.success(f"## 💵 TỔNG THỰC LÃNH: {luong_thuc_lanh:,} VNĐ")
            else:
                st.warning("Vui lòng chọn đầy đủ 'Từ ngày' và 'Đến ngày' để hệ thống tính toán.")            