from django.urls import path
from .views import index, other_page, profile, myads, BBLoginView, BBLogoutView, ProfileEditView, PasswordEditView, RegisterDoneView, RegisterView

app_name = 'main'
urlpatterns = [
    path('accounts/login/', BBLoginView.as_view(), name='login'),
    path('', index, name='index'),
    path('<str:page>/', other_page, name='other'),
    path('myads/', myads, name='myads'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('accounts/password/edit/', PasswordEditView.as_view(), name='password_edit'),
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'), 
    path('accounts/register/', RegisterView.as_view(), name='register'), 
    path('accounts/logout/', BBLogoutView.as_view(), name='logout'),
] 