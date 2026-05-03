from .analytics import record_page_visit


class PageVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.session_key:
            request.session.save()

        response = self.get_response(request)

        excluded_paths = [
            "/admin/",
            "/track-click/",
            "/favicon.ico",
        ]

        if (
            request.method == "GET"
            and not any(request.path.startswith(path) for path in excluded_paths)
            and not request.path.startswith("/static/")
            and not request.path.startswith("/media/")
        ):
            record_page_visit(request)

        return response
