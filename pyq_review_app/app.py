import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root .env file
ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

# Initialize Supabase client using SERVICE ROLE key
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Missing Supabase service role credentials")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

st.set_page_config(page_title="MU-Cortex | PYQ Review", layout="wide")

st.title("📘 PYQ Question Review & Approval")
st.caption("🔐 Review app using Supabase SERVICE ROLE")

# Initialize session state for questions (single source of truth)
# This allows us to:
# 1. Fetch questions only once on first load
# 2. Update counts dynamically without re-fetching
# 3. Make reruns fast (no database calls on rerun)
if "questions" not in st.session_state:
    st.session_state.questions = []
    st.session_state.questions_loaded = False

# Filters
col_filter1, col_filter2 = st.columns(2)

with col_filter1:
    subject_id = st.text_input("Optional: Filter by Subject UUID", placeholder="Enter UUID")
    st.caption("Leave empty to review all unapproved questions across subjects.")

with col_filter2:
    show_unapproved_only = st.checkbox("Show only unapproved questions", value=True)

# Normalize subject_id (trim whitespace, treat empty as None)
subject_id = subject_id.strip() if subject_id and subject_id.strip() else None

# Fetch questions from database ONLY on first load
# Session state caching ensures subsequent reruns are instant (no re-fetch)
if not st.session_state.questions_loaded:
    try:
        with st.spinner("Loading questions..."):
            # Base query: question_appearances with join to questions
            query = (
                supabase
                .table("question_appearances")
                .select(
                    "id, subject_id, appeared_in, year, "
                    "questions(id, question_text, marks, approved)"
                )
            )
            
            # Execute query (fetch all, we'll filter in memory)
            response = query.execute()
            all_rows = response.data or []
            
            # Store in session state
            st.session_state.questions = all_rows
            st.session_state.questions_loaded = True
            
    except Exception as e:
        st.error(f"Error fetching questions: {e}")
        st.stop()

# Filter questions from session state based on current filters
filtered_rows = st.session_state.questions.copy()

# Apply unapproved filter
if show_unapproved_only:
    filtered_rows = [
        row for row in filtered_rows
        if row.get("questions", {}).get("approved") is False
        or row.get("questions", {}).get("approved") is None
    ]

# Apply subject filter
if subject_id:
    filtered_rows = [
        row for row in filtered_rows
        if row.get("subject_id") == subject_id
    ]

# Compute counts from session state
total_count = len(st.session_state.questions)
unapproved_count = len([
    row for row in st.session_state.questions
    if row.get("questions", {}).get("approved") is False
    or row.get("questions", {}).get("approved") is None
])

# Display dynamic counts (updates immediately from session state)
st.markdown("### 📊 Statistics")
col_count1, col_count2, col_count3 = st.columns(3)
with col_count1:
    st.metric("Total Questions", total_count)
with col_count2:
    st.metric("Pending Review", unapproved_count)
with col_count3:
    st.metric("Visible Now", len(filtered_rows))

# Approve All button (subject-filter aware)
if len(filtered_rows) > 0:
    st.markdown("---")
    
    # Get unapproved question IDs from visible rows
    question_ids_to_approve = []
    for row in filtered_rows:
        question = row.get("questions")
        if question and question.get("id"):
            question_id = question.get("id")
            # Only approve if not already approved
            if not question.get("approved"):
                question_ids_to_approve.append(question_id)
    
    col_approve_all, _ = st.columns([1, 3])
    with col_approve_all:
        approve_all_disabled = len(question_ids_to_approve) == 0
        if st.button(
            f"✅ Approve All Visible ({len(question_ids_to_approve)} questions)",
            type="primary",
            use_container_width=True,
            disabled=approve_all_disabled
        ):
            # Confirmation dialog
            if len(question_ids_to_approve) > 0:
                try:
                    with st.spinner(f"Approving {len(question_ids_to_approve)} questions..."):
                        # Batch update: approve all questions
                        for q_id in question_ids_to_approve:
                            supabase.table("questions") \
                                .update({"approved": True}) \
                                .eq("id", q_id) \
                                .execute()
                        
                        # Update session state optimistically
                        for row in st.session_state.questions:
                            question = row.get("questions", {})
                            if question.get("id") in question_ids_to_approve:
                                question["approved"] = True
                        
                        st.success(f"✅ Approved {len(question_ids_to_approve)} questions!")
                        # Minimal rerun - session state cached, so no re-fetch
                        st.rerun()
                except Exception as e:
                    st.error(f"Error approving questions: {e}")

if not filtered_rows:
    st.warning("No questions to review.")
    st.stop()

st.markdown("---")
st.markdown(f"**Reviewing {len(filtered_rows)} question appearance(s)**")

# Display questions with optimistic updates
for idx, row in enumerate(filtered_rows):
    question = row.get("questions")
    if not question:
        continue
    
    question_id = question.get("id")
    question_text = question.get("question_text", "")
    marks = question.get("marks")
    approved = question.get("approved", False)
    subject_id_display = row.get("subject_id")
    appearance_id = row.get("id")
    
    # Skip if already approved and showing unapproved only
    if show_unapproved_only and approved:
        continue
    
    with st.container(border=True):
        st.markdown(f"### ❓ {question_text}")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown(f"**Marks:** {marks}M")
        
        with col_info2:
            status = "✅ Approved" if approved else "⏳ Pending Review"
            st.markdown(f"**Status:** {status}")
        
        st.markdown(f"**Question ID:** `{question_id}`")
        st.markdown(f"**Appearance ID:** `{appearance_id}`")
        if subject_id_display:
            st.markdown(f"**Subject ID:** `{subject_id_display}`")
        if row.get('appeared_in'):
            st.markdown(f"**Appeared in:** {row.get('appeared_in')}")
        if row.get('year'):
            st.markdown(f"**Year:** {row.get('year')}")

        col1, col2 = st.columns(2)

        with col1:
            approve_key = f"approve_{question_id}_{appearance_id}"
            if st.button("✅ Approve", key=approve_key, type="primary", disabled=approved):
                try:
                    # Update database
                    supabase.table("questions") \
                        .update({"approved": True}) \
                        .eq("id", question_id) \
                        .execute()
                    
                    # Update session state optimistically
                    for row_state in st.session_state.questions:
                        q = row_state.get("questions", {})
                        if q.get("id") == question_id:
                            q["approved"] = True
                            break
                    
                    st.success("✅ Question approved!")
                    # Minimal rerun - session state cached, so no re-fetch
                    st.rerun()
                except Exception as e:
                    st.error(f"Error approving question: {e}")

        with col2:
            reject_key = f"reject_{question_id}_{appearance_id}"
            if st.button("❌ Reject & Delete", key=reject_key):
                try:
                    # Update database
                    supabase.table("questions") \
                        .delete() \
                        .eq("id", question_id) \
                        .execute()
                    
                    # Update session state optimistically (remove from list)
                    st.session_state.questions = [
                        r for r in st.session_state.questions
                        if r.get("questions", {}).get("id") != question_id
                    ]
                    
                    st.warning("❌ Question rejected and removed")
                    # Minimal rerun - session state cached, so no re-fetch
                    st.rerun()
                except Exception as e:
                    st.error(f"Error rejecting question: {e}")

# Refresh button to reload from database (optional)
st.markdown("---")
if st.button("🔄 Refresh from Database"):
    st.session_state.questions_loaded = False
    st.session_state.questions = []
    st.rerun()
