import streamlit as st
import pandas as pd
import db_manager as db
from datetime import datetime
import time

def get_khoang_cach_ngay(deadline_str):
    if not deadline_str: return 9999 
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
            task_open = [t for t in tasks if t.get("status") == "Open"]
            task_done = [t for t in tasks if t.get("status") == 'Done']
            # BỘ LỌC BẤT TỬ: Bỏ qua các task đã Open, Done, và Paid
            task_dang_lam = [t for t in tasks if t.get("status") not in ['Open', 'Done', 'Paid']]
            
            task_tre_han = []
            task_can_han = []
            
            for t in tasks:
                if t.get("status") not in ['Done', 'Paid']:
                    kc = get_khoang_cach_ngay(t.get('deadline', ''))
                    if kc < 0:
                        task_tre_han.append(t)
                    elif kc in [0, 1]: 
                        task_can_han.append(t)

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
            
            with st.expander(f"🛒 Chưa ai nhận ({len(task_open)} task)"):
                for t in task_open:
                    st.write(f"- **[{t.get('project')}] {t.get('name')}** | Hạn: {t.get('deadline', 'Chưa có')}")
                    
            with st.expander(f"🔥 Đang làm ({len(task_dang_lam)} task)"):
                for t in task_dang_lam:
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
        st.subheader("🏦 Quản lý Ngân sách & Thanh toán")
        
        # 1. Tổng quỹ dự kiến: Bao gồm TẤT CẢ các task (Kể cả đã trả tiền), con số này chỉ TĂNG
        tong_ngan_sach = sum(t.get('reward', 0) for t in tasks)
        
        # 2. Quỹ cần trả (Đợt này): Chỉ tính các task trạng thái "Done" chờ Sếp phát lương
        tong_chi = sum(t.get('reward', 0) for t in tasks if t.get('status') == 'Done')
        
        users = db.lay_danh_sach_nhan_su()
        
        # 3. Tổng Nợ Studio: Tổng các khoản nợ từ ĐỢT TRƯỚC của tất cả nhân viên
        tong_no_studio = sum(u.get('studio_debt', 0) for u in users)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 TỔNG QUỸ DỰ KIẾN", f"{tong_ngan_sach:,} đ", help="Tổng tiền toàn bộ các task (Luôn tăng)")
        col2.metric("💸 QUỸ CẦN TRẢ (ĐỢT NÀY)", f"{tong_chi:,} đ", help="Tiền các task vừa Done, sẽ tự động trừ đi khi Sếp bấm Trả Lương")
        col3.metric("🚨 TỔNG NỢ STUDIO", f"{tong_no_studio:,} đ", help="Tổng lương còn thiếu nhân viên từ các đợt trước")

        st.markdown("---")
        st.subheader("💵 Bảng Tổng Kế Toán Toàn Studio")
        
        luong_data = []
        for u in users:
            t_thuc = sum(t.get('reward', 0) for t in tasks if t.get('assignee') == u['name'] and t.get('status') == 'Done')
            tien_no = u.get('studio_debt', 0)
            
            if t_thuc > 0 or tien_no != 0:
                luong_data.append({
                    "Tên NV": u['name'], 
                    "Lương Task (Đợt này)": t_thuc,
                    "Nợ Studio (Đợt trước)": tien_no,
                    "Tổng cần chuyển khoản": t_thuc + tien_no
                })
            
        if luong_data:
            df_luong = pd.DataFrame(luong_data)
            st.dataframe(df_luong, use_container_width=True, hide_index=True)
        else:
            st.info("Hiện không có khoản lương nào cần thanh toán.")

    # ==========================================
    # TAB 3: KHO DUYỆT
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

    # ==========================================
    # TAB 4: SẢN XUẤT
    # ==========================================
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
            tag_moi = c_tag.selectbox("Khâu (Tag)", ["All", "LO", "Sakkan", "Nigen", "Douga", "Shiage", "Concept", "Background", "Illustration"])
            r_moi = c_tien.number_input("Thù lao (VNĐ)", min_value=0, step=50000)
            d_moi = st.text_input("Hạn nộp (Ghi đúng định dạng DD/MM, VD: 26/02)")
            
            if st.button("🚀 Tung lên Chợ", type="primary") and n_moi:
                db.them_task_moi(p_moi, n_moi, tag_moi, "B", r_moi, d_moi)
                st.success("Task đã bay lên chợ!"); st.rerun()
                
        st.markdown("---")
        st.subheader("✏️ Sửa Deadline & Giá Tiền Task")
        if tasks:
            danh_sach_sua = {f"[{t.get('status')}] {t.get('project')} - {t.get('name')}": t for t in tasks}
            task_can_sua = st.selectbox("📌 Chọn task cần chỉnh sửa:", list(danh_sach_sua.keys()))
            if task_can_sua:
                t_sua = danh_sach_sua[task_can_sua]
                c_sua1, c_sua2 = st.columns(2)
                dl_moi = c_sua1.text_input("Hạn nộp mới (DD/MM):", value=t_sua.get('deadline', ''))
                gia_moi = c_sua2.number_input("Thù lao mới (VNĐ):", value=int(t_sua.get('reward', 0)), step=50000)
                
                if st.button("💾 Cập nhật thay đổi", type="primary"):
                    db.sua_thong_tin_task(t_sua['id'], dl_moi, gia_moi)
                    st.success("Đã cập nhật Deadline và Giá tiền mới vào Két sắt!")
                    st.rerun()
        else:
            st.info("Chưa có task nào để sửa.")

        st.markdown("---")
        st.subheader("🗑️ Xóa Task (Dọn dẹp rác)")
        st.warning("⚠️ LƯU Ý KẾ TOÁN: Xóa task đang có trạng thái 'Done' sẽ làm TỤT LƯƠNG của Artist trong bảng tính!")
        
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
    # TAB 5: QUẢN LÝ NHÂN SỰ
    # ==========================================
    with tab_nhansu:
        st.subheader("📋 Danh sách Nhân sự")
        ns = db.lay_danh_sach_nhan_su()
        if ns:
            df_nhansu = pd.DataFrame(ns)
            df_nhansu['Tag chuyên môn'] = df_nhansu['tags'].apply(lambda x: ", ".join(x) if isinstance(x, list) else "All")
            df_hien_thi = df_nhansu[['username', 'name', 'role', 'rank', 'Tag chuyên môn']]
            st.dataframe(df_hien_thi, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có nhân sự nào.")
        
        st.markdown("---")
        st.subheader("➕ Thêm/Sửa Nhân Sự (Cấp Tài Khoản & Tag)")
        with st.expander("Bấm để mở biểu mẫu quản lý", expanded=False):
            col_id, col_pass = st.columns(2)
            new_user = col_id.text_input("Tên đăng nhập (ID cố định, vd: hoang_artist)")
            new_pass = col_pass.text_input("Mật khẩu tạm")
            
            col_name, col_role = st.columns(2)
            new_name = col_name.text_input("Tên hiển thị")
            new_role = col_role.selectbox("Vai trò", ["User", "Leader", "Boss"])
            new_rank = st.selectbox("Hạng (Rank)", ["Thực tập", "C", "B", "A", "S"])
            
            danh_sach_tag = ["All", "Background", "Concept", "Character", "Sakkan", "LO", "Nigen", "Douga", "Shiage", "Illustration"]
            new_tags = st.multiselect("Gắn Tag Chuyên Môn (Có thể chọn nhiều)", danh_sach_tag, default=["All"])
            
            if st.button("✅ Lưu Thông Tin", type="primary"):
                if new_user and new_pass and new_name:
                    db.them_hoac_sua_nhan_su(new_user, new_pass, new_name, new_role, new_rank, new_tags)
                    st.success(f"Đã cập nhật hồ sơ cho: {new_name}!")
                    st.rerun()
                else:
                    st.warning("⚠️ Sếp điền thiếu thông tin kìa!")
        
        st.markdown("---")
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
        st.subheader("🗑️ Sa thải / Xóa nhân sự")
        if ns:
            id_xoa = st.selectbox("Chọn tài khoản xóa", [u['username'] for u in ns if u['role'] != 'Boss'])
            if st.button("❌ Xóa vĩnh viễn", type="secondary"):
                db.xoa_nhan_su(id_xoa)
                st.success(f"Đã xóa tài khoản {id_xoa} khỏi Studio!")
                st.rerun()

        st.markdown("---")
        st.subheader("🏷️ Cập nhật Tag cho nhân sự có sẵn")
        with st.expander("Bấm để gắn lại Tag chuyên môn", expanded=False):
            if ns:
                chon_nv_tag = st.selectbox("Chọn ID nhân viên cần gắn Tag:", [u['username'] for u in ns if u['role'] != 'Boss'])
                if chon_nv_tag:
                    nv_hien_tai = next(u for u in ns if u['username'] == chon_nv_tag)
                    tag_hien_tai = nv_hien_tai.get('tags', ["All"])
                    
                    danh_sach_tag = ["All", "Background", "Concept", "Character", "Sakkan", "LO", "Nigen", "Douga", "Shiage", "Illustration"]
                    tag_cap_nhat = st.multiselect(f"Chỉnh sửa Tag cho {nv_hien_tai['name']}:", danh_sach_tag, default=tag_hien_tai)
                    
                    if st.button("💾 Lưu Tag Mới", type="primary"):
                        db.db.collection("users").document(chon_nv_tag).update({"tags": tag_cap_nhat})
                        st.success(f"Đã cập nhật Tag mới cho {nv_hien_tai['name']}!")
                        st.rerun()

    # ==========================================
    # TAB 6: CHỐT LƯƠNG TỪNG CÁ NHÂN (V2.1 - SIÊU TỐI ƯU)
    # ==========================================
    with tab_chotluong:
        st.subheader("🧾 Bảng Chốt Lương & Thanh Toán Từng Nhân Sự")
        st.write("Chốt lương linh hoạt theo đợt. Bấm thanh toán xong là hệ thống tự động lưu sổ, task sẽ biến mất khỏi danh sách chờ!")
        
        ns_artist = [u for u in ns if u['role'] != 'Boss']
        if not ns_artist:
            st.info("Chưa có nhân sự nào trong hệ thống.")
        else:
            # 1. Chọn người cần trả lương
            col_chon_nguoi, _ = st.columns([1, 1])
            nv_chon_name = col_chon_nguoi.selectbox("👤 Chọn nhân sự cần trả lương:", [u['name'] for u in ns_artist])
            nv_chon_data = next(u for u in ns_artist if u['name'] == nv_chon_name)
            chon_nv_id = nv_chon_data['username']

            st.markdown("---")
            
            # 2. Hiển thị các task 'Done' chờ trả lương
            task_da_xong = [t for t in tasks if t.get("assignee") == nv_chon_name and t.get("status") == "Done"]
            
            st.subheader(f"Các task đang chờ thanh toán ({len(task_da_xong)} task)")
            tong_luong_co_ban = 0
            
            if not task_da_xong:
                st.info("Nhân sự này không có task nào đang chờ Sếp chuyển khoản.")
            else:
                for t in task_da_xong:
                    tong_luong_co_ban += t.get("reward", 0)
                    
                    # LOGIC BẮT LỖI TRỄ HẠN
                    ghi_chu_tre = ""
                    if t.get('deadline') and t.get('completed_at'):
                        try:
                            nam_hien_tai = datetime.now().year
                            dl_date = datetime.strptime(f"{t['deadline']}/{nam_hien_tai}", "%d/%m/%Y").date()
                            comp_date = datetime.strptime(t['completed_at'], "%d/%m/%Y").date()
                            if comp_date > dl_date:
                                days_late = (comp_date - dl_date).days
                                ghi_chu_tre = f" | ❌ TRỄ HẠN {days_late} NGÀY!"
                            else:
                                ghi_chu_tre = " | ✅ Đúng hạn"
                        except:
                            pass
                    
                    so_lan_retake = t.get("retake_count", 0)
                    canh_bao_retake = f"⚠️ Sửa {so_lan_retake} lần" if so_lan_retake > 0 else "✅ 1 Phát Ăn Ngay"
                    
                    with st.expander(f"📁 [{t.get('project')}] {t.get('name')} - {t.get('reward', 0):,} đ | {canh_bao_retake}{ghi_chu_tre}"):
                        st.write(f"- **Hạn chót (Deadline):** {t.get('deadline', 'Chưa có')}")
                        st.write(f"- **Ngày Sếp duyệt xong:** {t.get('completed_at', 'Chưa ghi nhận')}")
                        st.markdown(f"🔗 [Link file lưu trữ]({t.get('Submission_Link', '#')})")

            # 3. CHỐT SỔ TÀI CHÍNH
            st.markdown("---")
            st.subheader("🧮 CHỐT SỔ & XÁC NHẬN CHUYỂN KHOẢN")
            
            no_cu = nv_chon_data.get('studio_debt', 0)
            tong_can_tra = tong_luong_co_ban + no_cu
            
            st.write(f"- Lương Task (Đợt này): **{tong_luong_co_ban:,} đ**")
            st.write(f"- Lương còn thiếu (Nợ đợt trước): **{no_cu:,} đ**")
            st.success(f"### 💵 TỔNG PHẢI TRẢ ĐỢT NÀY: {tong_can_tra:,} VNĐ")
            
            st.markdown("---")
            st.write("✍️ **SẾP ĐIỀU CHỈNH TRƯỚC KHI TRẢ:**")
            
            # Ô để Sếp nhập số tiền TỰ QUYẾT định trả (Mặc định gợi ý số tổng)
            tien_chuyen_khoan = st.number_input("📲 Số tiền Sếp THỰC TẾ chuyển khoản đợt này:", value=int(tong_can_tra), step=50000)
            
            # Tính ra số dư/nợ
            no_moi = tong_can_tra - tien_chuyen_khoan
            
            if no_moi > 0:
                st.warning(f"⚠️ Sếp chuyển khoản thiếu, hệ thống sẽ tự động lưu **{no_moi:,} đ** vào Két sắt để cộng dồn trả bù vào đợt sau.")
            elif no_moi < 0:
                st.info(f"🎁 Sếp chuyển dư {-no_moi:,} đ (Hệ thống tính là Thưởng luôn đợt này, Nợ Studio sẽ reset về 0).")
                no_moi = 0 # Trả dư thì thôi, coi như thưởng nóng
                
            if st.button("✅ XÁC NHẬN ĐÃ CHUYỂN KHOẢN (LƯU SỔ SÁCH)", type="primary", use_container_width=True):
                # 1. Đánh dấu các task đợt này là 'Paid' để nó chìm đi, không tính vào đợt sau nữa
                for t in task_da_xong:
                    db.db.collection("tasks").document(t['id']).update({"status": "Paid"})
                
                # 2. Cập nhật số tiền nợ mới cho nhân viên vào Két sắt
                db.db.collection("users").document(chon_nv_id).update({"studio_debt": int(no_moi)})
                
                st.cache_data.clear()
                st.toast("✅ Đã chốt sổ và lưu lịch sử thanh toán thành công!")
                time.sleep(1.5)
                st.rerun()

    st.subheader("📢 Quản lý Bảng Thông Báo (Sidebar)")
    with st.expander("📝 Viết thông báo mới", expanded=False):
        tb_title = st.text_input("Tiêu đề thông báo (VD: Cập nhật rule ONA 7.1.111):")
        tb_content = st.text_area("Nội dung chi tiết:")
        if st.button("🚀 Phát loa thông báo", type="primary"):
            if tb_title and tb_content:
                db.tao_thong_bao(tb_title, tb_content)
                st.success("Đã ghim thông báo lên bảng của anh em!")
                st.rerun()
            else:
                st.warning("⚠️ Sếp nhập đủ tiêu đề và nội dung nhé!")

    st.write("**Lịch sử thông báo đã phát:**")
    ds_tb = db.lay_danh_sach_thong_bao()
    if ds_tb:
        for tb in ds_tb:
            with st.container(border=True):
                col_tb1, col_tb2 = st.columns([4, 1])
                with col_tb1:
                    st.markdown(f"**{tb['title']}** ({tb['time']})")
                    st.write(tb['content'])
                with col_tb2:
                    if st.button("🗑️ Xóa", key=f"del_tb_{tb['id']}"):
                        db.xoa_thong_bao(tb['id'])
                        st.success("Đã xóa thông báo!"); st.rerun()
    else:
        st.info("Chưa có thông báo nào trên bảng.")