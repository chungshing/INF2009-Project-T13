import streamlit as st
from app import create_app, db, bcrypt
from app.models import User
from aiModel import analyze_image
from flask_login import login_user, LoginManager
from werkzeug.utils import secure_filename
from streamlit_option_menu import option_menu
import os
from food_nutrition import get_nutritional_values_local
import re
from PIL.Image import Resampling
import torch
from flask import request, jsonify
from PIL import Image
import threading
import pandas as pd
from datetime import datetime, timedelta
from app.models import NutritionalIntake
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode
import secrets

# User and assistant names
U_NAME = "User"
A_NAME = "Assistant"

# Set page configuration
st.set_page_config(
    page_title="HawkerScan",
    page_icon="",
    layout="wide",
)

nutrient_field_mapping = {
    "Energy (kcal)": "energy_kcal",
    "Protein (g)": "protein_g",
    "Carbohydrate (g)": "carbohydrate_g",
    "Sodium (mg)": "sodium_mg",
    "Total fat (g)": "total_fat_g",
    "Saturated fat (g)": "saturated_fat_g",
    "Dietary fibre (g)": "dietary_fibre_g",
    "Cholesterol (mg)": "cholesterol_mg",
    "Cholesterol (g)": "cholesterol_g"
}

# Create and configure the Flask app
flask_app = create_app()
login_manager = LoginManager()
login_manager.init_app(flask_app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

flask_app.app_context().push()

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}_{secure_filename(file.name)}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, 'wb') as f:
        f.write(file.getbuffer())
    return file_path

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

if 'selected_image' not in st.session_state:
    st.session_state['selected_image'] = None

if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []

if 'context' not in st.session_state:
    st.session_state['context'] = []

# Set the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Authentication functions
def sidebar_with_logo():
    with st.sidebar:
        if st.session_state['authenticated']:
            menu_options = ["Home", "Nutritional Intake", "Manage Entries", "Logout"]
            menu_icons   = ["house", "calendar3", "pencil-square", "door-open"]
        else:
            menu_options = ["Login", "Register"]
            menu_icons   = ["person", "person-add"]

        selected = option_menu(
            "Menu",
            menu_options,
            icons=menu_icons,
            menu_icon="list",
            styles={
                "menu-title": {"font-size": "18px"},
                "icon": {"color": "orange", "font-size": "15px"},
                "nav-link": {"font-size": "15px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#E86A33"},
            },
            default_index=0,
            key="sidebar_menu"
        )
    return selected



