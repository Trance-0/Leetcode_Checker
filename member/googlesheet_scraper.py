"""
This file is used to parse the google sheet data and update the member data in the database

Helper modules only, do not do and server operations
"""

import csv
import random
import string
import requests

import logging

logger = logging.getLogger(__name__)

class GoogleSheetScraper:
    def __init__(self, spreadsheet_id, api_key):
        self.spreadsheet_id = spreadsheet_id
        self.api_key = api_key

    def get_google_sheet_data(self):
        # Construct the URL for the Google Sheets API
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}/values/!A1:Z?alt=json&key={self.api_key}"

        try:
            # Make a GET request to retrieve data from the Google Sheets API
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the JSON response
            data = response.json()
            return data

        except requests.exceptions.RequestException as e:
            # Handle any errors that occur during the request
            logger.error(f"An error occurred: {e}")
            return None

# testing code for google sheet scraper

if __name__ == "__main__":
    spreadsheet_id = input("Enter the spreadsheet id: ")
    api_key = input("Enter the api key: ")
    google_sheet_scraper = GoogleSheetScraper(spreadsheet_id, api_key)
    print(google_sheet_scraper.get_google_sheet_data())


