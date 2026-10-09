"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .forms import StyledPasswordResetForm, StyledSetPasswordForm

urlpatterns = [
    # path('',views.home,name='home'),# it means that when the user visits the root URL, the home function in the views.py file will be called.
  path('customers/',views.customers, name='customers_home'),# it means that when the user visits the customers URL, the home function in the views.py file will be called.
  path('customers/export/', views.export_csv, name='export_csv'),
  path('customers/import/', views.import_csv, name='import_csv'),
  path('',views.home, name='home'),
  path('login/', views.login_view, name='login'),
  path('signup/', views.signup_view, name='signup'),
  path('logout/', views.logout_view, name='logout'),

  # Password reset: Django's built-in views, our templates. The URL names are the ones Django expects.
  path('password-reset/', auth_views.PasswordResetView.as_view(
      template_name='customers/password_reset_form.html',
      email_template_name='customers/password_reset_email.txt',
      subject_template_name='customers/password_reset_subject.txt',
      form_class=StyledPasswordResetForm,
  ), name='password_reset'),
  path('password-reset/sent/', auth_views.PasswordResetDoneView.as_view(
      template_name='customers/password_reset_done.html',
  ), name='password_reset_done'),
  path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
      template_name='customers/password_reset_confirm.html',
      form_class=StyledSetPasswordForm,
  ), name='password_reset_confirm'),
  path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
      template_name='customers/password_reset_complete.html',
  ), name='password_reset_complete'),

  path('record/<int:pk>/', views.customer_record, name='record'),
  path('delete_record/<int:pk>/', views.delete_record, name='delete_record'),
  path('add_record/', views.add_record, name='add_record'),
  path('update_record/<int:pk>/', views.update_record, name='update_record'),

  path('record/<int:pk>/notes/add/', views.add_note, name='add_note'),
  path('notes/<int:pk>/delete/', views.delete_note, name='delete_note'),
]
