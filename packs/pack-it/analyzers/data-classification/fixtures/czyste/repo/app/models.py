from django.db import models


class Member(models.Model):
    nickname = models.CharField(max_length=50)
    birth_date = models.DateField()  # pii
    email_opt_in = models.BooleanField(default=False)
