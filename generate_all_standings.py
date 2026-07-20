import os
import json
import requests
from bs4 import BeautifulSoup

API_URL = "https://www.nttb-ranglijsten.nl/dwf/v2/?get_club"
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
    "comp": "2026_2",
    "club": "1603",
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IjAifQ.iEZheZoeSXMJe20oTxlelrXPCxD-lM2nPtSJAlWwrZA",
    "username": "0"
}

BASE_URL = "https://www.nttb-ranglijsten.nl/stand_frame.php?pID="
OUTPUT_FILE = "docs/all_standings.html"

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
    margin-bottom: 0.6rem;
    color: white;
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
    font-size: clamp(0.9rem, 1.3vw, 1.3rem);
    color: white;
  }

  th, td {
    padding: 0.5rem 0.7rem;
    text-align: left;
  }

  th {
    font-weight: 700;
    font-size: 1.1em;
    border-bottom: 2px solid white;
  }

  td {
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  }

  tbody tr:hover {
    background-color: rgba(255, 255, 255, 0.1);
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
    th, td { padding: 0.35rem 0.4rem; }
    .group-section { margin-bottom: 1.5rem; }
  }
"""


def get_pids_and_groups_from_api():
    response = requests.post(API_URL, headers=HEADERS, data=POST_DATA)
    response.raise_for_status()
    data = response.json()
    teams_json_str = data.get("teams", "[]")
    teams = json.loads(teams_json_str)
    seen = set()
    pid_group_list = []
    for team in teams:
        pid = team.get("pID")
        group = team.get("group_name", "Onbekende Groep")
        if pid and pid not in seen:
            seen.add(pid)
            pid_group_list.append((pid, group))
    return pid_group_list


def fetch_full_standings(pID):
    url = BASE_URL + pID
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    rows_data = []
    smash_team = None
    if not table:
        return rows_data, smash_team
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            team = cols[1].get_text(strip=True)
            played = cols[2].get_text(strip=True)
            points = cols[4].get_text(strip=True)
            rows_data.append((team, played, points))
            if "Smash '70" in team and smash_team is None:
                smash_team = team
    return rows_data, smash_team


def generate_html(all_data):
    sections_html = ""
    for group_name, smash_team, standings in all_data:
        subtitle = f" — {smash_team}" if smash_team else ""
        rows_html = ""
        for team, played, points in standings:
            bold = ' style="font-weight:bold;"' if "Smash '70" in team else ""
            rows_html += f"          <tr{bold}><td>{team}</td><td>{played}</td><td>{points}</td></tr>\n"

        sections_html += f"""    <div class="group-section">
      <div class="group-title">{group_name}{subtitle}</div>
      <div class="table-container">
        <table>
          <thead>
            <tr><th>Team</th><th>Gespeeld</th><th>Punten</th></tr>
          </thead>
          <tbody>
{rows_html}          </tbody>
        </table>
      </div>
    </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="300">
  <title>Alle Standen Smash '70</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
  <header>Alle competitiestand Smash '70</header>
  <div class="subtitle">Volledige standen per competitie</div>
{sections_html}  <footer>
    Dagelijks ververst. Bron: <a href="https://nttb-ranglijsten.nl" target="_blank" rel="noopener noreferrer">nttb-ranglijsten.nl</a>
  </footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"All standings written to {OUTPUT_FILE}")


def smash_played(standings, smash_team):
    for team, played, _ in standings:
        if team == smash_team:
            return int(played)
    return 0


def main():
    print("Fetching pIDs and groups from club API...")
    pid_group_list = get_pids_and_groups_from_api()
    if not pid_group_list:
        print("No pIDs found from the API.")
        return

    all_data = []
    for pID, group_name in pid_group_list:
        print(f"Fetching full standings for pID {pID} ({group_name})...")
        standings, smash_team = fetch_full_standings(pID)
        if standings:
            all_data.append((group_name, smash_team, standings))
        else:
            print(f"  No standings data for {group_name}.")

    seen = {}
    for group_name, smash_team, standings in all_data:
        key = (group_name, smash_team)
        if key in seen:
            existing_played = smash_played(seen[key][2], smash_team)
            new_played = smash_played(standings, smash_team)
            if new_played > existing_played:
                seen[key] = (group_name, smash_team, standings)
        else:
            seen[key] = (group_name, smash_team, standings)

    deduped = list(seen.values())

    if deduped:
        generate_html(deduped)
    else:
        print("No standings data found.")


if __name__ == "__main__":
    main()
