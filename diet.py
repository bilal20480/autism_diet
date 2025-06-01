import streamlit as st
import pandas as pd
import google.generativeai as genai
import base64
import os

# This must be the first Streamlit command
st.set_page_config(page_title="Autism Diet Planner", layout="wide")

# Configure Gemini API key
genai.configure(api_key="AIzaSyARK4nJZRCOLUgoS8w5temtyNtidK24H8E")

# Initialize Gemini model
model = genai.GenerativeModel("gemini-2.0-flash")
chat = model.start_chat(history=[])

def get_base64_image():
    # Try different image paths
    for ext in ["png", "jpg", "jpeg", "webp"]:
        image_path = f"bg.{ext}"  # Changed to match your filename
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
    return None

bg_img = get_base64_image()

# --- Custom CSS with Adjusted Background Opacity ---
custom_css = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.45), rgba(255, 255, 255, 0.85)),
                    url("data:image/png;base64,{bg_img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #2c3e50 !important;
    }}
    .stMarkdown p {{
        color: #333333 !important;
    }}
    </style>
"""

if bg_img:
    st.markdown(custom_css, unsafe_allow_html=True)
else:
    st.warning("Background image not found. Using plain background.")
    st.markdown("""
    <style>
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.95);
    }}
    </style>
    """, unsafe_allow_html=True)

# Function to get response from Gemini
def get_gemini_response(question):
    try:
        response = chat.send_message(question, stream=True)
        return "".join([chunk.text for chunk in response])
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

# Function to generate a sample meal plan (fallback or placeholder)
def generate_meal_plan(preferences, allergies, goals, activity_level, hydration, is_gfcf, diet_type):
    daily_plan = {
        "Meal": ["Breakfast", "Mid-Morning Snack", "Lunch", "Evening Snack", "Dinner"],
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": []
    }

    # Sample meal options (India-based, customizable)
    veg_options = {
        "Breakfast": ["Idli with chutney", "Oats porridge", "Poha", "Paratha with curd", "Dosa with sambar"],
        "Snack": ["Fruit salad", "Roasted makhana", "Peanut chikki", "Sprouts chaat"],
        "Lunch": ["Rice with dal and sabzi", "Roti with paneer curry", "Vegetable khichdi", "Curd rice"],
        "Evening Snack": ["Masala buttermilk", "Vegetable soup", "Handful of nuts"],
        "Dinner": ["Roti with sabzi", "Vegetable pulao", "Moong dal dosa with chutney", "Light dal khichdi"]
    }
    
    non_veg_options = {
        "Breakfast": ["Egg bhurji with toast", "Chicken sandwich", "Egg dosa"],
        "Snack": ["Boiled eggs", "Chicken soup"],
        "Lunch": ["Chicken curry with rice", "Fish curry with rice", "Egg fried rice"],
        "Evening Snack": ["Grilled chicken pieces", "Egg salad"],
        "Dinner": ["Fish fry with vegetables", "Chicken biryani", "Egg curry with roti"]
    }
    
    meal_options = veg_options if diet_type == "Vegetarian" else {**veg_options, **non_veg_options}

    # Populate the weekly plan with selected options
    for meal_time, options in meal_options.items():
        for day in daily_plan.keys():
            if day != "Meal":
                filtered_meals = [meal for meal in options if not any(allergy in meal for allergy in allergies)]
                daily_plan[day].append(filtered_meals[0] if filtered_meals else "Custom Option")

    return pd.DataFrame(daily_plan)

# App UI
st.title("Autism Diet Planner")
st.sidebar.header("User Inputs")

# Sidebar: User Inputs
age_range = st.sidebar.selectbox("Age Range", ["1-10", "11-20", "21-30", "31-40", "41-50", "51 and above"])
body_weight = st.sidebar.number_input("Body Weight (in kg)", min_value=10, max_value=200, value=50, step=1)
height = st.sidebar.number_input("Height (in cm)", min_value=50, max_value=250, value=150, step=1)
autism_severity = st.sidebar.selectbox("Autism Severity Level", ["Mild", "Moderate", "Severe"])
diet_type = st.sidebar.radio("Diet Type", ["Vegetarian", "Non-Vegetarian"])
preferences = st.sidebar.multiselect("Preferred Foods (Select all that apply)", ["Soft", "Crunchy", "Savory", "Sweet"])
allergies = st.sidebar.multiselect("Food Allergies or Intolerances", ["Gluten", "Dairy", "Nuts", "Soy", "Eggs"])
goals = st.sidebar.radio("Primary Goal", ["Improve Nutrition", "Expand Variety", "Support GI Health", "Weight Management"])
activity_level = st.sidebar.selectbox("Activity Level", ["Sedentary", "Moderately Active", "Very Active"])

# ✅ Changed hydration input from slider to number_input
hydration = st.sidebar.number_input("Daily Water Intake (in liters)", min_value=0.5, max_value=5.0, value=2.0, step=0.1)

is_gfcf = st.sidebar.checkbox("Gluten-Free, Casein-Free Diet")

# Generate Diet Plan Button
if st.sidebar.button("Generate Diet Plan"):
    # Construct the user input for the Gemini model
    user_input = f"""
    Create a personalized daily and weekly diet plan for an autistic individual in India.
    Consider the following:

    * Age Range: {age_range}
    * Body Weight: {body_weight} kg
    * Height: {height} cm
    * Autism Severity Level: {autism_severity}
    * Diet Type: {diet_type}
    * Preferences: {', '.join(preferences)}
    * Allergies or Intolerances: {', '.join(allergies)}
    * Primary Goal: {goals}
    * Activity Level: {activity_level}
    * Hydration Level: {hydration} liters/day
    * Gluten-Free, Casein-Free Diet: {is_gfcf}

    Requirements:
    - Provide Indian-specific food options.
    - Address sensory preferences (e.g., texture, taste).
    - Present the plan in a weekly tabular format.
    - Include {diet_type} options as specified.
    """

    # Get the response from Gemini
    response = get_gemini_response(user_input)

    # Display the diet plan
    if response:
        st.subheader("Generated Diet Plan:")
        st.write(response)

        # Provide download option
        st.download_button("Download Diet Plan", response, "diet_plan.txt")
    else:
        # Fallback to the sample diet plan if API fails
        st.subheader("Sample Diet Plan:")
        sample_plan = generate_meal_plan(preferences, allergies, goals, activity_level, hydration, is_gfcf, diet_type)
        st.dataframe(sample_plan)
        st.download_button("Download Sample Plan as CSV", sample_plan.to_csv(index=False), "sample_diet_plan.csv", "text/csv")

# Sidebar: Additional Tips
st.sidebar.subheader("Tips for Success")
st.sidebar.write("""
- Stick to routine meal times.
- Gradually introduce new foods.
- Ensure meals are visually appealing.
- Involve the individual in meal prep when possible.
""")