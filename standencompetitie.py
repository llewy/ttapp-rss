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
    "comp": "2025_2",
    "club": "1603",
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IjAifQ.iEZheZoeSXMJe20oTxlelrXPCxD-lM2nPtSJAlWwrZA",
    "username": "0"
}

BASE_URL = "https://www.nttb-ranglijsten.nl/stand_frame.php?pID="
OUTPUT_FILE = "docs/combined_standings.html"

CSS_STYLE = """
*, *::before, *::after { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
}
body {
  display: grid;
  place-items: center;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(rgba(10,30,60,0.85), rgba(10,30,60,0.85)), url('https://smash70.com/wp-content/uploads/2024/04/Kidspong-3.jpg') no-repeat center center fixed;
  background-size: cover;
  color: white;
  padding: 0.5rem;
}
.title {
  text-align: center;
  font-size: 1.25rem;
  font-weight: 800;
  margin-bottom: 0.5rem;
  color: white;
}
.table-wrapper {
  width: 100%;
  max-width: 550px;
  overflow-x: auto;
  background: rgba(0,0,0,0.4);
  padding: 0.4rem;
  border-radius: 10px;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
  color: white;
  min-width: 450px;
}
th, td {
  padding: 0.18rem 0.35rem;
  text-align: left;
}
th {
  font-weight: 700;
  font-size: 0.85em;
  border-bottom: 2px solid #FFF;
  background: rgba(10,30,60,0.75);
}
td {
  border-bottom: 1px solid rgba(255,255,255,0.12);
}
tr:nth-child(even) { background-color: rgba(255,255,255,0.07); }
tr:nth-child(odd)  { background-color: rgba(0,0,0,0.07); }
tr:hover { background-color: rgba(255,255,255,0.16); }
.footer-note {
  margin-top: 0.6rem;
  font-size: 0.6rem;
  color: rgba(255,255,255,0.7);
  text-align: center;
  font-style: italic;
}
.footer-note a {
  color: #b0d0ff;
  text-decoration: underline;
}
@media (max-width: 500px) {
  .title { font-size: 1rem; }
  .table-wrapper { max-width: 100vw; min-width: 0; }
  th, td { padding: 0.11rem 0.11rem; font-size: 0.54rem; }
}
"""


def get_pids_and_groups_from_api():
    response = requests.post(API_URL, headers=HEADERS, data=POST_DATA)
    response.raise_for_status()
    data = response.json()
    teams_json_str = data.get("teams", "[]")
    teams = json.loads(teams_json_str)
    pid_group_list = []
    for team in teams:
        pid = team.get("pID")
        group = team.get("group_name", "Onbekende Groep")
        if pid:
            pid_group_list.append((pid, group))
    return pid_group_list

def fetch_standings_and_group(pID):
    url = BASE_URL + pID
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    results = []
    if not table:
        return results
    position = 0
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            position += 1
            team = cols[1].get_text(strip=True)
            if "Smash '70" in team:
                results.append((position, team))
    return results

def format_position(pos):
    return f"{pos}e"

def generate_combined_html(results):
    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Samengevoegde Standen Smash '70</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
  <div class="title">Competitiestand per team</div>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr><th>Groep</th><th>Team</th><th>Positie</th></tr>
      </thead>
      <tbody>
"""

    for groep, team, positie in results:
        html += f"<tr><td>{groep}</td><td>{team}</td><td>{positie}</td></tr>\n"

    html += """      </tbody>
    </table>
  </div>
  <div class="footer-note">
    Dagelijks ververst. Bron: <a href="https://nttb-ranglijsten.nl" target="_blank" rel="noopener noreferrer">nttb-ranglijsten.nl</a>
  </div>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Combined standings written to {OUTPUT_FILE}")

def main():
    print("Fetching pIDs and groups from club API...")
    pid_group_list = get_pids_and_groups_from_api()
    if not pid_group_list:
        print("No pIDs found from the API.")
        return
    results = []
    for pID, groep in pid_group_list:
        print(f"Fetching standings for pID {pID} ({groep})...")
        smash_teams = fetch_standings_and_group(pID)
        for pos, team in smash_teams:
            results.append((groep, team, format_position(pos)))
    if results:
        generate_combined_html(results)
    else:
        print("No Smash '70 team standings found.")

if __name__ == "__main__":
    main()
