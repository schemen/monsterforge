from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model, get_user
from django.contrib.auth.models import Group
from paperminis.models import Bestiary, Creature, CreatureQuantity
# Create your tests here.

class QuickViewTests(TestCase):
    """Testing basic view functionality"""
    def test_quickbuild(self):
        response = self.client.get('/quickbuild/')
        self.assertEqual(response.status_code, 200)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_CreatureView_anon(self):
        response = self.client.get('/creatures/')
        self.assertEqual(response.status_code, 302)

    def test_BestiaryView_anon(self):
        response = self.client.get('/bestiaries/')
        self.assertEqual(response.status_code, 302)

    def test_login_view(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_signup_view(self):
        response = self.client.get('/signup/')
        self.assertEqual(response.status_code, 200)


class AccountTests(TestCase):

    def setUp(self):
        self.email = 'testuser@email.com'
        self.password = 'MyPassword1234$'
        self.group = Group(name='temp')
        self.group.save()

    def test_signup_page_url(self):
        response = self.client.get("/signup/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='signup.html')

    def test_signup_page_view_name(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, template_name='signup.html')

    def test_signup_form(self):
        response = self.client.post(reverse('signup'), data={
            'email': self.email,
            'password1': self.password,
            'password2': self.password
        })
        self.assertEqual(response.status_code, 302)
        users = get_user_model().objects.all()
        self.assertEqual(users.count(), 1)


class AuthenticatedViewsTests(TestCase):

    def setUp(self):
        self.email = 'testuser@email.com'
        self.password = 'MyPassword1234$'
        self.group = Group(name='temp')
        self.group.save()
        self.user = get_user_model().objects.create_user(email=self.email, password=self.password)
        self.client.login(email=self.email, password=self.password)

    def test_BestiaryView_auth(self):
        response = self.client.get('/bestiaries/')
        self.assertEqual(response.status_code, 200)

    def test_CreatureView_auth(self):
        response = self.client.get('/creatures/')
        self.assertEqual(response.status_code, 200)


class BestiaryCreaturesTests(TestCase):

    def setUp(self):
        self.email = 'testuser@email.com'
        self.password = 'MyPassword1234$'
        self.group = Group(name='temp')
        self.group.save()
        self.user = get_user_model().objects.create_user(email=self.email, password=self.password)
        self.client.login(email=self.email, password=self.password)

    def test_create_bestiary(self):
        response = self.client.post(reverse('bestiary-create'), data={
            'name': "test bestiary",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Bestiary.objects.first().name, "test bestiary")
        self.assertEqual(Bestiary.objects.all().count(), 1)
        self.assertEqual(Bestiary.objects.first().owner, self.user)

    def test_create_creatures(self):
        response = self.client.post(reverse('creature-create'), data={
            'name': "test creature",
            'img_url': "https://i.imgur.com/lVe3YlI.jpg",
            'show_name': "true",
            'size': 'M',
            'position': 'bottom',
            'color': 'a9a9a9'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Creature.objects.first().name, "test creature")
        self.assertEqual(Creature.objects.all().count(), 1)
        self.assertEqual(Creature.objects.first().owner, self.user)

    def test_create_ddb_enc(self):
        response = self.client.post(reverse('ddb-enc-bestiary-create'), data={
            'ddb_enc_url': "https://www.dndbeyond.com/encounters/905d737c-b647-4885-b8bf-51c73ecd1231"
        })
        self.assertEqual(Creature.objects.all().count(), 10)
        self.assertEqual(Bestiary.objects.all().count(), 1)
        self.assertEqual(Bestiary.objects.first().name, "TEST-Forge ALL + Many")
