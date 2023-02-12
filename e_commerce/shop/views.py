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

from shop.models import Product


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Page not found</h1>")


class ShopHome(DataMixin, ListView):
    paginate_by = 20
    template_name = 'shop/home.html'
    context_object_name = 'products'

    def get_queryset(self):
        queryset = Product.objects.all().order_by('access_number').reverse().prefetch_related('productimage_set')[:100]
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
        context.update({**self.get_user_context(title='АМУНІЦІЯ ДЛЯ СВОЇХ'),
                        'page_range': page_range, 'super_category_flag': True,
                        'cartJson': json.dumps(cart), 'flag': flag})
        return context


class RegisterUser(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'
    extra_context = {'title': "Реєстрація"}

    def form_valid(self, form):
        user = form.save()
        Buyer.objects.create(user=user, name=user.username, email=user.email)
        login(self.request, user)
        response = HttpResponseRedirect(reverse('shop:home'))
        authorization_handler(self.request, response, user)
        return response


class ModLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = 'shop/register/login.html'
    next_page = 'shop:home'
    extra_context = {'title': "Авторизація"}

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        response = HttpResponseRedirect(self.get_success_url())
        # cookie_cart, items = json.loads(self.request.COOKIES.get('cart')), []
        # if cookie_cart:
        #     order, created = Order.objects.get_or_create(buyer=user.buyer, complete=False)
        #     if not created:
        #         items = OrderItem.objects.filter(order=order)
        #         for item in items:
        #             item.delete()
        #     for item in cookie_cart.items():
        #         OrderItem.objects.create(product=Product.objects.get(id=int(item[0][0])), order=order,
        #                                  quantity=int(list(item[1].values())[0]))
        # else:
        #     response.set_cookie('flag', 1, max_age=1)
        return authorization_handler(self.request, response, user)


class AdminLoginView(LoginView):
    template_name = 'shop/register/login.html'

    def form_valid(self, form):
        user = form.get_user()
        response = super().form_valid(form)
        try:
            buyer = user.buyer
        except ObjectDoesNotExist:
            buyer = None
        if buyer:
            lastOrder = Order.objects.filter(buyer=buyer).last()
            if lastOrder and not lastOrder.complete:
                items = OrderItem.objects.filter(order=lastOrder)
                for item in items:
                    item.delete()
                lastOrder.delete()
        cart = json.loads(self.request.COOKIES.get('cart'))
        if cart:
            response.delete_cookie('cart')
        return response


class ModPasswordChangeView(DataMixin, PasswordChangeView):
    success_url = 'shop:home'
    template_name = 'shop/register/password_change_form.html'
    extra_context = {'title': "Зміна паролю"}


class ModPasswordResetView(DataMixin, PasswordResetView):
    template_name = 'shop/register/password_reset_form.html'
    email_template_name = 'shop/register/password_reset_email.html'
    success_url = reverse_lazy('shop:password_reset_done')
    extra_context = {'title': "Скидання паролю"}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        return context


class ModPasswordResetDoneView(DataMixin, PasswordResetDoneView):
    template_name = 'shop/register/password_reset_done.html'
    extra_context = {'title': "Пароль скинутий"}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        return context


class ModPasswordResetConfirmView(DataMixin, PasswordResetConfirmView):
    template_name = 'shop/register/password_reset_confirm.html'
    success_url = reverse_lazy('shop:password_reset_complete')
    extra_context = {'title': "Підтвердження скидання паролю"}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        return context


class ModPasswordResetCompleteView(DataMixin, PasswordResetCompleteView):
    template_name = 'shop/register/password_reset_complete.html'
    extra_context = {'title': "Скидання паролю виконано"}

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context())
        return context


