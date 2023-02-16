from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Buyer, Review, Sale, Order


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)


class UserAccountForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']


class UserCheckoutForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    class Meta:
        model = User
        fields = ['first_name', 'last_name']


class BuyerAccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tel'].required = True
        self.fields['address'].required = True
        self.fields['name'].required = True
        self.fields['email'].required = True

    class Meta:
        model = Buyer
        fields = ['name', 'email', 'tel', 'address']


class ReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['review_text'].widget = forms.Textarea(attrs={'rows': 4, 'cols': 80})

    class Meta:
        model = Review
        fields = ['grade', 'review_text', 'product', 'review_author']


class SaleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].widget = forms.HiddenInput()
        for field in self.Meta.required:
            self.fields[field].required = True

    class Meta:
        model = Sale
        fields = ['order', 'region', 'city', 'department']
        required = (
            'region',
            'city',
            'department',
        )


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=50, required=True, label="Ім'я")
    email = forms.EmailField(required=True, label="Пошта")
    tel = forms.CharField(max_length=15, min_length=8, required=True, label='Телефон')
    address = forms.CharField(max_length=30, required=True, label='Адреса')
    order = forms.ModelChoiceField(required=False, queryset=Order.objects.all(), widget=forms.HiddenInput())
    region = forms.CharField(max_length=80, required=True, label='Область')
    city = forms.CharField(max_length=80, required=True, label="Місто")
    department = forms.CharField(max_length=8, required=True, label="Відділення")


class BrandFilterForm(forms.Form):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brand'] = forms.MultipleChoiceField(choices=choices,
                                                         widget=forms.CheckboxSelectMultiple,
                                                         label="Бренд")


class PriceFilterForm(forms.Form):
    low = forms.DecimalField(
        label="Від",
        required=False,
        widget=forms.NumberInput(attrs={'style': 'width:70px; margin-right:5px'}))
    high = forms.DecimalField(label="До", required=False, widget=forms.NumberInput(attrs={'style': 'width:70px'}))
