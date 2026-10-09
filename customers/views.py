from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import SignUpForm, AddRecordForm
from .models import Record


SORT_FIELDS = {
    'name': ('first_name', 'last_name'),
    'email': ('email',),
    'city': ('city',),
    'created': ('created_at', 'pk'),
}

PER_PAGE = 10


def visible_records(user):
    """Superusers see every customer; everyone else only sees the customers they own."""
    if user.is_superuser:
        return Record.objects.all()
    return Record.objects.filter(owner=user)


def home(request):
    context = {}
    if request.user.is_authenticated:
        context['stats'] = customer_stats(visible_records(request.user))
    return render(request, 'home.html', context)


def customer_stats(records):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)

    this_month = records.filter(created_at__gte=month_start).count()
    last_month = records.filter(created_at__gte=last_month_start, created_at__lt=month_start).count()

    return {
        'total': records.count(),
        'today': records.filter(created_at__gte=today_start).count(),
        'this_week': records.filter(created_at__gte=now - timedelta(days=7)).count(),
        'this_month': this_month,
        'by_status': {value: records.filter(status=value).count() for value in Record.Status.values},
        # None means "no data last month", so the template can hide the growth badge
        'growth': round((this_month - last_month) / last_month * 100, 1) if last_month else None,
        'recent': records.order_by('-created_at', '-pk')[:3],
    }


# @login_required sends logged-out visitors to settings.LOGIN_URL with ?next=<this page>
@login_required
def customers(request):
    records = visible_records(request.user)

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

    # Count each status within the current search, before the status filter narrows it down
    status_counts = dict(records.values_list('status').annotate(n=Count('pk')))
    status_tabs = [('', 'All', sum(status_counts.values()))] + [
        (value, label, status_counts.get(value, 0)) for value, label in Record.Status.choices
    ]

    status = request.GET.get('status', '')
    if status in Record.Status.values:
        records = records.filter(status=status)
    else:
        status = ''

    # Only whitelisted keys reach order_by(), so the URL can't sort by arbitrary fields
    sort = request.GET.get('sort', '-created')
    if sort.lstrip('-') not in SORT_FIELDS:
        sort = '-created'
    direction = '-' if sort.startswith('-') else ''
    records = records.order_by(*[direction + field for field in SORT_FIELDS[sort.lstrip('-')]])

    # get_page() handles missing, non-numeric and out-of-range page numbers for us
    page_obj = Paginator(records, PER_PAGE).get_page(request.GET.get('page'))

    return render(request, 'customers/dashboard.html', {
        'page_obj': page_obj,
        'query': query,
        'sort': sort,
        'status': status,
        'status_tabs': status_tabs,
    })


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
    # Looking up inside visible_records() turns "someone else's customer" into a plain 404
    customer_record = get_object_or_404(visible_records(request.user), pk=pk)
    return render(request, 'customers/record.html', {'customer_record': customer_record})


@login_required
def delete_record(request, pk):
    record = get_object_or_404(visible_records(request.user), pk=pk)

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
        # commit=False builds the object without saving, so we can set fields the form doesn't show
        record = form.save(commit=False)
        record.owner = request.user
        record.save()
        messages.success(request, f"{record.first_name} {record.last_name} has been added.")
        return redirect('record', pk=record.pk)

    return render(request, 'customers/add_record.html', {'form': form})


@login_required
def update_record(request, pk):
    current_record = get_object_or_404(visible_records(request.user), pk=pk)
    form = AddRecordForm(request.POST or None, instance=current_record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Customer details have been updated.")
        return redirect('customers_home')

    return render(request, 'customers/update_record.html', {'form': form, 'customer_record': current_record})