class UserAccount(DataMixin, UserPassesTestMixin, FormView, ABC):
    form_class = BuyerAccountForm
    template_name = 'shop/account.html'
    success_url = reverse_lazy('shop:home')

    def test_func(self, **kwargs):
        return self.request.user.id == self.kwargs['pk']

    def get_context_data(self, **kwargs):
        user = self.request.user
        orders = Order.objects.filter(buyer__user=user).select_related('buyer').prefetch_related(
            'sale_set', 'orderitem_set', 'orderitem_set__product').order_by('date_ordered').reverse()
        order_list = []
        for order in orders:
            sale = order.sale_set.all()[0] if order.complete else "Не оплачений"
            orderItems = order.orderitem_set.all()
            order_list.append((order, sale, orderItems))
        if order_list:
            buyer = order_list[0][0].buyer
        else:
            try:
                buyer = user.buyer
            except ObjectDoesNotExist:
                buyer = Buyer.objects.create(user=user, name=user.username, email=user.email)
        self.initial = {'tel': buyer.tel, 'address': buyer.address,
                        'name': buyer.name, 'email': buyer.email}
        context = super().get_context_data(**kwargs)
        context.update({**self.get_user_context(title="Персональна інформація"), 'order_list': order_list})
        return context


class UserChangeAccount(UserPassesTestMixin, UpdateView, ABC):
    form_class = BuyerAccountForm
    template_name = 'shop/account.html'
    success_url = reverse_lazy('shop:home')

    def test_func(self, **kwargs):
        return self.request.user.id == self.kwargs['pk']

    def get_queryset(self):
        return User.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_context = {'title': "Кабінет покупця", 'pk': self.kwargs['pk']}
        context.update(new_context)
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return HttpResponseRedirect(reverse('shop:home'))


class CategoryView(DataMixin, ListView):
    model = Product
    paginate_by = 20
    template_name = 'shop/category.html'
    context_object_name = 'products'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.object_list = None

    def get_context_data(self, *, object_list=None, **kwargs):
        data_context = self.get_user_context()
        categories, category_list = data_context['category_list'], []
        slug, id_super_category = self.kwargs['category_slug'], None
        for category in categories:
            if category.slug == slug:
                id_super_category = category.super_category.id
                break
        for category in categories:
            if category.super_category.id == id_super_category:
                category_list.append(category)
        products = Product.objects.filter(category__slug=slug).select_related('category', 'brand',
                                                                              'productimage',
                                                                              'category__super_category')
        brands = list({(product.brand.name, product.brand.name) for product in products})
        try:
            category = products[0].category if products else categories.get(slug=slug)
            product_list, title = get_product_list(products), category.name
        except ObjectDoesNotExist:
            category, title, product_list = categories[0], categories[0].name, []
        if self.request.POST:
            product_list = handling_brand_price_form(self.request.POST, product_list)
        context = super().get_context_data(object_list=product_list, **kwargs)
        category_list = category_list if category_list else data_context['category_list']
        page_range = None
        if context['is_paginated']:
            page_range = context['paginator'].get_elided_page_range(
                context['page_obj'].number, on_each_side=1, on_ends=1)
        new_context = {'title': title, 'category': category, 'categories': category_list,
                       'category_flag': True, 'brand_filter_form': BrandFilterForm(brands, auto_id=False),
                       'price_filter_form': PriceFilterForm(auto_id=False), 'page_range': page_range,
                       'brands': brands}
        context.update({**data_context, **new_context})
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)
        context['brand_filter_form'] = BrandFilterForm(context['brands'], self.request.POST, auto_id=False)
        context['price_filter_form'] = PriceFilterForm(self.request.POST, auto_id=False)
        return self.render_to_response(context)


class ProductView(DataMixin, DetailView):
    model = Product
    slug_url_kwarg = 'product_slug'
    template_name = 'shop/product.html'
    context_object_name = 'product'
    queryset = Product.objects.select_related(
        'productfeature', 'productimage', 'category', 'category__super_category',
        'category__categoryfeatures')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        product.last_accessed = datetime.datetime.now(tz=timezone.utc)
        product.access_number = 0 if product.access_number is None else product.access_number + 1
        product.save()
        title, lang = product.name, self.request.LANGUAGE_CODE
        category_features = (
            [v for k, v in model_to_dict(product.category.categoryfeatures).items() if k.endswith(lang)]
            if hasattr(product.category, 'categoryfeatures') else [])
        # category_features = CategoryFeatures.objects.filter(category=product.category)
        product_features = (list(model_to_dict(product.productfeature).values())[2:]
                            if hasattr(product, 'productfeature') else [])
        product_images = (list(model_to_dict(product.productimage).values())[2:]
                          if hasattr(product, 'productimage') else [])
        product_review = product.review_set.all().select_related('review_author')
        product_eval = 0
        for review in product_review:
            product_eval += review.grade
        product_eval = str(int(math.ceil(2 * product_eval / product_review.count()))) if product_review.count() else 0
        new_context = {'category_features': category_features, 'product_features': product_features,
                       'product_images': product_images, 'product_review': product_review, 'title': title,
                       'review_form': ReviewForm, 'product_eval': product_eval,
                       'super_category': product.category.super_category}
        context.update({**self.get_user_context(), **new_context})
        return context


