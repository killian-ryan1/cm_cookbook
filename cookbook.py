import streamlit as st
import json
import os

# --- 1. PASSWORD PROTECTION LOGIC ---
def check_password():
    """Returns True if the user had the correct password."""
    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

def password_entered():
    """Checks whether a password entered by the user is correct."""
    if st.session_state["password"] == "max":  # <--- CHANGE THIS
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False

# --- 2. MAIN APP (ONLY RUNS IF PASSWORD IS CORRECT) ---
if check_password():
    FILE_NAME = 'recipes.json'

    def load_recipes():
        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, 'r') as f:
                return json.load(f)
        return {}

    recipes = load_recipes()

    st.title("🍽️ My Weekly Shop")

    # Selection Area
    st.header("Plan your week")
    selected_meals = st.multiselect(
        "Which meals are you having?", 
        options=list(recipes.keys())
    )

    # Ingredients Logic
    if selected_meals:
        st.divider()
        st.header("🛒 Shopping List")
        
        shopping_list = {}
        for meal in selected_meals:
            ingredients = recipes[meal]
            for item, qty in ingredients.items():
                # This combines totals (e.g. 1 onion + 1 onion = 2 onions)
                shopping_list[item] = shopping_list.get(item, 0) + qty

        # Display as a clean list with checkboxes for the store
        for item, qty in shopping_list.items():
            st.checkbox(f"{qty}x {item}", key=item)
            
        if st.button("Clear Selections"):
            st.rerun()
    else:
        st.info("Select your dinners from the dropdown above to generate your list.")
