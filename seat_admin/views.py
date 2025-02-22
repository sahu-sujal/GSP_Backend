# Ensure there are no circular imports here
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from django.views.decorators.http import require_POST
from seat_users.models import User, Course
import json

# Create your views here.

@csrf_exempt
@require_POST
def admin_login(request):
    data = json.loads(request.body)
    try:
        user = User.objects.get(email=data['email'], role='admin')
        if not check_password(user.password, data['password']):
            return JsonResponse({"message": "Invalid credentials"}, status=401)
        
        # Assuming you have a method to create access tokens
        access_token = create_access_token(user.id)
        return JsonResponse({"access_token": access_token})
    except User.DoesNotExist:
        return JsonResponse({"message": "Invalid credentials"}, status=401)

@csrf_exempt
def get_all_courses(request):
    courses = Course.objects.all()
    return JsonResponse([course.to_dict() for course in courses], safe=False)

@csrf_exempt
@require_POST
def create_course(request):
    data = json.loads(request.body)
    new_course = Course(
        course_name=data['course_name'],
        branch=data['branch'],
        total_seats=data['total_seats'],
        left_seats=data['total_seats'],
        price_per_seat=data['price_per_seat']
    )
    new_course.save()
    return JsonResponse(new_course.to_dict(), status=201)

@csrf_exempt
@require_POST
def update_course(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
        data = json.loads(request.body)
        
        course.total_seats = data.get('total_seats', course.total_seats)
        course.locked_seats = data.get('locked_seats', course.locked_seats)
        course.price_per_seat = data.get('price_per_seat', course.price_per_seat)
        course.update_seats()
        
        course.save()
        return JsonResponse(course.to_dict())
    except Course.DoesNotExist:
        return JsonResponse({"message": "Course not found"}, status=404)

@csrf_exempt
@require_POST
def delete_course(request, course_id):
    try:
        course = Course.objects.get(pk=course_id)
        course.delete()
        return JsonResponse({"message": "Course deleted successfully"})
    except Course.DoesNotExist:
        return JsonResponse({"message": "Course not found"}, status=404)
