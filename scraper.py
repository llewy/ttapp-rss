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

        # Extract player data using JavaScript
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

        # Clean and convert data
        seen = set()
        cleaned_players = []
        for p in players:
            try:
                key = (p['name'], p['rating'])  # Avoid duplicates
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
        /* Reset and base */
        *, *::before, *::after {{
          box-sizing: border-box;
        }}
        body {{
          margin: 0;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: #f4f7f8;
          color: #222;
          line-height: 1.6;
          padding: 20px;
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
        }}
        header {{
          max-width: 800px;
          width: 100%;
          text-align: center;
          margin-bottom: 2rem;
        }}
        header h1 {{
          font-weight: 700;
          font-size: 2.5rem;
          margin-bottom: 0.2rem;
          color: #0066cc;
        }}
        header p {{
          color: #555;
          font-size: 1.1rem;
          margin-top: 0;
        }}
        table {{
          border-collapse: collapse;
          width: 100%;
          max-width: 800px;
          background: white;
          box-shadow: 0 2px 5px rgb(0 0 0 / 0.1);
          border-radius: 8px;
          overflow: hidden;
        }}
        th, td {{
          text-align: left;
          padding: 12px 15px;
          border-bottom: 1px solid #ddd;
        }}
        th {{
          background-color: #007bff;
          color: white;
          font-weight: 600;
        }}
        tr:hover {{
          background-color: #f1faff;
        }}
        td.improvement {{
          font-weight: 700;
          color: #28a745;
        }}
        footer {{
          margin-top: auto;
          padding: 15px;
          font-size: 0.9rem;
          color: #666;
          text-align: center;
          width: 100%;
          max-width: 800px;
        }}
        @media (max-width: 600px) {{
          body {{
            padding: 10px;
          }}
          header h1 {{
            font-size: 1.8rem;
          }}
          table {{
            font-size: 0.9rem;
          }}
        }}
      </style>
    </head>
    <body>
      <header>
        <h1>Grootste stijgers in rating</h1>
        <p>Dagelijkse lijst van spelers met de hoogste stijging in rating</p>
      </header>

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

    </body>
    </html>
    
""".format(year=datetime.now().year)


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