def login():
    st.markdown("<h1 style='text-align: center;'>Login</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        email = st.text_input("Enter your email", key="email_login")
        password = st.text_input("Enter your password", type='password', key="password_login")
        if st.button("Login", key="login_button"):
            with flask_app.test_request_context('/login'):
                user = User.query.filter_by(email=email).first()
                if user and bcrypt.check_password_hash(user.password, password):
                    if not user.api_key:
                        user.api_key = generate_api_key()
                        db.session.commit()

                    login_user(user)
                    st.session_state['user_id'] = user.id
                    st.session_state['authenticated'] = True
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Login Unsuccessful. Please check email and password")


def generate_api_key(length=32):
    # Return a random URL-safe text string
    return secrets.token_urlsafe(length)[:length]

def register():
    st.markdown("<h1 style='text-align: center;'>Register</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        username = st.text_input("Enter your username", key="register_username")
        email = st.text_input("Enter your email", key="register_email")
        password = st.text_input("Enter your password", type='password', key="register_password")
        confirm_password = st.text_input("Confirm your password", type='password', key="register_confirm_password")

        if st.button("Sign Up", key="register_button"):
            if password == confirm_password:
                with flask_app.test_request_context('/register'):
                    # Check if the email already exists
                    existing_user = User.query.filter_by(email=email).first()
                    if existing_user:
                        st.error("This email is already registered. Please use another email.")
                        return

                    # Generate hashed password
                    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

                    # Add the user to the `user` table
                    user = User(username=username, email=email, password=hashed_password)

                    # Generate an API key
                    user.api_key = generate_api_key()

                    db.session.add(user)
                    db.session.commit()

                    st.success("Your account has been created! You can now log in.")
            else:
                st.error("Passwords do not match")

if 'dish_name' not in st.session_state:
    st.session_state.dish_name = None
if 'dish_mass' not in st.session_state:
    st.session_state.dish_mass = None
if 'ingredients' not in st.session_state:
    st.session_state.ingredients = []
if 'ingredients_mass' not in st.session_state:
    st.session_state.ingredients_mass = []

def extract_info_from_response(response):
    import sqlite3
    from fuzzywuzzy import process, fuzz

    # Initialize dish_name and ingredients in session state if not already present
    if 'dish_name' not in st.session_state:
        st.session_state.dish_name = None
    if 'ingredients' not in st.session_state:
        st.session_state.ingredients = []
    if 'dish_mass' not in st.session_state:
        st.session_state.dish_mass = None
    if 'ingredients_mass' not in st.session_state:
        st.session_state.ingredients_mass = []

    # Extract dish name from the response
    dish_name_match = re.search(r'This is a dish called (.+)\.', response)
    if dish_name_match:
        extracted_dish_name = dish_name_match.group(1).strip()
    else:
        # If dish name not found, retain existing value or handle accordingly
        extracted_dish_name = None

    # Fetch ingredients based on the dish name
    if extracted_dish_name:
        conn = sqlite3.connect('instance/site.db')
        cursor = conn.cursor()

        # Find the dish in the database using fuzzy matching
        cursor.execute("SELECT food_name FROM food_items")
        all_food_names = [row[0] for row in cursor.fetchall()]
        matched_food_name, score = process.extractOne(extracted_dish_name, all_food_names)
        if score >= 80:  # Adjust the threshold as needed
            st.session_state.dish_name = matched_food_name

            # Get the food_id for the matched food name
            cursor.execute("SELECT id FROM food_items WHERE food_name = ?", (st.session_state.dish_name,))
            food_id_row = cursor.fetchone()
            if food_id_row:
                food_id = food_id_row[0]

                # Fetch the ingredients for the matched dish using the relationships table
                cursor.execute("""
                    SELECT i.ingredient_name
                    FROM relationships r
                    JOIN ingredients i ON r.target_id = i.id
                    WHERE r.source_type = 'Food' AND r.source_id = ?
                    AND r.target_type = 'Ingredient' AND r.relation_type = 'CONTAINS_INGREDIENT'
                """, (food_id,))
                ingredients = [row[0] for row in cursor.fetchall()]
                st.session_state.ingredients = ingredients
            else:
                st.warning(f"Dish '{st.session_state.dish_name}' not found in the database.")
                st.session_state.ingredients = []
        else:
            st.warning(f"Dish '{extracted_dish_name}' not found in the database.")
            st.session_state.dish_name = extracted_dish_name  # Keep the extracted name for reference
            st.session_state.ingredients = []

        conn.close()
    else:
        st.session_state.ingredients = []

    # Extract dish mass if present and not already set
    if st.session_state.dish_mass is None:
        dish_mass_match = re.search(r'(?:mass is |mass of the dish is |mass of this dish is )([\d.]+)\s*(grams|g)?', response, re.IGNORECASE)
        if dish_mass_match:
            st.session_state.dish_mass = int(float(dish_mass_match.group(1)))
        else:
            # If mass not found, retain existing value
            pass

    # We don't have ingredients_mass since we're getting ingredients from the database
    st.session_state.ingredients_mass = []

    return {
        'dish_name': st.session_state.dish_name,
        'dish_mass': st.session_state.dish_mass,
        'ingredients': st.session_state.ingredients,
        'ingredients_mass': st.session_state.ingredients_mass
    }


def home():
    st.markdown("<h1 style='text-align: center;'>HawkerScan</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with flask_app.test_request_context('/home'):
        user = db.session.get(User, st.session_state['user_id'])
        if user and user.is_authenticated:
            if not st.session_state['chat_history']:
                st.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": f"Welcome! Please upload an image to obtain and track nutrition. "
                               f"**Your PI API Key**: `{user.api_key}`"
                })

            # Sidebar for image uploader
            with st.sidebar:
                uploaded_file = st.file_uploader("Upload an image", type=ALLOWED_EXTENSIONS, key='file_uploader')
                if uploaded_file is not None and allowed_file(uploaded_file.name):
                    # Get file details
                    file_details = {"name": uploaded_file.name, "size": uploaded_file.size}
                    if st.session_state.get('last_uploaded_file_details') != file_details:
                        st.session_state['last_uploaded_file_details'] = file_details

                        # Save the file
                        file_path = save_file(uploaded_file)
                        if file_path:
                            st.session_state['uploaded_files'].append(uploaded_file.name)
                            st.session_state['selected_image'] = file_path
                            st.session_state['context'] = []  # Reset context with new image
                            # Display the image in the chat history
                            st.session_state['chat_history'].append({
                                "role": "user",
                                "content": None,
                                "image": file_path
                            })
                            # Reset the global variables when new image is uploaded
                            st.session_state.dish_name = None
                            st.session_state.dish_mass = None
                            st.session_state.ingredients = []
                            st.session_state.ingredients_mass = []

                            # Automatically process the uploaded image
                            process_uploaded_image()

            # Display chat history
            for i, message in enumerate(st.session_state.chat_history):
                if message["role"] == "user":
                    with st.chat_message(name="user", avatar="user"):
                        if message.get("image") is not None:
                            # Limit the displayed image size to 512 pixels
                            st.image(message["image"], caption='User uploaded image', width=512, use_column_width=False)
                        elif message.get("content") is not None:
                            st.markdown(message["content"])
                else:
                    with st.chat_message(name="assistant", avatar="assistant"):
                        st.markdown(message.get("content", ""))
                        if message.get("image") is not None:
                            st.image(message["image"], caption="Assistant's Image", width=512, use_column_width=False)

            # Clear uploaded files after processing
            st.session_state['uploaded_files'] = []


def process_api_image(image: Image.Image, mass: float, user_id: int):
    """
    Process an image from the API route, classify the dish, compute nutritional values,
    and insert a new record into NutritionalIntake for the given user_id.

    Returns:
      A dict containing:
        - classification (str)
        - dish_name (str or None)
        - nutritional_values (dict or str)
        - db_insertion (bool) : whether we successfully inserted a row
    """
    # Save image to a temporary file
    temp_path = "temp_api_image.jpg"
    image.save(temp_path)

    # Classify with AI model
    classification, _ = analyze_image(temp_path, "Identify the dish in this image.", context=[])

    # Extract dish name
    info = extract_info_from_response(classification)
    dish_name = info.get('dish_name')

    try:
        os.remove(temp_path)
    except Exception as e:
        print(f"Warning: Could not remove temp file: {e}")

    # If dish name is found, compute nutritional values
    if dish_name and mass is not None:
        nutritional_values = get_nutritional_values_local(dish_name, mass)
    else:
        nutritional_values = "Nutritional information not available"

    # Attempt DB insertion if there's a valid dish name and a dictionary of nutrients
    db_insertion = False
    if nutritional_values != "Not found":
        record_data = {
            "user_id": user_id,
            "dish_name": dish_name,
            "date_consumed": datetime.utcnow(),
        }
        # Use existing nutrient_field_mapping
        for nutrient, field_name in nutrient_field_mapping.items():
            record_data[field_name] = nutritional_values.get(nutrient, 0.0)

        intake_record = NutritionalIntake(**record_data)
        # Insert into DB
        with flask_app.test_request_context():
            db.session.add(intake_record)
            db.session.commit()
            db_insertion = True

    return {
        "classification": classification,
        "dish_name": dish_name,
        "nutritional_values": nutritional_values,
        "db_insertion": db_insertion
    }

def process_uploaded_image():
    image_path = st.session_state['selected_image']
    if os.path.exists(image_path):
        # Load the image
        image = Image.open(image_path).convert("RGB")

        max_size = (512, 512)
        image.thumbnail(max_size, Resampling.LANCZOS)

        imagefile = image_path
        user_message = "Identify the dish in this image."
        bot_response, new_context = analyze_image(imagefile, user_message, st.session_state['context'])
        st.session_state['context'] = new_context
        bot_response_lower = bot_response.lower()

        # Display the classification result as assistant's message
        classification_message = f"**Classification Result:** {bot_response}"
        st.session_state['chat_history'].append({
            "role": "assistant",
            "content": classification_message,
            "image": None
        })

        # Extract information from the response
        info = extract_info_from_response(bot_response)
        print(info)

        # ---------------------
        # Nutritional Information
        # ---------------------
        dish_name = st.session_state.dish_name
        dish_mass = 150 # to replace with pi acquired data (was this before: st.session_state.dish_mass)
        if dish_name and dish_mass:
            nutritional_values = get_nutritional_values_local(dish_name, dish_mass)

            if nutritional_values != "Not found":
                # Build a dictionary for the record data
                record_data = {
                    "user_id": st.session_state['user_id'],
                    "dish_name": dish_name,
                    "date_consumed": datetime.utcnow(),
                }

                # Use the mapping to add only the available nutrients (or set to 0.0 if missing)
                for nutrient, field_name in nutrient_field_mapping.items():
                    record_data[field_name] = nutritional_values.get(nutrient, 0.0)

                # Create and insert the record
                intake_record = NutritionalIntake(**record_data)
                with flask_app.test_request_context():
                    db.session.add(intake_record)
                    db.session.commit()

                # Optionally, format the nutritional info for display:
                nutritional_message = "### Nutritional Information:\n" + "\n".join(
                    f"- **{nutrient}:** {nutritional_values.get(nutrient, 0.0):.2f}"
                    for nutrient in nutrient_field_mapping.keys()
                )
                st.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": nutritional_message,
                    "image": None
                })

            else:
                st.session_state['chat_history'].append({
                    "role": "assistant",
                    "content": "Nutritional information not found for the dish.",
                    "image": None
                })
        else:
            st.session_state['chat_history'].append({
                "role": "assistant",
                "content": "Dish name or mass not available for nutritional information.",
                "image": None
            })

