# VulnBrief

Genereert automatisch een leesbare briefing ter voorbereiding op een
klantmeeting, op basis van (handmatig ingevoerde) security-bevindingen en
actiepunten uit de vorige meeting.

**Status: MVP met handmatige data-invoer.** Er is nog geen live koppeling
met Tenable of Microsoft Graph (agenda/OneNote) — die volgen in een latere
fase. Zie de sectie "Later" onderaan.

## Wat je ermee kunt

1. Een client/label aanmaken (bijv. "Broodfonds")
2. Bevindingen handmatig invoeren (naam, severity, hosts, leeftijd, CVSS/VPR)
3. De actiepunten uit de vorige meeting vastleggen
4. Op één knop drukken: Claude genereert een briefing (actiepunten-status,
   voortgang, top-bevindingen, aanbevolen gespreekspunten)
5. Alle eerdere briefings terugvinden in de geschiedenis

## Lokaal draaien (zonder Docker)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# open .env en vul ANTHROPIC_API_KEY in

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ga naar `http://localhost:8000`.

Zonder `ANTHROPIC_API_KEY` werkt de app nog steeds — je kunt clients,
bevindingen en notities invoeren — maar de gegenereerde "briefing" bevat
dan alleen een melding dat de key ontbreekt, in plaats van een echte
samenvatting.

## Draaien met Docker

```bash
cp .env.example .env
# vul ANTHROPIC_API_KEY in

docker compose up --build
```

Ga naar `http://localhost:8000`. Data blijft bewaard in `./data/app.db`
(gekoppeld via een volume), ook als de container herstart.

## Hosten (zodat je een publieke link hebt)

Simpelste opties die direct vanuit GitHub deployen:

- **Render.com** — koppel je GitHub-repo, kies "Web Service", Render
  detecteert de Dockerfile automatisch. Zet `ANTHROPIC_API_KEY` als
  environment variable in het Render-dashboard.
- **Railway.app** — vergelijkbaar, ook Docker-gebaseerd, ook environment
  variables via het dashboard.

Beide hebben een gratis/goedkope laag die ruim voldoende is voor dit
gebruik (een paar requests per dag).

**Let op:** er zit in deze fase geen inlogscherm op de webapp. Zolang er
alleen door jezelf ingevoerde testdata in staat, is dat geen probleem.
Zodra er gevoeligere/klantdata in komt, eerst basic auth (of iets steviger)
toevoegen voordat je het publiek toegankelijk maakt.

## Projectstructuur

```
vulnbrief/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── db.py             # SQLite schema + queries
│   ├── synthesizer.py     # Claude API aanroep
│   ├── templates/         # Jinja2 HTML-templates
│   └── static/style.css
├── data/                  # SQLite-database (niet in git)
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Later (bewust nog niet gebouwd)

- **Microsoft Graph-koppeling** (agenda + OneNote): automatisch detecteren
  wanneer een klantmeeting eraan komt en de vorige-meeting-notitie ophalen
  in plaats van handmatig invoeren. Vereist een Azure AD app-registratie
  (delegated permissions `Calendars.Read`, `Notes.Read`).
- **Live Tenable-koppeling**: bevindingen automatisch ophalen per
  label/container in plaats van handmatig invoeren.
- **Scheduler**: periodiek checken of er een meeting binnen het
  trigger-window valt, en dan automatisch genereren i.p.v. op knopdruk.
- **Live risico-verrijking**: voor de belangrijkste bevindingen laten
  Claude via web search checken of er sinds de laatste scan nieuwe
  ontwikkelingen zijn (actieve exploitatie, nieuwe CISA KEV-vermelding,
  public PoC).

Bouw deze als losse modules die de handmatige invoer aanvullen/vervangen,
zonder de database, UI of synthese-logica te hoeven herschrijven.
