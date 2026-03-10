import streamlit as st
import pandas as pd
import json
from datetime import datetime
import io
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import gspread.utils

# --- CONFIGURATION ---
st.set_page_config(page_title="Attendance Tracker", layout="centered")

ML_STUDENTS = [
    "001", "002", "003", "004", "005",
    "006", "007", "008", "009", "010",
    "011", "012", "013", "014", "015",
    "016", "017", "018", "019", "020",
    "021", "022", "023", "024", "025",
    "026", "027", "028", "029", "030",
    "031", "032", "033", "034", "035",
    "036", "037", "038", "039", "040",
    "041", "042", "161", "167", "168",
    "169", "170", "171", "172", "173",
    "178", "179", "180", "181", "182",
    "197", "198", "199", "200", "201",
    "207", "208", "209", "210", "211",
    "218", "220", "223", "233", "298",
    "300", "301"
]
RM_STUDENTS = [
    "HIMNISH KUMAR R", "ISHA K S", "JAHNAVI PALAMBAKAM", "JAYA NIDHI",
    "JAYA PRAKASH K", "KARTHICK RAJA", "KISHAN R SHETTY", "LAKSHAY SHARMA",
    "LIKITH HN", "MALLIKAARJUN S", "N R VETRIVEL", "NAVYASHREE H", "NIKITH M",
    "NISHIMAY PARODKAR", "PALLAVI CHOUGULE", "PANKAJ SINGH", "PAVANA.V",
    "PRAPTI VINAY REVANKAR", "PRIYANSU SAHOO", "RAGHAV KEJRIWAL",
    "RAHUL SATYANARAYAN TUMMA", "Raj Bahadur", "RAJAT DAS", "RAKSHITHA V",
    "RESHIKA. M", "RITHISH NATARAJAN", "ROGAN RAJA I", "RUPESH SINGH",
    "S.V.NITHYASHREE", "SANGAVI"
]

TODAY = datetime.now().strftime("%d-%m-%Y")

# --- DATABASE MANAGEMENT (GOOGLE SHEETS) ---
@st.cache_resource
def get_gspread_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(credentials)

def load_db():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_url(st.secrets["ML_SHEET_URL"]) 
        ws_memory = sh.worksheet("App_Memory")
        val = ws_memory.acell('A1').value
        if val:
            return json.loads(val)
    except Exception:
        pass 
    return {"ML": {}, "RM": {}}

def save_db(db_data):
    for cls in ["ML", "RM"]:
        dates = list(db_data[cls].keys())
        if len(dates) > 3:
            dates.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y"))
            while len(dates) > 3:
                oldest = dates.pop(0)
                del db_data[cls][oldest]
    try:
        gc = get_gspread_client()
        sh = gc.open_by_url(st.secrets["ML_SHEET_URL"])
        ws_memory = sh.worksheet("App_Memory")
        ws_memory.update_acell('A1', json.dumps(db_data))
    except Exception as e:
        st.error(f"Failed to save to Google Sheets Memory: {e}")

if "db" not in st.session_state:
    db = load_db()
    if TODAY not in db["ML"]: db["ML"][TODAY] = []
    if TODAY not in db["RM"]: db["RM"][TODAY] = []
    save_db(db)
    st.session_state.db = db

