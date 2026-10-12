"""Small environment-configured CORS middleware; same-origin deployment needs no CORS."""
from decouple import config
from django.http import HttpResponse

class SimpleCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_origins = {item.strip() for item in config('CORS_ALLOWED_ORIGINS', default='').split(',') if item.strip()}

    def __call__(self, request):
        origin = request.headers.get('Origin')
        if request.method == 'OPTIONS' and origin in self.allowed_origins:
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)
        if origin and origin in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Vary'] = 'Origin'
        return response
