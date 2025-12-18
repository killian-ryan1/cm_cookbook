import streamlit as st
import json
import os
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
    if st.session_state["password"] == "max": # <--- SET YOUR PASSWORD
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

if check_password():
    FILE_NAME = 'recipes.json'

    def load_recipes():
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, 'r') as f:
                return json.load(f)
        return {}

    recipes = load_recipes()

    # --- UPDATED TITLE ---
    st.title("🍽️ Caoimhe's Smart Shopping List")

    # --- 2. SEARCH & SELECTION ---
    st.header("Plan your week")
    selected_meals = st.multiselect(
        "Search and select your meals:", 
        options=list(recipes.keys()),
        key="selected_meals_list" 
    )

    # --- 3. INDIVIDUAL SERVING SIZES ---
    meal_servings = {}
    if selected_meals:
        st.subheader("Set Servings")
        cols = st.columns(len(selected_meals))
        for i, meal in enumerate(selected_meals):
            with cols[i]:
                meal_servings[meal] = st.number_input(f"{meal}", min_value=1, value=1, key=f"serve_{meal}")

    # --- 4. AGGREGATION LOGIC ---
    if selected_meals:
        st.divider()
        st.header("🛒 Organized Shopping List")
        
        master_list = {}
        for meal in selected_meals:
            multiplier = meal_servings[meal]
            ingredients = recipes[meal]
            for item, info in ingredients.items():
                if isinstance(info, dict):
                    cat = info.get('cat', 'Other')
                    qty = info.get('qty', 0) * multiplier
                    unit = info.get('unit', '')
                else:
                    cat = 'Other'
                    qty = info * multiplier
                    unit = ''
                
                if cat not in master_list: master_list[cat] = {}
                if item not in master_list[cat]: master_list[cat][item] = {'qty': 0, 'unit': unit}
                master_list[cat][item]['qty'] += qty

        # --- 5. DISPLAY & WHATSAPP GENERATION ---
        # Added meal names to the top of the WhatsApp text
        meal_names_str = ", ".join(selected_meals)
        whatsapp_text = f"🍽️ *PLAN: {meal_names_str}*\n\n🛒 *SHOPPING LIST*\n\n"
        
        sorted_cats = sorted(master_list.keys())
        for category in sorted_cats:
            st.markdown(f"### 📍 {category}")
            whatsapp_text += f"*{category.upper()}*\n"
            for item, data in master_list[category].items():
                line = f"{data['qty']}{data['unit']} {item}"
                st.checkbox(line, key=f"check_{item}")
                whatsapp_text += f"- [ ] {line}\n"
            st.write("")
            whatsapp_text += "\n"

        # --- 6. ACTION BUTTONS ---
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