def nutritional_intake():
    st.markdown("<h2 style='text-align:center;'>Nutritional Intake</h2>", unsafe_allow_html=True)

    # 1. Top row: date inputs + grouping selectbox
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        start_date = st.date_input("Start Date", datetime.today() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.today())
    with col3:
        group_options = ["Daily", "Weekly", "Monthly"]
        group_by = st.selectbox("Group By", group_options)

    # Convert to full datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    user_id = st.session_state['user_id']
    intakes = NutritionalIntake.query.filter(
        NutritionalIntake.user_id == user_id,
        NutritionalIntake.date_consumed >= start_datetime,
        NutritionalIntake.date_consumed <= end_datetime
    ).all()

    if not intakes:
        st.warning("No records found in the selected date range.")
        return

    # 2. Convert records -> DataFrame (include 'id' for editing/deleting)
    data = []
    for record in intakes:
        data.append({
            "ID": record.id,  # for editing/deleting
            "Date Consumed": record.date_consumed,
            "Dish Name": record.dish_name,
            "Energy (kcal)": record.energy_kcal,
            "Protein (g)": record.protein_g,
            "Carbohydrate (g)": record.carbohydrate_g,
            "Sodium (mg)": record.sodium_mg,
            "Total Fat (g)": record.total_fat_g,
            "Saturated Fat (g)": record.saturated_fat_g,
            "Dietary Fibre (g)": record.dietary_fibre_g,
            "Cholesterol (mg)": record.cholesterol_mg,
            "Cholesterol (g)": record.cholesterol_g
        })
    df = pd.DataFrame(data)

    # 3. Two-column layout for the main display
    c1, c2 = st.columns([1, 1])

    # 3A. Left column: Show the raw table
    with c1:
        st.subheader("All Records in the Selected Range")
        st.dataframe(df.sort_values("Date Consumed", ascending=False), use_container_width=True)

    # 3B. Right column: Summaries
    with c2:
        st.subheader("Totals for Selected Date Range")
        total_energy = df["Energy (kcal)"].sum()
        total_protein = df["Protein (g)"].sum()
        total_carbs = df["Carbohydrate (g)"].sum()
        total_sodium = df["Sodium (mg)"].sum()
        total_fat = df["Total Fat (g)"].sum()
        total_sat_fat = df["Saturated Fat (g)"].sum()
        total_fibre = df["Dietary Fibre (g)"].sum()
        total_cholesterol_mg = df["Cholesterol (mg)"].sum()
        total_cholesterol_g = df["Cholesterol (g)"].sum()

        st.write(f"- **Energy (kcal):** {total_energy:.2f}")
        st.write(f"- **Protein (g):** {total_protein:.2f}")
        st.write(f"- **Carbohydrate (g):** {total_carbs:.2f}")
        st.write(f"- **Sodium (mg):** {total_sodium:.2f}")
        st.write(f"- **Total Fat (g):** {total_fat:.2f}")
        st.write(f"- **Saturated Fat (g):** {total_sat_fat:.2f}")
        st.write(f"- **Dietary Fibre (g):** {total_fibre:.2f}")
        st.write(f"- **Cholesterol (mg):** {total_cholesterol_mg:.2f}")
        st.write(f"- **Cholesterol (g):** {total_cholesterol_g:.2f}")

    # 4. Group the data by day, week, or month
    df["Date"] = pd.to_datetime(df["Date Consumed"]).dt.date  # daily grouping
    df["Year"] = pd.to_datetime(df["Date Consumed"]).dt.year
    df["Week"] = pd.to_datetime(df["Date Consumed"]).dt.isocalendar().week  # weekly grouping
    df["Month"] = pd.to_datetime(df["Date Consumed"]).dt.month  # monthly grouping

    if group_by == "Daily":
        grouped = df.groupby("Date").sum(numeric_only=True)
        grouping_label = "Date"
    elif group_by == "Weekly":
        grouped = df.groupby(["Year", "Week"]).sum(numeric_only=True)
        grouping_label = "Year-Week"
    else:  # "Monthly"
        grouped = df.groupby(["Year", "Month"]).sum(numeric_only=True)
        grouping_label = "Year-Month"

    st.subheader(f"{group_by} Totals")
    if grouped.empty:
        st.info(f"No data to display for {group_by} grouping.")
        return

    # Convert grouping index to a string for readability
    grouped = grouped.reset_index()
    if group_by == "Daily":
        pass
    elif group_by == "Weekly":
        grouped["Year-Week"] = grouped.apply(lambda row: f"{row['Year']}-W{row['Week']}", axis=1)
        grouped.drop(["Year", "Week"], axis=1, inplace=True)
    else:
        grouped["Year-Month"] = grouped.apply(lambda row: f"{row['Year']}-{int(row['Month']):02d}", axis=1)
        grouped.drop(["Year", "Month"], axis=1, inplace=True)

    st.dataframe(grouped, use_container_width=True)

    # 5. Nutrient selection for chart
    st.subheader("Custom Macro Chart")
    numeric_cols = [
        "Energy (kcal)",
        "Protein (g)",
        "Carbohydrate (g)",
        "Sodium (mg)",
        "Total Fat (g)",
        "Saturated Fat (g)",
        "Dietary Fibre (g)",
        "Cholesterol (mg)",
        "Cholesterol (g)"
    ]
    chosen_nutrients = st.multiselect("Choose nutrients to display", numeric_cols, default=["Energy (kcal)", "Protein (g)", "Carbohydrate (g)"])

    if group_by == "Daily":
        grouped_for_chart = grouped.set_index("Date")
    elif group_by == "Weekly":
        grouped_for_chart = grouped.set_index("Year-Week")
    else:
        grouped_for_chart = grouped.set_index("Year-Month")

    if chosen_nutrients:
        st.bar_chart(grouped_for_chart[chosen_nutrients])
    else:
        st.info("Select at least one nutrient to display in the chart.")

