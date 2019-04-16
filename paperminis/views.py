from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.forms.models import modelformset_factory
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Sum
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
#from django.shortcuts import get_object_or_404
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from django.template.defaultfilters import filesizeformat
from django.core.exceptions import ValidationError
from django import forms
from dndtools.settings import STATIC_URL
from django.utils.encoding import smart_str
from django.views.static import serve
from django.db import connection
import os
import json
from fractions import Fraction
import uuid

from django import template
from django.contrib.auth.models import Group

from .models import User
from .models import Creature
from .models import Bestiary
from .models import CreatureQuantity
from .models import PrintSettings
from .static.generate_minis.generate_minis import MiniBuilder
from .forms import QuantityForm
from .forms import UploadFileForm
from .forms import SignUpForm
from .forms import PrintForm

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Function to check Patreon status in templates."""
    group =  Group.objects.get(name=group_name)
    return group in user.groups.all()

def signup(request):
    """To register new users."""
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def temp_account(request):
    """Create temporary account."""
    if request.method == 'POST':
        # generate random username and password
        password = make_password(uuid.uuid4())
        email = uuid.uuid4()
        user = User(email=email, password=password)
        user.save()
        # add to group 'temp'
        temp_grp = Group.objects.get(name='temp')
        temp_grp.user_set.add(user)
        # log the user in (this can never be done manually)
        login(request, user)
        return render(request, 'temp_account.html')

    return reverse('signup')

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
            return HttpResponseRedirect(reverse('index'))
    else:
        form = SignUpForm()
    return render(request, 'convert.html', {'form': form})

def handle_json(f, user):
    """Load and process .json file.
    This version will update creatures if the json has more/different information.
    A creature is uniquely identified by the tuple (name, img_url).
    The update is still kind of slow for large files, but I can't see a better way to do it currently."""

    try:
        data = json.loads(f['file'].read().decode('utf-8'))
    except:
        return -1

    current = Creature.objects.filter(owner=user)
    current_name_url = [(x.name, x.img_url) for x in current]
    current_full = [(x.name, x.img_url, x.size, x.CR, x.creature_type) for x in current]
    size_map = {v: k for k, v in dict(Creature.CREATURE_SIZE_CHOICES).items()}
    creature_type_map = {v: k for k, v in dict(Creature.CREATURE_TYPE_CHOICES).items()}
    skip = 0
    obj_list = []
    for k,i in data.items():
        # mandatory fields
        try:
            name = i['name']
            img_url = i['img_url']
            name_url = (name,img_url)
        except:
            skip += 1
            continue

        # fix illegal size (default to medium)
        try:
            short_size = size_map[i['creature_size']]
        except:
            short_size = Creature.MEDIUM

        # fix illegal types (default to undefined)
        try:
            short_type = creature_type_map[i['creature_type']]
        except:
            short_type = Creature.UNDEFINED

        # fix illegal CRs (default to 0)
        try:
            cr = float(Fraction(i['CR']))
            if cr < 0 or cr > 1000: cr = 0
        except:
            cr = 0

        # check if unique
        if name_url in current_name_url:
            full_tup = (name, img_url, short_size, cr, short_type)
            if full_tup in current_full:
                # excact duplicate
                skip += 1
                continue
            else:
                # updated attributes
                # this is kinda slow :(
                Creature.objects.filter(owner=user, name=name, img_url=img_url).update(size=short_size, CR=cr, creature_type=short_type)
                current_full.append(full_tup)
                continue

        current_name_url.append(name_url)

        # if everything is ok, generate the object and store it
        obj = Creature(owner=user, name=i['name'], size=short_size, img_url=i['img_url'], CR=cr, creature_type=short_type)
        obj_list.append(obj)

    if len(obj_list) > 0:
        # MUCH faster than one query per entry!
        Creature.objects.bulk_create(obj_list)
    return skip

@login_required()
def json_upload(request):
    """Upload view and form handling."""
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid(): # validation happens in forms.py
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
    #paginate_by = 2 # pagination doesn't work with the current filter system and is not needed anyways

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
        return Bestiary.objects.filter(owner=self.request.user).annotate(total_creatures=Sum('creaturequantity__quantity'))


