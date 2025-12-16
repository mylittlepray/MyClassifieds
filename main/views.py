from nickname_gen.generator import Generator
from nickname_gen.words import RU_ADJECTIVES_WORDS, RU_ANIMALS_WORDS

from django.contrib import messages 
from django.contrib.auth.views import LoginView , LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template 

from django.views.generic.base import TemplateView 
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404

from django.core import signing
from django.core.paginator import Paginator

from django.conf import settings

from django.db.models import Q, Avg, Count
from functools import reduce
from operator import and_

from .utilities import signer, get_anon_author_from_cookie
from .models import SubRubric
from .models import AdvUser
from .models import SubRubric, Bb 
from .models import Comment

from .forms import SearchForm 
from .forms import ProfileEditForm, RegisterForm
from .forms import BbForm, AIFormSet
from .forms import CommentForm

COOKIE_KEY = getattr(settings, "ANON_AUTHOR_COOKIE_NAME", "anon_author")
COOKIE_MAX_AGE = getattr(settings, "ANON_AUTHOR_COOKIE_MAX_AGE", 60*60*24*365)
COOKIE_SALT = getattr(settings, "COOKIE_SALT", "anon-author-v1")

# Create your views here.
class BBLoginView(LoginView):
    template_name = 'main/login.html' 

class BBLogoutView(LogoutView):
    pass

class ProfileEditView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Данные пользователя изменены'
    
    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)
   
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
            
        return get_object_or_404(queryset, pk=self.user_id) 

class PasswordEditView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'main/password_edit.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль пользователя изменен' 

class RegisterView(CreateView):
    model = AdvUser
    template_name = 'main/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('main:register_done') 

class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html' 

class ProfileDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/profile_delete.html'
    success_url = reverse_lazy('main:index')
    success_message = 'Пользователь удален'
    
    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        logout(request)
        return super().post(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
            return get_object_or_404(queryset, pk=self.user_id) 
def index(request):
    bbs = Bb.objects.filter(is_active=True)  # Все активные объявления

    # Поиск по ключевому слову
    keyword = request.GET.get('keyword', '')
    if keyword:
        # Split by space and filter out empty strings
        keywords = [word for word in keyword.split() if word]
        if keywords:
            # Create a Q object for each keyword
            q_objects = []
            for kw in keywords:
                q_objects.append(Q(title__icontains=kw) | Q(content__icontains=kw))
            
            # Combine the Q objects with AND
            if q_objects:
                bbs = bbs.filter(reduce(and_, q_objects))

    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 5)  # например, 5 объявлений на страницу

    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    context = {
        'bbs': page.object_list,
        'page': page,
        'form': form,
        'keyword': keyword,
    }

    return render(request, 'main/index.html', context)

def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404()
    return HttpResponse(template.render(request=request))

def bb_detail(request, rubric_pk, pk):
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=bb, is_active=True)
    rating_stats = comments.aggregate(
        avg_rating=Avg('rating'),
        rating_count=Count('id')
    )
    avg_rating_value = float(rating_stats['avg_rating']) if rating_stats['avg_rating'] is not None else 0.0
    rating_count = rating_stats['rating_count'] or 0
    full_stars = int(avg_rating_value)
    if full_stars > 5:
        full_stars = 5
    has_half_star = full_stars < 5 and (avg_rating_value - full_stars) >= 0.5
    empty_stars = max(5 - full_stars - (1 if has_half_star else 0), 0)
    full_star_range = range(full_stars)
    empty_star_range = range(empty_stars)
    avg_rating = round(avg_rating_value, 1) if rating_count else 0
    if rating_count:
        avg_rating_text = f'{avg_rating:.1f} из 5'
        last_digit = rating_count % 10
        last_two_digits = rating_count % 100
        if last_digit == 1 and last_two_digits != 11:
            rating_label = f'{rating_count} оценка'
        elif last_digit in (2, 3, 4) and not 12 <= last_two_digits <= 14:
            rating_label = f'{rating_count} оценки'
        else:
            rating_label = f'{rating_count} оценок'
    else:
        avg_rating_text = 'Нет оценок'
        rating_label = ''
    form = CommentForm(request=request)

    if request.method == 'POST':
        form = CommentForm(request.POST, request=request)
        if form.is_valid():
            comment = form.save(commit=False)

            if request.user.is_authenticated:
                comment.author = request.user.username
            else:
                author = get_anon_author_from_cookie(request, COOKIE_KEY, COOKIE_SALT, COOKIE_MAX_AGE)
                if not author:
                    author = Generator.get_random_ru_nickname(
                        combos=[RU_ADJECTIVES_WORDS, RU_ANIMALS_WORDS]
                    )
                comment.author = author

            comment.bb = bb
            comment.save()
            messages.add_message(request, messages.SUCCESS, 'Комментарий добавлен')

            response = redirect(request.get_full_path_info())

            # В cookie кладём ASCII-safe подписанное значение
            if not request.user.is_authenticated:
                cookie_value = signing.dumps(comment.author, salt=COOKIE_SALT)
                response.set_cookie(
                    COOKIE_KEY,
                    cookie_value,
                    max_age=COOKIE_MAX_AGE,
                    httponly=True,
                    samesite="Lax",
                    secure=not settings.DEBUG,
                )
            return response
        else:
            messages.add_message(request, messages.WARNING, 'Комментарий не добавлен')

    context = {
        'bb': bb,
        'ais': ais,
        'comments': comments,
        'form': form,
        'avg_rating': avg_rating,
        'rating_count': rating_count,
        'avg_rating_text': avg_rating_text,
        'rating_label': rating_label,
        'full_stars': full_stars,
        'has_half_star': has_half_star,
        'empty_stars': empty_stars,
        'full_star_range': full_star_range,
        'empty_star_range': empty_star_range,
        'rating_range': range(1, 6),
    }
    return render(request, 'main/bb_detail.html', context)

