import streamlit as st
from analytics import get_data
import plotly.express as px


def run(user_id):
    st.title("📊 Dashboard")

    df = get_data(user_id)
    st.subheader("Health Records")
    st.dataframe(df)

    if not df.empty:
        fig1 = px.line(
            df,
            x="recorded_at",
            y="weight",
            title="Weight Progress"
        )
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.bar(
            df,
            x="recorded_at",
            y="water",
            title="Water Intake"
        )
        st.plotly_chart(fig2, use_container_width=True)


if __name__ == "__main__":
    run()