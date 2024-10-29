from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os
from pytz import timezone

from django.conf import settings
import requests
from warnings import filterwarnings
import logging

from check.models import LeetCodeSeverChoices, Schedule
from member.models import ServerOperationChoices, ServerOperations

server_timezone = timezone(settings.TIME_ZONE)
logger = logging.getLogger(__name__)

filterwarnings('ignore')

class LeetcodeScraper:

    def __init__(self,server_region):
        base_url='https://leetcode.com/graphql' if server_region == LeetCodeSeverChoices.US else 'https://leetcode.cn/graphql'
        self.base_url = base_url

    def scrape_user_recent_submissions(self,username):
        output = {}

        def scrape_single_operation(operation):
            json_data = {
                'query': operation_query_dict[operation],
                'variables': {
                    'username': username,
                },
                'operationName': operation,
            }

            if operation == 'recentAcSubmissions':
                json_data['variables']['limit'] = 15

            try:
                response = requests.post(self.base_url, json=json_data, stream=True, verify=False)
                output[operation] = response.json()['data'] 
            except Exception as e:
                logger.error(f'username: {username}', f'operation: {operation}', f'error: {e}', sep='\n')


        operation_query_dict = {
            'recentAcSubmissions':'\n    query recentAcSubmissions($username: String!, $limit: Int!) {\n  recentAcSubmissionList(username: $username, limit: $limit) {\n    id\n    title\n    titleSlug\n    timestamp\n  }\n}\n    ',
        }

        with ThreadPoolExecutor(max_workers=len(operation_query_dict)) as executor:
            executor.map(scrape_single_operation, operation_query_dict)

        return output

    def scrape_user_profile(self, username):

        output = {}

        def scrape_single_operation(operation):
            json_data = {
                'query': operation_query_dict[operation],
                'variables': {
                    'username': username,
                },
                'operationName': operation,
            }

            if operation == 'recentAcSubmissions':
                json_data['variables']['limit'] = 15

            try:
                response = requests.post(self.base_url, json=json_data, stream=True, verify=False)
                output[operation] = response.json()['data'] 
            except Exception as e:
                logger.error(f'username: {username}', f'operation: {operation}', f'error: {e}', sep='\n')


        operation_query_dict = {
            'userPublicProfile':'\n    query userPublicProfile($username: String!) {\n  matchedUser(username: $username) {\n    contestBadge {\n      name\n      expired\n      hoverText\n      icon\n    }\n    username\n    githubUrl\n    twitterUrl\n    linkedinUrl\n    profile {\n      ranking\n      userAvatar\n      realName\n      aboutMe\n      school\n      websites\n      countryName\n      company\n      jobTitle\n      skillTags\n      postViewCount\n      postViewCountDiff\n      reputation\n      reputationDiff\n      solutionCount\n      solutionCountDiff\n      categoryDiscussCount\n      categoryDiscussCountDiff\n    }\n  }\n}\n    ',
            'languageStats':'\n    query languageStats($username: String!) {\n  matchedUser(username: $username) {\n    languageProblemCount {\n      languageName\n      problemsSolved\n    }\n  }\n}\n    ',
            'skillStats':'\n    query skillStats($username: String!) {\n  matchedUser(username: $username) {\n    tagProblemCounts {\n      advanced {\n        tagName\n        tagSlug\n        problemsSolved\n      }\n      intermediate {\n        tagName\n        tagSlug\n        problemsSolved\n      }\n      fundamental {\n        tagName\n        tagSlug\n        problemsSolved\n      }\n    }\n  }\n}\n    ',
            'userContestRankingInfo':'\n    query userContestRankingInfo($username: String!) {\n  userContestRanking(username: $username) {\n    attendedContestsCount\n    rating\n    globalRanking\n    totalParticipants\n    topPercentage\n    badge {\n      name\n    }\n  }\n  userContestRankingHistory(username: $username) {\n    attended\n    trendDirection\n    problemsSolved\n    totalProblems\n    finishTimeInSeconds\n    rating\n    ranking\n    contest {\n      title\n      startTime\n    }\n  }\n}\n    ',
            'userProblemsSolved':'\n    query userProblemsSolved($username: String!) {\n  allQuestionsCount {\n    difficulty\n    count\n  }\n  matchedUser(username: $username) {\n    problemsSolvedBeatsStats {\n      difficulty\n      percentage\n    }\n    submitStatsGlobal {\n      acSubmissionNum {\n        difficulty\n        count\n      }\n    }\n  }\n}\n    ',
            'userBadges':'\n    query userBadges($username: String!) {\n  matchedUser(username: $username) {\n    badges {\n      id\n      name\n      shortName\n      displayName\n      icon\n      hoverText\n      medal {\n        slug\n        config {\n          iconGif\n          iconGifBackground\n        }\n      }\n      creationDate\n      category\n    }\n    upcomingBadges {\n      name\n      icon\n      progress\n    }\n  }\n}\n    ',
            'userProfileCalendar':'\n    query userProfileCalendar($username: String!, $year: Int) {\n  matchedUser(username: $username) {\n    userCalendar(year: $year) {\n      activeYears\n      streak\n      totalActiveDays\n      dccBadges {\n        timestamp\n        badge {\n          name\n          icon\n        }\n      }\n      submissionCalendar\n    }\n  }\n}\n    ',
            'recentAcSubmissions':'\n    query recentAcSubmissions($username: String!, $limit: Int!) {\n  recentAcSubmissionList(username: $username, limit: $limit) {\n    id\n    title\n    titleSlug\n    timestamp\n  }\n}\n    ',
        }

        with ThreadPoolExecutor(max_workers=len(operation_query_dict)) as executor:
            executor.map(scrape_single_operation, operation_query_dict)

        return output



    def _scrape_single_global_ranking_page(self, page_num, only_user_details=True):
        query = '''
        {
          globalRanking(page: %d) {
            totalUsers
            userPerPage
            rankingNodes {
              ranking
              currentRating
              currentGlobalRanking
              dataRegion
              user {
                username
                nameColor
                activeBadge {
                  displayName
                  icon
                }
                profile {
                  userAvatar
                  countryCode
                  countryName
                  realName
                }
              }
            }
          }
        }
        ''' % page_num
        
        try:
            response = requests.post(self.base_url, json={'query': query}, stream=True, verify=False)
            data = response.json()['data']['globalRanking']
            if only_user_details:
                return data['rankingNodes']
            else:
                return data
        except Exception as e:
            logger.error(f'Error in page number: {page_num}', f'Error: {e}', sep='\n')

    def scrape_all_global_ranking_users(self):
        first_response = self._scrape_single_global_ranking_page(1, only_user_details=False)
        total_leetcode_global_ranking_users = first_response['totalUsers']
        users_per_page = first_response['userPerPage']
        total_global_ranking_pages = total_leetcode_global_ranking_users // users_per_page
        logger.info(f'Total Leetcode users: {total_leetcode_global_ranking_users}', f'Users per page: {users_per_page}', f'Total pages: {total_global_ranking_pages}', sep='\n')

        final_response = first_response['rankingNodes']

        with ThreadPoolExecutor(max_workers=500) as executor:
            pages = range(2, total_global_ranking_pages + 1)
            results = executor.map(self._scrape_single_global_ranking_page, pages)
            for result in results:
                if result:
                    final_response.extend(result)
        
        return {
            'total_global_ranking_users_present': total_leetcode_global_ranking_users,
            'total_global_ranking_users_scraped': len(final_response),
            'total_global_ranking_pages': total_global_ranking_pages,
            'all_global_ranking_users': final_response
        }
    
