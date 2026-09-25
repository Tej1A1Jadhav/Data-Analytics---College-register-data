"""
Student & Teacher Performance Dashboard (Streamlit)
----------------------------------------------------
Two lookup views built on the same cleaned data pipeline used in analytics.py:

  1. Student Report  -> pick a student, see their report card + how they compare
  2. Teacher Insights -> pick a teacher, see feedback/performance framed constructively
                          (no rankings, no red "failing" colors, growth-oriented wording)

Run with:
    streamlit run app.py

Needs the same .env file as analytics.py (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).
"""

import os
import warnings

import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from urllib.parse import quote_plus

warnings.filterwarnings("ignore")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PASS_MARK = 40
LOW_ATTENDANCE = 75

st.set_page_config(page_title="Performance Dashboard", layout="wide")


# --------------------------------------------------------------------------- #
# Data loading (cached so we don't re-hit MySQL on every click)
# --------------------------------------------------------------------------- #

@st.cache_resource
def get_engine():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "3306")
    user = os.getenv("DB_USER", "root")
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    name = os.getenv("DB_NAME", "clg_register")
    return create_engine(f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}")


@st.cache_data(ttl=300)
def load_tables(_engine):
    tables = {}
    for t in ["students", "departments", "subjects", "teachers", "marks", "attendance", "feedback"]:
        try:
            tables[t] = pd.read_sql(f"SELECT * FROM {t}", _engine)
        except Exception:
            tables[t] = pd.DataFrame()
    return tables


def clean_tables(tables: dict) -> dict:
    marks = tables.get("marks", pd.DataFrame()).copy()
    attendance = tables.get("attendance", pd.DataFrame()).copy()
    feedback = tables.get("feedback", pd.DataFrame()).copy()

    if not marks.empty:
        marks["marks_obtained"] = pd.to_numeric(marks["marks_obtained"], errors="coerce")
        if "total_marks" in marks.columns:
            marks["total_marks"] = pd.to_numeric(marks["total_marks"], errors="coerce")
            marks["marks_pct"] = marks["marks_obtained"] / marks["total_marks"] * 100
        else:
            marks["marks_pct"] = marks["marks_obtained"]
        marks = marks.dropna(subset=["marks_obtained"]).drop_duplicates()

    if not attendance.empty:
        attendance["status"] = attendance["status"].astype(str).str.strip().str.capitalize()
        attendance = attendance[attendance["status"].isin(["Present", "Absent"])].drop_duplicates()

    if not feedback.empty:
        feedback["rating"] = pd.to_numeric(feedback["rating"], errors="coerce")
        feedback = feedback.dropna(subset=["rating"]).drop_duplicates()

    tables["marks"] = marks
    tables["attendance"] = attendance
    tables["feedback"] = feedback
    return tables


def build_student_summary(tables: dict) -> pd.DataFrame:
    students = tables.get("students", pd.DataFrame())
    marks = tables.get("marks", pd.DataFrame())
    attendance = tables.get("attendance", pd.DataFrame())
    departments = tables.get("departments", pd.DataFrame())

    avg_marks = marks.groupby("student_id")["marks_pct"].mean().rename("avg_marks_pct") \
        if not marks.empty else pd.Series(name="avg_marks_pct", dtype=float)
    att_pct = attendance.groupby("student_id")["status"].apply(lambda s: (s == "Present").mean() * 100).rename("attendance_pct") \
        if not attendance.empty else pd.Series(name="attendance_pct", dtype=float)

    cols = [c for c in ["student_id", "name", "department_id", "year"] if c in students.columns]
    summary = students[cols].copy() if cols else pd.DataFrame(columns=["student_id"])
    summary = summary.merge(avg_marks, on="student_id", how="left").merge(att_pct, on="student_id", how="left")

    if not departments.empty and "department_id" in summary.columns:
        dcols = [c for c in ["department_id", "department_name"] if c in departments.columns]
        summary = summary.merge(departments[dcols], on="department_id", how="left")

    summary["at_risk"] = (summary["avg_marks_pct"] < PASS_MARK) | (summary["attendance_pct"] < LOW_ATTENDANCE)
    return summary


def build_teacher_summary(tables: dict) -> pd.DataFrame:
    teachers = tables.get("teachers", pd.DataFrame())
    feedback = tables.get("feedback", pd.DataFrame())
    marks = tables.get("marks", pd.DataFrame())
    subjects = tables.get("subjects", pd.DataFrame())

    if teachers.empty:
        return pd.DataFrame()

    summary = teachers.copy()

    if not feedback.empty and "teacher_id" in feedback.columns:
        avg_fb = feedback.groupby("teacher_id")["rating"].mean().rename("avg_rating")
        summary = summary.merge(avg_fb, on="teacher_id", how="left")
    else:
        summary["avg_rating"] = np.nan

    if not marks.empty and "teacher_id" in marks.columns:
        avg_student_marks = marks.groupby("teacher_id")["marks_pct"].mean().rename("avg_student_marks_pct")
        summary = summary.merge(avg_student_marks, on="teacher_id", how="left")
    else:
        summary["avg_student_marks_pct"] = np.nan

    if not subjects.empty and "subject_id" in summary.columns and "subject_name" in subjects.columns:
        summary = summary.merge(subjects[["subject_id", "subject_name"]], on="subject_id", how="left")

    return summary


