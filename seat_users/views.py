from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Billing
import json
from django.views.decorators.http import require_POST
import random
import string
import requests
import os
from .models import Course,AdoptionAdmin
import pdfkit
from datetime import datetime
from .utils import admin_jwt_required

def send_sms_via_fast2sms(phone_number, otp, name):
    import urllib.parse
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    phone_number = str(phone_number).strip()
    message = f"Dear {name}, Your OTP for seat(s) adoption is: {otp}. Do not share this with anyone."
    
    # URL-encode the message and otp (variables_values)
    encoded_message = urllib.parse.quote_plus(message)
    encoded_variables = urllib.parse.quote_plus(str(otp))
    
    # Build payload as a form-encoded string for a single number only
    payload = f"sender_id=FTWSMS&message={encoded_message}&variables_values={encoded_variables}&route=dlt&numbers={phone_number}"
    
    headers = {
        "authorization": "va6ZfC7lpqmRAMOcwKJQ1tNruWyFL5hS4nIB0kjdTPXsYb9EGUTOvtd8DZQj5IroB07a3gJ2AuXV9lPi",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache",
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        
        if not response.text.strip():
            if response.status_code == 200:
                print(f"SMS sent successfully to {phone_number} - empty response but status 200")
                return {"status": True, "message": "SMS sent successfully"}
            else:
                print(f"Empty response received from SMS API for {phone_number}")
                return {"status": False, "message": "No response from SMS service"}
                
        try:
            response_data = response.json()
        except ValueError as json_err:
            print(f"Invalid JSON response from SMS API: {response.text}")
            return {"status": False, "message": f"Invalid response from SMS service: {str(json_err)}"}
        
        if response.status_code == 200 and response_data.get("return") is True:
            return {"status": True, "message": "SMS sent successfully"}
        else:
            error_msg = response_data.get("message", "Unknown error occurred")
            print(f"SMS API error: {error_msg}")
            return {"status": False, "message": f"Failed to send SMS: {error_msg}"}
    
    except requests.RequestException as e:
        print(f"SMS sending request failed: {str(e)}")
        return {"status": False, "message": f"Failed to connect to SMS service: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error in SMS sending: {str(e)}")
        return {"status": False, "message": f"Unexpected error: {str(e)}"}

@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({"message": "Email already registered"}, status=400)
        if User.objects.filter(phone_number=data['phone_number']).exists():
            return JsonResponse({"message": "Phone number already registered"}, status=400)
        
        hashed_password = make_password(data['password'])
        new_user = User(
            full_name=data['full_name'],
            designation=data['designation'],
            email=data['email'],
            phone_number=data['phone_number'],
            company_name=data['company_name'],
            password=hashed_password
        )
        new_user.save()
        return JsonResponse({"message": "User registered successfully"}, status=201)

@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        identifier = data.get('email') or data.get('phone_number')
        password = data['password']
        
        try:
            user = User.objects.get(email=identifier) if '@' in identifier else User.objects.get(phone_number=identifier)
            if not check_password(password, user.password):
                print("Invalid credentials")
                return JsonResponse({"message": "Invalid credentials"}, status=401)
            return JsonResponse({"user": user.to_dict()})
        except User.DoesNotExist:
            print("User not found")
            return JsonResponse({"message": "Invalid credentials"}, status=401)

@csrf_exempt
def get_profile(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        return JsonResponse(user.to_dict())
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)

@csrf_exempt
def update_profile(request, user_id):
    if request.method == 'PUT':
        try:
            user = User.objects.get(pk=user_id)
            data = json.loads(request.body)
            
            if 'full_name' in data:
                user.full_name = data['full_name']
            if 'designation' in data:
                user.designation = data['designation']
            if 'company_name' in data:
                user.company_name = data['company_name']
            if 'phone_number' in data:
                if User.objects.filter(phone_number=data['phone_number']).exclude(pk=user_id).exists():
                    return JsonResponse({"message": "Phone number already in use"}, status=400)
                user.phone_number = data['phone_number']
            if 'password' in data:
                user.password = make_password(data['password'])
            
            user.save()
            return JsonResponse({"message": "Profile updated successfully", "user": user.to_dict()})
        except User.DoesNotExist:
            return JsonResponse({"message": "User not found"}, status=404)

from django.template import Template, Context
# ...existing imports...

def send_sms(email, context):
    subject = "Your OTP Code - Global Skills Park"
    email_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OTP Verification</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 600px;
            margin: 20px auto;
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            padding: 32px;
        }
        .header {
            text-align: center;
            padding-bottom: 24px;
            border-bottom: 1px solid #eaeaea;
            margin-bottom: 24px;
        }
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #3b82f6;
            margin-bottom: 16px;
        }
        .title {
            color: #1f2937;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        .otp-container {
            background-color: #f8fafc;
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            margin: 24px 0;
        }
        .otp {
            font-size: 32px;
            font-weight: bold;
            color: #3b82f6;
            letter-spacing: 4px;
        }
        .warning {
            font-size: 14px;
            color: #64748b;
            margin-top: 24px;
        }
        .details {
            background-color: #f8fafc;
            border-radius: 8px;
            padding: 16px;
            margin-top: 24px;
        }
        .details-title {
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 12px;
        }
        .detail-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            color: #4b5563;
        }
        .footer {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 32px;
            padding-top: 24px;
            border-top: 1px solid #eaeaea;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Seat Adoption Portal</div>
            <div class="title">OTP Verification</div>
        </div>
        
        <p>Dear {{ full_name }},</p>
        
        <p>Thank you for using our service. Please use the following OTP to verify your seat booking:</p>
        
        <div class="otp-container">
            <div class="otp">{{ otp }}</div>
        </div>

        <div class="details">
            <div class="details-title">Your Adoption Details:</div>
            <div class="detail-item">
                <span>Name:</span>
                <span>{{ full_name }}</span>
            </div>
            <div class="detail-item">
                <span>Email:</span>
                <span>{{ email }}</span>
            </div>
            <div class="detail-item">
                <span>Phone:</span>
                <span>{{ phone_number }}</span>
            </div>
            <div class="detail-item">
                <span>Company:</span>
                <span>{{ company_name }}</span>
            </div>
            <div class="detail-item">
                <span>Industry:</span>
                <span>{{ industry }}</span>
            </div>
        </div>

        <p class="warning">Please do not share this OTP with anyone.</p>

        <div class="footer">
            This is an automated message. Please do not reply to this email.
        </div>
    </div>
</body>
</html>
"""
    template = Template(email_template)
    html_message = template.render(Context(context))
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(
            subject,
            "",  # Plain text version - empty as we're using HTML
            from_email,
            recipient_list,
            html_message=html_message
        )
        return {"status": True, "message": "Email sent successfully"}
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@csrf_exempt
@require_POST
def generate_otp(request):
    data = json.loads(request.body)
    print('data ', data)
    
    # Extract user details and OTP method from the request
    user_data = data.get('email', {})
    print('email', user_data)
    is_resend = data.get('isResend', False)  
    otp_method = user_data.get('otpMethod', 'email')  # Get OTP method from request
    print('otp_method ', otp_method)
    
    # Get total_price from the correct location in user_data
    total_price = user_data.get('totalPrice', 0)
    print('total_price ', total_price)

    if is_resend:
        contact = user_data
        try:
            # Find billing based on the contact method used
            if otp_method == 'email':
                user = User.objects.filter(email=contact).first()
            else:
                user = User.objects.filter(phone_number=contact).first()

            if not user:
                return JsonResponse({"message": "User not found"}, status=404)

            billing = Billing.objects.filter(
                user=user,
                payment_status='pending'
            ).first()

            if not billing:
                return JsonResponse({"message": "No pending transaction found"}, status=404)

            otp = ''.join(random.choices(string.digits, k=6))
            billing.otp = otp
            billing.save()
            
            if otp_method == 'email':
                email_context = {
                    'otp': otp,
                    'full_name': user.full_name or 'User',
                    'email': user.email or contact,
                    'phone_number': user.phone_number or 'N/A',
                    'company_name': user.company_name or 'N/A',
                    'designation': user.designation or 'N/A',
                    'industry': user.industry or 'N/A',
                    'total_price': billing.total_price or 0
                }
                response = send_sms(contact, email_context)
            else:
                print('sending sms')
                response = send_sms_via_fast2sms(contact, otp, user.full_name or 'User')
            
            if not response["status"]:
                return JsonResponse({"message": f"Failed to send OTP: {response['message']}"}, status=500)
            
            # Mask the contact information
            masked_contact = (
                f"{'*' * (len(contact.split('@')[0]) - 2)}{contact[-2:]}@{contact.split('@')[1]}"
                if otp_method == 'email'
                else f"{'*' * 6}{contact[-4:]}"
            )
            return JsonResponse({
                "message": "OTP resent successfully",
                "contact": masked_contact
            })
            
        except Exception as e:
            print(f"Error in resend: {str(e)}")
            return JsonResponse({"message": str(e)}, status=500)
    
    # Regular OTP generation flow
    user_id = user_data.get('userId')
    email = user_data.get('email')
    phone = user_data.get('phone')
    full_name = user_data.get('fullName')
    company_name = user_data.get('company')
    designation = user_data.get('designation')
    industry = user_data.get('industry')
    selected_courses = user_data.get('selectedCourses', {})
    print('total_price ', total_price)
    
    # Validate required fields based on OTP method
    if otp_method == 'email' and not email:
        return JsonResponse({"message": "Email is required for email OTP"}, status=400)
    if otp_method == 'phone' and not phone:
        return JsonResponse({"message": "Phone number is required for SMS OTP"}, status=400)

    try:
        # Try to get existing user or create new one
        if otp_method == 'email':
            user = User.objects.filter(email=email).order_by('-created_at').first()
        else:
            user = User.objects.filter(phone_number=phone).order_by('-created_at').first()

        if user:
            # Update existing user
            user.full_name = full_name or user.full_name
            user.phone_number = phone or user.phone_number
            user.email = email or user.email
            user.company_name = company_name or user.company_name
            user.designation = designation or user.designation
            user.industry = industry or user.industry
        else:
            # Create new user
            user = User.objects.create(
                full_name=full_name or 'User',
                email=email,
                phone_number=phone,
                company_name=company_name or 'N/A',
                designation=designation or 'N/A',
                industry=industry or 'N/A'
            )
        user.save()
        
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Send OTP based on selected method
        if otp_method == 'email':
            email_context = {
                'otp': otp,
                'full_name': user.full_name or 'User',
                'email': user.email or email,
                'phone_number': user.phone_number or 'N/A',
                'company_name': user.company_name or 'N/A',
                'designation': user.designation or 'N/A',
                'industry': user.industry or 'N/A',
                'total_price': total_price
            }
            response = send_sms(email, email_context)
        else:
            response = send_sms_via_fast2sms(phone, otp, user.full_name or 'User')
        
        if not response["status"]:
            return JsonResponse({"message": f"Failed to send OTP: {response['message']}"}, status=500)
        
        billing = Billing.objects.create(
            user=user,
            payment_status='pending',
            selected_courses=selected_courses,
            total_price=total_price,
            otp=otp
        )
        
        # Mask contact based on OTP method
        contact = email if otp_method == 'email' else phone
        print('contact ', contact)
        print('email ', email)
        masked_contact = (
            f"{'*' * (len(contact.split('@')[0]) - 2)}{contact[-2:]}@{contact.split('@')[1]}"
            if otp_method == 'email'
            else f"{'*' * 6}{contact[-4:]}"
        )
        
        return JsonResponse({
            "message": "OTP sent successfully", 
            "contact": masked_contact
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({"message": str(e)}, status=500)

@csrf_exempt
@require_POST
def verify_otp(request):
    data = json.loads(request.body)
    print('data ', data)
    otp_method = data.get('otpMethod', 'email')  # Get OTP method from request
    contact = data.get('email') if otp_method == 'email' else data.get('phone')
    user_id = data.get('user_id')

    try:
        # Find the billing based on the OTP method used
        
        if otp_method == 'email':
            user = User.objects.filter(email=contact).order_by('-created_at').first()
        else:
            user = User.objects.filter(phone_number=contact).order_by('-created_at').first()

        if user_id and str(user.id) != str(user_id):
            return JsonResponse({"message": "User ID mismatch"}, status=400)
            
        billing = Billing.objects.filter(user=user, payment_status='pending').order_by('-created_at').first()
        print('billing ', billing.otp, data['otp'])
        sent_otp = data.get('otp')
        if isinstance(sent_otp, dict):
            sent_otp = sent_otp.get('otp')
        print('sent_otp ', sent_otp)
        if billing.otp != sent_otp:
            print('Invalid OTP',billing.otp,sent_otp)
            return JsonResponse({"message": "Invalid OTP"}, status=400)

        # Handle selected courses and verify OTP
        selected_courses = billing.selected_courses
        print('selected_courses ', selected_courses)
        if selected_courses:
            if isinstance(selected_courses, dict):
                for course_id, selection in selected_courses.items():
                    try:
                        course = Course.objects.get(pk=course_id)
                        required_seats = int(selection.get('selectedSeats', 0))
                        if course.left_seats >= required_seats:
                            course.left_seats -= required_seats
                            course.save()
                        else:
                            return JsonResponse({"message": f"Not enough seats available for {course.course_name}"}, status=400)
                    except Course.DoesNotExist:
                        return JsonResponse({"message": "Selected course does not exist"}, status=404)
            else:
                for selection in selected_courses:
                    try:
                        course_id = selection.get('course_id') or selection.get('id')
                        course = Course.objects.get(pk=course_id)
                        required_seats = int(selection.get('selectedSeats') or selection.get('seats', 0))
                        if course.left_seats >= required_seats:
                            course.left_seats -= required_seats
                            course.save()
                        else:
                            return JsonResponse({"message": f"Not enough seats available for {course.course_name}"}, status=400)
                    except Course.DoesNotExist:
                        return JsonResponse({"message": "Selected course does not exist"}, status=404)

        billing.is_verified = True
        billing.save()
        return JsonResponse({
            "message": "OTP verified successfully",
            "user": user.to_dict()
        })
    except User.DoesNotExist:
        return JsonResponse({"message": "User not found"}, status=404)
    except Billing.DoesNotExist:
        return JsonResponse({"message": "No pending transaction found"}, status=404)

@csrf_exempt
@require_POST
def process_payment(request):
    user_id = request.user.id
    data = json.loads(request.body)
    
    try:
        billing = Billing.objects.get(user_id=user_id, payment_status='pending')
        if not billing.is_verified:
            return JsonResponse({"message": "Please verify OTP before proceeding with payment"}, status=400)
        
        billing.payment_status = 'completed'
        billing.save()
        
        return JsonResponse({
            "message": "Payment processed successfully",
            "transaction_id": billing.id
        })
    except Billing.DoesNotExist:
        return JsonResponse({"message": "No pending transaction found"}, status=404)

def get_available_courses(request):
    courses = Course.objects.all()
    return JsonResponse([course.to_dict() for course in courses], safe=False)

@csrf_exempt
@require_POST
def select_courses(request):
    user_id = request.user.id
    data = json.loads(request.body)
    
    selected_courses = data.get('selected_courses', [])
    total_students = 0
    
    try:
        user = User.objects.get(pk=user_id)
        
        for selection in selected_courses:
            course = Course.objects.get(pk=selection['course_id'])
            seats_requested = selection['seats']
            
            if course.left_seats < seats_requested:
                return JsonResponse({"message": f"Not enough seats available for {course.course_name}"}, status=400)
                
            course.left_seats -= seats_requested
            total_students += seats_requested
        
        user.adopted_students += total_students
        user.save()
        return JsonResponse({"message": "Courses selected successfully", "total_students": total_students}, status=200)
    except Course.DoesNotExist:
        return JsonResponse({"message": "Course not found"}, status=404)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

def get_course_details(request, course_name):
    try:
        branches = Course.objects.filter(course_name=course_name)
        
        if not branches:
            return JsonResponse({'message': 'Course not found'}, status=404)
            
        branches_data = {}
        for branch in branches:
            branches_data[str(branch.id)] = {
                'name': branch.branch,
                'totalSeats': branch.total_seats,
                'leftSeats': branch.left_seats,
                'lockedSeats': branch.locked_seats
            }
            
        return JsonResponse({'branches': branches_data, 'pricePerSeat': branch.price_per_seat})
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
@require_POST
def generate_course_otp(request):
    user_id = request.user.id
    data = json.loads(request.body)
    
    try:
        user = User.objects.get(pk=user_id)
        
        if not user:
            return JsonResponse({'message': 'User not found'}, status=404)
            
        otp = str(random.randint(100000, 999999))
        user.otp = otp
        user.course_selections = json.dumps(data.get('selections'))
        user.save()
        
        # TODO: Send OTP via email/SMS
        
        return JsonResponse({'message': 'OTP generated successfully'})
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
@require_POST
def verify_course_otp(request):
    user_id = request.user.id
    data = json.loads(request.body)
    
    try:
        user = User.objects.get(pk=user_id)
        
        if not user:
            return JsonResponse({'message': 'User not found'}, status=404)
            
        submitted_otp = data.get('otp')
        
        if not submitted_otp or submitted_otp != user.otp:
            return JsonResponse({'message': 'Invalid OTP'}, status=400)
            
        user.otp = None
        user.save()
        
        return JsonResponse({'message': 'OTP verified successfully', 'selections': json.loads(user.course_selections)})
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

# NOTE : for testing data creation
@csrf_exempt
def update_multiple_courses(request):
    try:
        Course.objects.filter(course_name='B.Tech').update(price_per_seat=250000)
        Course.objects.filter(course_name='M.Tech').update(price_per_seat=300000)
        Course.objects.filter(course_name='Polytechnic').update(price_per_seat=150000, course_name='Diploma')
        Course.objects.filter(course_name='Diploma').update(price_per_seat=150000)
        Course.objects.filter(course_name='ITI').update(price_per_seat=100000)
        
        return JsonResponse({"message": "Courses updated successfully", "updated_courses": "B.Tech, M.Tech, Polytechnic, Diploma, ITI"}, status=200)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

@csrf_exempt
def get_courses_by_city(request, city_name):
    try:
        courses = Course.objects.filter(city=city_name)
        if not courses:
            return JsonResponse({"message": "No courses found in this city"}, status=404)
            
        courses_by_type = {}
        for course in courses:
            if course.course_name not in courses_by_type:
                courses_by_type[course.course_name] = {
                    'branches': [],
                    'price_per_seat': course.price_per_seat
                }
            courses_by_type[course.course_name]['branches'].append({
                'id': course.id,
                'name': course.branch,
                'totalSeats': course.total_seats,
                'leftSeats': course.left_seats,
                'lockedSeats': course.locked_seats
            })
        
        return JsonResponse({
            'city': city_name,
            'courses': courses_by_type
        })
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

@csrf_exempt
def get_cities_with_seats(request):
    try:
        cities = Course.objects.values('city').annotate(
            total_seats=models.Sum('total_seats'),
            available_seats=models.Sum('left_seats')
        )
        
        city_data = {
            city['city']: {
                'totalSeats': city['total_seats'],
                'availableSeats': city['available_seats']
            }
            for city in cities
        }
        
        return JsonResponse(city_data)
    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

import csv

@csrf_exempt
def populate_initial_data(request):
    try:
        courses = Course.objects.all()
        if courses:
            courses.delete()
            
        csv_file_path = os.path.join(os.path.dirname(__file__), 'final.csv')
        
        # Mapping for course name conversion from "Types of Institute"
        institute_conversion = {
            'Engineering': 'B.Tech',
            'ITI': 'ITI',
            'Diploma': 'Diploma',
            'B.Tech': 'B.Tech',
        }
        
        # Price mapping (if needed)
        price_mapping = {
            'B.Tech': 250000,  # 2.5 lakh
            'Diploma': 150000,  # 1.5 lakh
            'ITI': 100000       # 1 lakh
        }
        
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(f"Processing record: {row}")
                record_type = row.get('Type ', '').strip()
                # Filter only records with Type as Government or Govt. Aided
                if record_type not in ['Government', 'Govt. Aided']:
                    print(f"Skipping record with type: {record_type}")
                    continue
                print(f"Processing record with type: {record_type}")
                seats_val = row.get('Seats', '').strip()
                if not seats_val:
                    print(f"Missing seats for institute: {row.get('Institute Name', '')}")
                    continue
                try:
                    total_seats = int(seats_val)
                except ValueError:
                    print(f"Invalid seats value: {seats_val}")
                    continue

                types_inst = row.get('Types of Institute', '').strip()
                course_name = institute_conversion.get(types_inst, types_inst)
                
                city = row.get('Distrcit ', '').strip()
                institute_name = row.get('Institute Name', '').strip()
                branch = row.get('Trade/ Branch Name', '').strip()
                left_seats = total_seats  # locked_seats is 0
                
                new_course = Course(
                    course_name=course_name,
                    branch=branch.title(),
                    city=city.title(),
                    institute_name=institute_name.title(),
                    total_seats=total_seats,
                    locked_seats=0,
                    left_seats=left_seats,
                    price_per_seat=price_mapping.get(course_name, 0),
                    institute_type=record_type  # Type column value
                )
                new_course.save()
        # new data which is demanded added 
        new_csv_file_path = os.path.join(os.path.dirname(__file__), 'new_data.csv')
        with open(new_csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(f"Processing record: {row}")
                record_type = row.get('Type', '').strip()
                print(f"Processing record with type: {record_type}")
                seats_val = row.get('Seats', '').strip()
                if not seats_val:
                    print(f"Missing seats for institute: {row.get('Institute Name', '')}")
                    continue
                try:
                    total_seats = int(seats_val)
                except ValueError:
                    print(f"Invalid seats value: {seats_val}")
                    continue

                types_inst = row.get('Types of Institute', '').strip()
                course_name = institute_conversion.get(types_inst, types_inst)
                
                city = row.get('District', '').strip()
                institute_name = row.get('Institute Name', '').strip()
                branch = row.get('Trade/ Branch Name', '').strip()
                left_seats = total_seats  # locked_seats is 0
                
                new_course = Course(
                    course_name=course_name,
                    branch=branch.title(),
                    city=city.title(),
                    institute_name=institute_name.title(),
                    total_seats=total_seats,
                    locked_seats=0,
                    left_seats=left_seats,
                    price_per_seat=price_mapping.get(course_name, 0),
                    institute_type=record_type  # Type column value
                )
                new_course.save()
        return JsonResponse({"message": "Data populated successfully"}, status=200)
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return JsonResponse({"message": f"Error: {str(e)}", "error_type": type(e).__name__}, status=500)

@csrf_exempt
def generate_pdf(request):
    try:
        data = json.loads(request.body)
        user_data = data.get('userData', {})
        selected_courses = data.get('selectedCourses', {})

        # Format courses data for template with region grouping
        courses_by_region = {}
        total_amount = 0

        # Handle courses data whether it's a dictionary or list
        if isinstance(selected_courses, dict):
            for course_id, course in selected_courses.items():
                amount = float(course.get('totalPrice', 0))
                region = course.get('city', '')
                
                if region not in courses_by_region:
                    courses_by_region[region] = {
                        'courses': [],
                        'region_total': 0
                    }

                courses_by_region[region]['courses'].append({
                    'course_name': course.get('courseName'),
                    'institute_name': course.get('institute', ''),
                    'city': course.get('city', ''),
                    'branch': course.get('branch'),
                    'seats': course.get('selectedSeats'),
                    'price_per_seat': float(course.get('pricePerSeat', 0)),
                    'amount': amount
                })
                courses_by_region[region]['region_total'] += amount
                total_amount += amount

        # Group courses by course name within each region
        course_groups = {}
        for region, data_region in courses_by_region.items():
            for course in data_region['courses']:
                course_name = course['course_name']
                if course_name not in course_groups:
                    course_groups[course_name] = {
                        'regions': {},
                        'total': 0
                    }
                if region not in course_groups[course_name]['regions']:
                    course_groups[course_name]['regions'][region] = {
                        'courses': [],
                        'total': 0
                    }
                course_groups[course_name]['regions'][region]['courses'].append(course)
                course_groups[course_name]['regions'][region]['total'] += course['amount']
                course_groups[course_name]['total'] += course['amount']

        # Prepare context for template
        context = {
            'name': user_data.get('fullName'),
            'designation': user_data.get('designation'),
            'company': user_data.get('company'),
            'industry': user_data.get('industry'),
            'amount': f"₹{total_amount:,.2f}",
            'course_groups': course_groups,
            'date': datetime.now().strftime('%d-%m-%Y'),
            'document_id': f"ADT-{datetime.now().strftime('%Y%m%d')}-{os.urandom(4).hex().upper()}"
        }

        # Render HTML
        html_content = render_to_string('ticket_generated.html', context)

        # PDF generation options with improved styling support
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None,
            'enable-smart-shrinking': None,
            'dpi': '300',
            'load-error-handling': 'ignore',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'javascript-delay': '1000',
            'load-media-error-handling': 'ignore',
            'enable-external-links': True,
            'enable-internal-links': True,
            'images': True,
            'quiet': None,
            'footer-spacing': '5',
            'minimum-font-size': '8'
        }

        # Configure wkhtmltopdf path based on environment
        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe" if os.name == 'nt' else r"/usr/bin/wkhtmltopdf"
        )

        # Generate PDF with improved configuration and include stylesheet
        css_path = os.path.join(os.path.dirname(__file__), 'static', 'ticket.css')
        pdf = pdfkit.from_string(
            html_content, 
            False,
            options=options,
            css=css_path,
            configuration=config
        )

        # Create a descriptive filename for the PDF
        filename = f"SSRGSP_Adoption_Certificate_{datetime.now().strftime('%Y%m%d')}_{user_data.get('fullName', 'User').replace(' ', '_')}.pdf"

        # Attempt to send the PDF via email if an email address is provided
        user_email = user_data.get('email')
        if user_email:
            from django.core.mail import EmailMessage
            email_subject = f"""Seat Adoption Certificate of {user_data.get('fullName', 'User')}, {user_data.get('designation')}{user_data.get('company')} {user_data.get('industry')}"""
            email_body = "Please find attached your adoption certificate."
            email_msg = EmailMessage(email_subject, email_body, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER])
            email_msg.attach(filename, pdf, 'application/pdf')
            try:
                email_msg.send()
            except Exception as email_error:
                print(f"Failed to send PDF via email: {str(email_error)}")
                # Optionally, you might return an error or continue to return the PDF response

        # Return the PDF as a downloadable response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return JsonResponse({
            "message": "Failed to generate PDF", 
            "error": str(e)
        }, status=500)
        
        

import jwt
from datetime import datetime, timedelta


@csrf_exempt
def admin_login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)
        
    username = data.get('username')
    password = data.get('password')
    
    try:
        admin = AdoptionAdmin.objects.get(username=username)
        if check_password(password, admin.password):
            payload = {
                'admin_id': admin.id,
                'username': admin.username,
                'is_admin': True,
                'exp': datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
            
            return JsonResponse({
                'token': token,
                'message': 'Login successful'
            })
        else:
            return JsonResponse({'message': 'Invalid credentials'}, status=401)
    except AdoptionAdmin.DoesNotExist:
        return JsonResponse({'message': 'Invalid credentials'}, status=401)

@csrf_exempt
def admin_register(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)
        
    username = data.get('username')
    password = data.get('password')
    
    if AdoptionAdmin.objects.filter(username=username).exists():
        return JsonResponse({'message': 'Username already exists'}, status=400)
    
    admin = AdoptionAdmin.objects.create(
        username=username,
        password=make_password(password)
    )
    
    return JsonResponse({'message': 'Admin registered successfully'}, status=201)

@csrf_exempt
@admin_jwt_required
def get_admin_dashboard_data(request):
    if request.method != 'GET':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    try :
        billings = Billing.objects.all()
        users = User.objects.all()
        user_data = []
        billings_data = []
        for user in users:
            user_data.append(user.to_dict())
        
        for bill in billings:
            billings_data.append(bill.to_dict())
        
        return JsonResponse({
            'users': user_data,
            'billings': billings_data
        }, status=200)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

import pandas as pd
from io import BytesIO
from datetime import datetime
from .utils import admin_jwt_required

@csrf_exempt
@admin_jwt_required
def download_users_data(request):
    if request.method != 'GET':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        users = User.objects.all()
        data = []
        
        for user in users:
            user_data = {
                'User Details': {
                    'Full Name': user.full_name,
                    'Designation': user.designation,
                },
                'Contact': {
                    'Email': user.email,
                    'Phone Number': user.phone_number,
                },
                'Company Info': {
                    'Company Name': user.company_name,
                    'Industry': user.industry,
                },
                'Status': {
                    'Created At': user.created_at.strftime('%Y-%m-%d %H:%M'),
                    'Adopted Students': calculate_adopted_students(user),
                }
            }
            
            # Flatten the nested dictionary
            flat_data = {}
            for category, details in user_data.items():
                for key, value in details.items():
                    flat_data[f"{category} - {key}"] = value
            
            data.append(flat_data)
        
        df = pd.DataFrame(data)
        
        # Create Excel writer using xlsxwriter
        excel_file = BytesIO()
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Users', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Users']
            
            # Define format for headers
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4F46E5',
                'font_color': 'white',
                'border': 1
            })
            
            # Apply formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 20)
        
        excel_file.seek(0)
        
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=users-data-{datetime.now().strftime("%Y-%m-%d")}.xlsx'
        return response
        
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
@admin_jwt_required
def download_billings_data(request):
    if request.method != 'GET':
        return JsonResponse({'message': 'Method not allowed'}, status=405)
    
    try:
        billings = Billing.objects.all()
        data = []
        
        for billing in billings:
            billing_data = {
                'Order Info': {
                    'Order ID': f"#{billing.id}",
                    'Total Price': billing.total_price,
                },
                'Course Details': {},  # Will be filled for each course
                'Payment Status': {
                    'Payment': billing.payment_status,
                    'Verification': 'Verified' if billing.is_verified else 'Not Verified',
                },
                'Created At': billing.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            
            # Add course details
            for idx, course in enumerate(billing.selected_courses.values()):
                course_prefix = f"Course {idx + 1}"
                billing_data['Course Details'].update({
                    f"{course_prefix} - Name": course['courseName'],
                    f"{course_prefix} - Branch": course['branch'],
                    f"{course_prefix} - Institute": course['institute'],
                    f"{course_prefix} - City": course['city'],
                    f"{course_prefix} - Seats": course['selectedSeats'],
                    f"{course_prefix} - Price per Seat": course['pricePerSeat'],
                })
            
            # Flatten the nested dictionary
            flat_data = {}
            for category, details in billing_data.items():
                if isinstance(details, dict):
                    for key, value in details.items():
                        flat_data[f"{category} - {key}"] = value
                else:
                    flat_data[category] = details
            
            data.append(flat_data)
        
        df = pd.DataFrame(data)
        
        # Create Excel writer using xlsxwriter
        excel_file = BytesIO()
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Billings', index=False)
            
            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Billings']
            
            # Define format for headers
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4F46E5',
                'font_color': 'white',
                'border': 1
            })
            
            # Apply formatting
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 20)
        
        excel_file.seek(0)
        
        response = HttpResponse(
            excel_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=billings-data-{datetime.now().strftime("%Y-%m-%d")}.xlsx'
        return response
        
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)

def calculate_adopted_students(user):
    """Helper function to calculate adopted students for a user"""
    adopted = 0
    billings = Billing.objects.filter(user_id=user.id, is_verified=True)
    for billing in billings:
        for course in billing.selected_courses.values():
            adopted += course.get('selectedSeats', 0)
    return adopted