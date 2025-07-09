
import random
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from abc import ABC, abstractmethod

# ------------------------------------
# UserAgentManager: Maneja rotación de User-Agents para simular diferentes navegadores
# ------------------------------------
class UserAgentManager:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    ]

    @staticmethod
    def get_random_user_agent():
        return random.choice(UserAgentManager.USER_AGENTS)

# ------------------------------------
# AntiBotMixin: Métodos comunes para simular comportamiento humano
# ------------------------------------
class AntiBotMixin:
    def random_sleep(self, min_seconds=2, max_seconds=5):
        duration = random.uniform(min_seconds, max_seconds)
        print(f"[Antibot] Durmiendo {duration:.2f}s")
        time.sleep(duration)

    def get_user_agent(self):
        return UserAgentManager.get_random_user_agent()

# ------------------------------------
# BaseScraper: Clase abstracta con lógica común de scraping y protección antibots
# ------------------------------------
class BaseScraper(ABC, AntiBotMixin):
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = self._init_driver()
    
    def _init_driver(self):
        user_agent = self.get_user_agent()
        print(f"[Antibot] Usando User-Agent: {user_agent}")

        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver

    def open_url(self, url):
        self.driver.get(url)
        print(f"Opened {url}")
        self.random_sleep(2, 4)

    @abstractmethod
    def scrape(self):
        pass

    def quit(self):
        self.driver.quit()

# ------------------------------------
# MartindaleScraper: Especialización para scrapear el sitio Martindale.com
# ------------------------------------
class MartindaleScraper(BaseScraper):
    def __init__(self, search_term="Puerto Rico, USA", pages=1):
        super().__init__(headless=False)
        self.search_term = search_term
        self.base_url = "https://www.martindale.com/"
        self.pages = pages
        self.results = []

    def _perform_search(self):
        self.open_url(self.base_url + "search/attorneys/")
        input_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "location"))
        )
        input_box.clear()
        input_box.send_keys(self.search_term)
        self.random_sleep()
        input_box.send_keys("\n")
        print("Search submitted")

    def _extract_profiles_from_page(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".search-result"))
        )
        profiles = self.driver.find_elements(By.CSS_SELECTOR, ".search-result")
        for profile in profiles:
            try:
                name = profile.find_element(By.CSS_SELECTOR, "a.name").text
                title = profile.find_element(By.CSS_SELECTOR, ".title").text
                location = profile.find_element(By.CSS_SELECTOR, ".location").text
                firm = profile.find_element(By.CSS_SELECTOR, ".org").text
                self.results.append({
                    "name": name,
                    "title": title,
                    "location": location,
                    "firm": firm
                })
            except Exception as e:
                print(f"Error extracting profile: {e}")

    def scrape(self):
        self._perform_search()
        for page in range(1, self.pages + 1):
            if page > 1:
                url = self.driver.current_url
                if "&page=" in url:
                    url = re.sub(r"&page=\d+", f"&page={page}", url)
                else:
                    url += f"&page={page}"
                self.open_url(url)

            self._extract_profiles_from_page()
            print(f"Page {page} scraped")
            self.random_sleep(3, 6)

        self.quit()
        return self.results

# ------------------------------------
# DataSaver: Clase utilitaria para guardar los datos
# ------------------------------------
class DataSaver:
    @staticmethod
    def to_excel(data: list, filename="output.xlsx"):
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        print(f"Data saved to {filename}")

    @staticmethod
    def to_csv(data: list, filename="output.csv"):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

# ------------------------------------
# Ejecución principal
# ------------------------------------
if __name__ == "__main__":
    scraper = MartindaleScraper(search_term="Puerto Rico, USA", pages=3)
    data = scraper.scrape()
    DataSaver.to_excel(data)