# --------------------------------------------------------------------------- #
# Rendering: Student Report view
# --------------------------------------------------------------------------- #

def render_student_view(student_summary: pd.DataFrame, marks: pd.DataFrame, subjects: pd.DataFrame):
    st.header("📋 Student Report")

    if student_summary.empty:
        st.info("No student data available yet.")
        return

    options = student_summary.assign(
        label=lambda d: d["name"].astype(str) + " (ID: " + d["student_id"].astype(str) + ")"
    )
    choice = st.selectbox("Search for a student", options["label"])
    row = options[options["label"] == choice].iloc[0]

    class_avg_marks = student_summary["avg_marks_pct"].mean()
    class_avg_att = student_summary["attendance_pct"].mean()
    dept_avg_marks = student_summary.loc[
        student_summary.get("department_name") == row.get("department_name"), "avg_marks_pct"
    ].mean() if "department_name" in student_summary.columns else np.nan

    status = "On Track" if not row["at_risk"] else "Needs Attention"
    status_color = "green" if not row["at_risk"] else "orange"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Average Marks", f"{row['avg_marks_pct']:.1f}%",
                delta=f"{row['avg_marks_pct'] - class_avg_marks:+.1f} vs class avg")
    col2.metric("Attendance", f"{row['attendance_pct']:.1f}%",
                delta=f"{row['attendance_pct'] - class_avg_att:+.1f} vs class avg")
    col3.metric("Department", str(row.get("department_name", "—")))
    col4.markdown(f"**Status:** :{status_color}[{status}]")

    st.subheader("How they compare")
    compare_df = pd.DataFrame({
        "Metric": ["Avg Marks %", "Avg Marks % (class)", "Avg Marks % (department)"],
        "Value": [row["avg_marks_pct"], class_avg_marks, dept_avg_marks],
    }).dropna()
    st.bar_chart(compare_df.set_index("Metric"))

    if not marks.empty and "subject_id" in marks.columns:
        student_marks = marks[marks["student_id"] == row["student_id"]]
        if not student_marks.empty:
            if not subjects.empty and "subject_name" in subjects.columns:
                student_marks = student_marks.merge(subjects[["subject_id", "subject_name"]], on="subject_id", how="left")
                x_col = "subject_name"
            else:
                x_col = "subject_id"
            st.subheader("Subject-wise marks")
            st.bar_chart(student_marks.set_index(x_col)["marks_pct"])


# --------------------------------------------------------------------------- #
# Rendering: Teacher Insights view (constructive framing, no rankings)
# --------------------------------------------------------------------------- #

def rating_phrase(rating: float) -> str:
    if pd.isna(rating):
        return "No feedback recorded yet."
    if rating >= 4:
        return "Students consistently rate this teaching highly."
    if rating >= 3:
        return "Feedback is generally positive, with some room to grow."
    return "Feedback suggests this could be a good area to reflect on and discuss with peers."


def render_teacher_view(teacher_summary: pd.DataFrame):
    st.header("🌱 Teaching Insights")
    st.caption("Framed for reflection and growth — not a ranking.")

    if teacher_summary.empty:
        st.info("No teacher data available yet.")
        return

    options = teacher_summary.assign(
        label=lambda d: d["name"].astype(str) + " (ID: " + d["teacher_id"].astype(str) + ")"
    )
    choice = st.selectbox("Select teacher profile", options["label"])
    row = options[options["label"] == choice].iloc[0]

    dept_avg_rating = teacher_summary["avg_rating"].mean()
    dept_avg_marks = teacher_summary["avg_student_marks_pct"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Subject", str(row.get("subject_name", "—")))
    col2.metric("Avg Feedback Rating", f"{row['avg_rating']:.2f}/5" if pd.notna(row["avg_rating"]) else "—")
    col3.metric("Students' Avg Marks", f"{row['avg_student_marks_pct']:.1f}%" if pd.notna(row["avg_student_marks_pct"]) else "—")

    st.markdown(f"> {rating_phrase(row['avg_rating'])}")

    st.subheader("Context (department average, for reference — not a ranking)")
    compare_df = pd.DataFrame({
        "Metric": ["Feedback Rating", "Feedback Rating (dept. avg)"],
        "Value": [row["avg_rating"], dept_avg_rating],
    }).dropna()
    if not compare_df.empty:
        st.bar_chart(compare_df.set_index("Metric"))

    st.caption(
        "Note: in a real deployment, each teacher would only be able to view their own "
        "profile after logging in — this demo lets you browse any profile for presentation purposes."
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    st.title("Student & Teacher Performance Dashboard")

    engine = get_engine()
    tables = load_tables(engine)
    tables = clean_tables(tables)

    student_summary = build_student_summary(tables)
    teacher_summary = build_teacher_summary(tables)

    view = st.sidebar.radio("Choose a view", ["Student Report", "Teacher Insights"])

    if view == "Student Report":
        render_student_view(student_summary, tables.get("marks", pd.DataFrame()), tables.get("subjects", pd.DataFrame()))
    else:
        render_teacher_view(teacher_summary)


if __name__ == "__main__":
    main()
