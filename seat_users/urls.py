from django.urls import path
from .views import (
    register,
    login,
    get_profile,
    update_profile,
    generate_otp,
    verify_otp,
    process_payment,
    get_available_courses,
    select_courses,
    get_course_details,
    generate_course_otp,
    verify_course_otp,
    update_multiple_courses,
    get_cities_with_seats,
    get_courses_by_city,
    generate_pdf,
    populate_initial_data,
    admin_register,
    admin_login,
    get_admin_dashboard_data,
    download_users_data,
    download_billings_data
)

urlpatterns = [
    path('register', register, name='register'),
    path('login', login, name='login'),
    path('profile/<int:user_id>', get_profile, name='get_profile'),
    path('profile/update/<int:user_id>', update_profile, name='update_profile'),
    path('generate-otp', generate_otp, name='generate_otp'),
    path('verify-otp', verify_otp, name='verify_otp'),
    path('process-payment', process_payment, name='process_payment'),
    path('courses', get_available_courses, name='get_available_courses'),
    path('course/select', select_courses, name='select_courses'),
    path('course/<str:course_name>', get_course_details, name='get_course_details'),
    path('course/generate-otp', generate_course_otp, name='generate_course_otp'),
    path('course/verify-otp', verify_course_otp, name='verify_course_otp'),
    path('course/update-multiple', update_multiple_courses, name='update_multiple_courses'),
    path('cities', get_cities_with_seats, name='get_cities_with_seats'),
    path('city/<str:city_name>', get_courses_by_city, name='get_courses_by_city'),
    path('seats-by-city', get_cities_with_seats, name='get_seats_by_city'),  # Fixed endpoint
    path('generate-pdf', generate_pdf, name='generate_pdf'),  # Updated with trailing slash
    path('populate_initial_data', populate_initial_data, name='populate_initial_data'),
    path('admin_login',admin_login,name='admin_login'),
    path('admin_register',admin_register,name='admin_register'),
    path('get_admin_dashboard_data',get_admin_dashboard_data,name='get_admin_dashboard_data'),
    path('download/users', download_users_data, name='download_users_data'),
    path('download/billings', download_billings_data, name='download_billings_data')
]
