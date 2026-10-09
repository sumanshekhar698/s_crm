"""
Run with:  uv run python manage.py test customers

Django creates a separate test database (test_crm_db), runs every test inside a
transaction that is rolled back afterwards, and deletes the database at the end.
Your real data is never touched.
"""

import csv
import io
import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Note, Record


def make_record(owner, **overrides):
    """Create a Record with sensible defaults; pass keyword arguments to change any field."""
    fields = {
        'first_name': 'Priya', 'last_name': 'Sharma', 'email': 'priya@example.com',
        'phone': '9876543210', 'address': '12 MG Road', 'city': 'Bengaluru',
        'state': 'KA', 'zipcode': '560001', 'owner': owner,
    }
    fields.update(overrides)
    return Record.objects.create(**fields)


FORM_DATA = {
    'first_name': 'Arjun', 'last_name': 'Mehta', 'email': 'arjun@example.com',
    'phone': '12345', 'address': '1 Main St', 'city': 'Pune', 'state': 'MH',
    'zipcode': '411001', 'status': 'lead',
}


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Runs once for the whole class; each test still gets a clean copy
        cls.alice = User.objects.create_user('alice', email='alice@example.com', password='Alice-pass-123')
        cls.bob = User.objects.create_user('bob', email='bob@example.com', password='Bob-pass-123')
        cls.admin = User.objects.create_superuser('boss', email='boss@example.com', password='Boss-pass-123')
        cls.record = make_record(cls.alice)

    def login(self, user):
        self.client.force_login(user)


