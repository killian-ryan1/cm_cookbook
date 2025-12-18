import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import urllib.parse

# --- 1. PASSWORD PROTECTION ---
def check_password():
    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    return True

def password_entered():
    # Keep the password "max" as requested
    if st.session_state["password"] == "max": 
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- 2. GOOGLE SHEETS CONNECTION ---
def get_data_from_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Authenticate using Streamlit Secrets (TOML format in Streamlit Cloud)
    creds_dict = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        "private_key": st.secrets["private_key"],
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"]
    }
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Replace with the EXACT name of your Google Sheet
    sheet = client.open("My_Recipe_Database").sheet1 
    return pd.DataFrame(sheet.get_all_records())

# --- MAIN APP ---
if check_password():
    try:
        df = get_data_from_google()
    except Exception as e:
        st.error(f"Could not connect to Google Sheets: {e}")
        st.stop()

    st.title("🍽️ Caoimhe's Smart Shopping List")

    # --- 3. SEARCH & SELECTION ---
    st.header("Plan your week")
    recipe_names = sorted(df['Recipe Name'].unique().tolist())
    selected_meals = st.multiselect("Select your meals:", options=recipe_names)

    # --- 4. SERVING SIZES ---
    meal_servings = {}
    if selected_meals:
        st.subheader("Set Servings")
        cols = st.columns(len(selected_meals))
        for i, meal in enumerate(selected_meals):
            with cols[i]:
                meal_servings[meal] = st.number_input(f"{meal}", min_value=1, value=1, key=f"serve_{meal}")

    # --- 5. AGGREGATION LOGIC ---
    if selected_meals:
        st.divider()
        st.header("🛒 Organized Shopping List")
        
        # This dictionary will store our data grouped by category
        master_list = {}
        
        selected_df = df[df['Recipe Name'].isin(selected_meals)]

        for _, row in selected_df.iterrows():
            item = row['Ingredient']
            qty = row['Quantity']
            unit = row['Unit']
            # READ CATEGORY FROM SHEET: defaults to 'Other' if cell is empty
            cat = str(row.get('Category', 'Other')).strip()
            if not cat: cat = "Other"
            
            multiplier = meal_servings.get(row['Recipe Name'], 1)
            total_qty = qty * multiplier
            
            # Organize into the master_list
            if cat not in master_list: master_list[cat] = {}
            if item not in master_list[cat]: 
                master_list[cat][item] = {'qty': 0, 'unit': unit}
            
            master_list[cat][item]['qty'] += total_qty

        # --- 6. DISPLAY & WHATSAPP ---
        whatsapp_text = f"🍽️ *PLAN: {', '.join(selected_meals)}*\n\n"
        
        # Sort categories alphabetically for a clean UI
        sorted_cats = sorted(master_list.keys())
        for category in sorted_cats:
            st.markdown(f"### 📍 {category}")
            whatsapp_text += f"*{category.upper()}*\n"
            
            for item, data in master_list[category].items():
                line = f"{data['qty']}{data['unit']} {item}"
                st.checkbox(line, key=f"chk_{item}_{category}")
                whatsapp_text += f"- [ ] {line}\n"
            st.write("")
            whatsapp_text += "\n"

        # --- 7. ACTION BUTTONS ---
        st.divider()
        
        encoded_text = urllib.parse.quote(whatsapp_text)
        wa_url = f"https://wa.me/?text={encoded_text}"
        st.link_button("📲 Share to WhatsApp", wa_url)

        if st.button("🗑️ Clear All Selections"):
            # Clear everything except the login status
            for key in list(st.session_state.keys()):
                if key != "password_correct":
                    del st.session_state[key]
            st.rerun()
            
    else:
        st.info("Start typing a meal name above to build your list.")
