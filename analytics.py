import pandas as pd
from tracker import create_health_table, get_connection

create_health_table()


def get_data(user_id):
    query = "SELECT * FROM health WHERE user_id = ? ORDER BY recorded_at"
    with get_connection() as connection:
        return pd.read_sql_query(query, connection, params=(user_id,))


def calculate_bmi(weight, height):
    if height > 0:
        return weight / (height ** 2)

    return 0