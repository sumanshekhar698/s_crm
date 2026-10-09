from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Record

class SignUpForm(UserCreationForm):
	first_name = forms.CharField(label="First name", max_length=100)
	last_name = forms.CharField(label="Last name", max_length=100)
	email = forms.EmailField(label="Email address")

	# field_order isn't an ordinary variable I made up. It's a setting Django looks for by that exact name on any form class.
	field_order = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		settings = {
			'username':   ('Username', 'Choose a username', 'username'),
			'first_name': ('First name', 'Enter your first name', 'given-name'),
			'last_name':  ('Last name', 'Enter your last name', 'family-name'),
			'email':      ('Email address', 'you@example.com', 'email'),
			'password1':  ('Password', 'Create a password', 'new-password'),
			'password2':  ('Confirm password', 'Repeat your password', 'new-password'),
		}
		for name, (label, placeholder, autocomplete) in settings.items():
			field = self.fields[name]
			field.label = label
			field.widget.attrs.update({
				'class': 'form-control',
				'placeholder': placeholder,
				'autocomplete': autocomplete,
			})

		self.fields['username'].help_text = 'Letters, digits and @/./+/-/_ only.'
		self.fields['password1'].help_text = 'At least 8 characters, not entirely numeric or too common.'
		self.fields['password2'].help_text = ''

	def clean_email(self):
		email = self.cleaned_data['email']
		if User.objects.filter(email__iexact=email).exists():
			raise forms.ValidationError('An account with this email already exists.')
		return email

	def full_clean(self):
		super().full_clean()
		for name in self.errors:
			if name in self.fields:
				css = self.fields[name].widget.attrs.get('class', '')
				self.fields[name].widget.attrs['class'] = f'{css} is-invalid'.strip()




# Create Add Record Form
class AddRecordForm(forms.ModelForm):
	email = forms.EmailField(label="Email address", max_length=100)

	class Meta:
		model = Record
		fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		settings = {
			'first_name': ('First name', 'e.g. Priya', 'given-name'),
			'last_name':  ('Last name', 'e.g. Sharma', 'family-name'),
			'email':      ('Email address', 'name@example.com', 'email'),
			'phone':      ('Phone', 'e.g. 98765 43210', 'tel'),
			'address':    ('Street address', 'House no., street, area', 'street-address'),
			'city':       ('City', 'e.g. Bengaluru', 'address-level2'),
			'state':      ('State', 'e.g. KA', 'address-level1'),
			'zipcode':    ('Zip code', 'e.g. 560001', 'postal-code'),
		}
		for name, (label, placeholder, autocomplete) in settings.items():
			field = self.fields[name]
			field.label = label
			field.widget.attrs.update({
				'class': 'form-control',
				'placeholder': placeholder,
				'autocomplete': autocomplete,
			})

	def full_clean(self):
		super().full_clean()
		for name in self.errors:
			if name in self.fields:
				css = self.fields[name].widget.attrs.get('class', '')
				self.fields[name].widget.attrs['class'] = f'{css} is-invalid'.strip()