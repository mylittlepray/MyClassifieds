from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static
from .views import index, set_timezone, other_page, profile, profile_my_bbs, user_activate, rubric_bbs, profile_bb_detail, profile_bb_toggle_active, profile_bb_edit, profile_bb_delete, profile_bb_add, bb_detail, BBLoginView, BBLogoutView, ProfileEditView, PasswordEditView, RegisterDoneView, RegisterView, ProfileDeleteView

app_name = 'main'
urlpatterns = [
    path("set-timezone/", set_timezone, name="set_timezone"),
    path('accounts/login/', BBLoginView.as_view(), name='login'),
    path('', index, name='index'),
    path('rubric_<int:pk>/', rubric_bbs, name='rubric_bbs'), 
    path('<str:page>/', other_page, name='other'),
    path('rubric_<int:rubric_pk>/bb_<int:pk>/', bb_detail, name='bb_detail'),
    path('accounts/profile/bbs/', profile_my_bbs, name='profile_my_bbs'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/profile/<int:pk>/', profile_bb_detail, name='profile_bb_detail'), 
    path('accounts/profile/edit/', ProfileEditView.as_view(), name='profile_edit'),
    path('accounts/profile/add/', profile_bb_add, name='profile_bb_add'), 
    path('accounts/profile/edit/<int:pk>/', profile_bb_edit, name='profile_bb_edit'), 
    path('accounts/profile/bb/<int:pk>/toggle-active/', profile_bb_toggle_active, name='profile_bb_toggle_active'),
    path('accounts/profile/delete/<int:pk>/', profile_bb_delete, name='profile_bb_delete'), 
    path('accounts/password/edit/', PasswordEditView.as_view(), name='password_edit'),
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'), 
    path('accounts/register/', RegisterView.as_view(), name='register'), 
    path('accounts/activate/<str:sign>/', user_activate, name='activate'),
    path('accounts/logout/', BBLogoutView.as_view(), name='logout'),
    path('accounts/profile/delete/', ProfileDeleteView.as_view(), name='profile_delete'),
]

if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 