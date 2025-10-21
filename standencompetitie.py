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
body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: #003b7d;
  color: white;
  padding: 2rem;
}
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 1.2rem;
}
th, td {
  padding: 0.8rem;
  border: 1px solid white;
  text-align: left;
}
th {
  background-color: #0059a3;
}
tr:nth-child(even) {
  background-color: rgba(255, 255, 255, 0.1);
}
"""

def get_pids_and_groups_from_api():
    response = requests.post(API_URL, headers=HEADERS, data=POST_DATA)
    response.raise_for_status()
    data = response.json()

    # Extract 'teams' JSON string and parse it
    teams_json_str = data.get("teams", "[]")
    teams = json.loads(teams_json_str)

    # Extract pID and group_name for each team entry
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

    # Extract group name from page, fallback to unknown
    group_name = "Onbekende Groep"
    b_tag = soup.find("b")
    if b_tag and b_tag.get_text(strip=True):
        group_name = b_tag.get_text(strip=True)
    else:
        for tag_name in ["h1", "h2", "h3", "p"]:
            tag = soup.find(tag_name)
            if tag and tag.get_text(strip=True):
                group_name = tag.get_text(strip=True)
                break

    table = soup.find("table")
    results = []
    if not table:
        return group_name, results

    position = 0
    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            position += 1
            team = cols[1].get_text(strip=True)
            if "Smash '70" in team:
                results.append((position, team))
    return group_name, results

def format_position(pos):
    return f"{pos}e"  # Dutch ordinal suffix

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
  <h1>Samengevoegde Standen van Smash '70 Teams</h1>
  <table>
    <thead>
      <tr><th>Groep</th><th>Team</th><th>Positie</th></tr>
    </thead>
    <tbody>
"""

    for groep, team, positie in results:
        html += f"      <tr><td>{groep}</td><td>{team}</td><td>{positie}</td></tr>\n"

    html += """    </tbody>
  </table>
  <footer>Bron: nttb-ranglijsten.nl</footer>
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
    print(f"Found pIDs and groups: {pid_group_list}")

    consolidated_results = []
    for pID, groep_from_api in pid_group_list:
        print(f"Fetching standings for pID {pID} with expected group '{groep_from_api}' ...")
        groep_page, smash_teams = fetch_standings_and_group(pID)
        # Use group from API for consistency, but can fallback or compare with page group
        groep = groep_from_api or groep_page
        for pos, team in smash_teams:
            consolidated_results.append((groep, team, format_position(pos)))

    if consolidated_results:
        generate_combined_html(consolidated_results)
    else:
        print("No Smash '70 team standings found.")

if __name__ == "__main__":
    main()
