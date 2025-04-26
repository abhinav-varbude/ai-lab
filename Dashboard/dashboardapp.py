import streamlit as st
import os
import yaml
import pandas as pd
import datetime
from pathlib import Path

# Constants
EXPERIMENTS_DIR = Path("../experiments")
LOG_FILE = Path("../logs/experiment-log.csv")

st.set_page_config(page_title="AI Lab Dashboard", layout="wide")
st.title("🧪 AI Lab Experiment Dashboard")

# Ensure directories exist
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ---------- Sidebar: Add New Experiment ----------
st.sidebar.header("➕ Add New Experiment")
with st.sidebar.form("add_experiment"):
    exp_name = st.text_input("Experiment Name", "my-cool-experiment")
    description = st.text_area("Short Description")
    tags = st.text_input("Tags (comma-separated)", "synthetic,gan")
    status = st.selectbox("Status", ["In Progress", "Completed", "Planned"])
    submitted = st.form_submit_button("Add Experiment")

    if submitted:
        date_str = datetime.date.today().isoformat()
        folder_name = f"{date_str}-{exp_name.strip().replace(' ', '-')[:30]}"
        folder_path = EXPERIMENTS_DIR / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)

        # Write metadata
        metadata = {
            "name": exp_name,
            "description": description,
            "status": status,
            "tags": [t.strip() for t in tags.split(",")],
            "created": date_str
        }
        with open(folder_path / "metadata.yaml", "w") as f:
            yaml.dump(metadata, f)

        # Append to central log
        log_df = pd.DataFrame([{
            "name": exp_name,
            "path": str(folder_path),
            "status": status,
            "tags": tags,
            "created": date_str
        }])
        if LOG_FILE.exists():
            old_log = pd.read_csv(LOG_FILE)
            log_df = pd.concat([old_log, log_df], ignore_index=True)
        log_df.to_csv(LOG_FILE, index=False)
        st.success(f"Experiment '{exp_name}' added.")

# ---------- Main Area: Display Experiments ----------
st.subheader("📂 Current Experiments")
if LOG_FILE.exists():
    df = pd.read_csv(LOG_FILE)

    # Search and filter
    search_term = st.text_input("🔍 Search by name or tag", "")
    status_filter = st.multiselect("Filter by status", df["status"].unique())

    filtered_df = df.copy()
    if search_term:
        filtered_df = filtered_df[filtered_df["name"].str.contains(search_term, case=False) | \
                                  filtered_df["tags"].str.contains(search_term, case=False)]
    if status_filter:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]

    for _, row in filtered_df.iterrows():
        with st.expander(f"🧪 {row['name']} ({row['status']})"):
            st.markdown(f"**Path:** `{row['path']}`")
            metadata_path = Path(row['path']) / "metadata.yaml"
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    meta = yaml.safe_load(f)
                st.markdown(f"**Description:** {meta.get('description', '-')}")
                st.markdown(f"**Tags:** {', '.join(meta.get('tags', []))}")
                st.markdown(f"**Created:** {meta.get('created', '-')}")

            # Log notes
            log_path = Path(row['path']) / "logs.txt"
            st.markdown("---")
            st.markdown("### 📓 Notes")
            note = ""
            if log_path.exists():
                note = log_path.read_text()
            new_note = st.text_area("Update Notes", value=note, height=200, key=row['path'])
            if st.button("💾 Save Notes", key=row['path'] + "_save"):
                log_path.write_text(new_note)
                st.success("Notes saved.")

            # Results visualization
            results_path = Path(row['path']) / "results.csv"
            if results_path.exists():
                st.markdown("### 📊 Results Preview")
                res_df = pd.read_csv(results_path)
                st.dataframe(res_df.head())
                numeric_cols = res_df.select_dtypes(include='number').columns
                if len(numeric_cols) >= 2:
                    x_axis = st.selectbox("X-axis", numeric_cols, key=row['path']+"x")
                    y_axis = st.selectbox("Y-axis", numeric_cols, index=1, key=row['path']+"y")
                    st.line_chart(res_df[[x_axis, y_axis]])
else:
    st.info("No experiments found. Use the sidebar to add your first one.")