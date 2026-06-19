import os
import json
import requests

API_URL = "https://www.nttb-ranglijsten.nl/dwf/v2/?get_club"
PLAYERS_URL = "https://www.nttb-ranglijsten.nl/dwf/v2/?get_players"
HEADERS = {
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "null",
    "Sec-Fetch-Mode": "cors",
    "Accept-Encoding": "gzip, deflate, br",
    "Host": "www.nttb-ranglijsten.nl",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Accept-Language": "nl-NL,nl;q=0.9",
    "Accept": "*/*"
}
POST_DATA = {
    "user": "0",
    "comp": "2026_1",
    "club": "1603",
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IjAifQ.iEZheZoeSXMJe20oTxlelrXPCxD-lM2nPtSJAlWwrZA",
    "username": "0"
}
OUTPUT_FILE = "docs/team_players.html"

CSS_STYLE = """
  *, *::before, *::after {
    box-sizing: border-box;
  }

  html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    min-height: 100%;
  }

  body {
    display: flex;
    flex-direction: column;
    align-items: center;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, rgba(0, 91, 172, 0.9), rgba(0, 123, 255, 0.9)),
                url('https://smash70.com/wp-content/uploads/2023/09/R188174-bewerkt-scaled.jpg') no-repeat center center fixed;
    background-size: cover;
    color: white;
    padding: 2rem 1rem;
  }

  header {
    text-align: center;
    font-size: clamp(1.8rem, 3vw, 3rem);
    font-weight: 800;
    margin-bottom: 0.5rem;
    color: white;
  }

  .subtitle {
    text-align: center;
    font-size: 1rem;
    margin-bottom: 2rem;
    color: rgba(255, 255, 255, 0.8);
  }

  .group-section {
    width: 100%;
    max-width: 900px;
    margin-bottom: 2.5rem;
  }

  .group-title {
    font-size: clamp(1.1rem, 1.6vw, 1.5rem);
    font-weight: 700;
    margin-bottom: 0.3rem;
    color: white;
    padding-left: 0.2rem;
  }

  .team-name {
    font-size: clamp(0.95rem, 1.3vw, 1.2rem);
    font-weight: 600;
    margin-bottom: 0.4rem;
    margin-top: 1rem;
    color: rgba(255, 255, 255, 0.9);
    padding-left: 0.2rem;
  }

  .table-container {
    width: 100%;
    overflow-x: auto;
    background: rgba(0, 0, 0, 0.4);
    padding: 0.6rem;
    border-radius: 12px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: clamp(0.85rem, 1.2vw, 1.1rem);
    color: white;
  }

  th, td {
    padding: 0.4rem 0.6rem;
    text-align: left;
  }

  th {
    font-weight: 700;
    font-size: 1.05em;
    border-bottom: 2px solid white;
  }

  td {
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  }

  tbody tr:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  .rating {
    text-align: right;
    font-family: 'Courier New', monospace;
  }

  footer {
    margin-top: 1rem;
    text-align: center;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
  }

  footer a {
    color: #b0d0ff;
  }

  @media (max-width: 768px) {
    body { padding: 1rem 0.3rem; }
    .table-container { padding: 0.3rem; }
    th, td { padding: 0.25rem 0.3rem; }
    .group-section { margin-bottom: 1.5rem; }
  }
"""


def get_club_teams():
    response = requests.post(API_URL, headers=HEADERS, data=POST_DATA)
    response.raise_for_status()
    data = response.json()
    teams_json_str = data.get("teams", "[]")
    teams = json.loads(teams_json_str)

    seen_tid = set()
    club_teams = []
    for team in teams:
        tid = team.get("tID")
        if tid and tid not in seen_tid:
            seen_tid.add(tid)
            club_teams.append({
                "tID": tid,
                "pID": team.get("pID"),
                "group_name": team.get("group_name", "Onbekend"),
                "aname": team.get("aname", ""),
                "teamnr": team.get("teamnr", ""),
                "klasse": team.get("klasse", ""),
            })
    return club_teams


def fetch_players(tid):
    data = {
        "home": tid,
        "guest": "0",
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IjAifQ.iEZheZoeSXMJe20oTxlelrXPCxD-lM2nPtSJAlWwrZA",
        "username": "0"
    }
    response = requests.post(PLAYERS_URL, headers=HEADERS, data=data)
    response.raise_for_status()
    result = response.json()
    info_str = result.get("info", "[]")
    info = json.loads(info_str)
    players = []
    if info and isinstance(info, list) and len(info) > 0:
        for p in info[0]:
            players.append({
                "name": p.get("name", ""),
                "rating": p.get("rat", ""),
                "bnr": p.get("bnr", ""),
            })
    return players


def generate_html(team_groups):
    sections_html = ""
    for group_name, teams in team_groups:
        teams_html = ""
        for tm in teams:
            players = [p for p in tm["players"] if p["name"].strip().lower() != "anoniem"]
            if not players:
                continue
            rows_html = ""
            for p in players:
                name = p["name"].replace("&", "&amp;").replace("<", "&lt;")
                rows_html += f"            <tr><td>{name}</td><td class=\"rating\">{p['rating']}</td></tr>\n"

            team_label = tm["team_label"]
            teams_html += f"""      <div class="team-name">{team_label}</div>
      <div class="table-container">
        <table>
          <thead>
            <tr><th>Speler</th><th class=\"rating\">Rating</th></tr>
          </thead>
          <tbody>
{rows_html}          </tbody>
        </table>
      </div>
"""

        if teams_html:
            sections_html += f"""  <div class="group-section">
    <div class="group-title">{group_name}</div>
{teams_html}  </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="300">
  <title>Teamleden Smash '70</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
  <header>Teamleden Smash '70</header>
  <div class="subtitle">Spelers per team en competitie</div>
{sections_html}  <footer>
    Dagelijks ververst. Bron: <a href="https://nttb-ranglijsten.nl" target="_blank" rel="noopener noreferrer">nttb-ranglijsten.nl</a>
  </footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Team players page written to {OUTPUT_FILE}")


def main():
    print("Fetching club teams...")
    club_teams = get_club_teams()
    if not club_teams:
        print("No teams found.")
        return

    seen = {}
    for tm in club_teams:
        tid = tm["tID"]
        print(f"Fetching players for tID {tid} ({tm['aname']} {tm['teamnr']})...")
        players = fetch_players(tid)
        label = f"{tm['aname']} {tm['teamnr']}".strip()
        key = (tm["group_name"], label)
        if key not in seen:
            seen[key] = {
                "group_name": tm["group_name"],
                "team_label": label,
                "players": players,
            }

    groups = {}
    for item in seen.values():
        groups.setdefault(item["group_name"], []).append(item)

    sorted_groups = sorted(groups.items())
    if sorted_groups:
        generate_html(sorted_groups)
    else:
        print("No team player data found.")


if __name__ == "__main__":
    main()
