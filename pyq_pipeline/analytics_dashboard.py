"""
Analytics Dashboard for MU-Cortex

Internal dashboard to validate prediction quality and frequency analytics.
Read-only analytics for Person C validation purposes.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from project root .env file
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Initialize Supabase client using SERVICE ROLE key
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    st.error("❌ Missing Supabase service role credentials in .env file")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

st.set_page_config(page_title="MU-Cortex | Analytics Dashboard", layout="wide")

st.title("📊 Analytics Dashboard")
st.caption("🔐 Internal validation dashboard - Read-only analytics")


@st.cache_data(ttl=300)
def get_subjects() -> List[Dict]:
    """Fetch all subjects from the database."""
    try:
        resp = supabase.table("subjects").select("id, name, code, scheme_id").order("name").execute()
        return resp.data or []
    except Exception as e:
        st.error(f"Error fetching subjects: {e}")
        return []


@st.cache_data(ttl=60)
def get_subject_stats(subject_id: str, scheme_id: str) -> Optional[Dict]:
    """Fetch subject statistics from subject_question_stats view."""
    try:
        resp = (
            supabase.table("subject_question_stats")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .execute()
        )
        return resp.data[0] if resp.data else None
    except Exception as e:
        st.error(f"Error fetching subject stats: {e}")
        return None


@st.cache_data(ttl=60)
def get_predictions(subject_id: str, scheme_id: str) -> List[Dict]:
    """Fetch question predictions from question_predictions view."""
    try:
        resp = (
            supabase.table("question_predictions")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .order("prediction_score", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as e:
        st.error(f"Error fetching predictions: {e}")
        return []


@st.cache_data(ttl=60)
def get_marks_distribution(subject_id: str, scheme_id: str) -> pd.DataFrame:
    """Fetch or calculate marks distribution."""
    try:
        # Try to fetch from marks_distribution view if it exists
        resp = (
            supabase.table("marks_distribution")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("scheme_id", scheme_id)
            .execute()
        )
        
        if resp.data:
            return pd.DataFrame(resp.data)
    except:
        pass
    
    # Fallback: calculate from predictions
    predictions = get_predictions(subject_id, scheme_id)
    if not predictions:
        return pd.DataFrame(columns=["marks", "question_count"])
    
    df = pd.DataFrame(predictions)
    marks_dist = df["marks"].value_counts().reset_index()
    marks_dist.columns = ["marks", "question_count"]
    marks_dist = marks_dist.sort_values("marks")
    return marks_dist


# Sidebar: Subject selection
st.sidebar.header("📚 Subject Selection")

subjects = get_subjects()
if not subjects:
    st.error("No subjects found in database.")
    st.stop()

# Create subject options with name + scheme
subject_options = {
    f"{s['name']} ({s['code']}) - Scheme {s['scheme_id']}": (s["id"], s["scheme_id"])
    for s in subjects
}

if not subject_options:
    st.error("No subjects available.")
    st.stop()

selected_label = st.sidebar.selectbox(
    "Select Subject",
    options=list(subject_options.keys()),
    index=0
)

selected_subject_id, selected_scheme_id = subject_options[selected_label]

# Fetch data
with st.spinner("Loading analytics data..."):
    stats = get_subject_stats(selected_subject_id, selected_scheme_id)
    predictions = get_predictions(selected_subject_id, selected_scheme_id)
    marks_dist = get_marks_distribution(selected_subject_id, selected_scheme_id)

if not stats:
    st.warning(f"No statistics found for selected subject.")
    st.stop()

if not predictions:
    st.warning(f"No predictions found for selected subject.")
    st.stop()

# Top metrics cards
st.markdown("### 📈 Key Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Questions", stats.get("total_questions", 0))

with col2:
    st.metric("High-Frequency Questions", stats.get("high_freq_questions", 0))

with col3:
    high_freq_pct = stats.get("high_freq_percentage", 0)
    st.metric("High-Frequency %", f"{high_freq_pct:.1f}%")

with col4:
    if predictions:
        avg_score = pd.DataFrame(predictions)["prediction_score"].mean()
        st.metric("Avg Prediction Score", f"{avg_score:.2f}")
    else:
        st.metric("Avg Prediction Score", "N/A")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Frequency Analysis", "🎯 Predictions", "📝 Marks Distribution"])

# TAB 1: Frequency Analysis
with tab1:
    st.markdown("### Question Frequency Analysis")
    
    if predictions:
        df = pd.DataFrame(predictions)
        
        # Histogram of appearance_count
        st.markdown("#### Appearance Count Distribution")
        fig_hist = px.histogram(
            df,
            x="appearance_count",
            nbins=20,
            title="Distribution of Question Appearance Counts",
            labels={"appearance_count": "Appearance Count", "count": "Number of Questions"}
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Top 10 most repeated questions
        st.markdown("#### Top 10 Most Repeated Questions")
        top_10 = (
            df.nlargest(10, "appearance_count")[
                ["question_text", "marks", "appearance_count", "last_appeared_year"]
            ]
            .reset_index(drop=True)
        )
        top_10.index = top_10.index + 1  # Start from 1
        st.dataframe(
            top_10,
            use_container_width=True,
            column_config={
                "question_text": st.column_config.TextColumn("Question Text", width="large"),
                "marks": st.column_config.NumberColumn("Marks", format="%d"),
                "appearance_count": st.column_config.NumberColumn("Appearances", format="%d"),
                "last_appeared_year": st.column_config.NumberColumn("Last Year", format="%d"),
            }
        )
    else:
        st.info("No prediction data available for frequency analysis.")

# TAB 2: Predictions
with tab2:
    st.markdown("### Prediction Analysis")
    
    if predictions:
        df = pd.DataFrame(predictions)
        
        # Pie chart: study_priority distribution
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### Study Priority Distribution")
            priority_counts = df["study_priority"].value_counts()
            if not priority_counts.empty:
                fig_pie = px.pie(
                    values=priority_counts.values,
                    names=priority_counts.index,
                    title="Questions by Study Priority"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No study priority data available.")
        
        with col_chart2:
            st.markdown("#### Prediction Score by Study Priority")
            if "study_priority" in df.columns and not df["study_priority"].isna().all():
                fig_box = px.box(
                    df,
                    x="study_priority",
                    y="prediction_score",
                    title="Prediction Score Distribution by Priority",
                    labels={
                        "study_priority": "Study Priority",
                        "prediction_score": "Prediction Score"
                    }
                )
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                # Fallback: bar chart if no priority data
                score_bins = pd.cut(df["prediction_score"], bins=5, labels=["Very Low", "Low", "Medium", "High", "Very High"])
                score_dist = score_bins.value_counts().sort_index()
                fig_bar = px.bar(
                    x=score_dist.index.astype(str),
                    y=score_dist.values,
                    title="Prediction Score Distribution",
                    labels={"x": "Score Range", "y": "Number of Questions"}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Top 20 predicted questions
        st.markdown("#### Top 20 Predicted Questions")
        top_20 = (
            df.head(20)[
                ["question_text", "marks", "appearance_count", "prediction_score", "study_priority"]
            ]
            .reset_index(drop=True)
        )
        top_20.index = top_20.index + 1
        st.dataframe(
            top_20,
            use_container_width=True,
            column_config={
                "question_text": st.column_config.TextColumn("Question Text", width="large"),
                "marks": st.column_config.NumberColumn("Marks", format="%d"),
                "appearance_count": st.column_config.NumberColumn("Appearances", format="%d"),
                "prediction_score": st.column_config.NumberColumn("Score", format="%.2f"),
                "study_priority": st.column_config.TextColumn("Priority"),
            }
        )
    else:
        st.info("No prediction data available.")

# TAB 3: Marks Distribution
with tab3:
    st.markdown("### Marks Distribution")
    
    if not marks_dist.empty:
        # Bar chart: marks vs question_count
        fig_bar = px.bar(
            marks_dist,
            x="marks",
            y="question_count",
            title="Question Count by Marks",
            labels={"marks": "Marks", "question_count": "Number of Questions"},
            text="question_count"
        )
        fig_bar.update_traces(texttemplate="%{text}", textposition="outside")
        
        # Calculate percentages
        total = marks_dist["question_count"].sum()
        marks_dist["percentage"] = (marks_dist["question_count"] / total * 100).round(1)
        
        # Add percentage labels
        fig_bar.add_trace(
            go.Scatter(
                x=marks_dist["marks"],
                y=marks_dist["question_count"] + (marks_dist["question_count"].max() * 0.05),
                text=marks_dist["percentage"].astype(str) + "%",
                mode="text",
                textfont=dict(size=12, color="black"),
                showlegend=False
            )
        )
        
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        # Table with percentages
        st.markdown("#### Marks Distribution Table")
        display_df = marks_dist.copy()
        display_df.columns = ["Marks", "Question Count", "Percentage"]
        display_df["Percentage"] = display_df["Percentage"].astype(str) + "%"
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No marks distribution data available.")

# Export section
st.markdown("---")
st.markdown("### 📥 Export Data")

if predictions:
    # Prepare CSV data
    export_df = pd.DataFrame(predictions)
    csv_data = export_df[[
        "question_text",
        "marks",
        "appearance_count",
        "last_appeared_year",
        "prediction_score",
        "study_priority"
    ]].to_csv(index=False).encode("utf-8")
    
    subject_name = stats.get("subject_name", "subject")
    filename = f"{subject_name.replace(' ', '_')}_predictions_{selected_scheme_id}.csv"
    
    st.download_button(
        label="📥 Download Predictions as CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("No data available for export.")
