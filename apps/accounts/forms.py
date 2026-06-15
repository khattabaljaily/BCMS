from django import forms
from django.contrib.auth import authenticate
from django.utils.text import slugify
from .models import User
from apps.core.models import Center, ServiceType
from apps.core.countries import ARAB_COUNTRIES, COUNTRY_CHOICES


class LoginForm(forms.Form):
    username = forms.CharField(label='اسم المستخدم', max_length=150)
    password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput)

    def clean(self):
        data = super().clean()
        user = authenticate(
            username=data.get('username'),
            password=data.get('password'),
        )
        if user is None:
            raise forms.ValidationError('اسم المستخدم أو كلمة المرور غير صحيحة.')
        if not user.is_active:
            raise forms.ValidationError('الحساب موقوف. تواصل مع الدعم الفني.')
        data['user'] = user
        return data


VALID_PLANS = {'starter', 'pro', 'enterprise'}


class RegisterForm(forms.Form):
    # بيانات المركز
    center_name   = forms.CharField(label='اسم المركز', max_length=200)
    phone         = forms.CharField(label='رقم الهاتف', max_length=20)
    country       = forms.ChoiceField(label='الدولة', choices=COUNTRY_CHOICES)
    city          = forms.CharField(label='المدينة', max_length=100, required=False)
    selected_plan = forms.CharField(max_length=20, required=False, widget=forms.HiddenInput)

    # بيانات المالك
    full_name = forms.CharField(label='اسمك الكامل', max_length=200)
    username  = forms.CharField(label='اسم المستخدم', max_length=150)
    password  = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput, min_length=6)
    password2 = forms.CharField(label='تأكيد كلمة المرور', widget=forms.PasswordInput)

    def clean_country(self):
        code = self.cleaned_data['country']
        if code not in ARAB_COUNTRIES:
            raise forms.ValidationError('يرجى اختيار دولة صالحة.')
        return code

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('اسم المستخدم مستخدم بالفعل.')
        return username

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('password2'):
            self.add_error('password2', 'كلمتا المرور غير متطابقتين.')
        return data

    def save(self):
        from datetime import date, timedelta
        data = self.cleaned_data
        country_code = data['country']
        country_info = ARAB_COUNTRIES[country_code]

        # Determine intended plan (stored for sysadmin visibility)
        intended_plan = data.get('selected_plan', '').strip()
        if intended_plan not in VALID_PLANS:
            intended_plan = 'pro'

        # All new registrations start with a 30-day trial
        trial_start   = date.today()
        trial_expires = trial_start + timedelta(days=30)

        # Set limits based on intended plan
        PLAN_LIMITS = {
            'starter':    {'max_staff': 3,  'max_users': 2},
            'pro':        {'max_staff': 10, 'max_users': 5},
            'enterprise': {'max_staff': 50, 'max_users': 20},
        }
        limits = PLAN_LIMITS.get(intended_plan, PLAN_LIMITS['pro'])

        # Build unique slug
        base_slug = slugify(data['center_name']) or 'center'
        slug = base_slug
        n = 1
        while Center.objects.filter(slug=slug).exists():
            slug = f'{base_slug}-{n}'
            n += 1

        service_type = ServiceType.objects.filter(is_active=True).first()
        if service_type is None:
            service_type = ServiceType.objects.create(
                name='عام', icon='fas fa-spa', color='#ec4899', is_active=True,
            )

        center = Center.objects.create(
            name=data['center_name'],
            slug=slug,
            service_type=service_type,
            phone=data['phone'],
            city=data.get('city', ''),
            country=country_code,
            timezone=country_info['timezone'],
            currency=country_info['currency'],
            plan='trial',
            plan_start=trial_start,
            plan_expires=trial_expires,
            max_staff=limits['max_staff'],
            max_users=limits['max_users'],
        )

        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            full_name=data['full_name'],
            center=center,
            is_owner=True,
        )

        from apps.core.models import Settings
        Settings.objects.create(center=center)

        return user
