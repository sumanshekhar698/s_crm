from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import SignUpForm, AddRecordForm
from .models import Record


SORT_FIELDS = {
    'name': ('first_name', 'last_name'),
    'email': ('email',),
    'city': ('city',),
    'created': ('created_at', 'pk'),
}


def home(request):
    return render(request, 'home.html')


# @login_required sends logged-out visitors to settings.LOGIN_URL with ?next=<this page>
@login_required
def customers(request):
    records = Record.objects.all()

    query = request.GET.get('q', '').strip()
    if query:
        # Q objects combine conditions with | (OR); icontains is a case-insensitive "contains"
        records = records.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone__icontains=query)
            | Q(city__icontains=query)
        )

    # Only whitelisted keys reach order_by(), so the URL can't sort by arbitrary fields
    sort = request.GET.get('sort', '-created')
    if sort.lstrip('-') not in SORT_FIELDS:
        sort = '-created'
    direction = '-' if sort.startswith('-') else ''
    records = records.order_by(*[direction + field for field in SORT_FIELDS[sort.lstrip('-')]])

    return render(request, 'customers/dashboard.html', {'records': records, 'query': query, 'sort': sort})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('customers_home')

    next_url = request.POST.get('next') or request.GET.get('next', '')

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user is not None:
            auth_login(request, user)
            messages.success(request, "You Have Been Logged In!")
            # Only follow ?next= if it points back to this site, otherwise it is an open redirect
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('customers_home')

        messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'customers/login.html', {'next': next_url})


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


def logout_view(request):
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, "You have been logged out!")

    return redirect('home')


@login_required
def customer_record(request, pk):
    customer_record = get_object_or_404(Record, pk=pk)
    return render(request, 'customers/record.html', {'customer_record': customer_record})


@login_required
def delete_record(request, pk):
    record = get_object_or_404(Record, pk=pk)

    # Deleting only on POST stops a plain link, prefetch or another site from removing data
    if request.method != 'POST':
        return redirect('record', pk=pk)

    name = f"{record.first_name} {record.last_name}"
    record.delete()
    messages.success(request, f"{name} has been deleted.")
    return redirect('customers_home')


@login_required
def add_record(request):
    form = AddRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save()
        messages.success(request, f"{record.first_name} {record.last_name} has been added.")
        return redirect('record', pk=record.pk)

    return render(request, 'customers/add_record.html', {'form': form})


@login_required
def update_record(request, pk):
    current_record = get_object_or_404(Record, pk=pk)
    form = AddRecordForm(request.POST or None, instance=current_record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Customer details have been updated.")
        return redirect('customers_home')

    return render(request, 'customers/update_record.html', {'form': form, 'customer_record': current_record})
