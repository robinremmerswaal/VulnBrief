"""
Synthese-stap: zet findings + vorige-meeting-actiepunten om in een
leesbare Markdown-briefing via de Claude API.
"""
import os

from anthropic import Anthropic

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """\
Je bent een assistent van een vulnerability management-specialist bij een \
cybersecuritybedrijf. Je stelt een korte, praktische briefing op ter \
voorbereiding van een klantmeeting. Doelgroep: de specialist zelf, vlak \
voor de meeting -- dus bondig, concreet, geen marketing-taal.

Structuur van je antwoord (Markdown):
1. Overzicht van actiepunten uit de vorige meeting, met status (opgelost /
   nog open / geaccepteerd risico) -- baseer dit op de status die is
   meegegeven, en of de bijbehorende bevinding nog voorkomt in de huidige
   openstaande findings.
2. Een korte alinea "Voortgang sinds vorige meeting".
3. Tabel met de belangrijkste openstaande bevindingen (naam, severity,
   leeftijd in dagen, betrokken hosts).
4. 3-5 concrete aanbevolen gespreekspunten, puntsgewijs, gericht op wat het
   langst open staat en wat nieuw/urgent is.

Wees feitelijk en to-the-point. Verzin geen aannames die niet uit de data
blijken.
"""


def _findings_to_text(findings: list[dict]) -> str:
    lines = []
    for f in findings:
        status = "OPGELOST" if f["is_resolved"] else "OPEN"
        cve_str = f", CVEs: {f['cves']}" if f.get("cves") else ""
        lines.append(
            f"- [{status}] {f['finding_name']} | severity={f['severity']} | "
            f"leeftijd={f['age_days']} dagen | hosts={f['hosts']} | "
            f"cvss={f.get('cvss_score')} | vpr={f.get('vpr_score')}{cve_str}"
        )
    return "\n".join(lines) if lines else "(geen bevindingen ingevoerd)"


def _previous_note_to_text(note: dict | None) -> str:
    if not note:
        return "(geen vorige meeting-notitie geregistreerd)"
    lines = [f"Vorige meeting: {note['meeting_date']}"]
    if note.get("raw_text"):
        lines.append(f"Notities: {note['raw_text']}")
    lines.append("Actiepunten:")
    for item in note.get("action_items", []):
        lines.append(f"- [{item['status']}] {item['text']}")
    return "\n".join(lines)


def generate_briefing(client_name: str, findings: list[dict], previous_note: dict | None) -> str:
    """Retourneert de briefing als Markdown-tekst."""
    open_findings = [f for f in findings if not f["is_resolved"]]
    total = len(open_findings)
    by_sev = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for f in open_findings:
        if f["severity"] in by_sev:
            by_sev[f["severity"]] += 1

    user_prompt = f"""\
Klant: {client_name}

Huidige samenvatting: {total} open bevindingen ({by_sev}).

Volledige lijst bevindingen (open en opgelost):
{_findings_to_text(findings)}

Vorige meeting-notitie en actiepunten:
{_previous_note_to_text(previous_note)}

Stel de briefing op volgens de structuur die je is meegegeven.
"""

    if not ANTHROPIC_API_KEY:
        return (
            "# Briefing kon niet gegenereerd worden\n\n"
            "Er is geen `ANTHROPIC_API_KEY` ingesteld in je `.env`-bestand. "
            "Vul deze in en probeer het opnieuw.\n\n"
            "## Ruwe data die verstuurd zou zijn\n\n```\n" + user_prompt + "\n```"
        )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
