import zoneinfo

from django.contrib import messages 
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, JsonResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template 

from django.views.generic.base import TemplateView 
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.decorators.http import require_POST

from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404

from django.core import signing
from django.core.cache import cache
from django.core.paginator import Paginator

from django.conf import settings

from django.db.models import Q, Avg, Count

from nickname_gen.generator import Generator
from nickname_gen.words import RU_ADJECTIVES_WORDS, RU_ANIMALS_WORDS

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

from .cache_utils import generate_cache_key, get_cached_or_set

COOKIE_KEY = getattr(settings, "ANON_AUTHOR_COOKIE_NAME", "anon_author")
COOKIE_MAX_AGE = getattr(settings, "ANON_AUTHOR_COOKIE_MAX_AGE", 60*60*24*365)
COOKIE_SALT = getattr(settings, "COOKIE_SALT", "anon-author-v1")


# ==================== КЛАССЫ ПРЕДСТАВЛЕНИЙ ====================

class BBLoginView(LoginView):
    template_name = 'main/login.html'
    
    def form_valid(self, form):
        """Добавляем приветственное сообщение при успешном входе"""
        messages.success(self.request, f'Добро пожаловать, {form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Сообщение об ошибке входа"""
        messages.error(self.request, 'Неверное имя пользователя или пароль')
        return super().form_invalid(form)


class BBLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        """Сообщение при выходе"""
        if request.user.is_authenticated:
            messages.info(request, 'Вы успешно вышли из системы')
        return super().dispatch(request, *args, **kwargs)


class ProfileEditView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'main/profile_edit.html'
    form_class = ProfileEditForm
    success_url = reverse_lazy('main:profile')
    success_message = '✅ Данные профиля успешно обновлены'
    
    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)
   
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)
    
    def form_invalid(self, form):
        """Сообщение об ошибках валидации"""
        messages.error(self.request, 'Не удалось сохранить изменения. Проверьте правильность заполнения полей')
        return super().form_invalid(form)


class PasswordEditView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):
    template_name = 'main/password_edit.html'
    success_url = reverse_lazy('main:profile')
    success_message = '🔒 Пароль успешно изменен'
    
    def form_valid(self, form):
        messages.info(self.request, 'Рекомендуем выйти и войти заново с новым паролем')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при смене пароля. Проверьте правильность текущего пароля')
        return super().form_invalid(form)


class RegisterView(CreateView):
    model = AdvUser
    template_name = 'main/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('main:register_done')
    
    def form_valid(self, form):
        """Сообщения при успешной регистрации"""
        messages.success(self.request, 'Регистрация прошла успешно!')
        messages.info(self.request, 'На вашу почту отправлено письмо с инструкциями по активации аккаунта')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при регистрации. Проверьте правильность заполнения формы')
        if 'username' in form.errors:
            messages.warning(self.request, 'Пользователь с таким именем уже существует')
        if 'email' in form.errors:
            messages.warning(self.request, 'Пользователь с таким email уже зарегистрирован')
        return super().form_invalid(form)


class RegisterDoneView(TemplateView):
    template_name = 'main/register_done.html'


