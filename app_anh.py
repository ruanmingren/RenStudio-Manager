import streamlit as st
import db_manager as db

def hien_thi():
    st.header("🛡️ App Anh - Trạm Kiểm Duyệt")
    st.markdown("---")
    
    tasks = db.lay_danh_sach_task()
    
    # Chia làm 3 Tab cho Leader dễ quản lý
    tab_duyet, tab_sua, tab_lichsu = st.tabs([
        "🔍 Cần Duyệt", "⚠️ Đang Yêu Cầu Sửa", "✅ Lịch Sử Đã Pass"
    ])
    
    # ==========================================
    # TAB 1: BÀI MỚI ARTIST NỘP
    # ==========================================
    with tab_duyet:
        cho_duyet = [t for t in tasks if t.get("status") == "Pending_Leader"]
        st.subheader(f"Bài mới chờ duyệt ({len(cho_duyet)} file)")
        
        if not cho_duyet:
            st.success("Bàn làm việc trống, Leader có thể nghỉ ngơi!")
            
        for t in cho_duyet:
            with st.expander(f"📁 [{t.get('project')}] {t.get('name')} (Artist: {t.get('assignee')})", expanded=True):
                st.markdown(f"🔗 **Link nộp:** [Bấm để xem Drive]({t.get('Submission_Link')})")
                
                ly_do_sua = st.text_area("Ghi chú/Vẽ đè lỗi (Feedback) nếu cần sửa:", key=f"err_{t['id']}")
                
                col1, col2 = st.columns(2)
                if col1.button("✅ Pass (Gửi lên Sếp)", key=f"p_{t['id']}", type="primary"):
                    db.leader_duyet_pass(t["id"])
                    st.success("Đã duyệt pass!")
                    st.rerun()
                    
                if col2.button("⚠️ Yêu cầu sửa lại", key=f"r_{t['id']}"):
                    if ly_do_sua:
                        db.leader_yeu_cau_sua(t["id"], ly_do_sua)
                        st.error("Đã trả bài về cho Artist!")
                        st.rerun()
                    else:
                        st.warning("Anh/Chị Leader hãy ghi rõ lỗi để Artist biết đường sửa nha!")

    # ==========================================
    # TAB 2: CÁC BÀI ĐANG BỊ TRẢ VỀ (CẬP NHẬT GÓP Ý)
    # ==========================================
    with tab_sua:
        dang_sua = [t for t in tasks if t.get("status") == "Revise"]
        st.subheader(f"Các bài đang chờ Artist sửa ({len(dang_sua)} file)")
        
        if not dang_sua:
            st.info("Không có task nào đang bị trả về.")
            
        for t in dang_sua:
            with st.expander(f"🚨 [{t.get('project')}] {t.get('name')} (Artist: {t.get('assignee')})"):
                st.write("**Góp ý/Feedback hiện tại:**")
                # Cho phép Leader sửa lại lời phê bình nếu lúc trước gõ thiếu ý
                new_feedback = st.text_area("Cập nhật lại góp ý (nếu cần):", value=t.get('Leader_Feedback', ''), key=f"upd_err_{t['id']}")
                
                if st.button("🔄 Cập nhật Góp ý mới", key=f"btn_upd_{t['id']}"):
                    # Chọc thẳng vào DB để sửa chữ (Tận dụng db có sẵn)
                    db.db.collection("tasks").document(t['id']).update({"Leader_Feedback": new_feedback})
                    st.success("Đã lưu lời góp ý mới cho Artist!")
                    st.rerun()

    # ==========================================
    # TAB 3: LỊCH SỬ BÀI ĐÃ PASS
    # ==========================================
    with tab_lichsu:
        da_pass = [t for t in tasks if t.get("status") in ["Pending_Boss", "Done"]]
        st.subheader("Danh sách các bài Leader đã Pass")
        
        if not da_pass:
            st.info("Chưa có task nào được Pass.")
            
        for t in da_pass:
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**[{t.get('project')}] {t.get('name')}**")
                    st.caption(f"Tác giả: {t.get('assignee')} | Link: [Xem Drive]({t.get('Submission_Link')})")
                with col_b:
                    if t.get("status") == "Pending_Boss":
                        st.warning("⏳ Đang chờ Sếp chốt")
                    else:
                        st.success("✅ Sếp đã chốt tiền")