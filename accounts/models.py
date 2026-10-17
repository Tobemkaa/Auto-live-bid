from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        STAFF = "staff", "Staff"
        
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)



# Create your models here.
