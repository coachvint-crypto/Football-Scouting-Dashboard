import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Football Scouting Dashboard – Predictive", layout="wide")

st.title("🏈 Football Scouting Dashboard – Merged + Predictive Analysis")
st.markdown("Toggle between Offense and Defense views and get predictions from historical data.")

# Try to load CSV from the same folder as this script
default_csv = Path(__file__).parent / "merged_offense_defense_tendency_heavy.csv"

uploaded_file = st.file_uploader("Upload a merged Offense+Defense CSV (optional). If you skip, we'll try the bundled demo file.", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
elif default_csv.exists():
    df = pd.read_csv(default_csv)
else:
    st.error("No data found. Please upload a merged CSV to continue.")
    st.stop()

dataset_type = st.radio("Select Dataset Type", ["Offense", "Defense"])
df_filtered = df[df["Dataset Type"] == dataset_type]

st.write("### Data Preview", df_filtered.head())

def bucket_distance(d):
    try:
        d = int(d)
    except:
        return None
    if d <= 3: return "1-3"
    if d <= 6: return "4-6"
    if d <= 10: return "7-10"
    return "11+"

# ----------------- Analysis Section -----------------
if dataset_type == "Offense":
    if "Distance" in df_filtered.columns:
        df_filtered["Distance Bucket"] = df_filtered["Distance"].apply(bucket_distance)
    group_cols = ["Down", "Distance Bucket", "Field Zone", "Personnel", "Formation"]
    if all(col in df_filtered.columns for col in group_cols + ["Play Call", "Yards Gained"]):
        st.subheader("High-Tendency Groups (>65% one call)")
        rows = []
        for keys, g in df_filtered.groupby(group_cols):
            total = len(g)
            call_counts = g["Play Call"].value_counts(normalize=True)
            if not call_counts.empty:
                top_call_val = call_counts.idxmax()
                top_pct = call_counts.max()
                avg_yards = g["Yards Gained"].mean()
                if top_pct >= 0.65 and total >= 3:
                    row = dict(zip(group_cols, keys))
                    row.update({"Samples": total, "Top Play Call": top_call_val, "Top Play %": round(top_pct*100,1), "Avg Yards": round(avg_yards,2)})
                    rows.append(row)
        if rows:
            st.dataframe(pd.DataFrame(rows).sort_values(["Top Play %"], ascending=False))
        else:
            st.info("No high-tendency groups found.")
    
    # Prediction Tool
    st.subheader("🔮 Predict Next Offensive Play")
    col1, col2, col3, col4, col5 = st.columns(5)
    down_sel = col1.selectbox("Down", sorted(df_filtered["Down"].dropna().unique()))
    dist_sel = col2.number_input("Distance", min_value=1, max_value=20, value=5)
    fz_sel = col3.selectbox("Field Zone", sorted(df_filtered["Field Zone"].dropna().unique()))
    pers_sel = col4.selectbox("Personnel", sorted(df_filtered["Personnel"].dropna().unique()))
    form_sel = col5.selectbox("Formation", sorted(df_filtered["Formation"].dropna().unique()))
    
    if st.button("Predict Offensive Play"):
        dist_bucket = bucket_distance(dist_sel)
        match_df = df_filtered[
            (df_filtered["Down"] == down_sel) &
            (df_filtered["Distance Bucket"] == dist_bucket) &
            (df_filtered["Field Zone"] == fz_sel) &
            (df_filtered["Personnel"] == pers_sel) &
            (df_filtered["Formation"] == form_sel)
        ]
        if not match_df.empty:
            top_call_val = match_df["Play Call"].value_counts(normalize=True).idxmax()
            confidence = match_df["Play Call"].value_counts(normalize=True).max()*100
            st.success(f"Most Likely Play: **{top_call_val}** (Confidence: {confidence:.1f}%)")
        else:
            st.warning("No historical matches for that situation.")

elif dataset_type == "Defense":
    if "Distance" in df_filtered.columns:
        df_filtered["Distance Bucket"] = df_filtered["Distance"].apply(bucket_distance)
    
    # Prediction Tool
    st.subheader("🔮 Predict Defensive Call")
    col1, col2, col3, col4 = st.columns(4)
    down_sel = col1.selectbox("Down", sorted(df_filtered["Down"].dropna().unique()))
    dist_sel = col2.number_input("Distance", min_value=1, max_value=20, value=5)
    off_form_sel = col3.selectbox("Offensive Formation", sorted(df_filtered["Offensive Formation"].dropna().unique()))
    back_sel = col4.selectbox("Backfield Set", sorted(df_filtered["Backfield Set"].dropna().unique()))
    
    if st.button("Predict Defensive Call"):
        match_df = df_filtered[
            (df_filtered["Down"] == down_sel) &
            (df_filtered["Distance"] == dist_sel) &
            (df_filtered["Offensive Formation"] == off_form_sel) &
            (df_filtered["Backfield Set"] == back_sel)
        ]
        if not match_df.empty:
            front = match_df["Defensive Front"].value_counts(normalize=True).idxmax()
            blitz = match_df["Blitz Type"].value_counts(normalize=True).idxmax()
            cov = match_df["Coverage"].value_counts(normalize=True).idxmax()
            front_conf = match_df["Defensive Front"].value_counts(normalize=True).max()*100
            blitz_conf = match_df["Blitz Type"].value_counts(normalize=True).max()*100
            cov_conf = match_df["Coverage"].value_counts(normalize=True).max()*100
            st.success(
                f"Most Likely Front: **{front}** ({front_conf:.1f}%)\n"
                f"Most Likely Blitz: **{blitz}** ({blitz_conf:.1f}%)\n"
                f"Most Likely Coverage: **{cov}** ({cov_conf:.1f}%)"
            )
        else:
            st.warning("No historical matches for that situation.")
