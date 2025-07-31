# ==================================================================================================
# Script_1.py
#
# DESCRIPTION:
# This script functions as a web scraper for the sofifa.com website.
# Its purpose is to collect squad data from a football team, then navigate to
# each player's profile page to gather more detailed information.
# The collected data will be saved in three different formats: Excel (.xlsx),
# Pipe-delimited text (.txt), and JSON (.json).
#
# USAGE:
# python Script_1.py --url [TEAM_URL_ON_SOFIFA] --output [OUTPUT_FOLDER_NAME]
#
# EXAMPLE:
# python Script_1.py --url "https://sofifa.com/team/11/real-madrid" --output "SCRAPING_RESULTS"
# ==================================================================================================


# --------------------------------------------------------------------------------------------------
# SECTION 1: LIBRARY IMPORTS
# Importing all necessary libraries to run the script.
# --------------------------------------------------------------------------------------------------
import os
import re
import csv
import time
import json
import random
import argparse
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import sys
import io


# --------------------------------------------------------------------------------------------------
# SECTION 2: GLOBAL CONFIGURATION
# Variables and settings that apply throughout the script.
# --------------------------------------------------------------------------------------------------

# Fix encoding issues for console output on some operating systems (especially Windows).
# Ensures all characters, including non-ASCII, can be printed to the console
# without causing encoding errors.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# List of diverse User-Agents to disguise HTTP requests.
# Each time the driver is initialized, a User-Agent is randomly selected from this list.
# This helps reduce the chance of detection and blocking by the target website.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0"
]


# --------------------------------------------------------------------------------------------------
# SECTION 3: MAIN FUNCTIONS
# Collection of functions that form the core logic of this web scraper.
# --------------------------------------------------------------------------------------------------

def setup_driver():
    """
    Initializes and configures a WebDriver (Chrome) object using `undetected_chromedriver`.
    This function adds various arguments to `ChromeOptions` to:
    - Disable sandbox, SHM usage, and GPU (important for headless/server environments).
    - Disable extensions and info bars.
    - Start the browser in maximized mode.
    - Run the browser in headless mode (without a visible GUI).
    - Set a random User-Agent from the `USER_AGENTS` list for each driver session.

    Returns:
        uc.Chrome: Configured Selenium driver object ready for
                   interacting with web pages.
    """
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
    driver = uc.Chrome(options=options)
    return driver

