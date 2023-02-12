import math
from abc import ABC

from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetView, PasswordResetDoneView, \
    PasswordResetConfirmView, PasswordResetCompleteView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, FormView, TemplateView
from django.forms.models import model_to_dict
from .utils import *
import json
import datetime

from e_commerce.shop.models import Product


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Page not found</h1>")


class ShopHome(DataMixin, ListView):
    paginate_by = 20
    template_name = 'shop/home.html'
    context_object_name = 'products'

    def get_queryset(self):
        queryset = Product.objects.all().order_by('access_number').reverse().select_related('productimage')[:100]
        return get_product_list(queryset)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        page_range = None
        if context['is_paginated']:
            page_range = context['paginator'].get_elided_page_range(
                context['page_obj'].number, on_each_side=1, on_ends=1)
        flag, cart = self.request.COOKIES.get('flag'), {}
        if flag:
            order = Order.objects.filter(buyer__user=self.request.user).last()
            if order and not order.complete:
                items = OrderItem.objects.filter(order=order)
                cart = create_cookie_cart(items)
        context.update({**self.get_user_context(title='Moby'),
                        'page_range': page_range, 'super_category_flag': True,
                        'cartJson': json.dumps(cart), 'flag': flag})
        return context


class RegisterUser(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    extra_context = {'title': _("Регистрация")}

    def form_valid(self, form):
        user = form.save()
        Buyer.objects.create(user=user, name=user.username, email=user.email)
        login(self.request, user)
        response = HttpResponseRedirect(reverse('shop:home'))
        authorization_handler(self.request, response, user)
        return response

