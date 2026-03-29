import os
import shutil
import sys
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

sys.path.append(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

from db.database import init_db
from core.analytics import AnalyticsService
from core.paths import DB_PATH, PDF_STORAGE_DIR, THUMBNAIL_DIR, ensure_directory
from core.services import DocumentService


if "selected_doc" not in st.session_state:
    st.session_state.selected_doc = None

if "current_page" not in st.session_state:
    st.session_state.current_page = 0

if "search_results" not in st.session_state:
    st.session_state.search_results = []

if "reader_mode" not in st.session_state:
    st.session_state.reader_mode = False

if "show_reset" not in st.session_state:
    st.session_state.show_reset = False


init_db()

service = DocumentService()
analytics = AnalyticsService()
reindexed_count = service.reindex_unindexed_documents()

st.set_page_config(page_title="DocManager", layout="wide")

st.title("🗂️ Smart PDF Document Manager")

if reindexed_count:
    st.info(f"Backfilled text index for {reindexed_count} existing document(s).")

st.divider()

st.subheader("⚙️ Admin Controls")

if ADMIN_PASSWORD:
    if st.button("🧹 Clean Database"):
        st.session_state.show_reset = True

    if st.session_state.show_reset:
        password_input = st.text_input("Enter Admin Password", type="password")
        col1, col2 = st.columns(2)

        with col1:
            confirm_reset = st.button("Confirm Reset")

        with col2:
            cancel_reset = st.button("Cancel Reset")

        if cancel_reset:
            st.session_state.show_reset = False
            st.rerun()

        if confirm_reset:
            if password_input == ADMIN_PASSWORD:
                if DB_PATH.exists():
                    DB_PATH.unlink()

                shutil.rmtree(PDF_STORAGE_DIR, ignore_errors=True)
                shutil.rmtree(THUMBNAIL_DIR, ignore_errors=True)

                ensure_directory(PDF_STORAGE_DIR)
                ensure_directory(THUMBNAIL_DIR)
                init_db()

                st.session_state.selected_doc = None
                st.session_state.current_page = 0
                st.session_state.search_results = []
                st.session_state.reader_mode = False
                st.session_state.show_reset = False

                st.success("✅ System reset successfully.")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
else:
    st.caption("Set `ADMIN_PASSWORD` in `.env` to enable admin reset controls.")


tabs = st.tabs(["Upload", "Search & View", "Analytics"])

with tabs[0]:
    st.header("Upload PDF")

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    tags = st.text_input("Tags (comma separated)")
    description = st.text_area("Description")
    lecture_date = st.date_input("Lecture Date (optional)", value=None)

    if st.button("Upload"):
        analytics.record_app_visit("upload_click")

        if uploaded_file:
            chunk_count = service.upload_document(uploaded_file, tags, description, lecture_date)

            if chunk_count:
                st.success(f"Upload complete. Indexed {chunk_count} searchable text chunk(s).")
            else:
                st.warning(
                    "Upload complete, but no searchable text was extracted from this PDF. "
                    "This usually means the PDF is scanned/image-only and needs OCR support."
                )
        else:
            st.error("Please upload a file")

with tabs[1]:
    st.header("Search & View")

    col1, col2 = st.columns(2)

    with col1:
        search_tag = st.text_input("Search by Tag")

    with col2:
        search_date = st.date_input("Search by Date", value=None)

    content_query = st.text_input("Search inside PDF text")

    if st.button("Search"):
        analytics.record_app_visit("search_click")
        st.session_state.search_results = service.search_documents(
            tag=search_tag if search_tag else None,
            date=str(search_date) if search_date else None,
            content_query=content_query if content_query else None,
        )

    results = st.session_state.search_results

    if results and not st.session_state.reader_mode:
        st.subheader(f"Results: {len(results)}")
        container = st.container(height=500)

        with container:
            for result_index, result in enumerate(results):
                doc = result.document
                col1, col2 = st.columns([1, 3])

                with col1:
                    if doc.thumbnail_path:
                        st.image(doc.thumbnail_path, width=120)

                with col2:
                    st.write(f"**{doc.name}**")
                    st.write(f"Tags: {doc.tags}")
                    st.write(f"Description: {doc.description}")
                    st.write(f"Lecture Date: {doc.lecture_date}")

                    if result.matched_page is not None:
                        st.write(f"Matched Page: {result.matched_page}")

                    if result.snippet:
                        st.caption(result.snippet)

                    if st.button("Open", key=f"open_{doc.id}_{result.matched_page}_{result_index}"):
                        analytics.record_app_visit("open_document")
                        st.session_state.selected_doc = doc
                        st.session_state.current_page = max(
                            0,
                            (result.matched_page - 1) if result.matched_page else 0,
                        )
                        st.session_state.reader_mode = True
                        st.rerun()

    if st.session_state.reader_mode and st.session_state.selected_doc:
        st.write("Reader Mode Active")

        doc = st.session_state.selected_doc
        st.subheader(f"📖 Reading: {doc.name}")

        image_dir = str(Path(doc.path).with_suffix(""))

        st.write("Image dir:", image_dir)
        st.write("Files:", os.listdir(image_dir) if os.path.exists(image_dir) else "NOT FOUND")

        if not os.path.exists(image_dir):
            st.error("Images not found. PDF conversion failed.")
        else:
            images = sorted(os.listdir(image_dir))
            total_pages = doc.total_pages
            current_page = st.session_state.current_page

            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                if st.button("⬅ Previous") and current_page > 0:
                    analytics.record_app_visit("prev_page")
                    st.session_state.current_page -= 1
                    st.rerun()

            with col3:
                if st.button("Next ➡") and current_page < total_pages - 1:
                    analytics.record_app_visit("next_page")
                    st.session_state.current_page += 1
                    st.rerun()

            img_path = os.path.join(image_dir, images[st.session_state.current_page])
            st.image(img_path, width="stretch")

            analytics.record_page_visit(doc.id, st.session_state.current_page + 1)

            unique_pages = analytics.get_unique_pages_viewed(doc.id)
            progress = (unique_pages / doc.total_pages) * 100 if doc.total_pages else 0

            st.progress(progress / 100)
            st.write(f"Progress: {progress:.2f}% ({unique_pages}/{doc.total_pages})")
            st.write(f"FILE : {doc.name}")

        if st.button("Close Reader"):
            analytics.record_app_visit("close_reader")
            st.session_state.selected_doc = None
            st.session_state.current_page = 0
            st.session_state.reader_mode = False
            st.rerun()

with tabs[2]:
    st.header("Analytics")

    if st.button("Reset Analytics"):
        analytics.reset_analytics()
        st.success("Analytics reset successfully")

    try:
        import pandas as pd
    except ImportError:
        st.warning("Install `pandas` to view analytics charts and tables.")
    else:
        st.subheader("App Usage")

        app_data = analytics.get_app_visits()
        df = pd.DataFrame(app_data, columns=["Event", "Count"])

        if df.empty:
            st.info("No analytics data yet. Perform some actions to see insights.")
        else:
            st.bar_chart(df.set_index("Event"))

        st.subheader("Document Progress")

        docs = service.get_all_documents()
        data = []

        for doc in docs:
            unique_pages = analytics.get_unique_pages_viewed(doc.id)
            progress = (unique_pages / doc.total_pages) * 100 if doc.total_pages else 0

            data.append({
                "Document": doc.name,
                "Pages Read": unique_pages,
                "Total Pages": doc.total_pages,
                "Progress (%)": round(progress, 2),
            })

        df_docs = pd.DataFrame(data)

        if df_docs.empty:
            st.info("No documents uploaded yet.")
        else:
            st.dataframe(df_docs, width='stretch')