class AuthTests(BaseTestCase):

    def test_customers_page_requires_login(self):
        response = self.client.get(reverse('customers_home'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('customers_home')}")

    def test_login_with_correct_password(self):
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'Alice-pass-123'})
        self.assertRedirects(response, reverse('customers_home'))

    def test_login_with_wrong_password_shows_error(self):
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'nope'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_login_follows_safe_next_only(self):
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'Alice-pass-123', 'next': '/add_record/'})
        self.assertRedirects(response, '/add_record/')

        self.client.logout()
        response = self.client.post(reverse('login'), {'username': 'alice', 'password': 'Alice-pass-123', 'next': 'https://evil.example/'})
        self.assertRedirects(response, reverse('customers_home'))

    def test_logout_requires_post(self):
        self.login(self.alice)
        self.client.get(reverse('logout'))
        self.assertEqual(self.client.get(reverse('customers_home')).status_code, 200)

        self.client.post(reverse('logout'))
        self.assertEqual(self.client.get(reverse('customers_home')).status_code, 302)

    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'first_name': 'New', 'last_name': 'User', 'username': 'newbie', 'email': 'new@example.com',
            'password1': 'Str0ng-passw0rd!', 'password2': 'Str0ng-passw0rd!',
        })
        self.assertRedirects(response, reverse('customers_home'))
        self.assertTrue(User.objects.filter(username='newbie').exists())

    def test_signup_rejects_duplicate_email(self):
        response = self.client.post(reverse('signup'), {
            'first_name': 'Copy', 'last_name': 'Cat', 'username': 'copycat', 'email': 'ALICE@example.com',
            'password1': 'Str0ng-passw0rd!', 'password2': 'Str0ng-passw0rd!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='copycat').exists())


class RecordCrudTests(BaseTestCase):

    def setUp(self):
        self.login(self.alice)

    def test_detail_page(self):
        response = self.client.get(reverse('record', args=[self.record.pk]))
        self.assertContains(response, 'Priya Sharma')
        self.assertContains(response, 'mailto:priya@example.com')

    def test_missing_record_is_404(self):
        self.assertEqual(self.client.get(reverse('record', args=[99999])).status_code, 404)

    def test_add_record_sets_owner(self):
        response = self.client.post(reverse('add_record'), FORM_DATA)
        record = Record.objects.get(email='arjun@example.com')
        self.assertRedirects(response, reverse('record', args=[record.pk]))
        self.assertEqual(record.owner, self.alice)

    def test_add_record_validates_email(self):
        response = self.client.post(reverse('add_record'), {**FORM_DATA, 'email': 'not-an-email'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].has_error('email'))
        self.assertFalse(Record.objects.filter(first_name='Arjun').exists())

    def test_update_record(self):
        response = self.client.post(reverse('update_record', args=[self.record.pk]), {**FORM_DATA, 'city': 'Mysuru'})
        self.assertRedirects(response, reverse('customers_home'))
        self.record.refresh_from_db()
        self.assertEqual(self.record.city, 'Mysuru')

    def test_delete_needs_post(self):
        self.client.get(reverse('delete_record', args=[self.record.pk]))
        self.assertTrue(Record.objects.filter(pk=self.record.pk).exists())

        self.client.post(reverse('delete_record', args=[self.record.pk]))
        self.assertFalse(Record.objects.filter(pk=self.record.pk).exists())


class OwnershipTests(BaseTestCase):

    def test_other_users_cannot_see_or_change_a_record(self):
        self.login(self.bob)
        pk = self.record.pk
        self.assertEqual(self.client.get(reverse('record', args=[pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('update_record', args=[pk]), FORM_DATA).status_code, 404)
        self.assertEqual(self.client.post(reverse('delete_record', args=[pk])).status_code, 404)
        self.assertTrue(Record.objects.filter(pk=pk).exists())

    def test_list_only_shows_own_records(self):
        make_record(self.bob, first_name='Bobs', email='b@example.com')
        self.login(self.bob)
        names = [r.first_name for r in self.client.get(reverse('customers_home')).context['page_obj']]
        self.assertEqual(names, ['Bobs'])

    def test_superuser_sees_everything(self):
        make_record(self.bob, first_name='Bobs', email='b@example.com')
        self.login(self.admin)
        response = self.client.get(reverse('customers_home'))
        self.assertEqual(response.context['page_obj'].paginator.count, 2)


class CustomerListTests(BaseTestCase):

    def setUp(self):
        self.login(self.alice)

    def names(self, **params):
        response = self.client.get(reverse('customers_home'), params)
        return [r.first_name for r in response.context['page_obj']]

    def test_search_matches_name_email_and_city(self):
        make_record(self.alice, first_name='Zara', email='zara@example.com', city='Agra')
        self.assertEqual(self.names(q='zara'), ['Zara'])
        self.assertEqual(self.names(q='AGRA'), ['Zara'])
        self.assertEqual(self.names(q='nobody'), [])

    def test_sort_by_name_both_directions(self):
        make_record(self.alice, first_name='Aman', email='a@example.com')
        self.assertEqual(self.names(sort='name'), ['Aman', 'Priya'])
        self.assertEqual(self.names(sort='-name'), ['Priya', 'Aman'])

    def test_unknown_sort_falls_back_to_newest_first(self):
        make_record(self.alice, first_name='Newest', email='n@example.com')
        self.assertEqual(self.names(sort='password'), ['Newest', 'Priya'])

    def test_status_filter(self):
        make_record(self.alice, first_name='Active', email='act@example.com', status=Record.Status.ACTIVE)
        self.assertEqual(self.names(status='active'), ['Active'])
        self.assertEqual(len(self.names(status='bogus')), 2)

    def test_pagination(self):
        for i in range(15):
            make_record(self.alice, first_name=f'Cust{i:02d}', email=f'c{i}@example.com')
        response = self.client.get(reverse('customers_home'), {'page': 2})
        page = response.context['page_obj']
        self.assertEqual(page.paginator.count, 16)
        self.assertEqual(len(page.object_list), 6)
        # Out-of-range page numbers show the last page instead of an error
        self.assertEqual(self.client.get(reverse('customers_home'), {'page': 99}).context['page_obj'].number, 2)


class HomeStatsTests(BaseTestCase):

    def test_visitors_see_sample_data(self):
        response = self.client.get(reverse('home'))
        self.assertNotIn('stats', response.context)
        self.assertContains(response, 'Sample data')
        # The sample widget happens to use the name "Priya Sharma" too, so check the email instead
        self.assertNotContains(response, self.record.email)

    def test_signed_in_users_see_their_counts(self):
        make_record(self.bob, first_name='Bobs', email='b@example.com')
        self.login(self.alice)
        stats = self.client.get(reverse('home')).context['stats']
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['today'], 1)
        self.assertEqual(stats['by_status']['lead'], 1)


class NoteTests(BaseTestCase):

    def test_add_and_delete_note(self):
        self.login(self.alice)
        self.client.post(reverse('add_note', args=[self.record.pk]), {'body': 'Called today'})
        note = self.record.notes.get()
        self.assertEqual(note.author, self.alice)

        self.client.post(reverse('delete_note', args=[note.pk]))
        self.assertFalse(Note.objects.exists())

    def test_empty_note_is_rejected(self):
        self.login(self.alice)
        self.client.post(reverse('add_note', args=[self.record.pk]), {'body': '   '})
        self.assertFalse(Note.objects.exists())

    def test_other_users_cannot_add_notes(self):
        self.login(self.bob)
        response = self.client.post(reverse('add_note', args=[self.record.pk]), {'body': 'sneaky'})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Note.objects.exists())

    def test_notes_are_deleted_with_their_customer(self):
        Note.objects.create(record=self.record, author=self.alice, body='x')
        self.record.delete()
        self.assertFalse(Note.objects.exists())


class CsvTests(BaseTestCase):

    def setUp(self):
        self.login(self.alice)

    def upload(self, text, name='customers.csv'):
        file = SimpleUploadedFile(name, text.encode('utf-8'), content_type='text/csv')
        return self.client.post(reverse('import_csv'), {'file': file})

    def test_export(self):
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        rows = list(csv.reader(io.StringIO(response.content.decode('utf-8-sig'))))
        self.assertEqual(rows[0][:3], ['first_name', 'last_name', 'email'])
        self.assertEqual(rows[1][:2], ['Priya', 'Sharma'])

    def test_import_valid_rows(self):
        response = self.upload(
            'first_name,last_name,email,phone,address,city,state,zipcode,status\n'
            'Ana,One,ana@example.com,1,a,b,c,1,active\n'
        )
        self.assertRedirects(response, reverse('customers_home'))
        ana = Record.objects.get(first_name='Ana')
        self.assertEqual((ana.owner, ana.status), (self.alice, 'active'))

    def test_import_reports_bad_rows_by_line(self):
        response = self.upload(
            'first_name,last_name,email,phone,address,city,state,zipcode\n'
            'Good,Row,good@example.com,1,a,b,c,1\n'
            'Bad,Row,not-an-email,1,a,b,c,1\n'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['created'], 1)
        self.assertEqual(response.context['errors'][0][0], 3)

    def test_import_rejects_non_csv_files(self):
        response = self.upload('hello', name='notes.txt')
        self.assertTrue(response.context['form'].has_error('file'))


class PasswordResetTests(BaseTestCase):

    def test_full_reset_flow(self):
        self.client.post(reverse('password_reset'), {'email': 'alice@example.com'})
        self.assertEqual(len(mail.outbox), 1)

        link = re.search(r'https?://[^/]+(/reset/\S+/)', mail.outbox[0].body).group(1)
        set_password_url = self.client.get(link)['Location']
        response = self.client.post(set_password_url, {'new_password1': 'Brand-new-456!', 'new_password2': 'Brand-new-456!'})
        self.assertRedirects(response, reverse('password_reset_complete'))

        self.assertTrue(self.client.login(username='alice', password='Brand-new-456!'))

    def test_unknown_email_sends_nothing_but_looks_the_same(self):
        response = self.client.post(reverse('password_reset'), {'email': 'nobody@example.com'})
        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)


class ApiTests(BaseTestCase):

    def test_requires_authentication(self):
        self.assertEqual(self.client.get('/api/customers/').status_code, 403)

    def test_list_only_own_records(self):
        make_record(self.bob, first_name='Bobs', email='b@example.com')
        self.login(self.alice)
        data = self.client.get('/api/customers/').json()
        self.assertEqual([r['first_name'] for r in data['results']], ['Priya'])

    def test_create_sets_owner_and_validates(self):
        self.login(self.alice)
        response = self.client.post('/api/customers/', {**FORM_DATA, 'owner': 'bob'}, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['owner'], 'alice')

        response = self.client.post('/api/customers/', {**FORM_DATA, 'email': 'bad'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())

    def test_other_users_get_404(self):
        self.login(self.bob)
        self.assertEqual(self.client.get(f'/api/customers/{self.record.pk}/').status_code, 404)
        self.assertEqual(self.client.delete(f'/api/customers/{self.record.pk}/').status_code, 404)


class ClassBasedViewTests(BaseTestCase):

    def setUp(self):
        self.login(self.alice)

    def test_list_and_detail(self):
        self.assertContains(self.client.get(reverse('cbv:list')), 'Priya Sharma')
        self.assertContains(self.client.get(reverse('cbv:detail', args=[self.record.pk])), 'Priya Sharma')

    def test_create_sets_owner(self):
        self.client.post(reverse('cbv:add'), FORM_DATA)
        self.assertEqual(Record.objects.get(first_name='Arjun').owner, self.alice)

    def test_delete_shows_confirmation_then_deletes(self):
        url = reverse('cbv:delete', args=[self.record.pk])
        self.assertContains(self.client.get(url), 'Delete customer?')
        self.client.post(url)
        self.assertFalse(Record.objects.filter(pk=self.record.pk).exists())

    def test_other_users_get_404(self):
        self.login(self.bob)
        self.assertEqual(self.client.get(reverse('cbv:detail', args=[self.record.pk])).status_code, 404)
