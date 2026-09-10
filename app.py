from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from auth import create_users_table, login, signup
from analytics import get_data
from BMI_cal import bmi_category, calculate_bmi, health_tips, ideal_weight_range
from goals import add_goal, create_goals_table, delete_goal, get_goal_by_id, get_goals_for_user, update_goal
from tracker import add_health_data, create_health_table
from streaks import calculate_goal_streak, calculate_user_streak_summary
from calendar_api import create_calendar_table, get_calendar_month, get_day_summary

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app = FastAPI(
    title="Health Tracker API",
    description="FastAPI backend for the personal health tracking app.",
    version="1.0.0",
)

create_users_table()
create_health_table()
create_goals_table()
create_calendar_table()
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    confirmation: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    username: str
    password: str


class HealthLogRequest(BaseModel):
    user_id: int
    weight: float = 0.0
    water: int = 0
    sleep: float = 0.0
    exercise: str = ""
    recorded_at: str | None = None


class GoalCreateRequest(BaseModel):
    user_id: int
    goal_type: str
    title: str
    target_value: float
    unit: str
    frequency: str = "daily"
    start_date: str | None = None
    end_date: str | None = None
    is_active: bool = True


class GoalUpdateRequest(BaseModel):
    goal_type: str | None = None
    title: str | None = None
    target_value: float | None = None
    unit: str | None = None
    frequency: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_active: bool | None = None


@app.get("/")
def root() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/signup", status_code=status.HTTP_201_CREATED)
def signup_route(payload: SignupRequest) -> dict[str, Any]:
    if payload.password != payload.confirmation:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    try:
        user_id = signup(payload.username, payload.password)
    except (ValueError, Exception):
        raise HTTPException(
            status_code=400,
            detail="Choose a valid, available username and password.",
        ) from None

    return {"message": "Account created successfully.", "user_id": user_id}


@app.post("/login")
def login_route(payload: LoginRequest) -> dict[str, Any]:
    user = login(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"user": user}


@app.get("/dashboard/{user_id}")
def dashboard(user_id: int) -> list[dict[str, Any]]:
    df = get_data(user_id)
    return df.to_dict(orient="records")


@app.post("/health", status_code=status.HTTP_201_CREATED)
def log_health(payload: HealthLogRequest) -> dict[str, Any]:
    try:
        entry_id = add_health_data(
            payload.user_id,
            payload.weight,
            payload.water,
            payload.sleep,
            payload.exercise,
            payload.recorded_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"message": "Health data saved successfully.", "entry_id": entry_id}


@app.get("/bmi")
def bmi_endpoint(
    weight: float = Query(..., gt=0),
    height_cm: float = Query(..., gt=0),
) -> dict[str, Any]:
    bmi = calculate_bmi(weight, height_cm)
    category = bmi_category(bmi)
    min_weight, max_weight = ideal_weight_range(height_cm)
    return {
        "bmi": bmi,
        "category": category,
        "ideal_weight_range": {"min_kg": min_weight, "max_kg": max_weight},
        "health_tips": health_tips(category),
    }


@app.post("/goals", status_code=status.HTTP_201_CREATED)
def create_goal(payload: GoalCreateRequest) -> dict[str, Any]:
    try:
        goal_id = add_goal(
            payload.user_id,
            payload.goal_type,
            payload.title,
            payload.target_value,
            payload.unit,
            payload.frequency,
            payload.start_date,
            payload.end_date,
            payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"message": "Goal created successfully.", "goal_id": goal_id}


@app.get("/goals")
def get_goals(user_id: int = Query(...)) -> list[dict[str, Any]]:
    return get_goals_for_user(user_id, include_inactive=True)


@app.get("/goals/{goal_id}")
def get_goal(goal_id: int, user_id: int = Query(...)) -> dict[str, Any]:
    goal = get_goal_by_id(user_id, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found for this user.")
    return goal


@app.put("/goals/{goal_id}")
def update_goal_route(goal_id: int, payload: GoalUpdateRequest, user_id: int = Query(...)) -> dict[str, Any]:
    goal = get_goal_by_id(user_id, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found for this user.")
    try:
        updated_goal = update_goal(user_id, goal_id, **payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return updated_goal


@app.delete("/goals/{goal_id}")
def delete_goal_route(goal_id: int, user_id: int = Query(...)) -> dict[str, Any]:
    goal = get_goal_by_id(user_id, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found for this user.")
    deleted = delete_goal(user_id, goal_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Goal could not be deleted.")
    return {"message": "Goal deleted successfully."}


@app.get("/streaks")
def get_user_streaks(user_id: int = Query(...)) -> dict[str, Any]:
    return calculate_user_streak_summary(user_id)


@app.get("/streaks/{goal_id}")
def get_goal_streak(goal_id: int, user_id: int = Query(...)) -> dict[str, Any]:
    return calculate_goal_streak(user_id, goal_id)


@app.get("/calendar")
def get_month_calendar(year: int = Query(...), month: int = Query(...), user_id: int = Query(...)) -> dict[str, Any]:
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")
    return get_calendar_month(user_id, year, month)


@app.get("/calendar/{date}")
def get_single_day_summary(date: str, user_id: int = Query(...)) -> dict[str, Any]:
    try:
        return get_day_summary(user_id, date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
