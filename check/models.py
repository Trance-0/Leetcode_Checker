from django.db import models
from django.utils.translation import gettext_lazy as _

from member.models import Member

# create your models here

class ScheduleTypeChoices(models.TextChoices):
    """Schedule type choices"""

    # free schedule, no goals
    FREE = "FREE", _("Free")
    # normal schedule, with goals
    NORMAL = "NORMAL", _("Normal")
    # root schedule, used for problem list
    ROOT = "ROOT", _("Root")


class Schedule(models.Model):
    """This is the activation code that will be used for create user."""

    member_id = models.ForeignKey(
        Member,
        # when member is delete, user would also be deleted
        on_delete=models.CASCADE,
        null=False,
    )
    sheet_row=models.IntegerField(null=True)
    schedule_type = models.CharField(
        null=False,
        max_length=6,
        choices=ScheduleTypeChoices.choices,
        default=ScheduleTypeChoices.FREE
    )
    # editable datetime field with auto-now
    # https://stackoverflow.com/a/18752680/14110380
    created_date = models.DateTimeField(auto_now=True,null=False)
    # 3 problems per week by default
    goals = models.IntegerField(default=3,null=False)
    start_date = models.DateTimeField(auto_now=True,null=False)
    # expire date is None for default schedule
    expire_date = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.member_id} - {self.start_date} - {self.expire_date}"

class ProblemStatusChoices(models.TextChoices):
    AC = "AC", _("Accepted")
    NA = "NA", _("Not Attempted")
    SP = "SP", _("Sample Problem")

class Problem(models.Model):
    
    schedule_id = models.ForeignKey(
        Schedule,
        # when member is delete, user would also be deleted
        on_delete=models.CASCADE,
        null=False,
    )
    problem_code = models.IntegerField(null=False)
    problem_title= models.CharField(null=False,max_length=256)
    problem_slug= models.CharField(null=False,max_length=256)
    # is the problem ac or not
    status=models.CharField(choices=ProblemStatusChoices.choices,default=ProblemStatusChoices.NA,null=False,max_length=2)
    # when the problem is done, timestamp       
    done_date = models.DateTimeField(null=True)
    # the url of the proof for recent AC
    proof_url = models.CharField(null=True,max_length=256)

    def __str__(self):
        return f"{self.schedule_id} - {self.problem_code} - {self.problem_title} - {self.status}"

