"""
Class-based versions of the customer pages in views.py.

Compare each class with its function in views.py: Django's generic views already
know how to list, show, create, update and delete a model, so we only write what's
specific to this app (which records a user can see, who owns new records, and where
to go afterwards).
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AddRecordForm
from .models import Record
from .views import PER_PAGE, search_records, visible_records


class OwnedRecordMixin(LoginRequiredMixin):
    """Shared by every view below: login required, and only the user's own customers."""
    model = Record

    def get_queryset(self):
        return visible_records(self.request.user)


class RecordListView(OwnedRecordMixin, ListView):
    template_name = 'customers/cbv/record_list.html'   # default would be customers/record_list.html
    paginate_by = PER_PAGE                               # gives the template page_obj, like Paginator in views.py

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        return search_records(super().get_queryset(), query).order_by('-created_at', '-pk')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        return context


class RecordDetailView(OwnedRecordMixin, DetailView):
    template_name = 'customers/cbv/record_detail.html'
    context_object_name = 'customer_record'   # default name would be "record" (or "object")


class RecordCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Record
    form_class = AddRecordForm
    template_name = 'customers/cbv/record_form.html'
    success_message = "%(first_name)s %(last_name)s has been added."

    def form_valid(self, form):
        # Same idea as form.save(commit=False) in views.add_record
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('cbv:detail', kwargs={'pk': self.object.pk})


class RecordUpdateView(OwnedRecordMixin, SuccessMessageMixin, UpdateView):
    form_class = AddRecordForm
    template_name = 'customers/cbv/record_form.html'
    context_object_name = 'customer_record'
    success_message = "Customer details have been updated."
    success_url = reverse_lazy('cbv:list')


class RecordDeleteView(OwnedRecordMixin, DeleteView):
    # GET shows a confirmation page; POST deletes. views.delete_record uses a JS confirm() instead.
    template_name = 'customers/cbv/record_confirm_delete.html'
    context_object_name = 'customer_record'
    success_url = reverse_lazy('cbv:list')

    def form_valid(self, form):
        messages.success(self.request, f"{self.object.first_name} {self.object.last_name} has been deleted.")
        return super().form_valid(form)
