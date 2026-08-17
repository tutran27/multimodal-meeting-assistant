import json
import requests
import streamlit as st

API_URL = "http://localhost:8000/api/v1/workflows/run"

st.set_page_config(
    page_title="Smart Personal Assistant",
    layout="wide",
)

st.title("Multi-modal Smart Personal Assistant")
st.caption("Audio + Image + Meeting Script → Action Items → Calendar/Web → PDF → Gmail Draft")

instruction = st.text_area(
    "Yêu cầu",
    value="Trích xuất việc cần làm, kiểm tra lịch rảnh, tìm thông tin đối tác, tạo báo cáo PDF và Gmail draft cho sếp.",
    height=100,
)

col1, col2, col3 = st.columns(3)

with col1:
    audio_file = st.file_uploader(
        "Audio meeting",
        type=["mp3", "wav", "m4a", "ogg", "webm", "flac"],
    )

with col2:
    image_file = st.file_uploader(
        "Ảnh ghi chú",
        type=["jpg", "jpeg", "png", "webp"],
    )

with col3:
    script_file = st.file_uploader(
        "Meeting script",
        type=["txt", "md", "docx", "pdf"],
    )

script_text = st.text_area(
    "Hoặc dán meeting script trực tiếp",
    height=180,
)

if st.button("Chạy workflow", type="primary"):
    files = {}

    if audio_file:
        files["audio_file"] = (audio_file.name, audio_file.getvalue(), audio_file.type)
    if image_file:
        files["image_file"] = (image_file.name, image_file.getvalue(), image_file.type)
    if script_file:
        files["script_file"] = (script_file.name, script_file.getvalue(), script_file.type)

    data = {
        "instruction": instruction,
        "script_text": script_text,
    }

    try:
        with st.spinner("Đang xử lý..."):
            response = requests.post(
                API_URL,
                data=data,
                files=files,
                timeout=600,
            )
            response.raise_for_status()
            result = response.json()

        st.success(f"Workflow status: {result['status']}")

        st.subheader("Meeting Summary")
        st.write(result.get("extraction", {}).get("summary", "Không có dữ liệu"))

        st.subheader("Action Items")
        st.dataframe(
            result.get("extraction", {}).get("action_items", []),
            use_container_width=True,
        )

        st.subheader("Execution Plan")
        st.dataframe(
            result.get("plan", []),
            use_container_width=True,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("PDF")
            st.write(result.get("report_path") or "Chưa tạo")

        with col_b:
            st.subheader("Gmail Draft")
            st.write(result.get("email_draft_id") or "Chưa tạo")

        st.subheader("Reflection")
        st.json(result.get("reflection"))

        with st.expander("Xem toàn bộ JSON"):
            st.code(
                json.dumps(result, ensure_ascii=False, indent=2),
                language="json",
            )

    except Exception as exc:
        st.error(str(exc))


if __name__ == "__main__":
    print("Run with: streamlit run frontend/streamlit_app.py")