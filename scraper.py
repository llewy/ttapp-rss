from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from feedgen.feed import FeedGenerator
from datetime import datetime
import time

CLUB_URL = "https://ttapp.nl/#/club/1603/p"
TOP_N = 5
RSS_FILE = "top_improvers.xml"

def get_player_data():
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.get(CLUB_URL)
    
    time.sleep(5)  # Wait for JS to load the data

    players = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 4:
            continue

        name = cols[0].text.strip()
        rating_str = cols[2].text.strip().replace(',', '.')
        diff_str = cols[3].text.strip().replace(',', '.')

        try:
            rating = float(rating_str)
            diff = float(diff_str)
            players.append((name, rating, diff))
        except ValueError:
            continue  # Skip rows with bad data

    driver.quit()
    return players

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
        fe.pubDate(datetime.utcnow())

    fg.rss_file(RSS_FILE)

def main():
    print("Fetching player data...")
    players = get_player_data()

    top_improvers = sorted(players, key=lambda x: x[2], reverse=True)[:TOP_N]

    print(f"Top {TOP_N} improvers:")
    for name, rating, diff in top_improvers:
        print(f"- {name}: +{diff:.2f} (Now {rating:.2f})")

    print("Generating RSS...")
    generate_rss(top_improvers)
    print(f"RSS feed written to {RSS_FILE}")

if __name__ == "__main__":
    main()
