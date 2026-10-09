from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, AddRecordForm
from .models import Record

# Create your views here.
def home(request):
    return render(request, 'home.html')
    # templates/customers/home.html


# @login_required
# def customers(request):
#     records = Record.objects.all()

#     return render(
#         request,
#         'customers/dashboard.html',
#         {'records': records}
#     )

def customers(request):
    records = Record.objects.all()
    # POST call
    # Check to see if logging in
    if request.method == 'POST':
        # username = request.POST.get('username')# get the username from the request.POST | None if not found in POST
        # password = request.POST.get('password')

        username = request.POST['username']# loud fail if username is not in the request.POST
        password = request.POST['password']
        # Authenticate
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, "You Have Been Logged In!")
            return redirect('customers_home')
        else:
            messages.success(request, "There Was An Error Logging In, Please Try Again...")
            return redirect('login')

    # GET call
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to view customers.")
        return redirect('login')

    return render(request, 'customers/dashboard.html', {'records': records})
    # templates/customers/dashboard.html



def login_view(request):
    return render(request, 'customers/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('customers_home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}! Your account has been created.")
            return redirect('customers_home')
    else:
        form = SignUpForm()

    return render(request, 'customers/signup.html', {'form': form})


# def logout_view(request):
#     auth_logout(request)
#     messages.success(request, "You Have Been Logged Out!")
#     return redirect('home')

def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, "You have been logged out!")
        return redirect('home')

    return redirect('home')


def customer_record(request, pk):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to view customers.")
        return redirect('login')

    customer_record = get_object_or_404(Record, pk=pk)
    return render(request, 'customers/record.html', {'customer_record': customer_record})


def delete_record(request, pk):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to manage customers.")
        return redirect('login')

    record = get_object_or_404(Record, pk=pk)

    # Deleting only on POST stops a plain link, prefetch or another site from removing data
    if request.method != 'POST':
        return redirect('record', pk=pk)

    name = f"{record.first_name} {record.last_name}"
    record.delete()
    messages.success(request, f"{name} has been deleted.")
    return redirect('customers_home')


def add_record(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to manage customers.")
        return redirect('login')

    form = AddRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save()
        messages.success(request, f"{record.first_name} {record.last_name} has been added.")
        return redirect('record', pk=record.pk)

    return render(request, 'customers/add_record.html', {'form': form})


def update_record(request, pk):
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to manage customers.")
        return redirect('login')

    current_record = get_object_or_404(Record, pk=pk)
    form = AddRecordForm(request.POST or None, instance=current_record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Customer details have been updated.")
        return redirect('customers_home')

    return render(request, 'customers/update_record.html', {'form': form, 'customer_record': current_record})
