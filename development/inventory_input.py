#%%
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from thefuzz import process
import datetime
import os

#%%
st.set_page_config(page_title="Inventory Input", layout="centered")
# st.title("📦 Inventory Usage Input")
st.markdown("# Inventory Usage Input")

# Get current directory (not required but useful)
current_dir = os.getcwd()

# Define scopes
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- Set Up Credentials ---
try:
    service_account_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"🔐 Credential error: {e}")
    st.stop()

# --- Open Sheet ---
try:
    SHEET_ID = st.secrets["google_sheets"]["sheet_id"]
    sheet = client.open_by_key(SHEET_ID)
except Exception as e:
    st.error(f"📄 Could not open sheet: {e}")
    st.stop()

# --- Load Worksheets ---
try:
    inventory_ws = sheet.worksheet("Inventory")
    events_ws = sheet.worksheet("Events")
    usage_log_ws = sheet.worksheet("UsageLog")
except Exception as e:
    st.error(f"📑 Error loading worksheets: {e}")
    st.stop()

# --- Load Data ---
try:
    inventory_data = inventory_ws.get_all_records()
    events_data = events_ws.get_all_records()
    # st.write("📋 Inventory Sample:", inventory_data[:3])
    # st.write("🎟️ Events Sample:", events_data[:3])
    st.text("Inventory Sample loaded.")
    st.text("Events Sample loaded.")

except Exception as e:
    st.error(f"❌ Error reading sheet data: {e}")
    st.stop()

# --- Build Select Options ---
try:
    item_options = [f"{item['item_id']} - {item['item_name']}" for item in inventory_data]
    event_names = [event['event_name'] for event in events_data]
except Exception as e:
    st.error(f"🔁 Error formatting dropdowns: {e}")
    st.stop()

# --- UI Inputs ---
try:
    selected_item = st.selectbox("Select Inventory Item", item_options)
    # selected_event = st.selectbox("Select Event", event_names)
    # Create input box
    user_input = st.text_input("Search or enter event name")

    # Only show results if user starts typing
    if user_input:
        # Top 5 closest matches
        matches = process.extract(user_input, event_names, limit=5)
        best_matches = [match[0] for match in matches]

    selected_event = st.selectbox("Select Closest Match", best_matches)
    used_qty = st.number_input("Quantity Used", min_value=0, step=1)
    lost_qty = st.number_input("Quantity Lost", min_value=0, step=1)
except Exception as e:
    st.error(f"📦 Input element error: {e}")
    st.stop()

# --- Submit ---
if st.button("✅ Submit Usage Log"):
    try:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item_id = selected_item.split(" - ")[0]

        usage_log_ws.append_row([
            now, item_id, selected_item, selected_event, used_qty, lost_qty
        ])
        st.success("✅ Inventory usage recorded!")
    except Exception as e:
        st.error(f"❌ Failed to write to UsageLog: {e}")
