# app.py

import streamlit as st
import pandas as pd
import re
from io import BytesIO
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px

# --- Helper Functions ---

def is_date_line(line):
    # Simple date pattern match
    return bool(re.search(r'\b(\d{1,2}(st|nd|rd|th)?\s+\w+|\d{1,2}/\d{1,2}/\d{2,4}|\w+\s+\d{1,2})\b', line.strip(), re.IGNORECASE))

def extract_item_amount(line):
    match = re.match(r'(.+?)\s+₹?\s?(\d+[,.]?\d*)', line.strip())
    if match:
        item = match.group(1).strip()
        amount = float(match.group(2).replace(",", ""))
        return item, amount
    return line.strip(), None

def parse_grouped_notes(note_block):
    lines = note_block.strip().split("\n")
    current_date = None
    parsed = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if is_date_line(line):
            try:
                current_date = str(pd.to_datetime(line, errors='coerce').date())
            except:
                current_date = line
        else:
            item, amount = extract_item_amount(line)
            parsed.append({
                "Date": current_date,
                "Item": item,
                "Amount": amount,
                "Description": line
            })

    return pd.DataFrame(parsed)

def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Parsed Notes')
    return output.getvalue()

def show_dashboard(df):
    st.subheader("📊 Expense Dashboard")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    col1, col2 = st.columns(2)

    with col1:
        daily_chart = px.bar(df.groupby("Date")["Amount"].sum().reset_index(),
                             x="Date", y="Amount", title="Total Spend per Day")
        st.plotly_chart(daily_chart, use_container_width=True)

    with col2:
        item_chart = px.pie(df, names="Item", values="Amount", title="Spend by Item")
        st.plotly_chart(item_chart, use_container_width=True)

# --- Streamlit UI ---
st.set_page_config(page_title="NoteParse", layout="wide")
st.title("🧠 NoteParse: Flexible Parsing for Grouped Notes")

st.markdown("Paste your grouped notes below. Use date headings followed by item lines.")

note_input = st.text_area("📋 Paste Notes Here", height=300, placeholder="e.g.\n3rd Sept\nVegetables 40\nMilk 25\nTransport 100")

if st.button("🔍 Parse Notes"):
    if note_input.strip():
        df = parse_grouped_notes(note_input)
        st.success("✅ Notes parsed successfully!")

        st.subheader("📝 Editable Table")
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(editable=True)
        grid_options = gb.build()
        grid_response = AgGrid(df, gridOptions=grid_options, update_mode="MODEL_CHANGED", fit_columns_on_grid_load=True)
        edited_df = grid_response["data"]

        st.download_button(
            label="📥 Download as Excel",
            data=convert_df_to_excel(pd.DataFrame(edited_df)),
            file_name=f"NoteParse_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        show_dashboard(pd.DataFrame(edited_df))
    else:
        st.warning("Please paste some notes to parse.")

st.markdown("---")
st.caption("Built by Gyanankur • Handles grouped notes, flexible formats, and clarity-first exports.")
