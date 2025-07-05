import jwt
from functools import wraps

from django.conf import settings
from django.http import JsonResponse


def jwt_required(view_func):
    """Ensure that request has valid JWT token."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return JsonResponse({"detail": "Authorization header missing"}, status=401)
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError:
            return JsonResponse({"detail": "Invalid token"}, status=401)
        request.jwt_payload = payload
        return view_func(request, *args, **kwargs)

    return _wrapped
  
