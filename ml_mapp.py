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
    
    with st.form("login_form"):
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if pwd == st.secrets.get("APP_PASSWORD", "killer123"):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Incorrect Password")
    st.stop() 


# --- ATTENDANCE DATA ---
ML_STUDENTS = [
    "001-AARON CHACKO JACOB", "002-ABHISHEK M NAIR", "003-ADITHYA KRISHNAN T N",
    "004-ARJUN KRESHNAN C M", "005-ASHER JACOB DANI", "006-BHARGAV K N",
    "007-GOWTHAM M S", "008-HANI MUHAMMED NOUSHAD", "009-HARIKIRAN S",
    "010-ISHA K S", "011-JAYA NIDHI", "012-KARAKAMUKKALA ASHRAF",
    "013-NIKITH M", "014-NISHIMAY MINAR PARODKAR", "015-RESHIKA M",
    "016-RITHISH NATARAJAN E", "017-RUPESH SINGH", "018-SANGAVI M",
    "019-SHUMAQUE SHARIQUE UKAYE", "020-YENUMULA VINUTHNA SRI",
    "021-ZIRGOM HAIDAR AMAN", "022-AADITYA A NAIR", "023-AMAN KUMAWAT",
    "024-ANUSHREE S JAMBAGI", "025-ARJUN P", "026-ARSHAD ALOM",
    "027-ASHISH U K", "028-DEBADRITA SAHA", "029-DEEPAK B M",
    "030-EZHILARASAN M", "031-GRACY SWEETY T", "032-HIMNISH KUMAR R",
    "033-KISHAN R SHETTY", "034-LAKSHAY SHARMA", "035-MALLIKAARJUN S",
    "036-PRAPTI VINAY REVANKAR", "037-RAGHAV KEJRIWAL", "038-RAKSHITHA V",
    "039-SATWARA RUSHIL KEYUR", "040-SYED AYAAN AHMED", "041-VRUNDA S",
    "042-YASHAS R", "161-PRATEEKSHA", "167-A K KARTHICK RAJA",
    "168-CHINMAYEE K RAJ", "169-CHIRANTH POONACHA P G", "170-JAYA PRAKASH K",
    "171-PAVANA V", "172-RAJ BAHADUR", "173-VINOD MOHAN",
    "178-AMINA MUNNA", "179-ANOON M R", "180-N R VETRIVEL",
    "181-PALLAVI VISHAL CHOUGULE", "182-VADHIYA NEEL JITENDRABHAI",
    "197-VINVALAN N", "198-I ROGAN RAJA", "199-ASSUDANI SIDDHI SATYANKUMR",
    "200-NAVYASHREE H", "201-DHANYA VARSHA V", "207-DARSHAN MURTHY K",
    "208-HARSH TIWARI", "209-LIKITH H N", "210-TOUFEEQ AHAMED QADRI",
    "211-PRIYANSU SAHOO", "218-SIMRAN CHAUDHARY", "220-VANSH RAJ PARASHAR",
    "223-PANKAJ SINGH", "233-BADANAEGOUGNON ABDOUGAFAR",
    "298-ZAKARIA MAHAMAT HAKI", "300-ABDUL KAIZ", "301-SHRIYA G KARNEES"
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

col_title, col_logout = st.columns([3, 1])
with col_logout:
    st.button("Log Out", on_click=lambda: st.session_state.update(logged_in=False), use_container_width=True)

tab_ml, tab_rm = st.tabs(["Machine Learning", "Research Methodology"])

# ==========================================
# MACHINE LEARNING TAB
# ==========================================
with tab_ml:
    st.header("Machine Learning")
    
    ml_dates = list(st.session_state.db["ML"].keys())
    ml_dates.sort(key=lambda date: datetime.strptime(date, "%d-%m-%Y"), reverse=True)
    selected_ml_date = st.selectbox("Select Date to Edit", ml_dates, key="ml_date")
    
    with st.form(key=f"ml_form_{selected_ml_date}", clear_on_submit=True):
        ml_input = st.text_input("Rapid Entry: Type 1-3 digits & press Enter (e.g. 5, 12, 161)")
        ml_submit = st.form_submit_button("Toggle Students")
        
        if ml_submit and ml_input.strip():
            entries = [s.strip().zfill(3) for s in ml_input.split(",") if s.strip()]
            for suffix in entries:
                if suffix in st.session_state.db["ML"][selected_ml_date]:
                    st.session_state.db["ML"][selected_ml_date].remove(suffix)
                else:
                    st.session_state.db["ML"][selected_ml_date].append(suffix)
            save_db(st.session_state.db)
            st.rerun()

    st.write("*(Tap a name or checkbox to toggle status, then click Save!)*")
    current_ml_absentees = st.session_state.db["ML"][selected_ml_date]
    
    # --- UPGRADED UI: Checkboxes allow tapping the name directly ---
    with st.form(key=f"editor_form_ml_{selected_ml_date}"):
        with st.container(height=500):
            checkbox_states = {}
            for student in ML_STUDENTS:
                # Extract USN so Rapid Entry stays compatible
                usn = student.split("-")[0] 
                is_present = usn not in current_ml_absentees
                
                # Checkbox natively allows clicking the text label to toggle!
                checkbox_states[usn] = st.checkbox(student, value=is_present)
                
        save_ml = st.form_submit_button("💾 Save Attendance")
        
        if save_ml:
            new_absentees_ml = [usn for usn, present in checkbox_states.items() if not present]
            if new_absentees_ml != current_ml_absentees:
                st.session_state.db["ML"][selected_ml_date] = new_absentees_ml
                save_db(st.session_state.db)
            st.success("✅ Saved! You can now Download or Copy.")
            st.rerun()

    # Rebuild Dataframe for Export based on latest DB status
    updated_ml_absentees = st.session_state.db["ML"][selected_ml_date]
    export_data_ml = [{"Identifier": student, "Present": student.split("-")[0] not in updated_ml_absentees} for student in ML_STUDENTS]
    edited_df_ml = pd.DataFrame(export_data_ml)

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
    st.write("*(Click precisely on the checkbox to toggle status, then click Save!)*")
    
    # Keeping RM Tab as Data Editor table for now
    with st.form(key=f"editor_form_rm_{selected_rm_date}"):
        with st.container(height=500):
            edited_df_rm = st.data_editor(df_rm, hide_index=True, use_container_width=True)
            
        save_rm = st.form_submit_button("💾 Save Attendance")
        
        if save_rm:
            new_presentees_rm = [row["Identifier"] for _, row in edited_df_rm.iterrows() if row["Present"]]
            if new_presentees_rm != current_rm_presentees:
                st.session_state.db["RM"][selected_rm_date] = new_presentees_rm
                save_db(st.session_state.db)
            st.success("✅ Saved! You can now Download or Copy.")

    st.divider()
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
