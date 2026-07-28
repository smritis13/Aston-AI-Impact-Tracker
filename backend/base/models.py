from django.db import models

# Create your views here.
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True  # This makes sure BaseModel is not created as a separate table


class Category(BaseModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self',  # Refers to the same model (self-referential)
        on_delete=models.CASCADE,
        related_name='subcategories',
        blank=True,
        null=True,
        default=None  # Ensure that a category can be top-level
    )

    def __str__(self):
        return self.name


class Metric(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='metrics')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Using JSONField to store a list of tags
    tags = models.JSONField(blank=True, default=list)

    def __str__(self):
        return self.name