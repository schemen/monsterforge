import json
import logging
import uuid
from urllib.parse import urljoin, urlparse

import requests
from django import template
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.forms import formset_factory
from django.http import (FileResponse, Http404, HttpResponseRedirect)
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from paperminis.forms import (DDBEncounterBestiaryCreate, PrintForm, QuantityForm,
                              SignUpForm, UploadFileForm, UserDeleteForm, QuickCreateSettingsForm,
                              QuickCreateCreatureForm)
from paperminis.generate_minis import MiniBuilder
from paperminis.models import Bestiary, Creature, CreatureQuantity, PrintSettings, User
from paperminis.utils import handle_json, quick_validate_creature

register = template.Library()

logger = logging.getLogger("django")


@register.filter(name='has_group')
def has_group(user, group_name):
    """Function to check Patreon status in templates."""
    group = Group.objects.get(name=group_name)
    return group in user.groups.all()


def signup(request):
    """To register new users."""
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('index'))
    else:
        if request.method == 'POST':
            form = SignUpForm(request.POST)
            if form.is_valid():
                form.save()
                email = form.cleaned_data.get('email')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(email=email, password=raw_password)
                login(request, user)
                logger.info("New user created! Email: %s" % email)
                return HttpResponseRedirect(reverse('index'))
        else:
            form = SignUpForm()
        return render(request, 'signup.html', {'form': form})


def temp_account(request):
    """Create temporary account."""
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('index'))
    else:
        if request.method == 'POST':
            # generate random username and password
            password = make_password(str(uuid.uuid4()))
            email = uuid.uuid4()
            user = User(email=email, password=password)
            user.save()
            # add to group 'temp'
            temp_grp = Group.objects.get(name='temp')
            temp_grp.user_set.add(user)
            # log the user in (this can never be done manually)
            login(request, user)
            logger.info("New temp user created! Email: %s" % email)
            return render(request, 'temp_account.html')

        return reverse('signup')


@login_required()
def profile(request):
    """A user profile view"""
    return render(request, 'profile.html')


def quickbuild(request):
    """Quickbuilder"""
    anon_max = 5
    auth_max = 1000
    settings_form = QuickCreateSettingsForm(prefix='settings')

    if request.user.is_authenticated:
        creature_formset = formset_factory(QuickCreateCreatureForm, max_num=1000, absolute_max=1000)
        qs = Creature.objects.filter(owner=request.user)
        max_forms = auth_max
    else:
        creature_formset = formset_factory(QuickCreateCreatureForm, max_num=10, absolute_max=10)
        qs = None
        max_forms = anon_max

    if request.method == 'POST':
        formset = creature_formset(request.POST, prefix='creatures')
        settings_form = QuickCreateSettingsForm(request.POST, prefix='settings')

        logger.info("Received Quickbuild request!")

        if settings_form.is_valid() and formset.is_valid():
            logger.info("Settings:")
            logger.info(settings_form.cleaned_data)
            logger.info("Creatures:")
            for form in formset:
                logger.info(form.cleaned_data)

            creatures = []
            failed_creatures = []

            if request.user.is_authenticated:
                forms = formset[0:auth_max]
            else:
                forms = formset[0:anon_max]

            for form in forms:
                i = form.cleaned_data
                if i:
                    try:
                        creature = quick_validate_creature(i)
                        creatures.append(creature)
                    except ValueError as e:
                        failed_creatures.append(str(e))
                        logger.warning(e)

            minis = MiniBuilder()
            minis.load_settings(paper_format=settings_form.cleaned_data["paper_format"],
                                grid_size=int(settings_form.cleaned_data["grid_size"]),
                                base_shape=settings_form.cleaned_data["base_shape"],
                                enumerate=settings_form.cleaned_data["enumerate"],)
            minis.add_quick_creatures(creatures)
            archive = minis.build_all_and_pdf()
            # serve file
            archive.seek(0)
            logger.info("Finished Quickbuild, serving now.")

            # Clean bestiary name
            return FileResponse(archive, as_attachment=True, filename="Monsterforge_Quickbuilder.pdf")

    creature = creature_formset(prefix='creatures')
    context = {'qs': qs, 'creature_formset': creature, 'settings_form': settings_form, 'max_forms': max_forms}
    return render(request, 'quickbuild.html', context=context)