# --- SMART PUSH TO SPREADSHEETS ---
def push_attendance_to_sheet(class_type, date_str, df):
    try:
        if class_type == "ML":
            sheet_url = st.secrets["ML_SHEET_URL"]
            header_row_idx = 3  
            student_start_row = 4 
            id_col = 6 
            date_start_col = 8 
        else:
            sheet_url = st.secrets["RM_SHEET_URL"]
            header_row_idx = 1  
            student_start_row = 2 
            id_col = 1 
            date_start_col = 2 

        gc = get_gspread_client()
        sh = gc.open_by_url(sheet_url)
        ws_master = sh.sheet1 
        
        all_vals = ws_master.get_all_values()
        header_row = all_vals[header_row_idx] if len(all_vals) > header_row_idx else []
        
        col_idx = date_start_col
        found_existing = False
        
        for idx in range(date_start_col, len(header_row)):
            if header_row[idx].strip() == date_str:
                col_idx = idx
                found_existing = True
                break
        
        if not found_existing:
            col_idx = date_start_col
            while col_idx < len(header_row) and header_row[col_idx].strip() != "":
                col_idx += 1
                
        status_map = {row["Identifier"]: ("P" if row["Present"] else "A") for _, row in df.iterrows()}
        
        max_student_row = student_start_row
        for r_idx in range(student_start_row, len(all_vals)):
            identifier = all_vals[r_idx][id_col] if len(all_vals[r_idx]) > id_col else ""
            if identifier in status_map:
                max_student_row = max(max_student_row, r_idx)
                
        col_data = [[""] for _ in range(max_student_row - header_row_idx + 1)]
        col_data[0] = [date_str] 
        
        for r_idx in range(student_start_row, max_student_row + 1):
            identifier = all_vals[r_idx][id_col] if len(all_vals[r_idx]) > id_col else ""
            if identifier in status_map:
                col_data[r_idx - header_row_idx] = [status_map[identifier]]

        start_cell = gspread.utils.rowcol_to_a1(header_row_idx + 1, col_idx + 1)
        end_cell = gspread.utils.rowcol_to_a1(max_student_row + 1, col_idx + 1)
        ws_master.update(range_name=f"{start_cell}:{end_cell}", values=col_data)
        
        if not found_existing and class_type == "ML":
            total_classes = ws_master.acell('F3').value
            if total_classes and str(total_classes).isdigit():
                ws_master.update_acell('F3', int(total_classes) + 1)
                
        return True, found_existing
    except Exception as e:
        st.error(f"Failed to push to {class_type} Master Sheet: {e}")
        return False, False

# --- EXPORT HELPERS ---
def generate_excel(df, date_str, export_type="status"):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if export_type == "names":
            export_df = df[df['Present'] == True][['Identifier']].rename(columns={'Identifier': f'Attendance for {date_str}'})
        else:
            export_df = df.copy()
            export_df["Status"] = export_df["Present"].apply(lambda x: "P" if x else "A")
            export_df = export_df[['Status']].rename(columns={'Status': date_str})
        export_df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def get_copy_html(df, date_str, export_type="status"):
    if export_type == "status":
        table_html = f"""<table id="hiddenTable" style="border-collapse: collapse; position: absolute; left: -9999px;">
            <tr><td style="font-family: Calibri, sans-serif; font-size: 12pt; font-weight: bold; background-color: #4A7ABB; color: white; text-align: center; border: 1px solid #000;">{date_str}</td></tr>"""
        for _, row in df.iterrows():
            status = "P" if row["Present"] else "A"
            color = "red" if status == "A" else "black"
            table_html += f"""<tr><td style="font-family: Calibri, sans-serif; font-size: 11pt; font-weight: bold; text-align: center; border: 1px solid #ccc; color: {color};">{status}</td></tr>"""
        table_html += "</table>"
        btn_text = "📋 Copy Column"
        
    elif export_type == "names":
        table_html = f"""<table id="hiddenTable" style="border-collapse: collapse; position: absolute; left: -9999px;">
            <tr><td style="font-family: Calibri, sans-serif; font-size: 12pt; font-weight: bold; background-color: #4A7ABB; color: white; text-align: center; border: 1px solid #000;">Attendance for {date_str}</td></tr>"""
        for _, row in df.iterrows():
            if row["Present"]:
                table_html += f"""<tr><td style="font-family: Calibri, sans-serif; font-size: 11pt; border: 1px solid #ccc; text-align: left;">{row["Identifier"]}</td></tr>"""
        table_html += "</table>"
        btn_text = "📋 Copy Names"

    html_code = f"""
    {table_html}
    <button onclick="copyTable()" style="width: 100%; padding: 8px; background-color: #28a745; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 15px; font-family: sans-serif; box-sizing: border-box; height: 100%;">{btn_text}</button>
    <script>
        function copyTable() {{
            var table = document.getElementById("hiddenTable");
            var range = document.createRange();
            range.selectNode(table);
            window.getSelection().removeAllRanges();
            window.getSelection().addRange(range);
            document.execCommand("copy");
            window.getSelection().removeAllRanges();
            var btn = document.querySelector("button");
            var orig = btn.innerText;
            btn.innerText = "✅ Copied!";
            btn.style.backgroundColor = "#20c997";
            setTimeout(() => {{ btn.innerText = orig; btn.style.backgroundColor = "#28a745"; }}, 1500);
        }}
    </script>
    <style>body {{ margin: 0; padding: 0; }}</style>
    """
    return html_code

