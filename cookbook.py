import streamlit as st
from streamlit_gsheets import GSheetsConnection
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
    if st.session_state["password"] == "max": 
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- 2. GOOGLE SHEETS CONNECTION ---
def get_data_from_google():
    # This library handles the 'handshake' more reliably in the cloud
    conn = st.connection("gsheets", type=GSheetsConnection)
    # It will look for the [connections.gsheets] section in your secrets
    return conn.read(ttl="1m")

# --- MAIN APP ---
if check_password():
    try:
        df = get_data_from_google()
        
        # Simple cleanup to remove any completely empty rows from the sheet
        df = df.dropna(subset=['Recipe Name', 'Ingredient'])
        
    except Exception as e:
        st.error(f"Could not connect to Google Sheets: {e}")
        st.info("Check your Streamlit Secrets and ensure the Sheet is shared with your Service Account email.")
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
        
        master_list = {}
        selected_df = df[df['Recipe Name'].isin(selected_meals)]

        for _, row in selected_df.iterrows():
            item = row['Ingredient']
            qty = row['Quantity']
            unit = row['Unit']
            cat = str(row.get('Category', 'Other')).strip()
            if not cat or cat == 'nan': cat = "Other"
            
            multiplier = meal_servings.get(row['Recipe Name'], 1)
            
            # Use float conversion to handle potential string numbers in Sheets
            try:
                total_qty = float(qty) * multiplier
            except:
                total_qty = 0
            
            if cat not in master_list: master_list[cat] = {}
            if item not in master_list[cat]: 
                master_list[cat][item] = {'qty': 0, 'unit': unit}
            
            master_list[cat][item]['qty'] += total_qty

        # --- 6. DISPLAY & WHATSAPP ---
        whatsapp_text = f"🍽️ *PLAN: {', '.join(selected_meals)}*\n\n"
        
        sorted_cats = sorted(master_list.keys())
        for category in sorted_cats:
            st.markdown(f"### 📍 {category}")
            whatsapp_text += f"*{category.upper()}*\n"
            
            for item, data in master_list[category].items():
                # Clean up display if qty is a whole number (e.g., 2.0 -> 2)
                display_qty = int(data['qty']) if data['qty'] == int(data['qty']) else data['qty']
                line = f"{display_qty}{data['unit']} {item}"
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
            for key in list(st.session_state.keys()):
                if key != "password_correct":
                    del st.session_state[key]
            st.rerun()
            
    else:
        st.info("Start typing a meal name above to build your list.")
