from django.db import models
from base.models import Category,BaseModel
from core.llm.utils.web.URLValidator import URLValidator
from django.utils.timezone import now

class ContentSource(BaseModel):
    INTERVAL_UNIT_CHOICES = [
        ('days', 'Days'),
        ('hours', 'Hours'),
        ('minutes', 'Minutes'),
    ]

    title = models.CharField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name='content_sources')
    scrape_interval_value = models.PositiveIntegerField(
        default=1,
        help_text="Numeric value to indicate scraping interval."
    )
    scrape_interval_unit = models.CharField(
        max_length=20,
        choices=INTERVAL_UNIT_CHOICES,
        default='days',
        help_text="Unit of time for the scraping interval."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable scraping."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last successful scrape."
    )
    next_scheduled = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the next scheduled scrape."
    )

    def __str__(self):
        return self.title

class ContentSourceURL(BaseModel):
    content_source = models.ForeignKey(ContentSource, on_delete=models.CASCADE, related_name='urls')
    url = models.URLField()

    def __str__(self):
        return self.url

class ContentSourceScrapeLog(BaseModel):
    """
    Tracks each scraping event for a given ContentSource.
    Store status, items scraped, error information, etc.
    """
    content_source = models.ForeignKey(ContentSource, on_delete=models.CASCADE)
    scraped_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='success')
    items_scraped = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.content_source.title} - {self.scraped_at} ({self.status})"


class Content(BaseModel):
    url = models.URLField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, null=True, related_name='contents')
    title = models.CharField(max_length=255, blank=True, null=True)
    original_content = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    tags = models.JSONField(blank=True, null=True)  # Tags stored as a JSON list
    scraped_at = models.DateTimeField(auto_now_add=True)
    image = models.CharField(max_length=5000, blank=True, null=True)


    def __str__(self):
        return self.title or self.url
    
    class Meta:
        ordering = ['-id']
    