# --- UI: MAIN APP ---
st.title("📱 Fast Attendance Marker")

tab_ml, tab_rm = st.tabs(["Machine Learning", "Research Methodology"])

# ==========================================
# MACHINE LEARNING TAB
# ==========================================
with tab_ml:
    st.header("Machine Learning")
    
    ml_dates = list(st.session_state.db["ML"].keys())
    ml_dates.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y"), reverse=True)
    selected_ml_date = st.selectbox("Select Date to Edit", ml_dates, key="ml_date")
    
    def process_ml_input():
        inp = st.session_state.ml_input.strip()
        if inp:
            entries = [s.strip() for s in inp.split(",") if s.strip()]
            for suffix in entries:
                if suffix in st.session_state.db["ML"][selected_ml_date]:
                    st.session_state.db["ML"][selected_ml_date].remove(suffix)
                else:
                    st.session_state.db["ML"][selected_ml_date].append(suffix)
            save_db(st.session_state.db)
        st.session_state.ml_input = "" 

    st.text_input("Rapid Entry: Type USN digits & press Enter", key="ml_input", on_change=process_ml_input)
    
    ml_data = []
    current_ml_absentees = st.session_state.db["ML"][selected_ml_date]
    for usn in ML_STUDENTS:
        is_present = not any(usn.endswith(abs_suffix) for abs_suffix in current_ml_absentees)
        ml_data.append({"Identifier": usn, "Present": is_present})
        
    df_ml = pd.DataFrame(ml_data)
    st.write("*(Tap the checkbox to toggle status)*")
    edited_df_ml = st.data_editor(df_ml, hide_index=True, use_container_width=True)
    
    new_absentees_ml = [row["Identifier"][-3:] for _, row in edited_df_ml.iterrows() if not row["Present"]]
    if new_absentees_ml != current_ml_absentees:
        st.session_state.db["ML"][selected_ml_date] = new_absentees_ml
        save_db(st.session_state.db)
        st.rerun()

    st.divider()
    st.markdown("### 🔒 Secure Push to Master Sheet")
    ml_password = st.text_input("Enter Authorization Password", type="password", key="ml_pass_input")
    
    if st.button(f"🚀 Push {selected_ml_date} to ML Master Sheet", use_container_width=True, type="primary"):
        # Checks against your Streamlit Secrets. Defaults to killer123 if you forget to set it.
        if ml_password == st.secrets.get("APP_PASSWORD", "killer123"):
            with st.spinner("Syncing to Google Sheets..."):
                success, overwritten = push_attendance_to_sheet("ML", selected_ml_date, edited_df_ml)
                if success:
                    if overwritten:
                        st.success(f"✅ Successfully OVERWRITTEN existing attendance for {selected_ml_date}!")
                    else:
                        st.success(f"✅ Successfully APPENDED new column for {selected_ml_date} and incremented Total Classes!")
        else:
            st.error("❌ Incorrect password. Push aborted.")

    col1, col2 = st.columns(2)
    with col1:
        excel_data_ml = generate_excel(edited_df_ml, selected_ml_date, "status")
        st.download_button(
            label="📥 Download Excel",
            data=excel_data_ml,
            file_name=f"ML_Attendance_{selected_ml_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col2:
        components.html(get_copy_html(edited_df_ml, selected_ml_date, "status"), height=45)


# ==========================================
# RESEARCH METHODOLOGY TAB
# ==========================================
with tab_rm:
    st.header("Research Methodology")
    
    rm_dates = list(st.session_state.db["RM"].keys())
    rm_dates.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y"), reverse=True)
    selected_rm_date = st.selectbox("Select Date to Edit", rm_dates, key="rm_date")
    
    def process_rm_input():
        inp = st.session_state.rm_input.strip()
        if inp:
            entries = [s.strip() for s in inp.split(",") if s.strip()]
            for entry in entries:
                matched_name = entry
                if entry not in RM_STUDENTS:
                    for name in RM_STUDENTS:
                        if entry.upper() in name.upper():
                            matched_name = name
                            break
                if matched_name in st.session_state.db["RM"][selected_rm_date]:
                    st.session_state.db["RM"][selected_rm_date].remove(matched_name)
                else:
                    st.session_state.db["RM"][selected_rm_date].append(matched_name)
            save_db(st.session_state.db)
        st.session_state.rm_input = ""

    st.text_input("Rapid Entry: Type Name & press Enter", key="rm_input", on_change=process_rm_input)
    
    rm_data = []
    current_rm_presentees = st.session_state.db["RM"][selected_rm_date]
    for name in RM_STUDENTS:
        rm_data.append({"Identifier": name, "Present": name in current_rm_presentees})
        
    df_rm = pd.DataFrame(rm_data)
    st.write("*(Tap the checkbox to toggle status)*")
    edited_df_rm = st.data_editor(df_rm, hide_index=True, use_container_width=True)
    
    new_presentees_rm = [row["Identifier"] for _, row in edited_df_rm.iterrows() if row["Present"]]
    if new_presentees_rm != current_rm_presentees:
        st.session_state.db["RM"][selected_rm_date] = new_presentees_rm
        save_db(st.session_state.db)
        st.rerun()

    st.divider()
    st.markdown("### 🔒 Secure Push to Master Sheet")
    rm_password = st.text_input("Enter Authorization Password", type="password", key="rm_pass_input")
    
    if st.button(f"🚀 Push {selected_rm_date} to RM Master Sheet", use_container_width=True, type="primary"):
        if rm_password == st.secrets.get("APP_PASSWORD", "killer123"):
            with st.spinner("Syncing to Google Sheets..."):
                success, overwritten = push_attendance_to_sheet("RM", selected_rm_date, edited_df_rm)
                if success:
                    if overwritten:
                        st.success(f"✅ Successfully OVERWRITTEN existing attendance for {selected_rm_date}!")
                    else:
                        st.success(f"✅ Successfully APPENDED new column for {selected_rm_date}!")
        else:
            st.error("❌ Incorrect password. Push aborted.")

    st.markdown("### Export Options")
    col_dl_names, col_cp_names = st.columns(2)
    with col_dl_names:
        excel_names_rm = generate_excel(edited_df_rm, selected_rm_date, "names")
        st.download_button(
            label="📥 Download Names",
            data=excel_names_rm,
            file_name=f"RM_Names_{selected_rm_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_cp_names:
         components.html(get_copy_html(edited_df_rm, selected_rm_date, "names"), height=45)

    col_dl_status, col_cp_status = st.columns(2)
    with col_dl_status:
        excel_status_rm = generate_excel(edited_df_rm, selected_rm_date, "status")
        st.download_button(
            label="📥 Download A/P",
            data=excel_status_rm,
            file_name=f"RM_Status_{selected_rm_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with col_cp_status:
        components.html(get_copy_html(edited_df_rm, selected_rm_date, "status"), height=45)