class ProfileDeleteView(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    model = AdvUser
    template_name = 'main/profile_delete.html'
    success_url = reverse_lazy('main:index')
    success_message = 'Ваш аккаунт успешно удален'
    
    def setup(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().setup(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        messages.warning(request, 'Ваш профиль и все связанные данные удалены')
        logout(request)
        return super().post(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


# ==================== ФУНКЦИОНАЛЬНЫЕ ПРЕДСТАВЛЕНИЯ ====================

def index(request):
    """Главная страница со списком объявлений с кешированием"""
    keyword = request.GET.get('keyword', '')
    page_number = request.GET.get('page', 1)
    
    cache_key = generate_cache_key('index_page', keyword, page_number)
    
    def get_bbs_data():
        """Внутренняя функция для получения данных (выполняется при cache miss)"""
        bbs = Bb.objects.filter(is_active=True).select_related('rubric')
        
        if keyword:
            keywords = [word for word in keyword.split() if word]
            if keywords:
                q_objects = []
                for kw in keywords:
                    q_objects.append(Q(title__icontains=kw) | Q(content__icontains=kw))
                
                if q_objects:
                    bbs = bbs.filter(reduce(and_, q_objects))
        
        return list(bbs.values_list('pk', flat=True))
    
    bb_ids = get_cached_or_set(cache_key, get_bbs_data, timeout=300)
    
    if bb_ids:
        preserved = {pk: i for i, pk in enumerate(bb_ids)}
        bbs = Bb.objects.filter(pk__in=bb_ids).select_related('rubric')
        bbs = sorted(bbs, key=lambda obj: preserved[obj.pk])
    else:
        bbs = []
    
    if keyword and request.method == 'GET' and bbs:
        messages.info(request, f'Найдено объявлений: {len(bbs)}')
    
    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 5)
    page = paginator.get_page(page_number)
    
    context = {
        'bbs': page.object_list,
        'page': page,
        'form': form,
        'keyword': keyword,
    }
    
    return render(request, 'main/index.html', context)

def other_page(request, page):
    """Отображение статических страниц"""
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        messages.error(request, f'Страница "{page}" не найдена')
        raise Http404()
    return HttpResponse(template.render(request=request))

def bb_detail(request, rubric_pk, pk):
    """Детальный просмотр объявления с комментариями и кешированием"""
    cache_key_bb = generate_cache_key('bb_detail', pk)
    
    def get_bb_data():
        """Получение данных объявления с дополнительными изображениями"""
        bb = get_object_or_404(Bb, pk=pk)
        ais = bb.additionalimage_set.all()
        return {'bb': bb, 'ais': ais}
    
    bb_data = get_cached_or_set(cache_key_bb, get_bb_data, timeout=600)
    bb = bb_data['bb']
    ais = bb_data['ais']
    
    comments = Comment.objects.filter(bb=bb, is_active=True).select_related('bb')
    
    cache_key_rating = generate_cache_key('bb_rating', pk)
    
    def get_rating_stats():
        """Вычисление статистики рейтинга"""
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
        
        return {
            'avg_rating': avg_rating,
            'rating_count': rating_count,
            'avg_rating_text': avg_rating_text,
            'rating_label': rating_label,
            'full_stars': full_stars,
            'has_half_star': has_half_star,
            'empty_stars': empty_stars,
            'full_star_range': range(full_stars),
            'empty_star_range': range(empty_stars),
        }
    
    rating_data = get_cached_or_set(cache_key_rating, get_rating_stats, timeout=120)
    
    form = CommentForm(request=request)

    if not request.user.is_authenticated and settings.DEBUG:
        messages.debug(request, f'Просмотр объявления #{pk} как гость')

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
                    messages.info(request, f'Вам присвоен временный ник: {author}')
                comment.author = author

            comment.bb = bb
            comment.save()
            
            messages.success(request, '✅ Комментарий успешно добавлен!')
            
            if comment.rating:
                messages.info(request, f'Ваша оценка: {comment.rating} из 5')
            
            cache.delete(cache_key_rating)

            response = redirect(request.get_full_path_info())

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
            messages.error(request, '❌ Не удалось добавить комментарий')
            if 'captcha' in form.errors:
                messages.warning(request, '⚠️ CAPTCHA введена неверно. Попробуйте еще раз')
            if 'content' in form.errors:
                messages.warning(request, 'Поле "Текст комментария" обязательно для заполнения')

    context = {
        'bb': bb,
        'ais': ais,
        'comments': comments,
        'form': form,
        'rating_range': range(1, 6),
        **rating_data
    }
    return render(request, 'main/bb_detail.html', context)

@login_required
def profile_bb_detail(request, rubric_pk, pk):
    """Просмотр собственного объявления"""
    bb = get_object_or_404(Bb, pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comment.objects.filter(bb=bb, is_active=True)

    context = {'bb': bb, 'ais': ais, 'comments': comments}
    return render(request, 'main/profile_bb_detail.html', context)

def user_activate(request, sign):
    """Активация аккаунта пользователя"""
    try:
        username = signer.unsign(sign)
    except signing.BadSignature:
        messages.error(request, '❌ Ссылка активации недействительна или устарела')
        return render(request, 'main/activation_failed.html')
    
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        messages.info(request, 'Ваш аккаунт уже был активирован ранее')
        template = 'main/activation_done_earlier.html'
    else:
        user.is_active = True
        user.is_activated = True
        user.save()
        
        messages.success(request, f'✅ Аккаунт {username} успешно активирован!')
        messages.info(request, 'Теперь вы можете войти в систему')
        template = 'main/activation_done.html'
        
    return render(request, template)

def rubric_bbs(request, pk):
    """Объявления в конкретной рубрике с кешированием"""
    rubric = get_object_or_404(SubRubric, pk=pk)
    keyword = request.GET.get('keyword', '')
    page_num = request.GET.get('page', 1)
    
    cache_key = generate_cache_key('rubric_bbs', pk, keyword, page_num)
    
    def get_rubric_bbs():
        """Получение объявлений рубрики"""
        bbs = Bb.objects.filter(is_active=True, rubric=pk).select_related('author', 'rubric')
        
        if keyword:
            q = Q(title__icontains=keyword) | Q(content__icontains=keyword)
            bbs = bbs.filter(q)
        
        return list(bbs.values_list('pk', flat=True))
    
    bb_ids = get_cached_or_set(cache_key, get_rubric_bbs, timeout=300)
    
    if bb_ids:
        preserved = {pk: i for i, pk in enumerate(bb_ids)}
        bbs = Bb.objects.filter(pk__in=bb_ids).select_related('author', 'rubric')
        bbs = sorted(bbs, key=lambda obj: preserved[obj.pk])
    else:
        bbs = []
    
    if keyword:
        if bbs:
            messages.info(request, f'В рубрике "{rubric.name}" найдено: {len(bbs)}')
        else:
            messages.warning(request, f'В рубрике "{rubric.name}" ничего не найдено по запросу "{keyword}"')
    
    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 2)
    page = paginator.get_page(page_num)
    
    context = {'rubric': rubric, 'page': page, 'bbs': page.object_list, 'form': form}
    
    return render(request, 'main/rubric_bbs.html', context)

@login_required
def profile(request):
    """Профиль пользователя"""
    return render(request, 'main/profile.html')

@login_required
def profile_my_bbs(request):
    """Мои объявления"""
    bbs = Bb.objects.filter(author=request.user.pk)
    if not bbs.exists():
        messages.info(request, 'У вас пока нет объявлений. Создайте первое!')
    context = {'bbs': bbs}
    return render(request, 'main/profile_my_bbs.html', context)

@login_required
def profile_bb_add(request):
    """Добавление нового объявления."""
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES)

        bb = form.save(commit=False) if form.is_valid() else None
        formset = AIFormSet(request.POST, request.FILES, instance=bb)

        if form.is_valid() and formset.is_valid():
            bb.author = request.user
            bb.is_active = True
            bb.save() 

            formset.instance = bb
            formset.save()

            uploaded_count = 0
            for cd in (formset.cleaned_data or []):
                if not cd:
                    continue
                if cd.get('DELETE'):
                    continue
                if cd.get('image'):
                    uploaded_count += 1

            messages.success(request, '✅ Объявление успешно добавлено!')
            messages.info(request, f'Объявление опубликовано в рубрике "{bb.rubric}"')
            if uploaded_count:
                messages.info(request, f'Загружено дополнительных изображений: {uploaded_count}')

            return redirect('main:profile_my_bbs')

        messages.error(request, '❌ Не удалось добавить объявление')

        if form.errors:
            messages.warning(request, 'Проверьте правильность заполнения основной формы')
            for field, errors in form.errors.items():
                if field == '__all__':
                    for e in errors:
                        messages.warning(request, str(e))
                else:
                    label = form.fields.get(field).label if field in form.fields else field
                    messages.warning(request, f'{label}: {", ".join(errors)}')

        if formset.non_form_errors():
            messages.warning(request, 'Ошибки при загрузке дополнительных изображений')
            for e in formset.non_form_errors():
                messages.warning(request, str(e))

        for f in formset.forms:
            if not f.errors:
                continue
            messages.warning(request, 'Ошибки при загрузке дополнительных изображений')
            for field, errors in f.errors.items():
                if field == '__all__':
                    for e in errors:
                        messages.warning(request, str(e))
                else:
                    label = f.fields.get(field).label if field in f.fields else field
                    messages.warning(request, f'{label}: {", ".join(errors)}')

    else:
        form = BbForm()
        formset = AIFormSet()

    return render(request, 'main/profile_bb_add.html', {'form': form, 'formset': formset})

@login_required
def profile_bb_edit(request, pk):
    """Редактирование объявления"""
    bb = get_object_or_404(Bb, pk=pk)
    
    if bb.author != request.user:
        messages.error(request, '❌ У вас нет прав для редактирования этого объявления')
        return redirect('main:profile_my_bbs')
    
    if request.method == 'POST':
        form = BbForm(request.POST, request.FILES, instance=bb)
        if form.is_valid():
            bb = form.save(commit=False)
            bb.author = request.user
            bb.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                formset.save()
                messages.success(request, '✅ Объявление успешно обновлено')
                messages.info(request, 'Все изменения сохранены')
                return redirect('main:profile_my_bbs')
            else:
                messages.error(request, 'Ошибка при обновлении дополнительных изображений')
        else:
            messages.error(request, '❌ Не удалось обновить объявление')
            messages.warning(request, 'Проверьте правильность заполнения формы')
    else:
        form = BbForm(instance=bb)
        formset = AIFormSet(instance=bb)

    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_bb_edit.html', context)

@login_required
def profile_bb_delete(request, pk):
    """Удаление объявления"""
    bb = get_object_or_404(Bb, pk=pk)
    
    if bb.author != request.user:
        messages.error(request, '❌ У вас нет прав для удаления этого объявления')
        return redirect('main:profile_my_bbs')
    
    if request.method == 'POST':
        bb_title = bb.title
        bb.delete()
        messages.success(request, f'✅ Объявление "{bb_title}" удалено')
        messages.info(request, 'Все связанные изображения и комментарии также удалены')
        return redirect('main:profile_my_bbs')
    else:
        context = {'bb': bb}
        return render(request, 'main/profile_bb_delete.html', context)
    
@require_POST
@login_required
def profile_bb_toggle_active(request, pk):
    bb = get_object_or_404(Bb, pk=pk, author=request.user)

    bb.is_active = not bb.is_active
    bb.save(update_fields=['is_active'])

    if bb.is_active:
        messages.success(request, '✅ Объявление теперь показывается в общем списке')
    else:
        messages.info(request, 'ℹ️ Объявление скрыто из общего списка')

    return redirect('main:profile_my_bbs')

@require_POST
def set_timezone(request):
    tz = request.POST.get("timezone")
    try:
        zoneinfo.ZoneInfo(tz)
    except Exception:
        return JsonResponse({"ok": False, "error": "Invalid timezone"}, status=400)

    request.session["django_timezone"] = tz
    return JsonResponse({"ok": True, "timezone": tz})