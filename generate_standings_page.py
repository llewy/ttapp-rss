import os
import requests
from bs4 import BeautifulSoup

STANDINGS_URL = "https://www.nttb-ranglijsten.nl/stand_frame.php?pID=1022398"
OUTPUT_FILE = "docs/stand.html"

CSS_STYLE = """
  *, *::before, *::after {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, rgba(0, 91, 172, 0.9), rgba(0, 123, 255, 0.9)),
                url('https://smash70.com/wp-content/uploads/2023/09/R188174-bewerkt-scaled.jpg') no-repeat center center fixed;
    background-size: cover;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1.5rem 1rem;
    min-height: 100vh;
    font-size: 1rem;
  }

  header {
    text-align: center;
    font-size: 2rem;
    font-weight: 700;
    margin: 1rem 0 0.5rem;
    color: white;
  }

  header p {
    display: none;
  }

  .table-container {
    width: 100%;
    max-width: 1000px;
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 12px;
    overflow-x: auto;
    padding: 1rem;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1rem;
    color: white;
    min-width: 600px;
  }

  th, td {
    padding: 10px 14px;
    text-align: left;
  }

  th {
    font-weight: 600;
    font-size: 1.1rem;
    border-bottom: 2px solid white;
  }

  td {
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  }

  tr:last-child td {
    border-bottom: none;
  }

  tr:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }

  footer {
    margin-top: auto;
    text-align: center;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.6);
    padding: 10px;
  }

  @media (max-width: 768px) {
    body {
      padding: 1rem;
      font-size: 0.95rem;
    }

    header {
      font-size: 1.6rem;
      margin: 0.5rem 0;
    }

    .table-container {
      padding: 0.5rem;
    }

    table {
      font-size: 0.95rem;
    }

    th, td {
      padding: 8px 10px;
    }
  }
"""

def get_standings_from_nttb(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    standings = []

    rows = table.find_all("tr")[1:]  # Skip header
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 5:
            team = cols[1].text.strip()
            played = cols[2].text.strip()
            points = cols[4].text.strip()
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

    """      </tbody>
    </table>
  </div>
  <footer>Bron: nttb-ranglijsten.nl — Pagina ververst elke dag</footer>
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
