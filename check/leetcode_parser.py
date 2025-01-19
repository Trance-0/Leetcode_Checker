"""
This file is used to parse the user submissions and update the problem data
"""

import csv
from datetime import datetime
import os
from pathlib import Path
from django.template.defaultfilters import slugify
from django.db.models import Q
from django.contrib.auth.models import User
from check.models import Problem, ProblemStatusChoices, Schedule, ScheduleTypeChoices

# typing
from typing import Optional

# import member models
from member.models import Member

# import leetcode api
from .leetcode_scraper import LeetcodeScraper
LEETCODE_SCRAPER_US=LeetcodeScraper('US')
LEETCODE_SCRAPER_CN=LeetcodeScraper('CN')

# import logging
import logging
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

def __update_root_problem_list()->Optional[Schedule]:
    """
    Update the root problem list from csv file

    takes 1 minute to update, do not call this function frequently
    """
    # create root schedule
    logger.info("Updating root schedule...")
    root_schedule = __get_root_schedule()
    # read csv file from static/leetcode_problem.csv
    with open(os.path.join(BASE_DIR, 'static/leetcode_problem.csv'), 'r') as file:
        reader = csv.reader(file)
        root_problem_list = [problem.problem_code for problem in Problem.objects.filter(schedule_id=root_schedule)]
        # logger.info(f"Root problem list: {root_problem_list}")
        # skip the first row (header)
        for row in reader:
            try:
                problem_code = int(row[0])
            except ValueError:
                logger.error(f"Problem code {row[0]} is not a valid integer, skip this problem")
                continue
            problem_name = row[1]
            # problem_difficulty = row[2]
            # problem_acceptance_rate = row[3]
            # create a new problem if not exists
            if problem_code not in root_problem_list:
                logger.info(f"Creating problem {problem_code} {problem_name}...")
                Problem.objects.create(
                    schedule_id=root_schedule,
                    problem_code=problem_code,
                    problem_title=problem_name,
                    # guess the problem slug, not accurate
                    problem_slug=slugify(problem_name),
                    status=ProblemStatusChoices.SP,
                    proof_url=None,
                )
    return root_schedule


def __get_root_schedule()->Optional[Schedule]:
    """
    Get the root schedule, if not exists, create one

    :return: root schedule
    :rtype: Schedule
    """
    # check if root schedule exists
    root_schedule = Schedule.objects.filter(schedule_type=ScheduleTypeChoices.ROOT).first()
    if root_schedule is None:
        root_schedule = Schedule.objects.create(
            schedule_type=ScheduleTypeChoices.ROOT,
            member_id=Member.objects.get(user_id=User.objects.get(username='root')),
            goals=65535,
        )
        __update_root_problem_list()
    return root_schedule

def get_root_problem_by_code(problem_code:int)->Optional[Problem]:
    """
    Get the problem data, if not exists, update the problem data

    :param problem_code: problem code
    :type problem_code: int

    :return: problem data
    :rtype: Problem or None
    """
    # get the problem
    root_schedule = __get_root_schedule()
    problem = Problem.objects.filter(schedule_id=root_schedule, problem_code=problem_code).first()
    if problem is not None:
        return problem
    logger.info(f"Problem with code {problem_code} not found, updating...")
    __update_root_problem_list()
    return Problem.objects.filter(schedule_id=root_schedule, problem_code=problem_code).first()


def get_root_problem_by_title(problem_title:str)->Optional[Problem]:
    """
    Get the root problem by problem title

    :param problem_title: problem title
    :type problem_title: str

    :return: root problem
    :rtype: Problem or None
    """
    root_schedule = __get_root_schedule()
    problem = Problem.objects.filter(schedule_id=root_schedule, problem_title=problem_title).first()
    if problem is not None:
        return problem
    logger.info(f"Problem with title {problem_title} not found, updating...")
    __update_root_problem_list()
    return Problem.objects.filter(schedule_id=root_schedule, problem_title=problem_title).first()

def get_full_problem_list()->Optional[list[Problem]]:
    """
    Get the full problem list from root schedule

    :return: list of problem
    :rtype: Problem
    """
    root_schedule = __get_root_schedule()
    return Problem.objects.filter(schedule_id=root_schedule)

def update_ac_problems(member) -> Optional[list[Problem]]:
    """ 
    Get the AC problems of a user

    :param member: member
    :type member: Member

    :return: list of ac problems
    :rtype: list[Problem]
    """
    scraper = LEETCODE_SCRAPER_US if member.server_region == 'US' else LEETCODE_SCRAPER_CN
    ac_problems = scraper.scrape_user_recent_submissions(member.leetcode_username)
    # get recent ac submissions
    try:
        submissions = ac_problems['recentAcSubmissions']['recentAcSubmissionList']
    except KeyError:
        logger.error(f"No recent ac submissions found for user {member.leetcode_username}, check the leetcode api, {ac_problems}")
        return []
    for submission in submissions:
        proof_url = f"https://leetcode.com/submissions/detail/{submission['id']}/"
        problem_title = submission['title']
        problem_slug = submission['titleSlug']
        timestamp = submission['timestamp']
        # check if problem is already registered
        if Problem.objects.filter(proof_url=proof_url).exists():
            logger.info(f"Problem {problem_title} already registered, ignore this problem")
            continue
        
        # get root problem, if not found, ignore this problem
        root_problem = get_root_problem_by_title(problem_title)
        if root_problem is None:
            logger.error(f"Root problem {problem_title} not found, ignore this problem")
            continue
        # update slug dynamically if root problem is incorrect
        if root_problem.problem_slug != problem_slug:
            for matched_problem in Problem.objects.filter(problem_title=problem_title):
                if matched_problem.problem_slug != problem_slug:
                    matched_problem.problem_slug = problem_slug
                    matched_problem.save()
                break

        # check satisfied problem for normal schedule
        satisfied_problem = Problem.objects.filter(
            Q(problem_title=problem_title) & 
            Q(schedule_id__member_id=member) & 
            Q(status=ProblemStatusChoices.NA) &
            Q(schedule_id__schedule_type=ScheduleTypeChoices.NORMAL)
        ).first()
        if satisfied_problem is not None:
            logger.info(f"Find satisfied problem {problem_title} for member {member.user_id.username}, mark as AC")
            satisfied_problem.status = ProblemStatusChoices.AC
            satisfied_problem.proof_url = proof_url
            satisfied_problem.done_date = datetime.fromtimestamp(int(timestamp))
            satisfied_problem.save()
            continue
        # add to latest free schedule set
        free_schedule = Schedule.objects.filter(Q(schedule_type=ScheduleTypeChoices.FREE)).order_by('-start_date').first()
        logger.info(f"Add recent ac problem {root_problem.problem_title} to free schedule: {free_schedule}")
        # create a free problem
        Problem.objects.create(
            schedule_id=free_schedule,
            problem_code=root_problem.problem_code,
            problem_title=root_problem.problem_title,
            problem_slug=root_problem.problem_slug,
            status=ProblemStatusChoices.AC,
            proof_url=proof_url,
            done_date=datetime.fromtimestamp(int(timestamp)),
        )
        # TODO: add credit to member
    return ac_problems



