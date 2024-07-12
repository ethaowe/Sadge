from openai import OpenAI
import streamlit as st
import requests

# Base URL for CarQuery API
base_url = 'https://www.carqueryapi.com/api/0.3/'

client = OpenAI(api_key="sk-sea-service-account-QpjdkS5UuD4xgu5RXdzDT3BlbkFJej0KTpg1FTXVjXizosNr")

# Title and description
st.title("🚗 AI Car Recommender")
st.write(
    "Welcome to the AI Car Recommender! This tool uses OpenAI's GPT-3.5-turbo model to recommend car models based on your preferences. "
    "To get started, please provide some information about what you're looking for in a car."
)

# Initialize session state
if "state" not in st.session_state:
    st.session_state.state = "start"
if "car_type" not in st.session_state:
    st.session_state.car_type = ""
if "budget" not in st.session_state:
    st.session_state.budget = ""
if "fuel_efficiency" not in st.session_state:
    st.session_state.fuel_efficiency = ""
if "preferences" not in st.session_state:
    st.session_state.preferences = ""
if "responses" not in st.session_state:
    st.session_state.responses = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define the dialog tree with polite messages
dialog_tree = {
    "start": {
        "message": "Let's find the perfect car for you! What type of car are you interested in? (e.g., sedan, SUV, truck)",
        "next_state": "get_car_type"
    },
    "get_car_type": {
        "message": "Great choice! What is your budget for the car?",
        "next_state": "get_budget"
    },
    "get_budget": {
        "message": "Got it. How important is fuel efficiency to you? (e.g., very important, moderately important, not important)",
        "next_state": "get_fuel_efficiency"
    },
    "get_fuel_efficiency": {
        "message": "Understood. Do you have any specific preferences or features you're looking for in a car?",
        "next_state": "get_preferences"
    },
    "get_preferences": {
        "message": "Thank you! Based on the information provided, here are some car recommendations for you:\n\n"
                   "Car Type: {car_type}\n"
                   "Budget: {budget}\n"
                   "Fuel Efficiency Preference: {fuel_efficiency}\n"
                   "Preferences: {preferences}\n\n"
                   "Recommended Car Models:\n",
        "next_state": None
    }
}

# Function to handle dialog
def handle_dialog(state, user_input=None):
    if state == "start":
        return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
    elif state == "get_car_type":
        car_type = extract_entity(user_input, "car_type")
        if car_type:
            st.session_state.car_type = car_type
            return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. Could you please tell me what type of car you're interested in?", state, False
    elif state == "get_budget":
        budget = extract_entity(user_input, "budget")
        if budget:
            st.session_state.budget = budget
            return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. What is your budget for the car?", state, False
    elif state == "get_fuel_efficiency":
        fuel_efficiency = extract_entity(user_input, "fuel_efficiency")
        if fuel_efficiency:
            st.session_state.fuel_efficiency = fuel_efficiency
            return dialog_tree[state]["message"], dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. How important is fuel efficiency to you?", state, False
    elif state == "get_preferences":
        preferences = extract_entity(user_input, "preferences")
        if preferences:
            st.session_state.preferences = preferences
            return dialog_tree[state]["message"].format(
                car_type=st.session_state.car_type,
                budget=st.session_state.budget,
                fuel_efficiency=st.session_state.fuel_efficiency,
                preferences=st.session_state.preferences
            ), dialog_tree[state]["next_state"], True
        else:
            return "I didn't catch that. Do you have any specific preferences or features you're looking for in a car?", state, False

# Function to recommend car models using OpenAI
def recommend_cars():
    prompt = f"Recommend car models that match the following criteria:\n\n" \
             f"Car Type: {st.session_state.car_type}\n" \
             f"Budget: {st.session_state.budget}\n" \
             f"Fuel Efficiency Preference: {st.session_state.fuel_efficiency}\n" \
            f"Preferences: {st.session_state.preferences}\n\n" \
             f"Please provide a list of recommended car models."

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}],
    max_tokens=500)
    return response.choices[0].message.content

# Function to extract specific entity from the text and validate it
def extract_entity(text, entity_type):
    prompt = f"Extract the {entity_type} from the following text:\n\n{text}\n\nProvide only the {entity_type}."
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[{"role": "system", "content": prompt}],
    max_tokens=50)
    extracted_entity = response.choices[0].message.content.strip()
    if extracted_entity and validate_entity(extracted_entity, entity_type):
        return extracted_entity
    return None

# Function to validate the extracted entity
def validate_entity(entity, entity_type):
    if entity_type == "car_type":
        valid_types = ["sedan", "truck", "hatchback", "coupe", "SUV"]
        return any(car_type in entity.lower() for car_type in valid_types)
    if entity_type == "budget":
        return entity.isdigit()  # Budget should be a valid number
    if entity_type == "fuel_efficiency":
       valid_efficiencies = ["very important", "moderately important", "not important"]
       return any(efficiency in entity.lower() for efficiency in valid_efficiencies)
    if entity_type == "preferences":
        return len(entity) > 0  # Preferences should not be empty
    return False

# Display the existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Function to handle user responses
def handle_user_response(prompt):
    if st.session_state.state:
        user_input = prompt
        st.session_state.messages.append({"role": "user", "content": user_input})
        message, next_state, valid_input = handle_dialog(st.session_state.state, user_input)
        st.session_state.messages.append({"role": "assistant", "content": message})
        if valid_input:
            st.session_state.state = next_state
        st.experimental_rerun()

# Display final car recommendations if in the final state
if st.session_state.state == "get_preferences":
    car_recommendations = recommend_cars()
    st.session_state.messages.append({"role": "assistant", "content": car_recommendations})
    st.session_state.state = None

# Handle user input at the bottom of the page
if prompt := st.chat_input("Your response:"):
    handle_user_response(prompt)
