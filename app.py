from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from auth import create_users_table, login, signup
from analytics import get_data
from BMI_cal import bmi_category, calculate_bmi, health_tips, ideal_weight_range
from tracker import add_health_data, create_health_table

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

app = FastAPI(
    title="Health Tracker API",
    description="FastAPI backend for the personal health tracking app.",
    version="1.0.0",
)

create_users_table()
create_health_table()
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
