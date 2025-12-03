from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.backend.database import get_session
from app.backend.models import Incident, User
from app.backend.dependencies.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")


def to_naive_utc(dt: datetime | None) -> datetime | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def is_active_status(status: str) -> bool:
    if not status:
        return False
    s = status.lower()
    return "cerrado" not in s


def build_kpis(incidents: list[Incident]) -> dict:
    now = to_naive_utc(datetime.now(timezone.utc))
    open_inc = [i for i in incidents if is_active_status(i.status)]
    open_incidents = len(open_inc)
    critical_incidents = sum(1 for i in open_inc if i.severity == "Crítico")

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    alerts_today = 0
    for i in incidents:
        dt = to_naive_utc(i.detected_at) or now
        if dt >= today_start:
            alerts_today += 1

    closed = [i for i in incidents if not is_active_status(i.status)]
    mttr_hours = 0
    if closed:
        deltas = []
        for i in closed:
            d_start = to_naive_utc(i.detected_at)
            d_end = to_naive_utc(i.updated_at)
            if d_start and d_end and d_end > d_start:
                deltas.append(d_end - d_start)
        if deltas:
            avg_delta = sum((d for d in deltas), timedelta()) / len(deltas)
            mttr_hours = int(avg_delta.total_seconds() // 3600)

    return {
        "open_incidents": open_incidents,
        "critical_incidents": critical_incidents,
        "alerts_today": alerts_today,
        "mttr": f"{mttr_hours}h",
    }


def build_severity_distribution(incidents: list[Incident]) -> dict:
    active = [i for i in incidents if is_active_status(i.status)]
    buckets = {"Crítico": 0, "Alto": 0, "Medio": 0, "Bajo": 0}
    for i in active:
        if i.severity in buckets:
            buckets[i.severity] += 1
    total = sum(buckets.values())
    if total == 0:
        return {
            "total_active": 0,
            "critico": {"count": 0, "percent": 0},
            "alto": {"count": 0, "percent": 0},
            "medio": {"count": 0, "percent": 0},
            "bajo": {"count": 0, "percent": 0},
        }

    def pct(v: int) -> int:
        return int(round(v * 100 / total))

    return {
        "total_active": total,
        "critico": {"count": buckets["Crítico"], "percent": pct(buckets["Crítico"])},
        "alto": {"count": buckets["Alto"], "percent": pct(buckets["Alto"])},
        "medio": {"count": buckets["Medio"], "percent": pct(buckets["Medio"])},
        "bajo": {"count": buckets["Bajo"], "percent": pct(buckets["Bajo"])},
    }


def build_trend_data(incidents: list[Incident]) -> dict:
    now = to_naive_utc(datetime.now(timezone.utc))
    window_start = now - timedelta(hours=24)

    labels: list[str] = []
    total_values = [0] * 24
    critical_values = [0] * 24

    for idx in range(24):
        hour_dt = window_start + timedelta(hours=idx)
        labels.append(hour_dt.strftime("%Hh"))

    for inc in incidents:
        dt = to_naive_utc(inc.detected_at or inc.updated_at)
        if not dt:
            continue
        if dt < window_start or dt > now:
            continue
        idx = int((dt - window_start).total_seconds() // 3600)
        if 0 <= idx < 24:
            total_values[idx] += 1
            if inc.severity == "Crítico":
                critical_values[idx] += 1

    return {
        "trend_labels": labels,
        "trend_total": total_values,
        "trend_critical": critical_values,
    }


def build_type_data(incidents: list[Incident]) -> dict:
    by_source: dict[str, dict[str, int]] = {}
    for inc in incidents:
        src = inc.source or "Desconocido"
        if src not in by_source:
            by_source[src] = {"info": 0, "high": 0, "critical": 0}
        if inc.severity == "Crítico":
            by_source[src]["critical"] += 1
        elif inc.severity == "Alto":
            by_source[src]["high"] += 1
        else:
            by_source[src]["info"] += 1

    items = sorted(
        by_source.items(),
        key=lambda kv: (kv[1]["info"] + kv[1]["high"] + kv[1]["critical"]),
        reverse=True,
    )
    items = items[:12]

    labels = [k for k, _ in items]
    info = [v["info"] for _, v in items]
    high = [v["high"] for _, v in items]
    critical = [v["critical"] for _, v in items]

    return {
        "type_labels": labels,
        "type_info": info,
        "type_high": high,
        "type_critical": critical,
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    incidents = session.exec(select(Incident)).all()

    stats = build_kpis(incidents)
    severity_data = build_severity_distribution(incidents)
    trend = build_trend_data(incidents)
    type_data = build_type_data(incidents)

    def sort_key(i: Incident) -> datetime:
        return to_naive_utc(i.updated_at or i.detected_at or datetime.now(timezone.utc))

    recent_incidents = sorted(
        [i for i in incidents if is_active_status(i.status)],
        key=sort_key,
        reverse=True,
    )[:6]

    activity = sorted(
        incidents,
        key=sort_key,
        reverse=True,
    )[:5]

    charts = {**trend, **type_data}

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "recent_incidents": recent_incidents,
            "severity_data": severity_data,
            "activity": activity,
            "charts": charts,
        },
    )