def scroll_to_bottom(driver):
    """
    Scrolls the web page from top to bottom gradually until reaching the very bottom.
    This function is important for websites that use "lazy loading" where new content
    is only loaded when the user scrolls down the page.

    Args:
        driver: Active Selenium driver object.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 3))
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def safe_get(driver, url, retries=3):
    """
    Attempts to navigate to a URL with a retry mechanism if errors occur,
    such as SSL/TLS errors or connection issues. The function will attempt to open the URL
    up to `retries` times.

    Args:
        driver: Selenium driver object.
        url (str): URL to open.
        retries (int): Maximum number of attempts to open the URL.

    Returns:
        bool: `True` if the URL is successfully opened on any attempt, `False` if all
              attempts fail.
    """
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            print(f"⚠️ Retry {i+1}/{retries} for {url} ({e})", flush=True)
            time.sleep(2)
    return False

def scrape_player_profile(player_url, driver, debug_dir="DEBUG", max_retries=3):
    """
    Collects detailed data from a player's profile page on sofifa.com.
    This function navigates to the player's profile URL and extracts various information
    (height, weight, preferred foot, skill moves, weak foot, contract, value, wage, nationality)
    from both standard HTML elements and hidden JSON-LD data.
    Also saves the page HTML for debugging.

    Args:
        player_url (str): Full URL of the player's profile page.
        driver: Selenium driver object used to access the page.
        debug_dir (str): Path to the folder for saving debug HTML files for each player.
        max_retries (int): Maximum number of attempts to fetch data from a single player URL.

    Returns:
        tuple: Tuple containing 9 extracted player data elements:
               (height, weight, foot, skill_moves, weak_foot, contract_end, value, wage, nationality).
               If all attempts fail, returns a tuple with "-" for each element.
    """
    for attempt in range(max_retries):
        try:
            if not safe_get(driver, player_url):
                continue

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(random.uniform(2, 4))
            soup = BeautifulSoup(driver.page_source, "html.parser")

            if soup.find("title") and "Page not found" in soup.title.text:
                print(f"⚠️ Page not found (404) for {player_url}. Skipping.", flush=True)
                return ["-"] * 9

            player_id_match = re.search(r'/player/(\d+)', player_url)
            player_id = player_id_match.group(1) if player_id_match else "unknown"
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, f"debug_{player_id}.html"), "w", encoding="utf-8") as f:
                f.write(soup.prettify())

            height = weight = foot = skill_moves = weak_foot = contract_valid_until = nationality = contract_duration = value = wage = "-"

            script = soup.find("script", type="application/ld+json")
            if script:
                try:
                    data = json.loads(script.string)
                    height = data.get("height", "-")
                    weight = data.get("weight", "-")
                    nationality = data.get("nationality", "-")
                except json.JSONDecodeError:
                    pass

            for p in soup.find_all("p"):
                label = p.find("label")
                if not label:
                    continue

                text = label.text.strip()
                value_field = p.get_text(strip=True).replace(text, "").strip()

                if text == "Preferred foot":
                    foot = value_field
                elif text == "Skill moves":
                    skill_moves = value_field
                elif text == "Weak foot":
                    weak_foot = value_field
                elif text == "Contract valid until":
                    contract_valid_until = value_field

            for div in soup.find_all("div", class_="info"):
                label = div.find("label")
                if label:
                    if "Value" in label.text:
                        value = div.get_text(strip=True).replace("Value", "").strip()
                    elif "Wage" in label.text:
                        wage = div.get_text(strip=True).replace("Wage", "").strip()

            span = soup.find("span", class_="pos")
            if span and span.next_sibling:
                match = re.search(r"\d{4}\s*~\s*\d{4}", str(span.next_sibling))
                if match:
                    contract_duration = match.group()

            contract_end = contract_duration if contract_duration != "-" else contract_valid_until

            return height, weight, foot, skill_moves, weak_foot, contract_end, value, wage, nationality

        except Exception as e:
            print(f"⏳ Attempt {attempt+1}/{max_retries} failed for {player_url} ({e})", flush=True)
            time.sleep(random.uniform(2, 4))

    return ["-"] * 9

def export_all_formats(dataframe, output_path):
    """
    Exports a Pandas DataFrame into three different file formats:
    - Excel file (.xlsx)
    - Text file (.txt) with pipe delimiter (|)
    - JSON file (.json)

    Args:
        dataframe (pd.DataFrame): DataFrame containing the data to export.
        output_path (str): Base path for the output file (filename without extension).
                           Extensions will be added automatically by this function.
    """
    base = os.path.splitext(output_path)[0]
    print(f"\n💾 Saving files to: {base}.[xlsx, txt, json]", flush=True)

    dataframe.to_excel(base + ".xlsx", index=False)
    dataframe.to_csv(base + ".txt", sep="|", index=False, encoding="utf-8-sig")
    dataframe.to_json(base + ".json", orient="records", force_ascii=False, indent=2)

# --------------------------------------------------------------------------------------------------
# SECTION 4: MAIN EXECUTION BLOCK - BAGIAN INI DIPERBAIKI
# --------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    # --- Step 1: Command Line Argument Parsing ---
    parser = argparse.ArgumentParser(description="Football player data scraper from sofifa.com")
    parser.add_argument("--url", required=True, help="Team page URL on sofifa.com")
    parser.add_argument("--output", default="OUTPUT", help="Folder name to save results")
    args = parser.parse_args()

    # --- Step 2: Initialization and Preparation ---
    team_url = args.url
    output_dir = args.output
    debug_dir = os.path.join(output_dir, "DEBUG")

    # Inisialisasi driver HANYA SATU KALI di awal
    driver = setup_driver()
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(debug_dir, exist_ok=True)

    print(f"\n🔗 Starting scraping from: {team_url}", flush=True)

    all_players_data = [] # List untuk menyimpan semua data pemain
    start_time = time.time()
    
    try:
        # --- Step 3: Fetching Player List from Team Page ---
        if not safe_get(driver, team_url):
            raise Exception("Gagal memuat halaman tim setelah beberapa kali percobaan.")

        scroll_to_bottom(driver)
        time.sleep(3)

        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.select("table tbody tr")

        print(f"🔗 Number of player links found: {len(rows)}", flush=True)

        # --- Step 4: Iterating and Scraping Data per Player ---
        for idx, row in enumerate(rows, 1):
            try:
                cols = row.find_all("td")
                if len(cols) < 8:
                    print(f"⚠️ Skipping row {idx} due to incompleteness.", flush=True)
                    continue

                name_tag = cols[1].find("a")
                if not name_tag:
                    continue
                
                name = name_tag.text.strip()
                player_href = name_tag['href']
                player_id_match = re.findall(r'/player/(\d+)', player_href)
                player_id = player_id_match[0] if player_id_match else "-"
                age = cols[2].text.strip()
                overall = cols[3].text.strip()
                potential = cols[4].text.strip()
                posisi_tag = cols[1].find("span", class_="pos")
                position = posisi_tag.text.strip() if posisi_tag else "-"
                full_url = f"https://sofifa.com{player_href}"

                print(f"\n➡️ Player {idx}/{len(rows)}", flush=True)
                print(f"🔍 Fetching data for player: {full_url}", flush=True)

                height, weight, foot, skill, weak, contract, value, wage, nationality = \
                    scrape_player_profile(full_url, driver, debug_dir)

                player_data = [
                    player_id, name, age, overall, potential, position, height,
                    weight, foot, skill, weak, contract, nationality
                ]
                all_players_data.append(player_data)

                print(f"📝 ID: {player_id} | Player Name: {name} | Ovrl: {overall} | Pot: {potential} | Nat: {nationality}", flush=True)
                
                time.sleep(random.uniform(1.5, 3.5))

            except Exception as e:
                print(f"❌ Failed to process player {idx} ({full_url if 'full_url' in locals() else 'unknown URL'}): {e}", flush=True)
        
    except Exception as e:
        print(f"\n❌ SCRIPT FAILED: A fatal error occurred: {e}", flush=True)
        
    finally:
        # --- Step 5: Finalization and Data Saving ---
        if 'driver' in locals() and driver.service.is_connectable():
             driver.quit()

        df = pd.DataFrame(all_players_data, columns=[
            "ID", "Name", "Age", "Overall", "Potential", "Position",
            "Height", "Weight", "Pref.Foot","Skill Moves",
            "Weak Foot", "Contract", "Nationality"
        ])
        
        df = df.sort_values(by="ID").reset_index(drop=True)
        identifier = f"SCRIPT_1_{team_url.strip('/').split('/')[-1]}"
        output_base = os.path.join(output_dir, identifier)
        export_all_formats(df, output_base)

        elapsed = time.time() - start_time
        print(f"\n✅ Scraping process completed in {elapsed:.1f} seconds.", flush=True)