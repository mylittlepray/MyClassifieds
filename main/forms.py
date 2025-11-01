from django import forms

from .models import AdvUser
from .models import SuperRubric, SubRubric
from .models import Bb, AdditionalImage 

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .signals import post_register 

from captcha.fields import CaptchaField
from .models import Comment

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    
    password1 = forms.CharField(label='Пароль', 
                                widget=forms.PasswordInput,
                                help_text=password_validation.password_validators_help_text_html()) 
    
    password2 = forms.CharField(label='Пароль (повторно)',
                                widget=forms.PasswordInput,
                                help_text='Введите тот же самый пароль еще раз для проверки')
    
    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        if password1:
            password_validation.validate_password(password1)
        return password1 
    
    def clean(self):
        super().clean()
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 != password2:
            errors = {'password2': ValidationError('Введенные пароли не совпадают', code='password_mismatch')}
            raise ValidationError(errors) 
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.is_activated = False
        
        if commit:
            user.save()

        post_register.send(RegisterForm, instance=user)
        return user
    
    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'send_messages') 

class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'first_name', 'last_name', 'send_messages')
    
class SubRubricForm(forms.ModelForm):
    super_rubric = forms.ModelChoiceField(queryset=SuperRubric.objects.all(), empty_label=None, label='Надрубрика', required=True)
    
    class Meta:
        model = SubRubric
        fields = '__all__' 

class SearchForm(forms.Form): 
    keyword = forms.CharField(required=False, max_length=20, label='') 

class BbForm(forms.ModelForm):
    class Meta:
        model = Bb
        fields = ('rubric', 'title', 'content', 'price', 'contacts', 'image', 'is_active')
        widgets = {
            'rubric': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 50}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'maxlength': 600}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '999999999999.99',
                'step': '0.01',
                'placeholder': 'до 1 000 000 000 000 (1 трлн)'
            }),
            'contacts': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 50}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None:
            return price
        if price < 0:
            raise forms.ValidationError('Цена не может быть отрицательной.')
        if price > 999999999999.99:
            raise forms.ValidationError('Максимальная цена — 999 999 999 999.99')
        return price

class AIForm(forms.ModelForm):
    class Meta:
        model = AdditionalImage
        fields = ('image',)
        widgets = {'image': forms.ClearableFileInput(attrs={'class': 'form-control'})}

AIFormSet = forms.inlineformset_factory(Bb, AdditionalImage, form=AIForm, extra=3)

class CommentForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput(attrs={'data-rating-input': 'true'})
    )

    class Meta:
        model = Comment
        fields = ('content', 'rating',)
        labels = {'content': ''}
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'card shadow-sm rounded-4 p-3 my-3',
                'rows': 3,
                'maxlength': 300,
                'style': 'resize: none;',
                'placeholder': 'Оставьте комментарий...',
            }),
        }

