"""
VulnBrief -- FastAPI hoofdapplicatie.

Start lokaal met:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Of via Docker: zie README.md
"""
import os
import markdown as md_lib
from datetime import date

from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import db
from app.synthesizer import generate_briefing

app = FastAPI(title="VulnBrief")

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.on_event("startup")
def on_startup():
    db.init_db()


# --- Home / clients overview ---

@app.get("/")
def home():
    return RedirectResponse(url="/clients")


@app.get("/clients")
def clients_list(request: Request):
    clients = db.list_clients()
    # voeg per client een kort aantal open findings toe voor het overzicht
    for c in clients:
        open_findings = db.list_findings(c["id"], only_open=True)
        c["open_count"] = len(open_findings)
    return templates.TemplateResponse("clients_list.html", {"request": request, "clients": clients})


@app.post("/clients")
def create_client(name: str = Form(...), notes: str = Form("")):
    db.create_client(name.strip(), notes.strip())
    return RedirectResponse(url="/clients", status_code=303)


# --- Client detail: findings + previous notes ---

@app.get("/clients/{client_id}")
def client_detail(request: Request, client_id: int):
    client = db.get_client(client_id)
    findings = db.list_findings(client_id)
    previous_notes = db.list_previous_notes(client_id)
    return templates.TemplateResponse(
        "client_detail.html",
        {
            "request": request,
            "client": client,
            "findings": findings,
            "previous_notes": previous_notes,
            "today": date.today().isoformat(),
        },
    )


@app.post("/clients/{client_id}/findings")
def add_finding(
    client_id: int,
    finding_name: str = Form(...),
    severity: str = Form(...),
    hosts: str = Form(""),
    age_days: int = Form(0),
    cvss_score: str = Form(""),
    vpr_score: str = Form(""),
    solution: str = Form(""),
    cves: str = Form(""),
):
    db.add_finding(
        client_id=client_id,
        finding_name=finding_name.strip(),
        severity=severity,
        hosts=hosts.strip(),
        age_days=age_days,
        cvss_score=float(cvss_score) if cvss_score.strip() else None,
        vpr_score=float(vpr_score) if vpr_score.strip() else None,
        solution=solution.strip(),
        cves=cves.strip(),
    )
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)


@app.post("/findings/{finding_id}/toggle-resolved")
def toggle_finding_resolved(finding_id: int, client_id: int = Form(...), resolved: str = Form("0")):
    db.set_finding_resolved(finding_id, resolved == "1")
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)


@app.post("/findings/{finding_id}/delete")
def delete_finding_route(finding_id: int, client_id: int = Form(...)):
    db.delete_finding(finding_id)
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)


@app.post("/clients/{client_id}/previous-notes")
def add_previous_note(
    client_id: int,
    meeting_date: str = Form(...),
    raw_text: str = Form(""),
    action_items_text: str = Form(""),
):
    note_id = db.add_previous_note(client_id, meeting_date, raw_text.strip())
    # Elke regel in action_items_text wordt een los actiepunt, status "open" default.
    # Format per regel: "tekst" of "tekst | status" (status: open/resolved/accepted)
    for line in action_items_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            text, status = line.split("|", 1)
            text, status = text.strip(), status.strip().lower()
            if status not in ("open", "resolved", "accepted"):
                status = "open"
        else:
            text, status = line, "open"
        db.add_action_item(note_id, text, status)
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)


@app.post("/action-items/{item_id}/status")
def update_action_item_status(item_id: int, client_id: int = Form(...), status: str = Form(...)):
    db.set_action_item_status(item_id, status)
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)


# --- Generate + view briefings ---

@app.post("/clients/{client_id}/generate")
def generate(client_id: int):
    client = db.get_client(client_id)
    findings = db.list_findings(client_id)
    previous_note = db.get_latest_previous_note(client_id)

    content_md = generate_briefing(client["name"], findings, previous_note)

    briefing_id = db.save_briefing(
        client_id=client_id,
        content_markdown=content_md,
        input_snapshot={"findings": findings, "previous_note": previous_note},
    )
    return RedirectResponse(url=f"/briefings/{briefing_id}", status_code=303)


@app.get("/briefings")
def briefings_list(request: Request):
    briefings = db.list_briefings()
    return templates.TemplateResponse("briefings_list.html", {"request": request, "briefings": briefings})


@app.get("/briefings/{briefing_id}")
def briefing_detail(request: Request, briefing_id: int):
    briefing = db.get_briefing(briefing_id)
    html_content = md_lib.markdown(briefing["content_markdown"], extensions=["tables"]) if briefing else ""
    return templates.TemplateResponse(
        "briefing_detail.html",
        {"request": request, "briefing": briefing, "html_content": html_content},
    )