class ReviewFormView(FormView):
    template_name = 'shop/product.html'
    form_class = ReviewForm

    def get_success_url(self):
        return reverse('shop:product', kwargs={'product_slug': self.kwargs['product_slug']})

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        slug = self.kwargs['product_slug']
        return HttpResponseRedirect(reverse('shop:product', kwargs={'product_slug': slug}))


def updateLike(request):
    data = json.loads(request.body)
    review = Review.objects.get(id=int(data['review']))
    author = User.objects.get(id=int(data['author']))
    like = True if data['like'] == 'True' else False
    dislike = False if like else True
    if not Like.objects.filter(review=review, like_author=author):
        Like.objects.create(review=review, like_author=author, like=like, dislike=dislike)
        if like:
            review.like_num = review.like_num + 1 if review.like_num else 1
        else:
            review.dislike_num = review.dislike_num + 1 if review.dislike_num else 1
        review.save()
        return JsonResponse('Like was added', safe=False)
    return JsonResponse('Like was not added', safe=False)


class SuperCategoryView(DataMixin, ListView):
    model = Category
    paginate_by = 20
    template_name = 'shop/super_category.html'
    context_object_name = 'categories'

    def get_context_data(self, *, object_list=None, **kwargs):
        pk = self.kwargs['super_category_pk']
        context_data = self.get_user_context()
        categories = context_data['category_list']
        category_list = []
        for category in categories:
            if category.super_category.id == pk:
                category_list.append(category)
        title = "Загальна категорія" if not category_list else category_list[0].super_category
        context = super().get_context_data(object_list=category_list, **kwargs)
        page_range = None
        if context['is_paginated']:
            page_range = context['paginator'].get_elided_page_range(
                context['page_obj'].number, on_each_side=1, on_ends=1)
        new_context = {'title': title, 'super_category_flag': True, 'page_range': page_range}
        context.update({**context_data, **new_context})
        return context


class SearchResultView(DataMixin, ListView):
    template_name = 'shop/search_results.html'
    paginate_by = 20
    context_object_name = 'products'

    def get_queryset(self):
        query = self.request.GET.get('q')
        return Product.objects.filter(name__icontains=query).select_related(
            'productimage'
        ).order_by('access_number').reverse()[:100]

    def get_context_data(self, *, object_list=None, **kwargs):
        object_list = get_product_list(self.get_queryset())
        context = super().get_context_data(object_list=object_list, **kwargs)
        page_range = None
        if context['is_paginated']:
            page_range = context['paginator'].get_elided_page_range(
                context['page_obj'].number, on_each_side=1, on_ends=1)
        context.update({**self.get_user_context(title="Пошук"), 'page_range': page_range,
                        'query': self.request.GET.get('q')})
        return context


class AboutView(DataMixin, TemplateView):
    template_name = 'shop/other/about.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Про нас"))
        return context


class TermsView(DataMixin, TemplateView):
    template_name = 'shop/other/terms.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Умови використання сайту"))
        return context


class ContactView(DataMixin, TemplateView):
    template_name = 'shop/other/contacts.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Контакти"))
        return context


class HelpView(DataMixin, TemplateView):
    template_name = 'shop/other/help.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Допомога"))
        return context


class DeliveryView(DataMixin, TemplateView):
    template_name = 'shop/other/delivery.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Доставка"))
        return context


class CreditView(DataMixin, TemplateView):
    template_name = 'shop/other/credit.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Кредит"))
        return context


