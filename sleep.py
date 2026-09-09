import streamlit as st
from tracker import add_health_data


def run(user_id):
    st.title("😴 Sleep Tracker")

    sleep_hours = st.number_input(
        "Enter sleep hours",
        min_value=0.0,
        max_value=24.0,
        value=8.0,
        step=0.5
    )

    if st.button("Save Sleep Data"):
        add_health_data(user_id, 0, 0, sleep_hours, "Sleep")
        st.success("Sleep data saved successfully!")


if __name__ == "__main__":
    run()