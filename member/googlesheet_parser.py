"""
This file is used to parse the google sheet data and update the member data

Here stores the functions that create, update, query the member data

And interaction with google sheet API
"""

# import models
from datetime import datetime
from member.models import Member, LeetCodeSeverChoices
from check.models import ProblemStatusChoices, Schedule, Problem, ScheduleTypeChoices
from check.leetcode_parser import get_root_problem_by_code, update_ac_problems
from member.googlesheet_scraper import GoogleSheetScraper
from django.contrib.auth.models import User

# typing
from typing import Optional

# import utils
import logging

logger = logging.getLogger(__name__)

def google_time_to_datetime(google_time: str)->datetime:
    return datetime.strptime(google_time, "%m/%d/%Y %H:%M:%S")

def google_time_to_date(google_time: str)->datetime:
    return datetime.strptime(google_time, "%Y-%m-%d")

def get_member_data(
    email: str, leetcode_username: str, display_name: str, register_date: str, server_region_raw: str, is_leetcode_username_public: bool
) -> Optional[Member]:
    """
    Get the member data, if not exists, create a new member, if exists, update the member data

    validate identity of the member by email, if not valid, return None

    :param email: email of the member, primary key
    :type email: str
    :param leetcode_username: leetcode username of the member
    :type leetcode_username: str
    :param display_name: display name of the member
    :type display_name: str
    :param register_date: register date of the member
    :type register_date: str
    :param server_region: server region of the member
    :type server_region: str    
    :param is_leetcode_username_public: whether the leetcode username is public
    :type is_leetcode_username_public: bool
    """
    member = Member.objects.filter(user_id__email=email).first()
    server_region = LeetCodeSeverChoices.CN if 'cn' in server_region_raw else LeetCodeSeverChoices.US
    if member is None:
        # create a new member
        user = User.objects.create_user(
            username=display_name, email=email, password=None
        )
        member = Member.objects.create(
            user_id=user, 
            leetcode_username=leetcode_username, 
            server_region=server_region, 
            is_leetcode_username_public=is_leetcode_username_public,
            date_joined=google_time_to_datetime(register_date),
            last_login=google_time_to_datetime(register_date)
        )
        # create default schedule
        Schedule.objects.create(
            member_id=member,
            schedule_type=ScheduleTypeChoices.FREE,
            goals=65535,
            start_date=google_time_to_datetime(register_date).date(),
            expire_date=None
        )
    else:
        # check member data matched
        if member.user_id.username!=display_name: 
            logger.error(f"Member {member.user_id.username} display name different from google sheet, ignore this member")
            return None
        if member.leetcode_username != leetcode_username:
            logger.error(f"Member {member.user_id.username} leetcode username different from google sheet, ignore this member")
            return None
        if member.server_region != server_region:
            logger.error(f"Member {member.user_id.username} server region different from google sheet, ignore this member")
            return None
        
        if member.is_leetcode_username_public != is_leetcode_username_public:
            logger.info(f"Member {member.user_id.username} is_leetcode_username_public changed from {member.is_leetcode_username_public} to {is_leetcode_username_public}")
        member.is_leetcode_username_public = is_leetcode_username_public
        member.save()
    return member


def get_schedule_data(
    member: Member,
    sheet_row: int,
    problems_per_week: str,
    start_date: str,
    expire_date: str,
    mode: str,
    scheduled_problems: list[str],
) -> Optional[Schedule]:
    """
    Get the schedule data for member, if not exists, create a new schedule

    :param member: member of the schedule
    :type member: Member
    :param problems_per_week: problems per week of the schedule
    :type problems_per_week: str
    :param start_date: start date of the schedule
    :type start_date: str
    :param expire_date: expire date of the schedule
    :type expire_date: str
    :param mode: mode of the schedule
    :type mode: str
    """
    # check if schedule exists
    schedule = Schedule.objects.filter(sheet_row=sheet_row,member_id=member).first()
    if schedule is not None:
        logger.info(f"Schedule for member {member.user_id.username} already exists, skip this schedule")
        return schedule
    problem_type = ScheduleTypeChoices.NORMAL if "Normal" in mode else ScheduleTypeChoices.FREE
    if problem_type == ScheduleTypeChoices.NORMAL:
        try:
            problems_per_week = int(problems_per_week)
        except ValueError:
            logger.error(f"Problems per week {problems_per_week} is not a valid integer, when parsing scheduled problems for member {member.user_id.username}")
            problems_per_week = 0
    else:
        problems_per_week = -1
    # create a new schedule
    new_schedule = Schedule.objects.create(
        member_id=member,
        sheet_row=sheet_row,
        start_date=google_time_to_date(start_date),
        expire_date=google_time_to_date(expire_date) if expire_date != "" else None,
        goals=problems_per_week,
        schedule_type=problem_type,
    )
    if problem_type == ScheduleTypeChoices.NORMAL:
        # load problem list
        # create problems
        for problem_code in scheduled_problems:
            logger.info(f"Parsing scheduled problem {problem_code} for member {member.user_id.username}")
            # try parse into int
            try:
                problem_code = int(problem_code)
            except ValueError:
                logger.error(
                    f"Problem code {problem_code} is not a valid integer, when parsing scheduled problems for member {member.user_id.username}"
                )
                continue
            # capture problem
            problem = get_root_problem_by_code(problem_code)
            if problem is None:
                logger.error(f"Problem {problem_code} not found, when parsing scheduled problems for member {member.user_id.username}")
                continue
            # create a new problem for this schedule
            Problem.objects.create(
                schedule_id=new_schedule,
                problem_code=problem_code,
                problem_title=problem.problem_title,
                problem_slug=problem.problem_slug,
                status=ProblemStatusChoices.NA,
                proof_url=None,
            )
    return new_schedule

def __create_root_user()->None:
    root_user = User.objects.filter(username='root').first()
    if root_user is None:
        root_user = User.objects.create_user(username='root', email='root@root.com', password=None,is_staff=True)
    root_member = Member.objects.filter(user_id=root_user).first()
    if root_member is None:
        root_member = Member.objects.create(
            user_id=root_user,
            leetcode_username='root',
            server_region=LeetCodeSeverChoices.US,
            is_leetcode_username_public=False,
            date_joined=datetime.now(),
            last_login=datetime.now()
        )

def update_member_data(google_sheet_scraper: GoogleSheetScraper)->None:
    """
    Update the member data

    :param google_sheet_scraper: google sheet scraper
    :type google_sheet_scraper: GoogleSheetScraper
    """
    # create root user if not exists (guarantee the root user exists)
    __create_root_user()
    # get the google sheet data
    google_sheet_data = google_sheet_scraper.get_google_sheet_data()
    # skip the first row header
    for sheet_row, row in enumerate(google_sheet_data["values"][1:]):
        # read the row data
        register_date = row[0]
        leetcode_username = row[1]
        server_region = row[2]
        problems_per_week = row[3]
        start_date = row[4]
        expire_date = row[5]
        scheduled_problems = row[6].split()
        email = row[7]
        mode = row[8]
        display_name = row[9] if len(row) > 9 else leetcode_username
        # check if the member is already in the database
        member = get_member_data(email, leetcode_username, display_name, register_date, server_region, False)
        # if member is not valid, skip this member
        if member is None:
            continue
        get_schedule_data(
            member,
            sheet_row,
            problems_per_week,
            start_date,
            expire_date,
            mode,
            scheduled_problems,
        )
        # update the member data

def update_benchmark()->None:
    # get all member
    members = Member.objects.all()
    for member in members:
        update_ac_problems(member)

