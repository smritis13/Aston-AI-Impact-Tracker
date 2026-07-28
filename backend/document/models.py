from django.db import models
from base.models import BaseModel,Category


class Document(BaseModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="files",null=True,blank=True)
    name = models.CharField(max_length=255,blank=True,null=True)
    summary = models.TextField(blank=True,null=True)
    content = models.TextField(blank=True,null=True)
    tags = models.TextField(blank=True,null=True)
    file = models.FileField(upload_to="documents/")
    size = models.PositiveIntegerField(blank=True, null=True)  # Size in bytes
    file_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'pdf', 'jpg'
    is_hidden = models.BooleanField(default=False,blank=True,null=True)

    def __str__(self):
        return self.name
