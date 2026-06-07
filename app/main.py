import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models import WeatherReading, get_db, init_db
from app import weather as wx

load_dotenv()

_PLACEHOLDER = "your_api_key_here"
_api_key = os.getenv("OPENWEATHER_API_KEY", "")
if not _api_key or _api_key == _PLACEHOLDER:
    raise SystemExit(
        "\n  ERROR: OPENWEATHER_API_KEY is not set.\n"
        "  Copy .env.example to .env and add your key from https://openweathermap.org/api\n"
    )

app = FastAPI(title="Weather Tracker")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.on_event("startup")
def startup():
    init_db()


# ── HTML routes ───────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, city: str = "", db: Session = Depends(get_db)):
    city = city or os.getenv("DEFAULT_CITY", "London")
    current = None
    forecast = None
    error = None

    try:
        raw_current = await wx.fetch_current(city)
        current = wx.parse_current(raw_current)

        raw_forecast = await wx.fetch_forecast(city)
        forecast = wx.parse_forecast(raw_forecast)
    except ValueError as e:
        error = str(e)
    except Exception as e:
        error = f"API error: {e}"

    history = (
        db.query(WeatherReading)
        .filter(WeatherReading.city.ilike(city))
        .order_by(WeatherReading.timestamp.desc())
        .limit(20)
        .all()
    )

    return templates.TemplateResponse("index.html", {
        "request": request,
        "city": city,
        "current": current,
        "forecast": forecast,
        "history": history,
        "error": error,
    })


@app.post("/log")
async def log_reading(city: str = Form(...), db: Session = Depends(get_db)):
    try:
        raw = await wx.fetch_current(city)
        parsed = wx.parse_current(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))

    reading = WeatherReading(**parsed)
    db.add(reading)
    db.commit()
    return RedirectResponse(url=f"/?city={city}", status_code=303)


# ── JSON API routes ───────────────────────────────────────────────────────────

@app.get("/api/current")
async def api_current(city: str = "London"):
    try:
        raw = await wx.fetch_current(city)
        return wx.parse_current(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/forecast")
async def api_forecast(city: str = "London"):
    try:
        raw = await wx.fetch_forecast(city)
        return wx.parse_forecast(raw)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/history")
def api_history(city: str = "London", limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(WeatherReading)
        .filter(WeatherReading.city.ilike(city))
        .order_by(WeatherReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "city": r.city,
            "timestamp": r.timestamp.isoformat(),
            "temp_c": r.temp_c,
            "humidity": r.humidity,
            "description": r.description,
            "wind_speed": r.wind_speed,
        }
        for r in rows
    ]