def update_problem_data():
    latest_update_operation = (
        ServerOperations.objects.filter(
            operation_name=ServerOperationChoices.UPDATE_PROBLEM
        )
        .order_by("-timestamp")
        .first()
    )
    # if it is the first time to run, then latest_update_time is None
    if latest_update_operation is None:
        latest_update_time = datetime(2000, 1, 1, 0, 0).replace(tzinfo=server_timezone)
    else:
        latest_update_time = latest_update_operation.timestamp
    # Print or return the current time as needed
    logger.info(f"latest update time: {latest_update_time}")
    leetcode_scraper_cn = LeetcodeScraper(LeetCodeSeverChoices.CN)
    leetcode_scraper_us = LeetcodeScraper(LeetCodeSeverChoices.US)
    active_schedules = Schedule.objects.filter(expire_date__lt=datetime.now())
    for schedule in active_schedules:
        if schedule.server_region == LeetCodeSeverChoices.US:
            leetcode_scraper = leetcode_scraper_us
        else:
            leetcode_scraper = leetcode_scraper_cn
        user_submissions = leetcode_scraper.scrape_user_recent_submissions(schedule.leetcode_username)
        logger.info(f'user_submissions raw for user {schedule.leetcode_username}: {user_submissions}')
        for submission in user_submissions['recentAcSubmissions']:
            logger.info(submission)
    ServerOperations.objects.create(
        operation_name=ServerOperationChoices.UPDATE_PROBLEM,
        timestamp=datetime.now()
    )
    logger.info(f'update problem data finished at {datetime.now()}')
    return
