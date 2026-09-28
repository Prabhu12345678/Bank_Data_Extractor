import streamlit as st
import requests
import os
import base64
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Finance Review", layout="wide")

st.title("Finance Data Extraction Agent")
st.write("Upload an invoice or statement (PDF or TXT) to process and validate against ERP modules. Supports legacy Monarch-style text dumps.")

tab1, tab2 = st.tabs(["Single Document Processing", "Bulk Ingestion & Queue"])

def display_document(filename, file_bytes):
    ext = filename.lower().split('.')[-1]
    if ext == 'pdf':
        base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    elif ext in ['png', 'jpg', 'jpeg', 'bmp']:
        try:
            st.image(file_bytes, use_container_width=True)
        except TypeError:
            try:
                st.image(file_bytes)
            except Exception as e:
                st.error(f"Cannot display image: {e}")
        except Exception as e:
            st.error(f"Cannot display image (corrupt or truncated data): {e}")
    else:
        st.text(file_bytes.decode('utf-8', errors='ignore'))

with tab1:
    if "tab1_key" not in st.session_state:
        st.session_state.tab1_key = 0
    if "tab1_data" not in st.session_state:
        st.session_state.tab1_data = None
    if "tab1_file_info" not in st.session_state:
        st.session_state.tab1_file_info = None

    uploaded_file = st.file_uploader(
        "Upload Document",
        type=["pdf", "txt", "prn", "csv", "png", "jpg", "jpeg", "bmp"],
        key=f"file_uploader_tab1_{st.session_state.tab1_key}"
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        process_btn = st.button("Process Document", key="process_doc_tab1")
    with col2:
        if st.button("Clear Selection", key="clear_selection_tab1"):
            st.session_state.tab1_key += 1
            st.session_state.tab1_data = None
            st.session_state.tab1_file_info = None
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()

    if uploaded_file is not None and process_btn:
        with st.spinner("Analyzing document with AI Agent..."):
            content_type = "application/pdf" if uploaded_file.name.lower().endswith(".pdf") else "text/plain"
            if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                content_type = "image/jpeg"

            file_bytes = uploaded_file.getvalue()
            files = {"file": (uploaded_file.name, file_bytes, content_type)}

            try:
                response = requests.post(f"{API_URL}/api/v1/process-document", files=files)
                if response.status_code == 200:
                    st.session_state.tab1_data = response.json()
                    st.session_state.tab1_file_info = (uploaded_file.name, file_bytes)
                else:
                    st.error(f"Failed to process. Code: {response.status_code}, Error: {response.text}")
            except Exception as e:
                st.error(f"Error reaching API Backend: {e}")

    if st.session_state.tab1_data is not None and st.session_state.tab1_file_info is not None:
        data = st.session_state.tab1_data
        filename, file_bytes = st.session_state.tab1_file_info

        doc_col, data_col = st.columns(2)

        with doc_col:
            st.subheader("Original Source Imagery")
            display_document(filename, file_bytes)

        with data_col:
            st.subheader("Analysis Results")
            if data.get("status") == "APPROVED":
                st.success("✅ Document Validated & Approved!")
            else:
                st.error("⚠️ REVIEW REQUIRED")
                st.write("**Flags:**", data.get("flags", []))

            st.write("**Extracted Data Structure:**")
            st.json(data.get("extracted_data"))

with tab2:
    st.header("Bulk Processing from Folder")
    st.write("Upload multiple files from a folder to process them in bulk. Documents will track auto-approval and list exceptions for manual review.")

    if "tab2_key" not in st.session_state:
        st.session_state.tab2_key = 0
    if "bulk_results" not in st.session_state:
        st.session_state.bulk_results = []
    if "review_selection" not in st.session_state:
        st.session_state.review_selection = None

    bulk_files = st.file_uploader(
        "Upload Folder / Multiple Documents",
        type=["pdf", "txt", "prn", "csv", "png", "jpg", "jpeg", "bmp"],
        accept_multiple_files=True,
        key=f"file_uploader_tab2_{st.session_state.tab2_key}"
    )

    col_b1, col_b2 = st.columns([1, 4])
    with col_b1:
        start_bulk = st.button("Start Bulk Processing", key="start_bulk_btn")
    with col_b2:
        if st.button("Clear Selection", key="clear_selection_tab2"):
            st.session_state.tab2_key += 1
            st.session_state.bulk_results = []
            st.session_state.review_selection = None
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()

    if bulk_files and start_bulk:
        st.session_state.bulk_results = []
        st.session_state.review_selection = None

        progress_text = "Processing documents..."
        my_bar = st.progress(0, text=progress_text)

        for i, f in enumerate(bulk_files):
            my_bar.progress(i / len(bulk_files), text=f"Processing {f.name}...")

            content_type = "application/pdf" if f.name.lower().endswith(".pdf") else "text/plain"
            if f.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                content_type = "image/jpeg"

            file_bytes = f.getvalue()
            files = {"file": (f.name, file_bytes, content_type)}

            res_data = {"filename": f.name, "bytes": file_bytes, "status": "ERROR", "data": None}
            try:
                response = requests.post(f"{API_URL}/api/v1/process-document", files=files)
                if response.status_code == 200:
                    data = response.json()
                    res_data["status"] = data.get("status", "ERROR")
                    res_data["data"] = data
                else:
                    res_data["error"] = response.text
            except Exception as e:
                res_data["error"] = str(e)

            st.session_state.bulk_results.append(res_data)

        my_bar.progress(1.0, text="Bulk processing complete!")

    if st.session_state.bulk_results:
        st.write("---")
        results = st.session_state.bulk_results
        auto_approved = [r for r in results if r["status"] == "APPROVED"]
        needs_review = [r for r in results if r["status"] != "APPROVED"]

        col_stat1, col_stat2 = st.columns(2)
        col_stat1.success(f"{len(auto_approved)} documents auto-approved.")
        col_stat2.warning(f"{len(needs_review)} documents require manual review.")

        col_q1, col_q2 = st.columns([1, 4])
        with col_q1:
            if st.button("Clear Bulk Queue", key="clear_bulk_queue_btn"):
                st.session_state.tab2_key += 1
                st.session_state.bulk_results = []
                st.session_state.review_selection = None
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()
        with col_q2:
            if st.session_state.review_selection:
                if st.button("Clear Item Selection", key="clear_review_item_selection"):
                    st.session_state.review_selection = None
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()

        if results:
            st.subheader("Document Queue")
            col_list, col_review = st.columns([1, 2])

            with col_list:
                st.write("### Processed Items")
                for item in results:
                    btn_label = f"✅ {item['filename']}" if item.get("status") == "APPROVED" else f"⚠️ {item['filename']}"
                    if st.button(btn_label, key=f"btn_{item['filename']}"):
                        st.session_state.review_selection = item['filename']
                        if hasattr(st, "rerun"):
                            st.rerun()
                        else:
                            st.experimental_rerun()

            with col_review:
                if st.session_state.review_selection:
                    selected_item = next((r for r in results if r['filename'] == st.session_state.review_selection), None)
                    if selected_item:
                        st.write(f"### Reviewing: {selected_item['filename']}")

                        doc_col, data_col = st.columns(2)

                        with doc_col:
                            st.subheader("Original Source Imagery")
                            display_document(selected_item['filename'], selected_item['bytes'])

                        with data_col:
                            st.subheader("Analysis Results")
                            if selected_item.get("error"):
                                st.error(f"Processing Error: {selected_item['error']}")
                            else:
                                data = selected_item["data"]
                                if selected_item.get("status") == "APPROVED":
                                    st.success("✅ Document Validated & Approved!")
                                else:
                                    st.error("⚠️ REVIEW REQUIRED")
                                    st.write("**Flags:**", data.get("flags", []))

                                st.write("**Extracted Data Structure:**")
                                st.json(data.get("extracted_data"))
