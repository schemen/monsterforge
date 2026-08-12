from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model, get_user
from django.contrib.auth.models import Group
from unittest.mock import patch
import numpy as np
from paperminis.generate_minis import MiniBuilder, crop_whitespace
from paperminis.models import Bestiary, Creature, CreatureQuantity, PrintSettings
# Create your tests here.


def _bordered_img(size=400, content=100):
    img = np.full((size, size, 3), 255, np.uint8)
    start = (size - content) // 2
    img[start:start + content, start:start + content] = (0, 0, 255)
    return img


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


class CropWhitespaceTests(TestCase):
    """Testing the whitespace cropping helper."""

    def test_crops_uniform_border(self):
        img = _bordered_img()
        out = crop_whitespace(img)
        self.assertLess(out.shape[0], img.shape[0])
        self.assertLess(out.shape[1], img.shape[1])

    def test_solid_image_unchanged(self):
        img = np.zeros((200, 200, 3), np.uint8)
        out = crop_whitespace(img)
        self.assertEqual(out.shape, img.shape)

    def test_tiny_content_unchanged(self):
        img = np.full((400, 400, 3), 255, np.uint8)
        img[200, 200] = (0, 0, 0)
        out = crop_whitespace(img)
        self.assertEqual(out.shape, img.shape)

    def test_tiny_image_unchanged(self):
        img = np.zeros((2, 2, 3), np.uint8)
        out = crop_whitespace(img)
        self.assertEqual(out.shape, img.shape)

    def test_content_at_or_above_ratio_is_cropped(self):
        out = crop_whitespace(_bordered_img(size=400, content=90))
        self.assertLess(out.shape[0], 400)

    def test_explicit_margin(self):
        out = crop_whitespace(_bordered_img(size=400, content=100), margin=5)
        self.assertEqual(out.shape, (110, 110, 3))

    def test_threshold(self):
        img = np.full((400, 400, 3), 255, np.uint8)
        start = 150
        img[start:start + 100, start:start + 100] = (245, 245, 245)
        # content differs from the white border by 10, below the default threshold
        self.assertEqual(crop_whitespace(img).shape, img.shape)
        # a lower threshold picks it up
        out = crop_whitespace(img, threshold=5)
        self.assertLess(out.shape[0], img.shape[0])

    def test_crop_margin_is_symmetric(self):
        out = crop_whitespace(_bordered_img(size=400, content=100))
        self.assertEqual(out.shape, (104, 104, 3))  # content + 2*margin on each side
        red = np.all(out == (0, 0, 255), axis=2)
        rows = np.nonzero(red.any(axis=1))[0]
        cols = np.nonzero(red.any(axis=0))[0]
        self.assertEqual(rows.min(), 2)
        self.assertEqual(out.shape[0] - 1 - rows.max(), 2)
        self.assertEqual(cols.min(), 2)
        self.assertEqual(out.shape[1] - 1 - cols.max(), 2)


class MiniBuilderCropTests(TestCase):
    """Testing that enabling whitespace cropping increases mini real estate."""

    def setUp(self):
        self.group = Group(name='temp')
        self.group.save()
        self.user = get_user_model().objects.create_user(email='test@email.com', password='MyPassword1234$')

    @patch('paperminis.generate_minis.download_image')
    def test_crop_flag_increases_content(self, mock_download):
        mock_download.return_value = _bordered_img()
        creature = Creature.objects.create(
            name="Test", owner=self.user,
            img_url="https://example.com/img.jpg",
            size="M", position="bottom", show_name=False,
        )

        builder = MiniBuilder()
        builder.load_settings(crop_whitespace=False)
        mini_no_crop = builder.build_mini(creature)

        builder = MiniBuilder()
        builder.load_settings(crop_whitespace=True)
        mini_crop = builder.build_mini(creature)

        self.assertIsInstance(mini_no_crop, np.ndarray)
        self.assertIsInstance(mini_crop, np.ndarray)
        self.assertEqual(mini_no_crop.shape[1], 240)
        self.assertEqual(mini_crop.shape[1], 240)

        red_no_crop = int(np.sum(np.all(mini_no_crop == (0, 0, 255), axis=2)))
        red_crop = int(np.sum(np.all(mini_crop == (0, 0, 255), axis=2)))
        self.assertGreater(red_crop, red_no_crop)

    @patch('paperminis.generate_minis.download_image')
    def test_rgba_png_flattened_before_crop(self, mock_download):
        img = np.zeros((400, 400, 4), np.uint8)
        img[:, :, :3] = 255  # white border, transparent (alpha 0)
        start = 100
        img[start:start + 200, start:start + 200, :3] = (0, 0, 255)  # red content
        img[start:start + 200, start:start + 200, 3] = 255  # opaque content
        mock_download.return_value = img
        creature = Creature.objects.create(
            name="Test", owner=self.user,
            img_url="https://example.com/img.png",
            size="M", position="bottom", show_name=False,
        )

        builder = MiniBuilder()
        builder.load_settings(crop_whitespace=False)
        mini_no_crop = builder.build_mini(creature)

        builder = MiniBuilder()
        builder.load_settings(crop_whitespace=True)
        mini_crop = builder.build_mini(creature)

        self.assertIsInstance(mini_no_crop, np.ndarray)
        self.assertIsInstance(mini_crop, np.ndarray)
        self.assertEqual(mini_crop.shape[1], 240)
        red_no_crop = int(np.sum(np.all(mini_no_crop == (0, 0, 255), axis=2)))
        red_crop = int(np.sum(np.all(mini_crop == (0, 0, 255), axis=2)))
        self.assertGreater(red_crop, red_no_crop)

    @patch('paperminis.generate_minis.download_image')
    def test_grayscale_image_cropped(self, mock_download):
        img = np.full((400, 400), 255, np.uint8)
        start = 100
        img[start:start + 200, start:start + 200] = 0
        mock_download.return_value = img
        creature = Creature.objects.create(
            name="Test", owner=self.user,
            img_url="https://example.com/img.jpg",
            size="M", position="bottom", show_name=False,
        )

        builder = MiniBuilder()
        builder.load_settings(crop_whitespace=False)
        mini_no_crop = builder.build_mini(creature)

        builder = MiniBuilder()
        builder.load_settings(crop_whitespace=True)
        mini_crop = builder.build_mini(creature)

        self.assertIsInstance(mini_no_crop, np.ndarray)
        self.assertIsInstance(mini_crop, np.ndarray)
        self.assertEqual(mini_crop.shape[1], 240)
        dark_no_crop = int(np.sum(np.all(mini_no_crop == 0, axis=2)))
        dark_crop = int(np.sum(np.all(mini_crop == 0, axis=2)))
        self.assertGreater(dark_crop, dark_no_crop)

    def test_printsettings_crop_whitespace_default(self):
        ps = PrintSettings.objects.create(user=self.user)
        self.assertFalse(ps.crop_whitespace)
        ps.crop_whitespace = True
        ps.save()
        ps.refresh_from_db()
        self.assertTrue(ps.crop_whitespace)
