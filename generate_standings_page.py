import os
import requests
from bs4 import BeautifulSoup

STANDINGS_URL = "https://www.nttb-ranglijsten.nl/stand_frame.php?pID=1023540"
OUTPUT_FILE = "docs/stand.html"

CSS_STYLE = """
  *, *::before, *::after {
    box-sizing: border-box;
  }

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
    background: linear-gradient(135deg, rgba(0, 91, 172, 0.9), rgba(0, 123, 255, 0.9)),
                url('https://smash70.com/wp-content/uploads/2023/09/R188174-bewerkt-scaled.jpg') no-repeat center center fixed;
    background-size: cover;
    color: white;
    padding: 2rem;
  }

  header {
    text-align: center;
    font-size: clamp(2.25rem, 3.6vw, 3.6rem);
    font-weight: 800;
    margin-bottom: 2rem;
    color: white;
  }

  .table-container {
    width: 100%;
    max-width: 900px;
    overflow-x: auto;
    background: rgba(0, 0, 0, 0.4);
    padding: 0.9rem;
    border-radius: 12px;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: clamp(1.08rem, 1.8vw, 1.8rem);
    color: white;
  }

  th, td {
    padding: 0.9rem;
    text-align: left;
  }

  th {
    font-weight: 700;
    font-size: 1.26em;
    border-bottom: 2px solid white;
  }

  td {
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  }

  tr:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  footer {
    margin-top: 2rem;
    text-align: center;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.7);
  }

  @media (max-width: 768px) {
    .table-container {
      padding: 0.45rem;
    }

    th, td {
      padding: 0.45rem;
    }
  }
"""


def get_standings_from_nttb(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    standings = []

    rows = table.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            team = cols[1].get_text(strip=True)
            played = cols[2].get_text(strip=True)
            points = cols[4].get_text(strip=True)
            standings.append((team, played, points))

    return standings

def generate_standings_html(standings):
    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="300">
  <title>Stand Eredivisie</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
  <header>Eredivisie Stand</header>
  <div class="table-container">
    <table>
      <thead>
        <tr><th>Team</th><th>Gespeeld</th><th>Punten</th></tr>
      </thead>
      <tbody>
"""

    for team, played, points in standings:
        row_style = ' style="font-weight:bold;"' if "Smash '70" in team else ""
        html += f"<tr{row_style}><td>{team}</td><td>{played}</td><td>{points}</td></tr>\n"

    html += """      </tbody>
    </table>
  </div>
  <footer>Bron: nttb-ranglijsten.nl</footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Standings page written to {OUTPUT_FILE}")

def main():
    print("Fetching Eredivisie standings...")
    standings = get_standings_from_nttb(STANDINGS_URL)
    if standings:
        generate_standings_html(standings)
    else:
        print("No standings data found.")

if __name__ == "__main__":
    main()
