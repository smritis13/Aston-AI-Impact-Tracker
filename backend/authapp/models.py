from django.db import models

# Create your models here.
# authapp/models.py
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    # You can add more fields (e.g., profile picture, location, etc.)

    def __str__(self):
        return f"{self.user.username}'s Profile"
