from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time

CLUB_URL = "https://ttapp.nl/#/club/1603/p"
OUTPUT_FILE = "docs/all_ratings.html"
SCREENSHOT_FILE = "debug_screenshot_all.png"

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
    background: linear-gradient(rgba(10, 30, 60, 0.85), rgba(10, 30, 60, 0.85)),
                url('https://smash70.com/wp-content/uploads/2024/04/Kidspong-3.jpg') no-repeat center center fixed;
    background-size: cover;
    color: white;
    padding: 1.5rem;
  }

  .title {
    text-align: center;
    font-size: clamp(2rem, 3vh, 3rem);
    font-weight: 800;
    margin-bottom: 1rem;
  }

  .table-container {
    width: 100%;
    max-width: 1000px;
    height: 80vh;
    background: rgba(0, 0, 0, 0.4);
    padding: 0.8rem;
    border-radius: 12px;
    display: flex;
    align-items: center;
  }

  table {
    width: 100%;
    height: 100%;
    border-collapse: collapse;
    font-size: clamp(0.8rem, 1.4vh, 1.2rem);
    color: white;
  }

  th, td {
    padding: 0.4rem 0.5rem;
    text-align: left;
  }

  th {
    font-weight: 700;
    font-size: 1.05em;
    border-bottom: 2px solid white;
    position: sticky;
    top: 0;
    background: rgba(10, 30, 60, 0.95);
  }

  td {
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  }

  tbody tr:hover {
    background-color: rgba(255, 255, 255, 0.08);
  }

  .improvement {
    color: #00ff88;
    font-weight: bold;
  }

  .decline {
    color: #ff6b6b;
    font-weight: bold;
  }

  .footer-note {
    margin-top: 1rem;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    font-style: italic;
  }

  .footer-note a {
    color: rgba(200, 220, 255, 0.9);
    text-decoration: underline;
  }

  @media (max-width: 768px) {
    .title { font-size: 1.5rem; }
    th, td { padding: 0.25rem 0.3rem; }
  }
"""


def get_player_data():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')
    driver = webdriver.Chrome(options=options)
    players = []

    try:
        driver.get(CLUB_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        time.sleep(5)
        driver.save_screenshot(SCREENSHOT_FILE)
        print(f"Screenshot saved to {SCREENSHOT_FILE}")

        players = driver.execute_script("""
            return Array.from(document.querySelectorAll('table tbody tr')).map(row => {
                const cols = row.querySelectorAll('td');
                if (cols.length < 2) return null;

                const nameBlock = cols[0].innerText.trim().split('\\n');
                const name = nameBlock.length >= 2 ? nameBlock[1] : nameBlock[0];

                const ratingBlock = cols[1].innerText.trim().split('\\n');
                const rating = ratingBlock[0];
                const diff = ratingBlock.length > 1 ? ratingBlock[1] : '0';

                return { name, rating, diff };
            }).filter(Boolean);
        """)

        seen = set()
        cleaned = []
        for p in players:
            try:
                key = (p['name'], p['rating'])
                if key in seen:
                    continue
                seen.add(key)
                rating = float(p['rating'].replace(',', '.').replace('>', '').replace('<', ''))
                diff = float(p['diff'].replace(',', '.').replace('>', '').replace('<', '').replace('+', ''))
                cleaned.append((p['name'], rating, diff))
            except ValueError:
                print(f"Skipping: {p}")
                continue
        return cleaned

    except Exception as e:
        print(f"Error while scraping: {e}")
        driver.save_screenshot(SCREENSHOT_FILE)
        return []

    finally:
        driver.quit()


def generate_html(players):
    rows_html = ""
    for name, rating, diff in players:
        cls = "improvement" if diff >= 0 else "decline"
        sign = "+" if diff >= 0 else ""
        rows_html += f"""
            <tr>
              <td>{name}</td>
              <td>{rating:.0f}</td>
              <td class="{cls}">{sign}{diff:.0f}</td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Alle ratings Smash '70</title>
  <style>{CSS_STYLE}</style>
</head>
<body>
  <div class="title">Alle ratingwijzigingen Smash '70</div>
  <div class="table-container">
    <table>
      <thead>
        <tr>
          <th>Naam</th>
          <th>Huidige rating</th>
          <th>Verschil</th>
        </tr>
      </thead>
      <tbody>{rows_html}
      </tbody>
    </table>
  </div>
  <div class="footer-note">
    Alle spelers gesorteerd op dalende rating. Bron:
    <a href="https://nttb-ranglijsten.nl" target="_blank">nttb-ranglijsten.nl</a>
  </div>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"All ratings written to {OUTPUT_FILE}")


def main():
    print("Fetching player data...")
    players = get_player_data()
    print(f"Found {len(players)} players")

    if not players:
        print("No players found!")
        return

    all_players = sorted(players, key=lambda x: x[1], reverse=True)

    print("Generating html...")
    generate_html(all_players)


if __name__ == "__main__":
    main()
