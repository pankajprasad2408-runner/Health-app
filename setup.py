from auth import create_users_table
from tracker import create_health_table

create_users_table()
create_health_table()

print("Database setup complete!")