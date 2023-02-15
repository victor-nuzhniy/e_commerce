import math
from abc import ABC

from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import prefetch_related_objects
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
        queryset = Product.objects.all().order_by(
            'access_number'
        ).prefetch_related("productimage_set").reverse()[:100]
        return get_product_list(queryset)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        page_range = define_page_range(context)
        flag = self.request.COOKIES.get('flag')
        cart = define_cart(flag, self.request.user)
        context.update({
            **self.get_user_context(title='АМУНІЦІЯ ДЛЯ СВОЇХ'),
            'page_range': page_range,
            'super_category_flag': True,
            'cartJson': json.dumps(cart),
            'flag': flag,
        })
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
        return authorization_handler(self.request, response, user)


class ModLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = 'shop/register/login.html'
    next_page = 'shop:home'
    extra_context = {'title': "Авторизація"}

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        response = HttpResponseRedirect(self.get_success_url())
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
        clear_not_completed_order(buyer)
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
        orders = Order.objects.filter(
            buyer__user=user
        ).select_related('buyer').prefetch_related(
            'sale_set', 'orderitem_set', 'orderitem_set__product'
        ).order_by('date_ordered').reverse()
        order_list = define_order_list(orders)
        self.initial = define_buyer_data(order_list, user)
        context = super().get_context_data(**kwargs)
        context.update({
            **self.get_user_context(title="Персональна інформація"),
            'order_list': order_list
        })
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
        categories, slug = data_context['category_list'], self.kwargs['category_slug']

        category_list = define_category_list(slug, data_context['category_list'])
        products = Product.objects.filter(
            category__slug=slug
        ).select_related(
            'category', 'brand', 'category__super_category'
        ).prefetch_related('productimage_set')

        brands = define_brand_list(products)

        category, title, product_list = define_category_title_product_list(
            products, slug, categories
        )
        product_list = handling_brand_price_form(self.request.POST, product_list)

        context = super().get_context_data(object_list=product_list, **kwargs)
        category_list = category_list if category_list else data_context['category_list']
        page_range = define_page_range(context)
        new_context = {
            'title': title,
            'category': category,
            'categories': category_list,
            'category_flag': True,
            'brand_filter_form': BrandFilterForm(brands, auto_id=False),
            'price_filter_form': PriceFilterForm(auto_id=False),
            'page_range': page_range,
            'brands': brands,
        }
        context.update({**data_context, **new_context})
        return context

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data(**kwargs)
        context['brand_filter_form'] = BrandFilterForm(
            context['brands'], self.request.POST, auto_id=False
        )
        context['price_filter_form'] = PriceFilterForm(
            self.request.POST, auto_id=False
        )
        return self.render_to_response(context)


class ProductView(DataMixin, DetailView):
    model = Product
    slug_url_kwarg = 'product_slug'
    template_name = 'shop/product.html'
    context_object_name = 'product'
    queryset = Product.objects.select_related(
        'category', 'category__super_category'
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = context['product']
        product.last_accessed = datetime.datetime.now(tz=timezone.utc)
        product.access_number = F('access_number') + 1
        product.save()
        title = product.name
        product_features = ProductFeature.objects.filter(
            product=product
        ).select_related('feature_name')
        product_images = ProductImage.objects.filter(product=product)
        product_review = product.review_set.all().select_related('review_author')
        product_eval = define_product_eval(product_review)
        new_context = {'product_features': product_features,
                       'product_images': product_images,
                       'product_review': product_review,
                       'title': title,
                       'review_form': ReviewForm,
                       'product_eval': product_eval,
                       'super_category': product.category.super_category,
                       }
        context.update({**self.get_user_context(), **new_context})
        return context


class ReviewFormView(FormView):
    template_name = 'shop/product.html'
    form_class = ReviewForm

    def get_success_url(self):
        return reverse(
            'shop:product', kwargs={'product_slug': self.kwargs['product_slug']}
        )

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        slug = self.kwargs['product_slug']
        return HttpResponseRedirect(
            reverse('shop:product', kwargs={'product_slug': slug})
        )


def updateLike(request):
    data = json.loads(request.body)
    review = Review.objects.get(id=int(data['review']))
    author = User.objects.get(id=int(data['author']))
    like = True if data['like'] == 'True' else False
    dislike = False if like else True
    return modify_like_with_response(review, author, like, dislike)


class SuperCategoryView(DataMixin, ListView):
    model = Category
    paginate_by = 20
    template_name = 'shop/super_category.html'
    context_object_name = 'categories'

    def get_context_data(self, *, object_list=None, **kwargs):
        pk = self.kwargs['super_category_pk']
        context_data = self.get_user_context()
        categories = context_data['category_list']
        category_list = define_category_with_super_category(categories, pk)
        title = "Загальна категорія" if not category_list else category_list[0].super_category
        context = super().get_context_data(object_list=category_list, **kwargs)
        page_range = define_page_range(context)
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
        page_range = define_page_range(context)
        context.update({
            **self.get_user_context(title="Пошук"),
            'page_range': page_range,
            'query': self.request.GET.get('q'),
        })
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
    user = request.user
    if buyer := check_buyer_existence(user):
        perform_orderItem_actions(productId, action, buyer)
        return JsonResponse('Item was added', safe=False)


class CartView(DataMixin, TemplateView):
    template_name = 'shop/cart.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        items, order, cartItems = get_cookies_cart(self.request)
        new_context = {
            'title': 'Корзина', 'order': order, 'items': items, 'flag': True
        }
        context.update({**self.get_user_context(), **new_context})
        return context


class CheckoutView(CartView):
    template_name = 'shop/checkout.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user, cart = self.request.user, {}
        checkout_form = get_checkout_form(user)

        items, order = context['items'], context['order']
        message, items = check_quantity_in_stock(items)
        if message:
            cart, order = correct_cart_order(items, order)
        context.update({
            'title': 'Заказ',
            'flag': False,
            'checkout_form': checkout_form,
            'message': message,
            'items': items,
            'order': order,
            'cartJson': json.dumps(cart)
        })
        return context

    def post(self, request, *args, **kwargs):
        user, args = self.request.user, self.request.POST
        checkout_form = CheckoutForm(args)
        items, order, cartItems = get_cookies_cart(request)
        message, items = check_quantity_in_stock(items)
        if checkout_form.is_valid() and not message:
            return self.render_to_response({
                **self.get_context_data(),
                **get_response_dict_with_sale_creation(checkout_form, user, items),
            })
        else:
            return self.render_to_response(get_updated_response_dict(
                    self.get_user_context(),
                    message,
                    items,
                    order,
                    args,
                ))