class ReturnProductsView(DataMixin, TemplateView):
    template_name = 'shop/other/return_products.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Повернення товару"))
        return context


class ServiceCentersView(DataMixin, TemplateView):
    template_name = 'shop/other/service_centers.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Сервісні центри"))
        return context


class ForPartnersView(DataMixin, TemplateView):
    template_name = 'shop/other/for_partners.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_user_context(title="Партнерам"))
        return context


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    try:
        buyer = Buyer.objects.get(user=request.user)
    except ObjectDoesNotExist:
        buyer = None
    if buyer:
        product = Product.objects.get(id=productId)
        if not product.sold:
            order, created = Order.objects.get_or_create(buyer=buyer, complete=False)
            orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
            if action == 'add':
                orderItem.quantity += 1
            elif action == 'remove':
                orderItem.quantity -= 1
            orderItem.save()
            if orderItem.quantity <= 0:
                orderItem.delete()
        return JsonResponse('Item was added', safe=False)


class CartView(DataMixin, TemplateView):
    template_name = 'shop/cart.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        items, order, cartItems = get_cookies_cart(self.request)
        new_context = {'title': _('Корзина'), 'order': order, 'items': items, 'flag': True}
        context.update({**self.get_user_context(), **new_context})
        return context


class CheckoutView(CartView):
    template_name = 'shop/checkout.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user, cart = self.request.user, {}
        if user.is_authenticated:
            try:
                buyer = user.buyer
            except ObjectDoesNotExist:
                buyer = Buyer.objects.create(user=user, name=user.name, email=user.email)
            checkout_form = CheckoutForm(initial={'name': buyer.name, 'email': buyer.email,
                                                  'tel': buyer.tel, 'address': buyer.address})
        else:
            checkout_form = CheckoutForm()
        items, order = context['items'], context['order']
        message, items = check_quantity_in_stock(items)
        if message:
            cart, order = correct_cart_order(items, order)
        context.update({'title': 'Заказ', 'flag': False, 'checkout_form': checkout_form, 'message': message,
                        'items': items, 'order': order, 'cartJson': json.dumps(cart)})
        return context

    def post(self, request, *args, **kwargs):
        user, args = self.request.user, self.request.POST
        checkout_form = CheckoutForm(args)
        items, order, cartItems = get_cookies_cart(request)
        message, items = check_quantity_in_stock(items)
        if checkout_form.is_valid() and not message:
            data = checkout_form.cleaned_data
            if user.is_authenticated:
                order, created = Order.objects.get_or_create(buyer=user.buyer, complete=False)
                if not created:
                    orderItems = OrderItem.objects.filter(order=order)
                    for orderItem in orderItems:
                        orderItem.delete()
                user.buyer.name, user.buyer.email = data['name'], data['email']
                user.buyer.tel, user.buyer.address = data['tel'], data['address']
                user.buyer.save()
                order.complete = True
                order.save()
            else:
                buyer = Buyer.objects.create(name=data['name'], email=data['email'],
                                             tel=data['tel'], address=data['address'])
                order = Order.objects.create(buyer=buyer, complete=True)
            orderItems = []
            for item in items:
                orderItem = OrderItem.objects.create(product=Product.objects.get(id=int(item.product.id)),
                                                     order=order, quantity=int(item.quantity))
                orderItems.append(orderItem)
            items = orderItems
            Sale.objects.create(order=order, region=data['region'],
                                city=data['city'], department=data['department'])
            decreasing_stock_items(items)
            message = ''
            warning = None
            if items:
                message = _('Оплата прошла успешно')
                warning = ':)'
            return self.render_to_response({**self.get_context_data(), 'items': [], 'order': {'get_order_total': 0,
                                                                                              'get_order_items': 0},
                                            'message': message, 'warning': warning, 'cartJson': json.dumps({})})
        else:
            context = self.get_context_data()
            cart = {}
            if message:
                cart, order = correct_cart_order(items, order)
            context.update({'checkout_form': CheckoutForm(args), 'message': message,
                            'cartJson': json.dumps(cart)})
            return self.render_to_response(context)
