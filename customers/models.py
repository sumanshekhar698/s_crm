from django.conf import settings
from django.db import models

# Create your models here.
class Record(models.Model):

	class Status(models.TextChoices):
		# value stored in the database, label shown to users
		LEAD = 'lead', 'Lead'
		ACTIVE = 'active', 'Active'
		INACTIVE = 'inactive', 'Inactive'

	created_at = models.DateTimeField(auto_now_add=True)
	first_name = models.CharField(max_length=50)
	last_name =  models.CharField(max_length=50)
	email =  models.CharField(max_length=100)
	phone = models.CharField(max_length=15)
	address =  models.CharField(max_length=100)
	city =  models.CharField(max_length=50)
	state =  models.CharField(max_length=50)
	zipcode =  models.CharField(max_length=20)
	status = models.CharField(max_length=10, choices=Status.choices, default=Status.LEAD)
	# null=True lets rows that existed before this field was added be migrated, then filled in by 0004
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='records',
		null=True,
		blank=True,
	)

	def __str__(self):
		return(f"{self.first_name} {self.last_name}")


class Note(models.Model):
	# related_name='notes' lets us write record.notes.all() instead of record.note_set.all()
	record = models.ForeignKey(Record, on_delete=models.CASCADE, related_name='notes')
	author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
	body = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at', '-pk']

	def __str__(self):
		return f"Note on {self.record} ({self.created_at:%Y-%m-%d})"
