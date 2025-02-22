from seat_users.models import Billing, User
from .models import Admin
from django.contrib.auth.hashers import make_password, check_password
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from datetime import timedelta, datetime
from functools import wraps
from django.conf import settings
import json
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

def admin_token_required(f):
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
            # 24 hours = 86400 seconds
            data = signing.loads(token, max_age=86400, salt='admin token')
            if not data.get('is_admin'):
                return JsonResponse({'message': 'Invalid admin token'}, status=401)
        except SignatureExpired:
            return JsonResponse({'message': 'Token has expired'}, status=401)
        except BadSignature:
            return JsonResponse({'message': 'Invalid token'}, status=401)
            
        return f(request, *args, **kwargs)
    return decorated


@csrf_exempt
def admin_login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)
        
    username = data.get('username')
    password = data.get('password')
    
    try:
        admin = Admin.objects.get(username=username)
        if check_password(password, admin.password):
            token = signing.dumps({
                'admin_id': admin.id,
                'username': admin.username,
                'is_admin': True
            }, salt='admin token')
            
            return JsonResponse({
                'token': token,
                'message': 'Login successful'
            })
        else:
            return JsonResponse({'message': 'Invalid credentials'}, status=401)
    except Admin.DoesNotExist:
        return JsonResponse({'message': 'Invalid credentials'}, status=401)

@csrf_exempt
def admin_register(request):
    try:
        data = json.loads(request.body)
        print('data:', data)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)
        
    username = data.get('username')
    password = data.get('password')
    
    if Admin.objects.filter(username=username).exists():
        return JsonResponse({'message': 'Username already exists'}, status=400)
    
    admin = Admin.objects.create(
        username=username,
        password=make_password(password)
    )
    
    return JsonResponse({'message': 'Admin registered successfully'}, status=201)

@require_GET
@admin_token_required
def protected_route(request):
    return JsonResponse({'message': 'This is a protected route'})