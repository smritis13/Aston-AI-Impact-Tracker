from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # Default page size - Impact Tracker displays 10 items per page
    page_size_query_param = 'size'  # Allow clients to set page size
    max_page_size = 200  # Prevent excessive page sizes
