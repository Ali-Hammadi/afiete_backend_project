# doctors/pagination.py

from rest_framework.pagination import PageNumberPagination

class DoctorPagination(PageNumberPagination):
    page_size             = 5
    page_size_query_param = 'page_size'  # ?page_size=5 لو بدو يغير
    max_page_size         = 50