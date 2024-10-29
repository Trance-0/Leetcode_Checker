import csv
from pathlib import Path
import random
import string
from django.conf import settings
from pytz import timezone
import requests
from dotenv import load_dotenv

from .models import LeetCodeSeverChoices, Problem, ProblemStatusChoices, Schedule
from member.models import ServerOperationChoices, ServerOperations
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from datetime import datetime, timedelta
import os

import logging

from member.models import Member

logger = logging.getLogger(__name__)
server_timezone = timezone(settings.TIME_ZONE)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
load_dotenv(os.path.join(settings.BASE_DIR, ".env"))


def update_problem_list():
    """
    Update the problem list in the database
    """
    # create admin member if not present
    if not Member.objects.filter(
        user_id__username=os.getenv("DJANGO_SUPERUSER_USERNAME")
    ).exists():
        Member.objects.create(
            user_id=User.objects.get(username=os.getenv("DJANGO_SUPERUSER_USERNAME")),
            credit_remains=0,
        )
    admin_member = Member.objects.get(
        user_id__username=os.getenv("DJANGO_SUPERUSER_USERNAME")
    )
    # create admin schedule if not present
    if not Schedule.objects.filter(member_id=admin_member).exists():
        Schedule.objects.create(
            member_id=admin_member,
            leetcode_username="ADMIN_PROBLEM_LIST",
            is_name_public=False,
            start_date=datetime.now().replace(tzinfo=server_timezone),
            expire_date=datetime.now().replace(tzinfo=server_timezone)
            - timedelta(days=365),
            server_region=LeetCodeSeverChoices.US,
            weekly_goal=7,
        )
    event_space = Schedule.objects.get(member_id=admin_member)
    update_entry=[]
    with open(
        os.path.join(settings.BASE_DIR, "static/leetcode_problem.csv"), "r"
    ) as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if not Problem.objects.filter(
                schedule_id=event_space, problem_name=row["Problem Name"]
            ).exists():
                update_entry.append(
                    Problem.objects.create(
                        schedule_id=event_space,
                        problem_code=row["Problem ID"],
                        problem_name=row["Problem Name"],
                        status=ProblemStatusChoices.SP,
                    )
                )
    logger.info(f"Created {len(update_entry)} new problems")


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
    latest_update_operation = (
        ServerOperations.objects.filter(
            operation_name=ServerOperationChoices.UPDATE_MEMBER
        )
        .order_by("-timestamp")
        .first()
    )
    # if it is the first time to run, then latest_update_time is None
    if latest_update_operation is None:
        latest_update_time = datetime(2000, 1, 1, 0, 0).replace(tzinfo=server_timezone)
    else:
        latest_update_time = latest_update_operation.timestamp
    sheet_data = get_google_sheet_data(
        os.getenv("GOOGLE_SHEET_ID"), os.getenv("GOOGLE_API_KEY")
    )
    # Print or return the current time as needed
    logger.info(f"latest update time: {latest_update_time}")
    ## TODO: add cd for requests
    # Extract the values from the sheet data
    values = sheet_data.get("values", [])
    logger.info(
        f"Google sheet data length: {len(values)}, record_length: {len(values[0])}"
    )
    # Skip the header row and iterate over the data rows
    for row in values[1:]:
        logger.info(f"row: {row}")
        record_timestamp = (
            datetime.strptime(row[0], "%m/%d/%Y %H:%M:%S")
            .replace(
                hour=int(row[0][-8:-6]),
                minute=int(row[0][-5:-3]),
                second=int(row[0][-2:]),
            )
            .replace(tzinfo=server_timezone)
        )
        logger.info(f"record_timestamp: {record_timestamp}, latest_update_time: {latest_update_time}")
        if record_timestamp <= latest_update_time:
            logger.info(f"Record timestamp is less than latest update time, skipping")
            continue
        leetcode_username = row[1]
        leetcode_region = row[2]
        weekly_goal = int(row[3]) if row[3] else 7
        start_date = datetime.strptime(row[4], "%Y-%m-%d").replace(
            tzinfo=server_timezone
        )
        end_date = (
            datetime.strptime(row[5], "%Y-%m-%d").replace(tzinfo=server_timezone)
            if row[5]
            else None
        )
        problem_ids = row[6].split()
        email = row[7]
        mode_enrolled = row[8]
        display_name = row[9]

        # Compress log output
        logger.info(
            f"Timestamp: {record_timestamp}, "
            f"LeetCode Username: {leetcode_username}, "
            f"LeetCode Region: {leetcode_region}, "
            f"Weekly Goal: {weekly_goal}, "
            f"Start Date: {start_date}, "
            f"End Date: {end_date}, "
            f"Problem IDs: {problem_ids}, "
            f"Email: {email}, "
            f"Mode Enrolled: {mode_enrolled}, "
            f"Display Name: {display_name}"
        )
        # Create new member if not exists
        if not Member.objects.filter(user_id__email=email).exists():
            logger.info(f"Member {email} not found, creating new member")
            generated_password = "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
            user = User.objects.create_user(
                username=display_name if display_name else leetcode_username,
                email=email,
                password=make_password(generated_password),
            )
            member = Member.objects.create(user_id=user, credit_remains=0)
        else:
            logger.info(f"Member {email} found, skipping")
            member = Member.objects.get(user_id__email=email)
        # Create new schedule
        if leetcode_username == "ADMIN_PROBLEM_LIST":
            logger.error("ADMIN_PROBLEM_LIST is reserved for admin problem list")
            continue
        schedule = Schedule.objects.create(
            member_id=member,
            leetcode_username=leetcode_username,
            is_name_public=display_name is not None,
            start_date=start_date,
            expire_date=end_date,
            server_region=(
                LeetCodeSeverChoices.US
                if leetcode_region == "美区 （Leetcode.com）"
                else LeetCodeSeverChoices.CN
            ),
            weekly_goal=weekly_goal if weekly_goal else 7,
        )
        logger.info(f"Created schedule {schedule}")
        # Create new problems
        for problem_code in problem_ids:
            # try to update problem list if not exists
            if not Problem.objects.filter(
                schedule_id__leetcode_username="ADMIN_PROBLEM_LIST",
                problem_code=problem_code,
            ).exists():
                logger.info(f"Problem {problem_code} not found, updating problem list")
                update_problem_list()
            if not Problem.objects.filter(
                schedule_id__leetcode_username="ADMIN_PROBLEM_LIST",
                problem_code=problem_code,
            ).exists():
                logger.error(f"Problem {problem_code} not found, skipping")
                continue
            source_problem = Problem.objects.get(
                schedule_id__leetcode_username="ADMIN_PROBLEM_LIST",
                problem_code=problem_code,
            )
            problem = Problem.objects.create(
                schedule_id=schedule,
                problem_code=source_problem.problem_code,
                problem_name=source_problem.problem_name,
                status=ProblemStatusChoices.NA,
            )
            logger.info(f"Created problem {problem}")
    # Update the last update time
    update_time = datetime.now().replace(tzinfo=server_timezone)
    ServerOperations.objects.create(
        operation_name=ServerOperationChoices.UPDATE_MEMBER, timestamp=update_time
    )
    logger.info(f'update member data finished at {update_time}')
    return


# if __name__ == "__main__":
# update_member_data()
# print(get_google_sheet_data(
#     os.getenv("GOOGLE_SHEET_ID"), os.getenv("GOOGLE_API_KEY")
# ))
