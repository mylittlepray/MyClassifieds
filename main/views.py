from django.shortcuts import render
from django.contrib.auth.views import LoginView , LogoutView
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template 
from django.contrib.auth.decorators import login_required

# Create your views here.
class BBLoginView(LoginView):
    template_name = 'main/login.html' 

class BBLogoutView(LogoutView):
    pass

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