@login_required()
def delete_account(request):
    if request.method == 'POST':
        form = UserDeleteForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            logger.info("User deleted it's account! Email: %s" % user.email)
            user.delete()
            logout(request)
            return render(request, 'delete_account_done.html')
    else:
        form = UserDeleteForm(user=request.user)
    """A user profile view"""
    return render(request, 'delete_account_confirm.html', {'form': form})


@login_required()
def convert_account(request):
    """Convert temporary account to full account."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # validation should take care of any issues like duplicate email
            # update user info
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = request.user
            user.email = email
            user.password = make_password(raw_password)
            user.save()
            # remove from temp group
            temp_grp = Group.objects.get(name='temp')
            temp_grp.user_set.remove(user)
            login(request, user)
            logger.info("Temporary user converted to full user: %s" % user.id)
            return HttpResponseRedirect(reverse('index'))
    else:
        form = SignUpForm()
    return render(request, 'convert.html', {'form': form})


@login_required()
def json_upload(request):
    """Upload view and form handling."""
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():  # validation happens in forms.py
            result = int(handle_json(request.FILES, request.user))
            if result == -1:
                request.session['upload_error'] = 'Invalid File'
            elif result > 0:
                request.session['skipped'] = result
            else:
                request.session['success'] = True
            return HttpResponseRedirect(reverse('creatures'))
    else:
        form = UploadFileForm()
    return render(request, 'json_form.html', {'form': form})


def index(request):
    """View function for home page."""

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html')


class CreatureDetailView(LoginRequiredMixin, generic.DetailView):
    """Generic creature detail page."""
    model = Creature

    def get_queryset(self):
        return Creature.objects.filter(owner=self.request.user)


class CreatureByUserListView(LoginRequiredMixin, generic.ListView):
    """Generic creatures by user list view."""
    model = Creature

    # paginate_by = 2 # pagination doesn't work with the current filter system and is not needed anyways

    def get_queryset(self):
        return Creature.objects.filter(owner=self.request.user).order_by('name')

    def get_context_data(self, **kwargs):
        context = super(CreatureByUserListView, self).get_context_data(**kwargs)
        context['skipped'] = self.request.session.pop('skipped', None)
        context['upload_error'] = self.request.session.pop('upload_error', None)
        context['success'] = self.request.session.pop('success', None)
        return context


class BestiaryDetailView(LoginRequiredMixin, generic.DetailView):
    """Generic bestiary detail view."""
    model = Bestiary

    def get_queryset(self):
        # get sum of creatures in there
        return Bestiary.objects.filter(owner=self.request.user).annotate(
            total_creatures=Sum('creaturequantity__quantity'))


@login_required()
def bestiary_print(request, pk):
    # validation and proper redirects
    bestiary = Bestiary.objects.filter(owner=request.user, id=pk).first()
    if not bestiary:
        return HttpResponseRedirect(reverse('bestiaries'))
    elif bestiary.creatures.count() <= 0:
        return HttpResponseRedirect(reverse('bestiary-detail', kwargs={'pk': pk}))

    # load print settings
    print_settings = PrintSettings.objects.filter(user=request.user)
    if not print_settings:
        print_settings = PrintSettings(user=request.user)
        print_settings.save()
    else:
        print_settings = print_settings.first()

    if request.method == 'POST':
        user = request.user
        formset = PrintForm(request.POST)
        if formset.is_valid():
            logger.info("Building minis from bestiary %s for user with ID %s..." % (pk, user.id))
            minis = MiniBuilder(user=request.user)
            # update settings
            new_settings = formset.save(commit=False)

            print_settings.paper_format = new_settings.paper_format
            print_settings.grid_size = new_settings.grid_size
            print_settings.base_shape = new_settings.base_shape
            print_settings.enumerate = new_settings.enumerate
            print_settings.force_name = new_settings.force_name
            print_settings.fixed_height = new_settings.fixed_height
            print_settings.darken = new_settings.darken
            print_settings.save()
            # load settings into the mini builder
            minis.load_settings(paper_format=print_settings.paper_format,
                                grid_size=print_settings.grid_size,
                                base_shape=print_settings.base_shape,
                                enumerate=print_settings.enumerate,
                                force_name=print_settings.force_name,
                                fixed_height=print_settings.base_shape,
                                darken=print_settings.darken)
            # load creatures into the mini builder
            minis.add_bestiary(request.user, pk)
            # build minis
            archive = minis.build_all_and_pdf()
            # serve file
            archive.seek(0)
            logger.info("Finished building, serving now.")

            # Clean bestiary name
            name = minis.sanitize.sub('', bestiary.name)
            return FileResponse(archive, as_attachment=True, filename=name + "_forged.pdf")

    # seed form with loaded settings
    form = PrintForm(initial=print_settings.__dict__)

    return render(request, 'bestiary_print.html', {'form': form})


@login_required()
def bestiary_unlink(request, pk, ci=None):
    """Unlink all (ci=None) or a specific creature (id=ci) from a bestiary """
    bestiary = Bestiary.objects.filter(owner=request.user, id=pk).first()
    if ci:
        creature = Creature.objects.filter(owner=request.user, id=ci).first()
        # Get the CreatureQuantity object that describes the link
        obj = CreatureQuantity.objects.filter(bestiary=bestiary, creature=creature, owner=request.user)
        if len(obj) == 1:
            # and delete it
            obj.delete()
    else:
        bestiary.creatures.clear()
    return HttpResponseRedirect(reverse('bestiary-detail', kwargs={'pk': pk}))


@login_required()
def bestiary_link(request, pk):
    """Link creatures to a bestiary.
    This function is a bit of a mess. Happy to recieve a proper implementation of this!
    The validation might be unsatisfying too."""

    qs = Creature.objects.filter(owner=request.user)
    formset = QuantityForm()
    if request.method == 'POST':
        formset = QuantityForm(request.POST)
        bestiary = Bestiary.objects.filter(owner=request.user, id=pk).first()
        mgmt = ['csrfmiddlewaretoken', 'form-TOTAL_FORMS', 'form-INITIAL_FORMS', 'form-MIN_NUM_FORMS',
                'form-MAX_NUM_FORMS']
        for id, q in request.POST.items():
            if id in mgmt:
                continue
            try:
                if not q: q = 0
                q = int(q)
            except:
                raise ValidationError('Only use numbers please.')
            if q <= 0:
                continue

            try:
                creature = Creature.objects.filter(owner=request.user, id=id)[0]
            except:
                continue

            quantity_obj = CreatureQuantity.objects.filter(creature=creature, bestiary=bestiary,
                                                           owner=request.user).first()
            # update or create
            if quantity_obj:
                quantity_obj.quantity = q
            else:
                quantity_obj = CreatureQuantity(creature=creature, bestiary=bestiary, owner=request.user, quantity=q)
            # save
            quantity_obj.save()
        logger.info("Expanded bestiary %s %s from user %s with new creatures!" % (
            bestiary.id, bestiary.name, bestiary.owner.id))
        return HttpResponseRedirect(reverse('bestiary-detail', kwargs={'pk': pk}))

    else:
        context = {'qs': qs, 'formset': formset, 'form': formset}
        return render(request, 'bestiary_link.html', context=context)


class BestiaryListView(LoginRequiredMixin, generic.ListView):
    """Generic Bestiary list view."""
    model = Bestiary

    def get_queryset(self):
        # ok = Bestiary.objects.filter(owner=self.request.user).values('name', 'creaturequantity__quantity').aggregate(total_creatures=Sum('creaturequantity__quantity'))
        return Bestiary.objects.filter(owner=self.request.user).values('name', 'id').annotate(
            total_creatures=Sum('creaturequantity__quantity'))


from .forms import BestiaryModifyForm, CreatureModifyForm


# Creature Forms
class CreatureCreate(LoginRequiredMixin, CreateView):
    """Generic create view."""
    model = Creature
    initial = {'size': Creature.MEDIUM, 'color': Creature.DARKGRAY, 'position': Creature.WALKING, 'show_name': True}
    form_class = CreatureModifyForm

    def get_form_kwargs(self):
        kwargs = super(CreatureCreate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        user = self.request.user
        form.instance.owner = user
        if self.request.POST.get('save_and_next'):
            self.success_url = reverse('creature-create')
        logger.info("Creature %s created for user %s" % (form.instance.name, user.id))
        return super(CreatureCreate, self).form_valid(form)


class CreatureUpdate(LoginRequiredMixin, UpdateView):
    """Generic update view."""
    model = Creature
    form_class = CreatureModifyForm

    def get_form_kwargs(self):
        kwargs = super(CreatureUpdate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(CreatureUpdate, self).get_object()
        if not obj.owner == self.request.user:
            raise Http404
        return obj

    # Validate if patron, or don't change color (backend validation)
    def form_valid(self, form):
        creature_form = form.save(commit=False)
        form_color = creature_form.color
        pk = creature_form.id
        db_color = Creature.objects.filter(owner=self.request.user, pk=pk).first().color
        # print(form_color, db_color, self.request.user.groups.filter(name='Patrons').count())
        # if db_color != form_color and self.request.user.groups.filter(name='Patrons').count() <= 0:
        #     creature_form.color = db_color
        logger.info("Creature %s updated for user %s" % (form.instance.name, self.request.user.id))
        return super(CreatureUpdate, self).form_valid(form)


class CreatureDelete(LoginRequiredMixin, DeleteView):
    """Generic creature delete view."""
    model = Creature
    success_url = reverse_lazy('creatures')

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(CreatureDelete, self).get_object()
        if not obj.owner == self.request.user:
            raise Http404
        return obj


class CreatureAllDelete(LoginRequiredMixin, DeleteView):
    """Generic creature ALL delete view."""
    model = Creature
    success_url = reverse_lazy('creatures')

    def get_object(self, queryset=None):
        obj = Creature.objects.filter(owner=self.request.user)
        return obj


# Bestiary Forms
class BestiaryCreate(LoginRequiredMixin, CreateView):
    """Generic bestiary create view."""
    form_class = BestiaryModifyForm
    model = Bestiary

    def form_valid(self, form):
        form.instance.owner = self.request.user
        logger.info("Bestiary %s created for user %s" % (form.instance.name, self.request.user.id))
        return super(BestiaryCreate, self).form_valid(form)


@login_required()
def create_ddb_enc_bestiary(request):
    """Dndbeyond Encounter bestiary create view."""
    if request.method == 'POST':
        form = DDBEncounterBestiaryCreate(request.POST)
        if form.is_valid():
            logger.info("Creating Dndbeyond Encounter Bestiary!")
            # DDB API Endpoints
            DDB_ENCOUTNER_ENDPOINT = "https://encounter-service.dndbeyond.com/v1/encounters/"
            DDB_MONSTER_ENDPOINT = "https://monster-service.dndbeyond.com/v1/Monster?"

            # Try to get DDB Encounter data
            enc_url = form.cleaned_data.get('ddb_enc_url')
            enc_uuid = str(urlparse(enc_url).path).replace("/encounters/", "")
            enc_api_url = urljoin(DDB_ENCOUTNER_ENDPOINT, enc_uuid)
            logger.info("DDB Enc URL: %s" % (enc_url))
            logger.debug("DDB Enc API URL: %s" % (enc_api_url))
            try:
                response = requests.get(enc_api_url)
                enc_dict = response.json()
            except requests.RequestException as exception:
                logger.error("Could not download DDB Enc Data, Error: \n %s" % exception)

            # Monster ID List
            raw_monster_list = []
            monster_params = {}
            for i in enc_dict["data"]["monsters"]:
                raw_monster_list.append(str(i["id"]))

            # Add their quantity for use later
            for i in raw_monster_list:
                monster_params[i] = raw_monster_list.count(i)

            # Prepare the URL to get all monster data
            monster_url = DDB_MONSTER_ENDPOINT
            for i in monster_params:
                monster_url = "".join(monster_url + "ids=" + i + "&")

            logger.debug("DDB Monsters API URLs: %s" % str(monster_url))

            monsters_list = []

            # Get monster data
            try:
                response = requests.get(monster_url)
            except requests.RequestException as exception:
                logger.error("Could not download DDB Monster Data, Error: \n %s" % exception)

            try:
                monsters_list = response.json()["data"]
            except json.decoder.JSONDecodeError as exception:
                logger.error("Could not download DDB Monster Data, Error: \n %s" % exception)

            # Create a bestiary
            bestiary = Bestiary()
            bestiary.name = str(enc_dict["data"]["name"])
            bestiary.owner = request.user
            bestiary.from_ddb = True
            bestiary.save()
            logger.info("Bestiary %s created for user %s via DDB Enc" % (bestiary.name, request.user.id))

            # Create monsters if they don't exist already and link
            for i in monsters_list:
                if not Creature.objects.filter(owner=request.user, name=i["name"]).exists():
                    creature = Creature()
                    creature.name = i["name"]

                    # Figure out which image to use, if none are available use a basic SRD creature image
                    if i["isReleased"]:
                        # This is a monster of the SRD or Publicly available
                        if i["basicAvatarUrl"]:
                            # Seems DDB is publishing wrong URLs, fixing those here
                            if urlparse(i["basicAvatarUrl"]).netloc == "www.dndbeyond.com.com":
                                creature.img_url = "https://www.dndbeyond.com" + urlparse(i["basicAvatarUrl"]).path
                            else:
                                creature.img_url = i["basicAvatarUrl"]
                        else:
                            if i["avatarUrl"]:
                                creature.img_url = i["avatarUrl"]
                            else:
                                creature.img_url = "https://media-waterdeep.cursecdn.com/avatars/4675/664/636747837303835953.jpeg"
                    else:
                        if i["avatarUrl"]:
                            creature.img_url = i["avatarUrl"]
                        else:
                            creature.img_url = "https://media-waterdeep.cursecdn.com/avatars/4675/664/636747837303835953.jpeg"

                    # Determine correct size. Be aware this might change on ddb side
                    if i["sizeId"] == 2:
                        creature.size = "T"
                    if i["sizeId"] == 3:
                        creature.size = "S"
                    if i["sizeId"] == 4:
                        creature.size = "M"
                    if i["sizeId"] == 5:
                        creature.size = "L"
                    if i["sizeId"] == 6:
                        creature.size = "H"
                    if i["sizeId"] == 7:
                        creature.size = "G"

                    creature.owner = request.user
                    creature.from_ddb = True
                    creature.save()
                    logger.info("Creature %s created for user %s via DDB Enc" % (creature.name, request.user.id))

                    # Link monster
                    bestiary_monsters = CreatureQuantity()
                    bestiary_monsters.creature = creature
                    bestiary_monsters.bestiary = bestiary
                    bestiary_monsters.owner = request.user

                    for var in monster_params:
                        if str(i["id"]) == var:
                            bestiary_monsters.quantity = monster_params[var]
                    bestiary_monsters.save()

                # If the create already exists, link it
                else:
                    # Link monster
                    bestiary_monsters = CreatureQuantity()
                    bestiary_monsters.creature = Creature.objects.filter(owner=request.user, name=i["name"]).first()
                    bestiary_monsters.bestiary = bestiary
                    for var in monster_params:
                        if str(i["id"]) == var:
                            bestiary_monsters.quantity = monster_params[var]
                    bestiary_monsters.owner = request.user
                    bestiary_monsters.save()
            return HttpResponseRedirect(reverse('bestiaries'))

    else:
        form = DDBEncounterBestiaryCreate()
    return render(request, 'ddb_enc_bestiary.html', {'form': form})


class BestiaryUpdate(LoginRequiredMixin, UpdateView):
    """Generic bestiary update view."""
    model = Bestiary
    form_class = BestiaryModifyForm

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(BestiaryUpdate, self).get_object()
        if not obj.owner == self.request.user:
            raise Http404
        return obj


class BestiaryDelete(LoginRequiredMixin, DeleteView):
    """Generic bestiary delete view."""
    model = Bestiary
    success_url = reverse_lazy('bestiaries')

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(BestiaryDelete, self).get_object()
        if not obj.owner == self.request.user:
            raise Http404
        return obj


# patreon
def patreon(request):
    """Simple rendering of patreon info page."""
    return render(request, 'patreon.html')