@login_required
def profile_bb_detail(request, rubric_pk, pk): 
    bb = get_object_or_404(Bb, pk=pk) 
    ais = bb.additionalimage_set.all() 

    comments = Comment.objects.filter(bb=bb, is_active=True)

    context = {'bb': bb, 'ais': ais, 'comments': comments} 
    
    return render(request, 'main/profile_bb_detail.html', context) 

def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except signing.BadSignature:
        return render(request, 'main/activation_failed.html')
    
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'main/activation_done_earlier.html'
    else:
        template = 'main/activation_done.html'
        
        user.is_active = True
        user.is_activated = True
        user.save()
        
    return render(request, template) 

def rubric_bbs(request, pk):
    rubric = get_object_or_404(SubRubric, pk=pk) 
    bbs = Bb.objects.filter(is_active=True, rubric=pk) 
    
    if 'keyword' in request.GET: 
        keyword = request.GET['keyword'] 
        q = Q(title__icontains=keyword) | Q(content__icontains=keyword) 
        bbs = bbs.filter(q) 
    else: 
        keyword = ''

    form = SearchForm(initial={'keyword': keyword}) 
    paginator = Paginator(bbs, 2) 
        
    if 'page' in request.GET: 
        page_num = request.GET['page'] 
    else: 
        page_num = 1 
    
    page = paginator.get_page(page_num) 
    context = {'rubric': rubric, 'page': page, 'bbs': page.object_list, 'form': form} 
    
    return render(request, 'main/rubric_bbs.html', context)

@login_required
def profile(request):
    return render(request, 'main/profile.html') 

@login_required
def profile_my_bbs(request):
    bbs = Bb.objects.filter(author=request.user.pk) 
    context = {'bbs': bbs} 
    return render(request, 'main/profile_my_bbs.html', context) 

@login_required
def profile_bb_add(request):
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES)
        formset = AIFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            bb = form.save(commit=False)
            bb.author = request.user
            bb.save()
            raise Exception('Test Exception in profile_bb_add')
            formset.instance = bb
            formset.save()
            messages.success(request, 'Объявление успешно добавлено!')
            return redirect('main:profile')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = BbForm(initial={'author': request.user.pk})
        formset = AIFormSet()

    return render(request, 'main/profile_bb_add.html', {'form': form, 'formset': formset})

@login_required 
def profile_bb_edit(request, pk): 
    bb = get_object_or_404(Bb, pk=pk) 
    
    if request.method == 'POST': 
        form = BbForm(request.POST, request.FILES, instance=bb) 
        if form.is_valid(): 
            bb = form.save(commit=False) 
            bb.author = request.user 
            bb.save() 
            formset = AIFormSet(request.POST, request.FILES, instance=bb) 
            if formset.is_valid(): 
                formset.save() 
                messages.add_message(request, messages.SUCCESS, 'Объявление исправлено') 
                return redirect('main:profile_my_bbs')
    else: 
        form = BbForm(instance=bb) 
        formset = AIFormSet(instance=bb) 

    context = {'form': form, 'formset': formset} 
    return render(request, 'main/profile_bb_edit.html', context)  

 
@login_required 
def profile_bb_delete(request, pk): 
    bb = get_object_or_404(Bb, pk=pk) 
    if request.method == 'POST': 
        bb.delete() 
        messages.add_message(request, messages.SUCCESS, 'Объявление удалено') 
        return redirect('main:profile_my_bbs') 
    else:
        context = {'bb': bb} 
        return render(request, 'main/profile_bb_delete.html', context)
