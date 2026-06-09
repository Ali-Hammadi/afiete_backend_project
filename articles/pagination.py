# Path: articles/pagination.py

from rest_framework.pagination import PageNumberPagination

class ArticlePagination(PageNumberPagination):
    page_size             = 5
    page_size_query_param = 'page_size'
    max_page_size         = 50

    def get_next_link(self):
        # تأكيد توليد الرابط بناءً على مسار الطلب الحالي للمقالات دون تداخل مع تطبيقات أخرى
        return super().get_next_link()

    def get_previous_link(self):
        return super().get_previous_link()