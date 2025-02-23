from functools import wraps
import jwt
from django.conf import settings
from django.http import JsonResponse

def admin_jwt_required(f):
    @wraps(f)
    def decorated(request, *args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return JsonResponse({'message': 'Invalid token format'}, status=401)
        
        if not token:
            return JsonResponse({'message': 'Token is missing'}, status=401)
        
        try:
            # Decode the JWT token
            data = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if not data.get('is_admin'):
                return JsonResponse({'message': 'Invalid admin token'}, status=401)
        except jwt.ExpiredSignatureError:
            return JsonResponse({'message': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'message': 'Invalid token'}, status=401)
            
        return f(request, *args, **kwargs)
    return decorated