def nutritional_intake_aggrid():
    st.markdown("<h2 style='text-align:center;'>Manage Entries</h2>", unsafe_allow_html=True)

    # Date filtering
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", datetime.today() - timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", datetime.today())

    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    user_id = st.session_state['user_id']
    intakes = (
        NutritionalIntake.query
        .filter(NutritionalIntake.user_id == user_id)
        .filter(NutritionalIntake.date_consumed >= start_datetime)
        .filter(NutritionalIntake.date_consumed <= end_datetime)
        .all()
    )

    if not intakes:
        st.warning("No records found in the selected date range.")
        return

    # Convert to DataFrame
    data = []
    for rec in intakes:
        data.append({
            "ID": rec.id,
            "Date Consumed": rec.date_consumed,
            "Dish Name": rec.dish_name,
            "Energy (kcal)": rec.energy_kcal,
            "Protein (g)": rec.protein_g,
            "Carbohydrate (g)": rec.carbohydrate_g,
            "Sodium (mg)": rec.sodium_mg,
            "Total Fat (g)": rec.total_fat_g,
            "Saturated Fat (g)": rec.saturated_fat_g,
            "Dietary Fibre (g)": rec.dietary_fibre_g,
            "Cholesterol (mg)": rec.cholesterol_mg,
            "Cholesterol (g)": rec.cholesterol_g
        })
    df = pd.DataFrame(data)

    # Configure the AG Grid (no selection checkboxes)
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=True, paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_side_bar()  # filters in the sidebar
    gb.configure_default_column(editable=True)
    gb.configure_column("ID", editable=False)
    gb.configure_column("Date Consumed", editable=False)
    # Ensure cell edits are committed when user clicks away
    gb.configure_grid_options(stopEditingWhenCellsLoseFocus=True)

    grid_options = gb.build()

    # Show the grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True
    )

    # The updated DataFrame (after any in-line edits)
    updated_df = grid_response["data"]

    if st.button("Save Changes"):
        updated_df = pd.DataFrame(updated_df)

        # Compare updated_df with original df to detect changes
        for idx in updated_df.index:
            row = updated_df.loc[idx]
            original = df.loc[df["ID"] == row["ID"]].iloc[0]
            rec_id = row["ID"]
            rec = NutritionalIntake.query.get(rec_id)
            if not rec:
                continue

            changed = False
            # Check dish name
            if row["Dish Name"] != original["Dish Name"]:
                rec.dish_name = row["Dish Name"]
                changed = True

            # Check numeric columns
            numeric_cols = [
                "Energy (kcal)",
                "Protein (g)",
                "Carbohydrate (g)",
                "Sodium (mg)",
                "Total Fat (g)",
                "Saturated Fat (g)",
                "Dietary Fibre (g)",
                "Cholesterol (mg)",
                "Cholesterol (g)"
            ]
            for col in numeric_cols:
                if row[col] != original[col]:
                    setattr(rec, map_column(col), row[col])
                    changed = True

            if changed:
                db.session.add(rec)

        db.session.commit()
        st.success("Changes saved successfully!")
        st.experimental_rerun()

