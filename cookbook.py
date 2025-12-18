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
    conn = st.connection("gsheets", type=GSheetsConnection)
    return conn.read(ttl="1m")

# --- MAIN APP ---
if check_password():
    try:
        df = get_data_from_google()
        df = df.dropna(subset=['Recipe Name', 'Ingredient'])
    except Exception as e:
        st.error(f"Could not connect to Google Sheets: {e}")
        st.stop()

    st.title("🍽️ Caoimhe's Smart Shopping List")

    # --- 3. SEARCH & SELECTION (ALPHABETICAL & SEARCHABLE) ---
    st.header("Plan your week")
    # Rule 1: Sorting alphabetically
    recipe_names = sorted(df['Recipe Name'].unique().tolist())
    
    # Rule 2: multiselect in Streamlit is natively searchable on mobile!
    selected_meals = st.multiselect(
        "Search and select your meals:", 
        options=recipe_names,
        placeholder="Start typing (e.g. 'Spag')..."
    )

    # --- 4. INDIVIDUAL SERVING SIZES (0.5 INCREMENTS) ---
    meal_servings = {}
    if selected_meals:
        st.subheader("Set Servings")
        cols = st.columns(len(selected_meals))
        for i, meal in enumerate(selected_meals):
            with cols[i]:
                # Rule 4: Changed to number_input with step=0.5 and float format
                meal_servings[meal] = st.number_input(
                    f"{meal}", 
                    min_value=0.0, 
                    value=1.0, 
                    step=0.5, 
                    key=f"serve_{meal}"
                )

    # --- 5. AGGREGATION LOGIC ---
    if selected_meals:
        st.divider()
        st.header("🛒 Organized Shopping List")
        
        master_list = {}
        selected_df = df[df['Recipe Name'].isin(selected_meals)]

        for _, row in selected_df.iterrows():
            item = row['Ingredient']
            qty = row['Quantity']
            unit = str(row['Unit']).strip()
            cat = str(row.get('Category', 'Other')).strip()
            if not cat or cat == 'nan': cat = "Other"
            
            multiplier = meal_servings.get(row['Recipe Name'], 1.0)
            
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
                # Rule 3: Smart Spacing
                # If unit is common (g, kg, ml, etc), keep it tight. Otherwise, add a space.
                tight_units = ['g', 'kg', 'ml', 'l', 'lb', 'lbs', 'oz']
                unit_str = data['unit']
                
                if unit_str.lower() in tight_units or not unit_str:
                    spacing = ""
                else:
                    spacing = " " # Add space for "whole", "tin", "pack" etc.

                display_qty = int(data['qty']) if data['qty'] == int(data['qty']) else data['qty']
                
                line = f"{display_qty}{spacing}{unit_str} {item}"
                st.checkbox(line, key=f"chk_{item}_{category}")
                whatsapp_text += f"- [ ] {line}\n"
            st.write("")
            whatsapp_text += "\n"

        # --- 7. ACTION BUTTONS ---
        st.divider()
        encoded_text = urllib.parse.quote(whatsapp_text)
        st.link_button("📲 Share to WhatsApp", f"https://wa.me/?text={encoded_text}")

        if st.button("🗑️ Clear All Selections"):
            for key in list(st.session_state.keys()):
                if key != "password_correct":
                    del st.session_state[key]
            st.rerun()
            
    else:
        st.info("Start typing a meal name above to build your list.")
