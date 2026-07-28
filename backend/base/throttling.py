from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class DefaultRateThrottle(UserRateThrottle):
    """
    Default rate limit that applies to all views unless specifically overridden.
    This is a global rate limit that works for both authenticated and anonymous users.
    """
    scope = 'default'
    rate = '120/minute'  # 120 requests per minute by default

class ThemesRateThrottle(UserRateThrottle):
    """
    Specific rate limit for the themes endpoint.
    This allows more frequent access to the themes endpoint.
    """
    scope = 'themes'
    rate = '300/minute'  # 300 requests per minute for themes endpoint

class ReportGenerationRateThrottle(UserRateThrottle):
    """
    Specific rate limit for report generation.
    This is a more restrictive limit since report generation is resource-intensive.
    """
    scope = 'report_generation'
    rate = '1/minute'  # 10 report generations per minute

class BurstRateThrottle(UserRateThrottle):
    """
    Throttle for burst requests (short time period)
    """
    rate = '100/minute'  # 100 requests per minute

class SustainedRateThrottle(UserRateThrottle):
    """
    Throttle for sustained requests (longer time period)
    """
    rate = '1000/hour'  # 1000 requests per hour

class AnonBurstRateThrottle(AnonRateThrottle):
    """
    Throttle for anonymous burst requests
    """
    rate = '100/minute'  # 100 requests per minute

class AnonSustainedRateThrottle(AnonRateThrottle):
    """
    Throttle for anonymous sustained requests
    """
    rate = '1000/hour'  # 1000 requests per hour 