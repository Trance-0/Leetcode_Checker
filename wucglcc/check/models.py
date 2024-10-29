from django.db import models

from member.models import Member,ServerOperationChoices,ServerOperations

from django.utils.translation import gettext_lazy as _

# create your models here

class LeetCodeSeverChoices(models.TextChoices):
    """User group choices, may be more efficient if use django internal group"""

    CN= "CN", _("China Mainland")
    US = "US", _("United States")

class Schedule(models.Model):
    """This is the activation code that will be used for create user."""

    member_id = models.ForeignKey(
        Member,
        # when member is delete, user would also be deleted
        on_delete=models.CASCADE,
        null=False,
    )
    leetcode_username= models.CharField(null=False,max_length=256)
    is_name_public = models.BooleanField(default=False,null=False)
    # editable datetime field with auto-now
    # https://stackoverflow.com/a/18752680/14110380
    created_date = models.DateTimeField(auto_now=True,null=False)
    weekly_goal = models.IntegerField(default=7,null=False)
    start_date = models.DateTimeField(auto_now=True,null=False)
    last_update = models.DateTimeField(auto_now_add=True,null=False)
    expire_date = models.DateTimeField(null=True)
    server_region = models.CharField(
        null=False,
        max_length=2,
        choices=LeetCodeSeverChoices.choices,
        default=LeetCodeSeverChoices.US
    )
    def __str__(self):
        return f"{self.member_id} - {self.leetcode_username} - {self.start_date} - {self.expire_date}"

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
    problem_name= models.CharField(null=False,max_length=256)
    # is the problem ac or not
    status=models.CharField(choices=ProblemStatusChoices.choices,default=ProblemStatusChoices.NA,null=False,max_length=2)
    done_date = models.DateTimeField(auto_now=True,null=False)
    def __str__(self):
        return f"{self.schedule_id} - {self.problem_name} - {self.status}"

