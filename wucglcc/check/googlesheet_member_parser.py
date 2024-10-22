from pathlib import Path
import random
import string
import requests
from dotenv import load_dotenv
from check.models import LeetCodeSeverChoices, Problem, Schedule, ServerOperationChoices, ServerOperations
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from datetime import datetime
import os

import logging

from member.models import Member

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_google_sheet_data(spreadsheet_id, api_key):
    # Construct the URL for the Google Sheets API
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/!A1:Z?alt=json&key={api_key}"

    try:
        # Make a GET request to retrieve data from the Google Sheets API
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        print(f"An error occurred: {e}")
        return None


def update_member_data():
    # Get the latest member update time
    latest_update_time = (
        ServerOperations.objects.filter(
            operation_name=ServerOperationChoices.UPDATE_MEMBER
        )
        .order_by("-timestamp")
        .first()
    )
    sheet_data = get_google_sheet_data(
        os.getenv("GOOGLE_SHEET_ID"), os.getenv("GOOGLE_API_KEY")
    )
    # Print or return the current time as needed
    # print(f"Current time: {current_time}")
    # Extract the values from the sheet data
    values = sheet_data.get("values", [])
    # Skip the header row and iterate over the data rows
    for row in values[1:]:
        timestamp = datetime.strptime(row[0], "%Y-%m-%d %p%I:%M:%S").replace(
            hour=int(row[0][-8:-6]), minute=int(row[0][-5:-3]), second=int(row[0][-2:])
        )
        if timestamp <= latest_update_time.timestamp:
            break
        leetcode_username = row[1]
        leetcode_region = row[2]
        weekly_goal = int(row[3])
        start_date = datetime.strptime(row[4], "%Y-%m-%d")
        end_date = datetime.strptime(row[5], "%Y-%m-%d")
        problem_ids = row[6].split()
        email = row[7]

        # Compress log output
        logger.info(
            f"Timestamp: {timestamp}, "
            f"LeetCode Username: {leetcode_username}, "
            f"LeetCode Region: {leetcode_region}, "
            f"Weekly Goal: {weekly_goal}, "
            f"Start Date: {start_date}, "
            f"End Date: {end_date}, "
            f"Problem IDs: {problem_ids}, "
            f"Email: {email}"
        )
        # Create new member if not exists
        if not Member.objects.filter(email=email).exists():
            logger.info(f"Member {email} not found, creating new member")
            generated_password = "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
            user = User.objects.create_user(
                username=leetcode_username,
                email=email,
                password=make_password(generated_password),
            )
            member = Member.objects.create(user=user, motto="None", credit_remains=0)
        else:
            logger.info(f"Member {email} found, skipping")
            member = Member.objects.get(email=email)
        # Create new schedule
        schedule = Schedule.objects.create(
            member_id=member,
            leetcode_username=leetcode_username,
            start_date=start_date,
            expire_date=end_date,
            server=LeetCodeSeverChoices.US if leetcode_region == "美区 （Leetcode.com）" else LeetCodeSeverChoices.CN,
            weekly_goal=weekly_goal,
        )
        logger.info(f"Created schedule {schedule}") 
        # Create new problems
        for problem_id in problem_ids:
            problem = Problem.objects.create(
                schedule=schedule, problem_name=problem_id, status=False
            )
            logger.info(f"Created problem {problem}")
    # Update the last update time
    update_time = datetime.now()
    ServerOperations.objects.create(
        operation_name=ServerOperationChoices.UPDATE_MEMBER, timestamp=update_time
    )


if __name__ == "__main__":
    update_member_data()