def map_column(col_name):
    """Helper function to map DataFrame column names to NutritionalIntake model fields."""
    mapping = {
        "Energy (kcal)": "energy_kcal",
        "Protein (g)": "protein_g",
        "Carbohydrate (g)": "carbohydrate_g",
        "Sodium (mg)": "sodium_mg",
        "Total Fat (g)": "total_fat_g",
        "Saturated Fat (g)": "saturated_fat_g",
        "Dietary Fibre (g)": "dietary_fibre_g",
        "Cholesterol (mg)": "cholesterol_mg",
        "Cholesterol (g)": "cholesterol_g"
    }
    return mapping.get(col_name)


@flask_app.route('/api/process-image', methods=['POST'])
def api_process_image_endpoint():
    # 1) Check if the request has an API key in the headers
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return jsonify({'error': 'No API key provided'}), 400

    # 2) Find the user with this API key
    user = User.query.filter_by(api_key=api_key).first()
    if not user:
        return jsonify({'error': 'Invalid API key'}), 403

    # 3) Ensure an image file is included
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    # 4) Parse the mass from the form data
    mass_str = request.form.get('mass')
    if not mass_str:
        return jsonify({'error': 'Mass value is required'}), 400

    try:
        mass = float(mass_str)
    except ValueError:
        return jsonify({'error': 'Mass must be a number'}), 400

    # 5) Open the image using PIL and convert to RGB
    try:
        image = Image.open(file).convert("RGB")
    except Exception as e:
        return jsonify({'error': f'Invalid image file: {str(e)}'}), 400

    # 6) Call a new version of process_api_image that stores the record
    result = process_api_image(image, mass, user.id)

    return jsonify(result)

def main():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None

    choice = sidebar_with_logo()

    if choice == "Login":
        if st.session_state['authenticated']:
            home()
        else:
            login()
    elif choice == "Register":
        register()
    elif choice == "Home":
        if st.session_state['authenticated']:
            home()
        else:
            st.error("You need to log in to access this page")
    elif choice == "Nutritional Intake":
        if st.session_state['authenticated']:
            nutritional_intake()
        else:
            st.error("You need to log in to access this page")
    elif choice == "Manage Entries":
        if st.session_state['authenticated']:
            nutritional_intake_aggrid()
        else:
            st.error("You need to log in to access this page")
    elif choice == "Logout":
        if st.session_state['authenticated']:
            st.session_state['authenticated'] = False
            st.session_state['user_id'] = None
            st.success("Logged out successfully!")
            login()
            st.rerun()

def run_api():
    flask_app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    # Start the Flask API in a separate daemon thread.
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    # Now start the Streamlit app.
    main()