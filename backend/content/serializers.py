from rest_framework import serializers
from .models import  *
from base.models import Category
from base.serializers import CategorySerializer
from .models import WebsiteEvaluation

class ContentSourceURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSourceURL
        fields = ['id', 'url']

class ContentSourceSerializer(serializers.ModelSerializer):
    urls = ContentSourceURLSerializer(many=True, read_only=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = ContentSource
        fields = [
            'id', 'title', 'category', 'scrape_interval_value', 'scrape_interval_unit',
            'is_active', 'last_scraped', 'next_scheduled', 'urls'
        ]

class ContentSourceScrapeLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSourceScrapeLog
        fields = ['id', 'content_source', 'scraped_at', 'status', 'items_scraped', 'error_message']


class ContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Content
        fields = '__all__'

class ContentListSerializer(serializers.ModelSerializer):

    category = CategorySerializer()
    class Meta:
        model = Content
        fields = '__all__'



class PromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prompt
        fields = '__all__'


class ReportSerializer(serializers.ModelSerializer):
    prompt = PromptSerializer(read_only=True)
    prompt_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Report
        fields = ['id', 'topic', 'query', 'generated_report', 'thoughts', 'metadata', 'prompt', 'prompt_id', 'created_at', 'updated_at', 'type']
        read_only_fields = ['id', 'generated_report', 'thoughts', 'metadata']

class ReportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'



class WebsiteEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteEvaluation
        fields = '__all__'

# Specialized serializers for extracted medical/software use cases removed to keep codebase lean

class UseCaseSerializer(serializers.ModelSerializer):
    """Serializer for generic research impact use cases."""
    url_validation_score = serializers.SerializerMethodField()
    ref_period_status = serializers.SerializerMethodField()

    def get_ref_period_status(self, obj):
        """
        Whether this use case's date falls inside the applicable REF 2029
        window (research window for peer-reviewed sources, impact window for
        everything else) - computed with the same shared logic the final
        report uses, so a reviewer can check this at the evidence-browsing
        stage instead of only after a report is generated.
        Returns "within_period" | "outside_period" | None (undated, can't judge).
        """
        from core.llm.langchain.langgraph.report_generator_utils import (
            is_within_period,
            ref_period_for_content_type,
        )
        period = ref_period_for_content_type(obj.content_type)
        within = is_within_period(obj.use_case_date, period)
        if within is None:
            return None
        return "within_period" if within else "outside_period"

    def get_url_validation_score(self, obj):
        if not obj.source:
            return None
        try:
            # Extract domain from source URL
            from urllib.parse import urlparse
            parsed_url = urlparse(obj.source)
            domain = parsed_url.netloc.lower()
            
            # Remove 'www.' prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
            
            if not domain:
                return None
                
            # Get the website evaluation for this domain
            evaluation = WebsiteEvaluation.objects.filter(base_domain__icontains=domain).first()
            return evaluation.total_score if evaluation else None
        except Exception as e:
            # Log the exception for debugging but don't break serialization
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting URL validation score for source {obj.source}: {str(e)}")
            return None

    class Meta:
        model = UseCase
        fields = '__all__'

class UseCaseThemeSerializer(serializers.ModelSerializer):
    """
    Serializer for UseCaseTheme model.
    """
    class Meta:
        model = UseCaseTheme
        fields = ['id', 'title', 'description', 'created_at', 'featured']
        read_only_fields = ['created_at']

    def validate_title(self, value):
        # title has no DB-level unique constraint any more (deleted themes keep
        # their row so they can be restored), so uniqueness among *active*
        # themes is enforced here instead.
        existing = UseCaseTheme.objects.filter(title=value, is_deleted=False)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError("A theme with this title already exists.")
        return value


class SavedEntitySearchSerializer(serializers.ModelSerializer):
    """
    Serializer for SavedEntitySearch model.
    Allows users to save favorite company/institution searches.
    """
    class Meta:
        model = SavedEntitySearch
        fields = [
            'id', 'display_name', 'entity_name', 'entity_type', 
            'additional_filters', 'strict_matching', 'usage_count', 
            'last_used', 'is_favorite', 'created_at', 'updated_at'
        ]
        read_only_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']