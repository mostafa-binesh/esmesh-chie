from rest_framework.renderers import JSONRenderer
from rest_framework.utils.serializer_helpers import ReturnList


class CustomJSONRenderer(JSONRenderer):
    """
    Custom JSON renderer that:
    - Wraps non-paginated data in a 'data' key for normal responses.
    - For error responses:
      - Wraps custom errors in 'error'.
      - Wraps validation errors in 'errors'.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context['response']

        # Check if the response status code indicates an error (4xx, 5xx)
        if response.status_code >= 400:
            # Check if it's a validation error
            if isinstance(data, dict) and 'detail' not in data:
                # This is likely a validation error (DRF default structure for validation)
                errors = {
                    'errors': data  # Wrap validation errors in 'errors'
                }
            else:
                # This is a custom error
                errors = {
                    'error': data
                }

            # Render the error response
            return super(CustomJSONRenderer, self).render(errors, accepted_media_type, renderer_context)

        # Handle normal data wrapping for successful responses
        if isinstance(data, dict) and 'results' in data:
            # Pagination keys detected; keep the data structure as is
            response_data = data
        elif isinstance(data, ReturnList):
            # If it's a list (non-paginated), we keep it as is
            response_data = data
        else:
            # Non-paginated data; wrap in 'data'
            response_data = {'data': data}

        # Call super to render the data into the content type specified by the renderer
        return super(CustomJSONRenderer, self).render(response_data, accepted_media_type, renderer_context)
