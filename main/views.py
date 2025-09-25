from django.contrib.auth.views import LoginView , LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template 

from django.views.generic.base import TemplateView 
from django.views.generic.edit import UpdateView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404

from .models import AdvUser
from .forms import ProfileEditForm, RegisterForm

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

def index(request):
    return render(request, 'main/index.html')

def other_page(request, page):
    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404()
    return HttpResponse(template.render(request=request))

@login_required
def profile(request):
    return render(request, 'main/profile.html') 

@login_required
def myads(request):
    return render(request, 'main/myads.html') 