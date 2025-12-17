import streamlit as st
import json
import os

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

    st.title("🍽️ Smart Meal Planner")

    # --- 2. SEARCH & SELECTION ---
    st.header("Plan your week")
    
    # Multiselect with a search filter built-in
    selected_meals = st.multiselect(
        "Search and select your meals:", 
        options=list(recipes.keys()),
        help="Type to filter recipes"
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
        
        # Structure: {Category: {Ingredient: {qty: X, unit: Y}}}
        master_list = {}

        for meal in selected_meals:
            multiplier = meal_servings[meal]
            ingredients = recipes[meal]
            
            for item, info in ingredients.items():
                cat = info.get('cat', 'Other')
                qty = info['qty'] * multiplier
                unit = info['unit']
                
                if cat not in master_list:
                    master_list[cat] = {}
                
                if item not in master_list[cat]:
                    master_list[cat][item] = {'qty': 0, 'unit': unit}
                
                master_list[cat][item]['qty'] += qty

        # --- 5. DISPLAY BY CATEGORY ---
        # Sort categories so Protein is usually near the top
        sorted_cats = sorted(master_list.keys())
        
        for category in sorted_cats:
            st.markdown(f"### 📍 {category}")
            for item, data in master_list[category].items():
                # Display nicely: "300g Minced Beef"
                st.checkbox(f"{data['qty']}{data['unit']} {item}", key=f"check_{item}")
            st.write("") # Add spacing

        if st.button("Clear All"):
            st.rerun()
    else:
        st.info("Start typing a meal name above to build your list.")
