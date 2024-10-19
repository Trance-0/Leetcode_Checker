from django.db import models

from member.models import Member

from django.utils.translation import gettext_lazy as _

# Create your models here.

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
    last_update = models.DateTimeField(auto_now_add=True,null=False)
    expire_date = models.DateTimeField(auto_now=True,null=False)
    server = models.CharField(
        null=False,
        max_length=2,
        choices=LeetCodeSeverChoices.choices,
        default=LeetCodeSeverChoices.US
    )

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