class UrlToScrape(BaseModel):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]

    url = models.URLField(unique=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    content = models.OneToOneField(Content, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_url')

    def __str__(self):
        return f"{self.url} ({self.status})"
    
    class Meta:
        ordering = ['-created_at']


class UseCaseTheme(models.Model):
    """
    Model to store different themes for use cases.
    """
    # Title is not DB-unique any more: a deleted (is_deleted=True) theme keeps
    # its row (and its reports/use cases) around for restoring, and a new
    # active theme is allowed to reuse the same title. Uniqueness among
    # *active* themes is enforced in UseCaseThemeSerializer.validate_title.
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    featured = models.BooleanField(default=False,null=True,blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-id']

class Report(BaseModel):
    topic = models.TextField()  # e.g., "AI in Healthcare Research" or any research topic
    query = models.TextField()  # The original query
    generated_report = models.TextField()  # The AI-generated report
    type = models.CharField(max_length=20, blank=True, null=True)
    thoughts = models.JSONField(default=list)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    prompt = models.ForeignKey('Prompt', on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    theme = models.ForeignKey(UseCaseTheme, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    
    def __str__(self):
        return f"Report: {self.topic} (Last Updated: {self.updated_at})"
    
    class Meta:
        ordering = ['-id']

# ExtractedUseCase model removed; the project now stores only generic research impact use cases




# UseCase is retained as the primary model for storing generic research impact use cases.
# Documentation updated to remove medical/SDLC references.

class UseCase(models.Model):
    """
    Model to store generic research impact use cases tied to reports and themes.
    """
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='user_cases', null=True, blank=True)
    theme = models.ForeignKey(UseCaseTheme, on_delete=models.SET_NULL, null=True, blank=True, related_name='use_cases')
    use_case_name = models.CharField(max_length=1000, null=True, blank=True, help_text="A clear, concise one-sentence summary of the use case")
    use_case_type = models.CharField(max_length=400,null=True,blank=True)
    company = models.CharField(max_length=400,null=True,blank=True)
    industry = models.CharField(max_length=400,null=True, blank=True)
    tools = models.TextField(null=True,blank=True)
    use_case_description = models.TextField()
    performance_improvement_category = models.CharField(max_length=400,null=True, blank=True)
    geography = models.CharField(max_length=400,null=True, blank=True)
    country = models.CharField(max_length=400,null=True, blank=True)
    performance_impact = models.TextField(blank=True,null=True)
    use_case_date = models.CharField(max_length=40,null=True, blank=True)
    published_date = models.CharField(max_length=40, null=True, blank=True, help_text="Date the source document itself was published/last updated, distinct from use_case_date (the impact date)")
    source = models.CharField(max_length=400, blank=True,null=True )
    source_type = models.CharField(max_length=50, blank=True, null=True, choices=[
        ('PDF', 'Uploaded PDF'),
        ('External Verification', 'External Verification'),
        ('Web', 'Web Search'),
    ], help_text="Type of source for this use case")
    source_reference = models.TextField(blank=True, null=True, help_text="Reference details (page number, paragraph, URL, etc.)")
    domain = models.CharField(max_length=255, blank=True, null=True, help_text="Domain parsed from the source URL, e.g. aston.ac.uk")
    publisher = models.CharField(max_length=255, blank=True, null=True, help_text="Publisher/organisation that published the source, if identifiable")
    content_type = models.CharField(max_length=30, blank=True, null=True, choices=[
        ('press_release', 'Press Release'),
        ('peer_reviewed', 'Peer-Reviewed Output'),
        ('news', 'News Article'),
        ('policy', 'Policy Document'),
        ('testimonial', 'Testimonial/Letter'),
        ('other', 'Other'),
    ], help_text="Classification of the source's publication type")
    direct_quote = models.TextField(blank=True, null=True, help_text="Verbatim quote from the source supporting a citation or impact claim")
    affiliation_note = models.TextField(blank=True, null=True, help_text="Statement from this source of when a named researcher joined/left Aston or another institution, if stated")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Fields for credibility and relevance remain useful
    credibility_score = models.IntegerField(null=True, blank=True, help_text="Score from 0-10 indicating the credibility of the use case")
    is_credible = models.BooleanField(null=True, blank=True, help_text="Whether the use case is considered credible")
    credibility_reasoning = models.TextField(blank=True, null=True, help_text="Explanation of the credibility assessment")
    relevance_score = models.IntegerField(null=True, blank=True, help_text="Score from 0-10 indicating the relevance to user requirements")
    is_relevant = models.BooleanField(null=True, blank=True, help_text="Whether the use case is relevant to user requirements")
    relevance_reasoning = models.TextField(blank=True, null=True, help_text="Explanation of the relevance assessment")
    reference_number = models.IntegerField(null=True, blank=True, help_text="Hard-coded reference number for case study generation")

    def __str__(self):
        return f"{self.company} - {self.use_case_name}"
    
    class Meta:
        ordering = ['-id']




class ScrapedURL(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, null=True, blank=True, related_name="scraped_urls")
    url = models.CharField(max_length=400, blank=True, null=True)
    scraped_at = models.DateTimeField(default=now)
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url

class Prompt(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    json_structure = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-id']


class WebsiteEvaluation(models.Model):
    """
    Model to store evaluation metrics for websites based on their base domain.
    """
    base_domain = models.CharField(max_length=255, unique=True, help_text="The base domain (e.g., google.com)")
    source = models.CharField(max_length=100, help_text="Type of source (e.g., University, Private company)")


    
    authority = models.CharField(max_length=50, help_text="Level of authority (e.g., University, Government)")
    data_origin = models.CharField(max_length=255, help_text="Origin of the data (e.g., Curated academic data)")
    transparency = models.CharField(
        max_length=20,
        choices=[("Very High", "Very High"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        help_text="Transparency level of the source"
    )
    bias_risk = models.CharField(
        max_length=20,
        choices=[("Very High", "Very High"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        help_text="Risk of bias in the content"
    )
    peer_review = models.CharField(
        max_length=20,
        choices=[("Very High", "Very High"), ("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        help_text="Level of peer review"
    )
    updated = models.BooleanField(default=False, help_text="Whether the content is regularly updated")
    domain_authority_score = models.IntegerField(
        default=0,
        help_text="Initial score based on domain type (0-3)"
    )
    security_score = models.IntegerField(
        default=0,
        help_text="Score for HTTPS usage (0-1)"
    )
    recency_score = models.IntegerField(
        default=0,
        help_text="Score based on content age (0-3)"
    )
    content_quality_score = models.IntegerField(
        default=0,
        help_text="Score based on content length and quality (0-3)"
    )
    total_score = models.IntegerField(
        default=0,
        help_text="Total validity score (0-10)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.base_domain} (Score: {self.total_score}/10)"

    def update_scores(self, content=None):
        """
        Dynamically update scores based on runtime evaluation.
        """
        validator = URLValidator()
        score, details = validator.rank_url(f"https://{self.base_domain}", content)
        self.domain_authority_score = details["reasons"].count("Trusted domain") * 3 or details["reasons"].count("High-authority domain") * 3 or details["reasons"].count("Moderate-authority domain") * 2 or details["reasons"].count("Generic domain") * 1 or 0
        self.security_score = 1 if details["reasons"].count("Secure (HTTPS)") else 0
        self.recency_score = details["reasons"].count("Recent content") * 3 or details["reasons"].count("Moderately recent") * 2 or details["reasons"].count("Older content") * 1 or 0
        self.content_quality_score = details["reasons"].count("Detailed content") * 3 or details["reasons"].count("Moderate content") * 2 or details["reasons"].count("Short content") * 1 or 0
        self.total_score = min(self.domain_authority_score + self.security_score + self.recency_score + self.content_quality_score, 10)
        self.save()

    class Meta:
        ordering = ['-total_score']


class SavedEntitySearch(BaseModel):
    """
    Model to store saved entity searches for quick access.
    Users can save favorite companies/institutions/people for quick filtering.
    """
    ENTITY_TYPE_CHOICES = [
        ('company', 'Company'),
        ('university', 'University'),
        ('research_institution', 'Research Institution'),
        ('person', 'Person'),
    ]
    
    # Name that appears in UI (e.g., "Siemens Sustainability Research")
    display_name = models.CharField(max_length=255, help_text="Friendly name for this saved search")
    
    # The entity being searched for (e.g., "Siemens")
    entity_name = models.CharField(max_length=255, help_text="Name of the company/institution/person")
    
    # Type of entity
    entity_type = models.CharField(
        max_length=30, 
        choices=ENTITY_TYPE_CHOICES,
        default='company',
        help_text="Type of entity (company, university, research institution, or person)"
    )
    
    # Additional filters applied with this search
    additional_filters = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Additional filters (industry, geography, etc.) as JSON"
    )
    
    # Whether to use strict matching
    strict_matching = models.BooleanField(
        default=False,
        help_text="If True, only show results for the exact entity"
    )
    
    # Number of times this search has been used
    usage_count = models.PositiveIntegerField(default=0)
    
    # Last time this search was used
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Whether this is marked as a favorite
    is_favorite = models.BooleanField(default=False)
    
    # User who created this saved search (optional - for future multi-user support)
    user = models.CharField(max_length=255, blank=True, null=True, help_text="User who created this saved search")
    
    def __str__(self):
        return f"{self.display_name} ({self.entity_type}: {self.entity_name})"
    
    class Meta:
        ordering = ['-is_favorite', '-usage_count', '-updated_at']
        verbose_name = "Saved Entity Search"
        verbose_name_plural = "Saved Entity Searches"