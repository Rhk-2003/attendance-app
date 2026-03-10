import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import io
import streamlit.components.v1 as components

# --- CONFIGURATION ---
st.set_page_config(page_title="Attendance Tracker", layout="centered")

# --- SECURE LOGIN GATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Secure Access")
    st.write("Please log in to access the Attendance Tracker.")
    
    # We use a form so hitting Enter submits the password
    with st.form("login_form"):
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Checks your Streamlit Secrets. Defaults to 'killer123' if not set.
            if pwd == st.secrets.get("APP_PASSWORD", "killer123"):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password")
    st.stop() # Stops the rest of the app from loading until logged in


# --- ATTENDANCE DATA ---
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

DB_FILE = "attendance_db.json"
TODAY = datetime.now().strftime("%d-%m-%Y")

# --- LOCAL DATABASE MANAGEMENT ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"ML": {}, "RM": {}}

def save_db(db_data):
    for cls in ["ML", "RM"]:
        dates = list(db_data[cls].keys())
        if len(dates) > 3:
            dates.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y"))
            while len(dates) > 3:
                oldest = dates.pop(0)
                del db_data[cls][oldest]
                
    with open(DB_FILE, "w") as f:
        json.dump(db_data, f, indent=4)

if "db" not in st.session_state:
    db = load_db()
    if TODAY not in db["ML"]: db["ML"][TODAY] = []
    if TODAY not in db["RM"]: db["RM"][TODAY] = []
    save_db(db)
    st.session_state.db = db

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
st.button("Log Out", on_click=lambda: st.session_state.update(logged_in=False))

tab_ml, tab_rm = st.tabs(["Machine Learning", "Research Methodology"])

# ==========================================
# MACHINE LEARNING TAB
# ==========================================
with tab_ml:
    st.header("Machine Learning")
    
    ml_dates = list(st.session_state.db["ML"].keys())
    ml_dates.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y"), reverse=True)
    selected_ml_date = st.selectbox("Select Date to Edit", ml_dates, key="ml_date")
    
    # Using a Form here stops the page from jumping while you are typing
    with st.form(key=f"ml_form_{selected_ml_date}", clear_on_submit=True):
        ml_input = st.text_input("Rapid Entry: Type USN digits & press Enter")
        ml_submit = st.form_submit_button("Toggle Students")
        
        if ml_submit and ml_input.strip():
            entries = [s.strip() for s in ml_input.split(",") if s.strip()]
            for suffix in entries:
                if suffix in st.session_state.db["ML"][selected_ml_date]:
                    st.session_state.db["ML"][selected_ml_date].remove(suffix)
                else:
                    st.session_state.db["ML"][selected_ml_date].append(suffix)
            save_db(st.session_state.db)
            st.rerun()

    ml_data = []
    current_ml_absentees = st.session_state.db["ML"][selected_ml_date]
    for usn in ML_STUDENTS:
        is_present = not any(usn.endswith(abs_suffix) for abs_suffix in current_ml_absentees)
        ml_data.append({"Identifier": usn, "Present": is_present})
        
    df_ml = pd.DataFrame(ml_data)
    st.write("*(Tap the checkbox to toggle status)*")
    
    edited_df_ml = st.data_editor(df_ml, hide_index=True, use_container_width=True, key=f"editor_ml_{selected_ml_date}")
    
    # Process checkbox edits and save locally
    new_absentees_ml = [row["Identifier"][-3:] for _, row in edited_df_ml.iterrows() if not row["Present"]]
    if new_absentees_ml != current_ml_absentees:
        st.session_state.db["ML"][selected_ml_date] = new_absentees_ml
        save_db(st.session_state.db)

    st.divider()
    st.markdown("### Export Options")
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
    
    with st.form(key=f"rm_form_{selected_rm_date}", clear_on_submit=True):
        rm_input = st.text_input("Rapid Entry: Type Name & press Enter")
        rm_submit = st.form_submit_button("Toggle Students")
        
        if rm_submit and rm_input.strip():
            entries = [s.strip() for s in rm_input.split(",") if s.strip()]
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
            st.rerun()
    
    rm_data = []
    current_rm_presentees = st.session_state.db["RM"][selected_rm_date]
    for name in RM_STUDENTS:
        rm_data.append({"Identifier": name, "Present": name in current_rm_presentees})
        
    df_rm = pd.DataFrame(rm_data)
    st.write("*(Tap the checkbox to toggle status)*")
    
    edited_df_rm = st.data_editor(df_rm, hide_index=True, use_container_width=True, key=f"editor_rm_{selected_rm_date}")
    
    new_presentees_rm = [row["Identifier"] for _, row in edited_df_rm.iterrows() if row["Present"]]
    if new_presentees_rm != current_rm_presentees:
        st.session_state.db["RM"][selected_rm_date] = new_presentees_rm
        save_db(st.session_state.db)

    st.divider()
    st.markdown("### Export Options (Names Only)")
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

    st.markdown("### Export Options (A/P Column)")
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
