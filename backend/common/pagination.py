"""Standard pagination used across the API."""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "pageSize"
    max_page_size = 200

    def get_paginated_response(self, data):
        return Response(
            {
                "success": True,
                "data": {
                    "items": data,
                    "page": self.page.number,
                    "pageSize": self.page.paginator.per_page,
                    "total": self.page.paginator.count,
                    "totalPages": self.page.paginator.num_pages,
                },
            }
        )
