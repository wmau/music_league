from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from selenium.common.exceptions import NoSuchElementException
import re
import pandas as pd
import numpy as np

if "SPOTIFY_USERNAME" in os.environ and "SPOTIFY_PASSWORD" in os.environ:
    pass
else:
    raise ValueError(
        "Set up your environment variables for SPOTIFY_USERNAME and SPOTIFY_PASSWORD first"
    )


class Scraper:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)
        self.homepage = "https://app.musicleague.com/home/"

    def login(self):
        # First Music League login page
        login_url = "https://app.musicleague.com/login/"
        self.driver.get(login_url)
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Log in with Spotify"))
        ).click()

        # Spotify login page
        spotify_credentials = {
            "login-username": os.environ["SPOTIFY_USERNAME"],
            "login-password": os.environ["SPOTIFY_PASSWORD"],
        }
        for id, credential in spotify_credentials.items():
            credential_element = self.wait.until(
                EC.presence_of_element_located((By.ID, id))
            )
            credential_element.send_keys(credential)
        time.sleep(0.2)
        self.driver.find_element(By.ID, "login-button").click()

        # Terms and agreements page
        time.sleep(0.4)
        self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[data-testid="auth-accept"]')
            )
        ).click()

    def gather_leagues(self):
        self.go_to_league_list()
        time.sleep(3)

        league_cards = self.wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h6.card-title a"))
        )

        league_data = {
            league_card.text: league_card.get_attribute("href")
            for league_card in league_cards
        }

        return league_data

    def go_to_league_list(self):
        self.driver.get(self.homepage)
        self.wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "View completed"))
        ).click()

    def go_to_league(self, league_name):
        self.driver.get(self.leagues[league_name])

    def get_rounds(self, league_name):
        self.go_to_league(league_name)
        time.sleep(2)

        round_cards = self.wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//div[contains(span[@class='card-text text-body-tertiary'], 'ROUND')]",
                )
            )
        )

        round_data = {}
        for element in round_cards:
            round_text = element.find_element(
                By.XPATH, "./span[@class='card-text text-body-tertiary']"
            ).text
            round_title = element.find_element(
                By.XPATH, "./h5[@class='card-title']"
            ).get_attribute("textContent") # .text strips trailing whitespace

            # Extract the round number using regex
            round_number = re.search(r"ROUND (\d+)", round_text)
            if round_number:
                round_number = int(round_number.group(1))

            round_data[round_number] = round_title

        return round_data

    def get_round_data(self, league_title, round_name):
        self.go_to_league(league_title)

        # Get round link and navigate to it.
        round_card = self.wait.until(
            EC.presence_of_element_located(
                (By.XPATH, f'//h5[text()="{round_name}"]/ancestor::div[@class="card"]')
            )
        )
        round_link = round_card.find_element(
            By.XPATH, ".//p[contains(text(), 'RESULTS')]/ancestor::a"
        ).get_attribute("href")
        self.driver.get(round_link)

        submissions = self.wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//*[contains(@id, 'spotify:track:')]")
            )
        )

        df_list = [self.get_submission_data(submission) for submission in submissions]
        round_df = pd.concat(df_list, axis=0)

        return round_df

    def compile_league_data(self, league_title):
        time.sleep(5)
        round_data = self.get_rounds(league_title)

        df_list = []
        for i, round_title in round_data.items():
            round_df = self.get_round_data(league_title, round_title)
            time.sleep(np.random.uniform(low=1, high=2, size=1)[0])
            round_df["round_number"] = i
            df_list.append(round_df)

        league_df = pd.concat(df_list, axis=0)
        league_df["league_title"] = league_title

        return league_df

    @staticmethod
    def get_submission_data(submission):
        css_mapping = {
            "song_name": "h6.card-title a",
            "song_artist": "p.card-text:nth-of-type(1)",
            "song_album": "p.card-text:nth-of-type(2)",
            "submitter_name": "[class*=rank] .fw-semibold",
        }
        submission_data = {
            key: submission.find_element(By.CSS_SELECTOR, css_element).text
            for key, css_element in css_mapping.items()
        }

        # Spotify link
        submission_data["spotify_link"] = submission.find_element(
            By.CSS_SELECTOR, "h6.card-title a"
        ).get_attribute("href")

        # Submission rank within the round
        submission_data["rank"] = int(
            re.sub(
                r"\D",
                "",
                submission.find_element(
                    By.CSS_SELECTOR, "[class*=rank] .font-monospace"
                ).text,
            )
        )

        # Submitter comment.
        try:  # try/except necessary because comments are optional.
            submitter_comment = submission.find_element(
                By.CSS_SELECTOR, ".bi.bi-quote.flex-shrink-0.me-1.fs-5 + span",
            ).text
        except NoSuchElementException:
            submitter_comment = None
        submission_data["submitter_comment"] = submitter_comment

        # Voting data
        voters = {}
        card_footer_id = submission.find_element(
            By.CSS_SELECTOR, ".card-footer"
        ).get_attribute("id")
        vote_blocks = submission.find_elements(
            By.CSS_SELECTOR, f"#{card_footer_id} .row.align-items-start"
        )
        for vote_block in vote_blocks:
            voter_name = vote_block.find_element(By.CSS_SELECTOR, "b.text-body").text

            try:  # try/except is necessary because votes are optional (e.g., only sending in a comment)
                vote_value = int(
                    vote_block.find_element(By.CSS_SELECTOR, "h6.m-0").text
                )
            except NoSuchElementException:  # Assign vote value to 0 if voter only sent in a comment
                vote_value = 0

            try:  # try/except is necessary because comments are optional
                voter_comment = vote_block.find_element(
                    By.CSS_SELECTOR, "span.text-break.ws-pre-wrap"
                ).text
            except NoSuchElementException:
                voter_comment = None

            voters[voter_name] = (vote_value, voter_comment)

        # Make df out of voter-level data
        df = (
            pd.DataFrame.from_dict(
                voters, orient="index", columns=["vote_value", "voter_comment"]
            )
            .rename_axis("voter_name")
            .reset_index()
        )
        # Add submission-level data
        for key, item in submission_data.items():
            df[key] = item

        return df

    def run(self):
        self.login()
        self.leagues = self.gather_leagues()

        league_dfs = [
            self.compile_league_data(league) for league in self.leagues.keys()
        ]
        mega_df = pd.concat(league_dfs, axis=0)

        return mega_df