def bestiary_serve_minis(request, minis):
    """Serve zip file to browser."""
    response = HttpResponse(content_type='application/force-download')  # mimetype is replaced by content_type for django 1.7
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(minis.zip_fn)
    response['X-Accel-Redirect'] = smart_str(minis.nginx_url + "/" + minis.zip_fn)
    #response = serve(request, os.path.basename(minis.zip_fn), os.path.dirname(minis.zip_path)) # for local testing!!
    #print(minis.zip_static_path)
    return response

@login_required()
def bestiary_print(request, pk):
    # validation and proper redirects
    bestiary = Bestiary.objects.filter(owner=request.user, id=pk).first()
    if not bestiary:
        return HttpResponseRedirect(reverse('bestiaries'))
    elif bestiary.creatures.count() <= 0:
        return HttpResponseRedirect(reverse('bestiary-detail', kwargs={'pk':pk}))

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
            minis = MiniBuilder(user=request.user)
            # update settings
            new_settings = formset.save(commit=False)

            # patreon early access backend validation
            if user.groups.filter(name='Patrons').count() < 1:
                new_settings.darken = 0

            print_settings.paper_format = new_settings.paper_format
            print_settings.grid_size = new_settings.grid_size
            print_settings.base_shape = new_settings.base_shape
            print_settings.enumerate = new_settings.enumerate
            print_settings.fixed_height = new_settings.fixed_height
            print_settings.darken = new_settings.darken
            print_settings.save()
            # load settings into the mini builder
            minis.load_settings(paper_format=print_settings.paper_format,
                            grid_size=print_settings.grid_size,
                            base_shape=print_settings.base_shape,
                            enumerate=print_settings.enumerate,
                            fixed_height = print_settings.base_shape,
                            darken= print_settings.darken)
            # load creatures into the mini builder
            minis.add_bestiary(pk)
            # build minis
            minis.build_all_and_zip()
            # serve file
            serve = bestiary_serve_minis(request, minis)
            #context = {'pk': pk, 'file': minis.zip_path}
            return serve

    # seed form with loaded settings
    form = PrintForm(initial=print_settings.__dict__)

    return render(request, 'bestiary_print.html', {'form':form})

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
        mgmt = ['csrfmiddlewaretoken', 'form-TOTAL_FORMS', 'form-INITIAL_FORMS', 'form-MIN_NUM_FORMS', 'form-MAX_NUM_FORMS']
        for id,q in request.POST.items():
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
                creature = Creature.objects.filter(owner=request.user,id=id)[0]
            except:
                continue

            quantity_obj = CreatureQuantity.objects.filter(creature=creature, bestiary=bestiary, owner=request.user).first()
            # update or create
            if quantity_obj: quantity_obj.quantity = q
            else: quantity_obj = CreatureQuantity(creature=creature, bestiary=bestiary, owner=request.user, quantity=q)
            # save
            quantity_obj.save()

        return HttpResponseRedirect(reverse('bestiary-detail', kwargs={'pk':pk}))

    else:
        context = {'qs':qs, 'formset': formset, 'form': formset}
        return render(request, 'bestiary_link.html', context=context)



class BestiaryListView(LoginRequiredMixin, generic.ListView):
    """Generic Bestiary list view."""
    model = Bestiary

    def get_queryset(self):
        #ok = Bestiary.objects.filter(owner=self.request.user).values('name', 'creaturequantity__quantity').aggregate(total_creatures=Sum('creaturequantity__quantity'))
        return Bestiary.objects.filter(owner=self.request.user).values('name', 'id').annotate(total_creatures=Sum('creaturequantity__quantity'))



from .forms import CreatureModifyForm
from .forms import BestiaryModifyForm

# Creature Forms
class CreatureCreate(LoginRequiredMixin, CreateView):
    """Generic create view."""
    model = Creature
    initial={'size':Creature.MEDIUM,'color': Creature.DARKGRAY,'position': Creature.WALKING,'show_name': True}
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
        #print(form_color, db_color, self.request.user.groups.filter(name='Patrons').count())
        # if db_color != form_color and self.request.user.groups.filter(name='Patrons').count() <= 0:
        #     creature_form.color = db_color
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
        return super(BestiaryCreate, self).form_valid(form)

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
