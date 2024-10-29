from django.conf import settings
from django.db import models

from django.utils.translation import gettext_lazy as _
# Create your models here.

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

class Member(models.Model):

    # This objects contains the username, password, first_name, last_name, and email of member.
    user_id = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        # when member is delete, user would also be deleted
        on_delete=models.CASCADE,
        null=False,
    )
    # motto = models.CharField(max_length=100, blank=True, null=True)
    credit_remains = models.IntegerField(default=0, null=False)

    # last_login and date_joined automatically created by user_id, for these field, create one time value to timezone.now()
    # The field is only automatically updated when calling Model.save().
    last_login=models.DateTimeField(auto_now=True, null=False)
    # Automatically set the field to now when the object is first created. 
    date_joined=models.DateTimeField(auto_now_add=True, null=False)

    # user status is determined by the group in user attribute

    def __str__(self):
        """for better list display"""
        return f"{self.user_id.username}: {self.credit_remains}"
    
