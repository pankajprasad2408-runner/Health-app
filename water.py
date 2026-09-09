import streamlit as st
from tracker import add_health_data


def run(user_id):
    st.title("💧 Water Tracker")

    water = st.number_input(
        "Water intake (glasses)",
        min_value=0,
        step=1,
        value=0
    )

    if st.button("Save Water Data"):
        add_health_data(user_id, 0, water, 0, "Water Intake")
        st.success("Water intake saved successfully!")


if __name__ == "__main__":
    run()