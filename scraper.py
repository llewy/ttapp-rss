from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import time

CLUB_URL = "https://ttapp.nl/#/club/1603/p"
TOP_N = 5
SCREENSHOT_FILE = "debug_screenshot.png"

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
        cleaned_players = []
        for p in players:
            try:
                key = (p['name'], p['rating'])
                if key in seen:
                    continue
                seen.add(key)

                rating = float(p['rating'].replace(',', '.').replace('>', '').replace('<', ''))
                diff = float(p['diff'].replace(',', '.').replace('>', '').replace('<', '').replace('+', ''))
                cleaned_players.append((p['name'], rating, diff))
            except ValueError:
                print(f"Skipping: {p}")
                continue

        return cleaned_players

    except Exception as e:
        print(f"Error while scraping: {e}")
        driver.save_screenshot(SCREENSHOT_FILE)
        return []

    finally:
        driver.quit()

def generate_html(players):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="nl">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Grootste stijgers in rating</title>
      <style>
        *, *::before, *::after {{
          box-sizing: border-box;
        }}

        html, body {{
          margin: 0;
          padding: 0;
          width: 100%;
          height: 100%;
        }}

        body {{
          display: grid;
          place-items: center;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: linear-gradient(rgba(10, 30, 60, 0.85), rgba(10, 30, 60, 0.85)),
                      url('https://smash70.com/wp-content/uploads/2024/04/Kidspong-3.jpg') no-repeat center center fixed;
          background-size: cover;
          color: white;
          padding: 2rem;
        }}

        .title {{
          text-align: center;
          font-size: clamp(2.5rem, 4vw, 4rem);
          font-weight: 800;
          margin-bottom: 2rem;
          color: white;
        }}

        .table-container {{
          width: 100%;
          max-width: 1000px;
          overflow-x: auto;
          background: rgba(0, 0, 0, 0.4);
          padding: 1rem;
          border-radius: 12px;
        }}

        table {{
          width: 100%;
          border-collapse: collapse;
          font-size: clamp(1.2rem, 2vw, 2rem);
          color: white;
        }}

        th, td {{
          padding: 1rem;
          text-align: left;
        }}

        th {{
          font-weight: 700;
          font-size: 1.4em;
          border-bottom: 2px solid white;
        }}

        td {{
          border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        }}

        tr:hover {{
          background-color: rgba(255, 255, 255, 0.1);
        }}

        .improvement {{
          color: #00ff88;
          font-weight: bold;
        }}

        @media (max-width: 768px) {{
          .table-container {{
            padding: 0.5rem;
          }}

          th, td {{
            padding: 0.5rem;
          }}
        }}
      </style>
    </head>
    <body>

      <div class="title">Grootste stijgers in rating</div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Naam</th>
              <th>Huidige rating</th>
              <th>Verbetering</th>
            </tr>
          </thead>
          <tbody>
    """

    for name, rating, diff in players:
        html_content += f"""
            <tr>
              <td>{name}</td>
              <td>{rating:.2f}</td>
              <td class="improvement">+{diff:.2f}</td>
            </tr>
        """

    html_content += """
          </tbody>
        </table>
      </div>

    </body>
    </html>
    """

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    print("Fetching player data...")
    players = get_player_data()
    print(f"Found {len(players)} players")

    if not players:
        print("No players found! Check screenshot or website structure.")
        return

    top_improvers = sorted(players, key=lambda x: x[2], reverse=True)[:TOP_N]

    print(f"Top {TOP_N} improvers:")
    for name, rating, diff in top_improvers:
        print(f"- {name}: +{diff:.2f} (Now {rating:.2f})")

    print("Generating html...")
    generate_html(top_improvers)

if __name__ == "__main__":
    main()
