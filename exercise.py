import streamlit as st
from tracker import add_health_data


def run(user_id):
    st.title("🏋️ Exercise Tracker")

    exercise = st.text_input("Enter exercise name")
    weight = st.number_input(
        "Enter your weight (kg)",
        min_value=1.0,
        value=70.0
    )
    height = st.number_input(
        "Enter your height (meters)",
        min_value=0.1,
        value=1.7,
        step=0.01
    )

    if height > 0:
        bmi = weight / (height ** 2)
        st.subheader(f"Your BMI: {bmi:.2f}")

    if st.button("Save Exercise Data"):
        add_health_data(user_id, weight, 0, 0, exercise or "Exercise")
        st.success("Exercise data saved successfully!")


if __name__ == "__main__":
    run()