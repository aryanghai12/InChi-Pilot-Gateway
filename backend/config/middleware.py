import uuid


class CorrelationIdMiddleware:
    """
    Middleware that reads or generates an X-Correlation-ID header for end-to-end request tracing.
    Attaches correlation_id to the request object and sets the response header.
    """

    HEADER_NAME = "HTTP_X_CORRELATION_ID"
    RESPONSE_HEADER_NAME = "X-Correlation-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        correlation_id = request.META.get(self.HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request.correlation_id = correlation_id
        response = self.get_response(request)
        response[self.RESPONSE_HEADER_NAME] = correlation_id
        return response
