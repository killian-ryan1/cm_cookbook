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

    # --- 3. SEARCH & SELECTION ---
    st.header("Plan your week")
    
    all_recipes = sorted(df['Recipe Name'].unique().tolist())
    
    # Get current selections
    current_selections = st.session_state.get('selected_meals_list', [])

    # ADDED 'key' to allow the button to clear the text box
    search_term = st.text_input("🔍 Search for a meal:", placeholder="Type here...", key="search_query")

    if search_term:
        search_results = [r for r in all_recipes if search_term.lower() in r.lower()]
    else:
        search_results = all_recipes

    combined_options = sorted(list(set(search_results + current_selections)))

    selected_meals = st.multiselect(
        "Choose from list:", 
        options=combined_options,
        default=current_selections,
        key="selected_meals_list"
    )

    # --- 4. INDIVIDUAL SERVING SIZES ---
    meal_servings = {}
    if selected_meals:
        st.subheader("Set Servings")
        for meal in selected_meals:
            meal_servings[meal] = st.number_input(
                f"Servings for {meal}:", 
                min_value=0.0, 
                value=1.0, 
                step=0.5, 
                format="%.1f",
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
                tight_units = ['g', 'kg', 'ml', 'l', 'lb', 'lbs', 'oz']
                unit_str = data['unit']
                spacing = "" if unit_str.lower() in tight_units or not unit_str else " "

                q = data['qty']
                display_qty = int(q) if q == int(q) else q
                
                line = f"{display_qty}{spacing}{unit_str} {item}"
                st.checkbox(line, key=f"chk_{item}_{category}")
                whatsapp_text += f"- [ ] {line}\n"
            st.write("")
            whatsapp_text += "\n"

        # --- 7. ACTION BUTTONS ---
        st.divider()
        encoded_text = urllib.parse.quote(whatsapp_text)
        st.link_button("📲 Share to WhatsApp", f"https://wa.me/?text={encoded_text}")

        # --- IMPROVED CLEAR LOGIC ---
        if st.button("🗑️ Clear All Selections"):
            # We wipe the search box and the selection list
            st.session_state["search_query"] = ""
            st.session_state["selected_meals_list"] = []
            
            # Wipe everything else (serving sizes, etc.)
            for key in list(st.session_state.keys()):
                if key not in ["password_correct", "search_query", "selected_meals_list"]:
                    del st.session_state[key]
            
            st.rerun()
            
    else:
        st.info("Search for a meal above to start building your list.")
