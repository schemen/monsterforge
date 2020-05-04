from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
import uuid
from constrainedfilefield.fields import ConstrainedFileField

# Create your models here.

# New User without name
from django.contrib.auth.models import AbstractUser, BaseUserManager ## A new class is imported. ##
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """User model."""

    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager() ## This is the new line in the User model. ##

class Creature(models.Model):
    """Model for Creatures"""

    # Size
    TINY = 'T'
    SMALL = 'S'
    MEDIUM = 'M'
    LARGE = 'L'
    HUGE = 'H'
    GARGANTUAN = 'G'

    CREATURE_SIZE_CHOICES =(
        (TINY, 'Tiny'),
        (SMALL, 'Small'),
        (MEDIUM, 'Medium'),
        (LARGE, 'Large'),
        (HUGE, 'Huge'),
        (GARGANTUAN, 'Gargantuan')
    )

    # Base Color
    GREEN = '228b22'
    RED = 'aa3939'
    BLUE = '005b96'
    LIGHTGRAY = 'd3d3d3'
    DARKGRAY = 'a9a9a9'
    BLACK = '000000'
    WHITE = 'ffffff'

    COLOR_CHOICES = (
        (GREEN, 'Green'),
        (RED, 'Red'),
        (BLUE, 'Blue'),
        (LIGHTGRAY, 'Light Gray'),
        (DARKGRAY, 'Dark Gray'),
        (BLACK, 'Black'),
        (WHITE, 'White')
    )

    # Alignment
    FLYING = 'top'
    HOVERING = 'center'
    WALKING = 'bottom'

    POSITION_CHOICES = (
        (FLYING, 'Flying (Top)'),
        (HOVERING, 'Hovering (Middle)'),
        (WALKING, 'Walking (Bottom)')
    )

    # Creature Type
    UNDEFINED = 'undefined'
    ABERRATION = 'aberration'
    BEAST = 'beast'
    CELESTIAL = 'celestial'
    CONSTRUCT = 'construct'
    DRAGON = 'dragon'
    ELEMENTAL = 'elemental'
    FEY = 'fey'
    FIEND = 'fiend'
    GIANT = 'giant'
    HUMANOID = 'humanoid'
    MONSTROSITY = 'monstrosity'
    OOZE = 'ooze'
    PLANT = 'plant'
    UNDEAD = 'undead'
    TYPE1 = 'type1'
    TYPE2 = 'type2'
    TYPE3 = 'type3'
    TYPE4 = 'type4'

    CREATURE_TYPE_CHOICES = (
        (UNDEFINED, 'Undefined'),
        (ABERRATION, 'Aberration'),
        (BEAST, 'Beast'),
        (CELESTIAL, 'Celestial'),
        (CONSTRUCT, 'Construct'),
        (DRAGON, 'Dragon'),
        (ELEMENTAL, 'Elemental'),
        (FEY, 'Fey'),
        (FIEND, 'Fiend'),
        (GIANT, 'Giant'),
        (HUMANOID, 'Humanoid'),
        (MONSTROSITY, 'Monstrosity'),
        (OOZE, 'Ooze'),
        (PLANT, 'Plant'),
        (UNDEAD, 'Undead'),
        (TYPE1, 'Type 1'),
        (TYPE2, 'Type 2'),
        (TYPE3, 'Type 3'),
        (TYPE4, 'Type 4'),
    )

    # fields
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    img_url = models.TextField(max_length=500)
    size = models.CharField(max_length=1, choices=CREATURE_SIZE_CHOICES, default=MEDIUM)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    color = models.CharField(max_length=6, choices=COLOR_CHOICES, default=DARKGRAY)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, default=WALKING)
    show_name = models.BooleanField(default=True)
    creature_type = models.CharField(max_length=100, choices=CREATURE_TYPE_CHOICES, default=UNDEFINED)
    CR = models.FloatField(default=0)


    # Metadata
    class Meta:
        ordering = ['name']

    # Methods
    def get_absolute_url(self):
        """Returns the url to access a particular instance of Creature."""
        return reverse('creature-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Creature object (in Admin site etc.)."""
        return self.name



class Bestiary(models.Model):
    """Bestiary Model"""

    # fields
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    creatures = models.ManyToManyField(Creature, through='CreatureQuantity',
                                      help_text='A list of creatures belonging to this bestiary.')
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Bestiaries"


    def get_absolute_url(self):
        """Returns the url to access a particular instance of Bestiary."""
        return reverse('bestiary-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Bestiary object (in Admin site etc.)."""
        return self.name

class CreatureQuantity(models.Model):
    """Model to link bestiary with a quantity of creatures. "owner" is technically not needed
    (since it should be the same as owner of the bestiary), but adds another layer of security."""
    creature = models.ForeignKey(Creature, on_delete=models.CASCADE)
    bestiary = models.ForeignKey(Bestiary, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class PrintSettings(models.Model):
    """Save the print settings for each user"""

    # paper format
    A4 = 'a4'
    A3 = 'a3'
    LETTER = 'letter'
    LEGAL = 'legal'
    TABLOID = 'tabloid'
    PAPER_FORMAT_CHOICES = (
        (A4, 'A4'),
        (A3, 'A3'),
        (LETTER, 'Letter'),
        (LEGAL, 'Legal'),
        (TABLOID, 'Tabloid')
    )
    # grid size
    GRID24 = 24
    GRID18 = 18
    GRID12 = 12
    GRID_SIZE_CHOICES = (
        (GRID24, '24 mm ~ 1 inch'),
        (GRID18, '18 mm ~ 3/4 inch'),
        (GRID12, '12 mm ~ 1/2 inch')
    )
    # base shape
    SQUARE = 'square'
    HEXAGONAL = 'hexagon'
    CIRCLE = 'circle'
    BASE_SHAPE_CHOICES = (
        (SQUARE, 'Square'),
        (HEXAGONAL, 'Hexagon'),
        (CIRCLE, 'Circle')
    )

    # Name behaviour
    NO_FORCE = 'no_force'
    FORCE_NAME = 'force_name'
    FORCE_BLANK = 'force_blank'
    NAME_BEHAVIOUR_CHOICES = (
        (NO_FORCE, 'Leave it to the Creature (default)'),
        (FORCE_NAME, 'Force printing of all names'),
        (FORCE_BLANK, 'Force printing no names')
    )

    # fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper_format = models.CharField(max_length=50, choices=PAPER_FORMAT_CHOICES, default=A4)
    grid_size = models.IntegerField(choices=GRID_SIZE_CHOICES, default=GRID24)
    base_shape = models.CharField(max_length=50, choices=BASE_SHAPE_CHOICES, default=SQUARE)
    enumerate = models.BooleanField(default=False)
    force_name = models.CharField(max_length=50, choices=NAME_BEHAVIOUR_CHOICES, default=NO_FORCE)
    fixed_height = models.BooleanField(default=False)
    darken = models.IntegerField(default=0)
