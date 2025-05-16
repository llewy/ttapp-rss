from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone
import os
import time

CLUB_URL = "https://ttapp.nl/#/club/1603/p"
TOP_N = 5
RSS_FILE = "docs/top_improvers.xml"
SCREENSHOT_FILE = "debug_screenshot.png"

def get_player_data():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)

    players = []

    try:
        driver.get(CLUB_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        time.sleep(5)  # Allow JS to render

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

def generate_rss(improvements):
    fg = FeedGenerator()
    fg.title("Top Rating Improvers - TTapp Club 1603")
    fg.link(href=CLUB_URL)
    fg.description("Top rating improvements for TTapp Club 1603")
    fg.language("en")

    for name, rating, diff in improvements:
        fe = fg.add_entry()
        fe.title(f"{name}: +{diff:.2f} points")
        fe.link(href=CLUB_URL)
        fe.description(f"{name} improved by {diff:.2f} points (Current Rating: {rating:.2f})")
        fe.pubDate(datetime.now(timezone.utc))

    os.makedirs(os.path.dirname(RSS_FILE), exist_ok=True)
    fg.rss_file(RSS_FILE)

def generate_html(players):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Grootste stijgers in rating</title>
      <style>
        *, *::before, *::after {{
          box-sizing: border-box;
        }}

        body {{
          margin: 0;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: linear-gradient(135deg, rgba(0, 91, 172, 0.9), rgba(0, 123, 255, 0.9)),
                      url('https://smash70.com/wp-content/uploads/2024/04/Kidspong-3.jpg') no-repeat center center fixed;
          background-size: cover;
          color: white;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 120px 40px;
          min-height: 100vh;
          font-size: 1.8rem;
        }}

        table {{
          width: 100%;
          max-width: 1200px;
          border-collapse: collapse;
          font-size: 2rem;
          color: white;
        }}

        th {{
          text-align: left;
          padding: 20px 30px;
          font-weight: 600;
          font-size: 2.2rem;
          border-bottom: 2px solid white;
        }}

        td {{
          padding: 18px 30px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.3);
        }}

        tr:last-child td {{
          border-bottom: none;
        }}

        tr:hover {{
          background-color: rgba(255, 255, 255, 0.1);
        }}

        .title {{
          text-align: center;
          font-size: 6rem;
          font-weight: 700;
          margin-top: 4rem;
          color: white;
        }}

        @media (max-width: 768px) {{
          body {{
            padding: 40px;
            font-size: 1.2rem;
          }}

          .title {{
            font-size: 2.5rem;
          }}

          table {{
            font-size: 1.4rem;
          }}

          th, td {{
            padding: 15px 20px;
          }}
        }}
      </style>
    </head>
    <body>

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

      <div class="title">Grootste stijgers in rating</div>

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

    print("Generating RSS...")
    generate_rss(top_improvers)
    generate_html(top_improvers)
    print(f"RSS feed written to {RSS_FILE}")

if __name__ == "__main__":
    main()
