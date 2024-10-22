from django.db import models

from member.models import Member

from django.utils.translation import gettext_lazy as _

# create your models here

class ServerOperationChoices(models.TextChoices):
    """Server operation choices"""
    UPDATE_MEMBER = "UPDATE_MEMBER", _("Update Member")
    UPDATE_PROBLEM = "UPDATE_PROBLEM", _("Update Problem")
    UPDATE_BENCHMARK = "UPDATE_BENCHMARK", _("Update Benchmark")

class ServerOperations(models.Model):
    operation_name = models.CharField(choices=ServerOperationChoices.choices,null=False,max_length=256)
    timestamp = models.DateTimeField(auto_now=True,null=False)

    def __str__(self):
        return f"{self.operation_name} at {self.timestamp}" 

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
    # editable datetime field with auto-now
    # https://stackoverflow.com/a/18752680/14110380
    created_date = models.DateTimeField(auto_now=True,null=False)
    start_date = models.DateTimeField(null=False)
    last_update = models.DateTimeField(auto_now_add=True,null=False)
    expire_date = models.DateTimeField(null=False)
    server = models.CharField(
        null=False,
        max_length=2,
        choices=LeetCodeSeverChoices.choices,
        default=LeetCodeSeverChoices.US
    )
    def __str__(self):
        return f"{self.member_id} - {self.leetcode_username} - {self.start_date} - {self.expire_date}"

class Problem(models.Model):
    
    schedule_id = models.ForeignKey(
        Schedule,
        # when member is delete, user would also be deleted
        on_delete=models.CASCADE,
        null=False,
    )
    problem_name= models.CharField(null=False,max_length=256)
    # is the problem ac or not
    status=models.BooleanField(default=False,null=False)
    done_date = models.DateTimeField(auto_now=True,null=False)
    def __str__(self):
        return f"{self.schedule_id} - {self.problem_name} - {self.status}"
