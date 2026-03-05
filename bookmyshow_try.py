import time
import json
import re
import random
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_bms_pune_events():
    options = uc.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    print("Initializing undetected browser...")
    driver = uc.Chrome(options=options, version_main=145)
    url = "https://in.bookmyshow.com/explore/events-pune"
    driver.get(url)
    events_data = []
    try:
        print("Scrolling the page to load ALL event cards...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                driver.execute_script("window.scrollBy(0, -500);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Reached the absolute end of the page. All events loaded.")
                    break
            last_height = new_height
            scroll_attempts += 1
            print(f"Scroll iteration {scroll_attempts} completed...")
        print("Parsing the main page for Card Details...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        card_elements = soup.find_all('a', href=re.compile(r'/events/|/activities/'))
        unique_links = {}
        for card in card_elements:
            href = "https://in.bookmyshow.com" + card['href'] if card['href'].startswith('/') else card['href']
            if href not in unique_links:
                img_tag = card.find('img')
                img_src = img_tag['src'] if img_tag and 'src' in img_tag.attrs else "Not Mentioned"
                card_texts = list(card.stripped_strings)
                unique_links[href] = {"url": href,"img": img_src,"texts": card_texts}
        links_to_scrape = list(unique_links.values())
        print(f"Found {len(links_to_scrape)} unique events. Starting exhaustive detail extraction...")
        for i,item in enumerate(links_to_scrape):
            href=item["url"]
            texts=item["texts"]
            event={"event_name":"Not Mentioned","card_venue":"Not Mentioned","city":"Pune","card_category":"Not Mentioned","card_price":"Not Mentioned","detail_url":href,"detail_about":"Not Mentioned","detail_date_info":"Not Mentioned","detail_time_info":"Not Mentioned","detail_venue":"Not Mentioned","detail_age_limit":"Not Mentioned","detail_languages":"Not Mentioned","detail_genres":"Not Mentioned","detail_price_info":"Not Mentioned","duration_of_event":"Not Mentioned","card_image link":item["img"],"source":"BookMyShow","is_active":"Active","artist_organizer":"Not Mentioned"}
            if len(texts)>0:
                event["event_name"]=texts[0]
                prices_in_card=[t for t in texts if '₹' in t]
                price_idx=texts.index(prices_in_card[0]) if prices_in_card else -1
                if prices_in_card:
                    event["card_price"]=prices_in_card[0]
                if price_idx==-1:
                    if len(texts)>=3:
                        event["card_venue"]=texts[1]
                        event["card_category"]=texts[2]
                    elif len(texts)==2:
                        event["card_venue"]=texts[1]
                else:
                    if price_idx>=2:
                        event["card_venue"]=texts[1]
                    if price_idx>=3:
                        event["card_category"]=texts[2]
            try:
                sleep_time=random.uniform(4.0,8.0)
                print(f"\nSleeping for {sleep_time:.2f}s to avoid rate-limiting/blocking...")
                time.sleep(sleep_time)
                driver.get(href)
                try:
                    WebDriverWait(driver,8).until(EC.presence_of_element_located((By.TAG_NAME,"h1")))
                except:
                    time.sleep(3)
                detail_soup=BeautifulSoup(driver.page_source,'html.parser')
                all_page_texts=list(detail_soup.stripped_strings)
                h1_tag=detail_soup.find('h1')
                if h1_tag:
                    event["event_name"]=h1_tag.get_text(strip=True)
                events_data.append(event)
                print(f"\n[{i+1}/{len(links_to_scrape)}] --- Event Captured Successfully ---")
                print(json.dumps(event,indent=4,ensure_ascii=False))
            except Exception as e:
                print(f"\n[{i+1}/{len(links_to_scrape)}] Error fetching detail page for {href}. Error: {e}")
                continue
    finally:
        driver.quit()
    if events_data:
        df=pd.DataFrame(events_data)
        cols=['event_name','card_venue','city','card_category','card_price','detail_url','detail_about','detail_date_info','detail_time_info','detail_venue','detail_age_limit','detail_languages','detail_genres','detail_price_info','duration_of_event','card_image link','source','is_active','artist_organizer']
        df=df[cols]
        output_file="Pune_Upcoming_Events_Scraped.csv"
        df.to_csv(output_file,index=False,encoding='utf-8')
        print(f"\nSuccess! Saved {len(events_data)} fully detailed events to '{output_file}'.")
    else:
        print("No events could be retrieved.")

if __name__ == "__main__":
    scrape_bms_pune_events()