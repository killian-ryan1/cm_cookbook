import streamlit as st
import json
import os

# --- DATA HANDLING ---
FILE_NAME = 'recipes.json'

def load_recipes():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, 'r') as f:
            return json.load(f)
    return {}

def save_recipes(data):
    with open(FILE_NAME, 'w') as f:
        json.dump(data, f, indent=4)

recipes = load_recipes()

# --- APP INTERFACE ---
st.title("Selection & Shop")

# Selection Area
st.header("Plan your week")
selected_meals = st.multiselect("Which meals are you having?", options=list(recipes.keys()))

if selected_meals:
    st.header("Your Shopping List")
    shopping_list = {}
    for meal in selected_meals:
        for item, qty in recipes[meal].items():
            shopping_list[item] = shopping_list.get(item, 0) + qty
    
    for item, qty in shopping_list.items():
        st.checkbox(f"{qty}x {item}")

# --- ADD NEW RECIPES ---
st.divider()
with st.expander("Add a New Recipe"):
    new_name = st.text_input("Recipe Name")
    new_ingredients = st.text_area("Ingredients (Format: Item:Quantity, one per line)", "Onion:1")
    
    if st.button("Save Recipe"):
        # Convert text area to dictionary
        ing_dict = {}
        for line in new_ingredients.split('\n'):
            if ':' in line:
                item, qty = line.split(':')
                ing_dict[item.strip()] = int(qty.strip())
        
        recipes[new_name] = ing_dict
        save_recipes(recipes)
        st.success(f"Added {new_name}!")
        st.rerun() # Refresh to show the new recipe in the list