from typing import List

import pytest
from django.http import QueryDict
from django.test import Client
from django.urls import reverse, reverse_lazy
import json
from django.contrib import admin
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from faker import Faker
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from shop.models import (
    Brand,
    Buyer,
    Category,
    CategoryFeatures,
    Income,
    Like,
    Order,
    OrderItem,
    PageData,
    Product,
    ProductFeature,
    ProductImage,
    Review,
    Sale,
    Stock,
    SuperCategory,
    Supplier,
    user_directory_path,
)
from shop.utils import (
    EmailBackend,
    DataMixin,
    NestedNamespace,
    check_quantity_in_stock,
    decreasing_stock_items,
    create_item,
    define_cart_from_cookies,
    get_cookies_cart,
    correct_cart_order,
    handling_brand_price_form,
    get_product_list,
    get_cart_item_quantity,
    create_cookie_cart,
    cart_authorization_handler,
    define_cart,
    define_page_range,
    clear_not_completed_order,
    define_order_list,
    define_buyer_data,
    define_category_with_super_category,
    define_category_list,
    define_brand_list,
    define_category_title_product_list,
    define_product_eval,
    modify_like_with_response,
    check_buyer_existence,
    perform_orderItem_actions,
    get_order_with_cleaning,
    update_buyer,
    get_order,
    get_order_items_list,
    get_message_and_warning,
    get_checkout_form,
    get_response_dict_with_sale_creation,
    get_updated_response_dict,
)
from shop.querysets import querysets
from tests.e_commerce.conftest import check_data_mixin, check_data_mixin_without_cart
from tests.e_commerce.factories import (
    BrandFactory,
    BuyerFactory,
    CategoryFactory,
    CategoryFeatureFactory,
    IncomeFactory,
    LikeFactory,
    OrderFactory,
    OrderItemFactory,
    PageDataFactory,
    ProductFactory,
    ProductFeatureFactory,
    ProductImageFactory,
    ReviewFactory,
    SaleFactory,
    StockFactory,
    SuperCategoryFactory,
    SupplierFactory,
    UserFactory,
)
from shop.forms import (
    BrandFilterForm,
    BuyerAccountForm,
    CheckoutForm,
    CustomUserCreationForm,
    PriceFilterForm,
    ReviewForm,
)
from django.contrib.auth.forms import (
    AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
)
from django.core.cache import cache
from django.contrib.auth.models import User

#
# @pytest.mark.django_db
# class TestHomeView:
#     pytestmark = pytest.mark.django_db
#
#     def test_home_view(
#             self, client: Client
#     ) -> None:
#         cache.clear()
#         url = reverse('shop:home')
#         products = get_product_list(
#             querysets.get_product_queryset_for_shop_home_view()
#         )
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert len(response.context['products']) == 20
#         for i, product in enumerate(response.context['products']):
#             assert product == products[i]
#         assert response.context['super_category_flag'] is True
#         assert response.context['cartJson'] == json.dumps({})
#         assert not response.context['flag']
#         assert response.context['page_data'] == PageData.objects.filter(name='home').first()
#
#     def test_home_view_next_page(
#             self, client: Client
#     ) -> None:
#         cache.clear()
#         url = reverse('shop:home')
#         products = get_product_list(
#             querysets.get_product_queryset_for_shop_home_view()
#         )
#         response = client.get(url, {'page': 2})
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert len(response.context['products']) == 20
#         for i, product in enumerate(response.context['products']):
#             assert product == products[i+20]
#         assert response.context['super_category_flag'] is True
#         assert response.context['cartJson'] == json.dumps({})
#         assert not response.context['flag']
#         assert response.context['page_data'] == PageData.objects.filter(name='home').first()
#
#
# @pytest.mark.django_db
# class TestRegisterUserView:
#     pytestmark = pytest.mark.django_db
#
#     def test_register_user_view_get(self, client: Client) -> None:
#         cache.clear()
#         url = reverse('shop:registration')
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert isinstance(response.context['form'], CustomUserCreationForm)
#         assert response.context['title'] == 'Реєстрація'
#
#     def test_register_user_view_post(self, client: Client, faker: Faker) -> None:
#         cache.clear()
#         url = reverse('shop:registration')
#         password = faker.pystr(min_chars=15, max_chars=20)
#         form_data = {
#             'username': faker.user_name(),
#             'password1': password,
#             'password2': password,
#         }
#         response = client.post(url, form_data)
#         assert response.status_code == 302
#         assert response.url == reverse('shop:home')
#
#
# @pytest.mark.django_db
# class TestModLoginView:
#     pytestmark = pytest.mark.django_db
#
#     def test_mod_login_view_get(self, client: Client, faker: Faker) -> None:
#         cache.clear()
#         url = reverse('shop:login')
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert isinstance(response.context['form'], AuthenticationForm)
#         assert response.context['title'] == 'Авторизація'
#
#     def test_mod_login_view_post(self, client: Client, faker: Faker) -> None:
#         url = reverse('shop:login')
#         password = faker.pystr(min_chars=15, max_chars=20)
#         user = User.objects.create_user(
#             faker.user_name(),
#             faker.email(),
#             password
#         )
#         form_data = {'username': user.username, 'password': password}
#         response = client.post(url, form_data)
#         assert response.status_code == 302
#         assert response.url == reverse('shop:home')
#
#
# @pytest.mark.django_db
# class TestAdminLoginView:
#     pytestmark = pytest.mark.django_db
#
#     def test_admin_login_view_get(self, client: Client, faker: Faker) -> None:
#         cache.clear()
#         url = reverse('login')
#         quantity = faker.pyint(min_value=1, max_value=10000)
#         cart = json.dumps({1: {'quantity': quantity}})
#         client.cookies.load({'cart': cart})
#         response = client.get(url)
#         check_data_mixin_without_cart(response)
#         assert response.context['cartItem'] == quantity
#         assert response.status_code == 200
#         assert isinstance(response.context['form'], AuthenticationForm)
#
#     def test_admin_login_view_post(self, client: Client, faker: Faker) -> None:
#         url = reverse('login')
#         quantity = faker.pyint(min_value=1, max_value=10000)
#         cart = json.dumps({1: {'quantity': quantity}})
#         client.cookies.load({'cart': cart})
#         password = faker.pystr(min_chars=15, max_chars=20)
#         user = User.objects.create_user(
#             faker.user_name(),
#             faker.email(),
#             password
#         )
#         user.is_staff = True
#         user.save()
#         form_data = {'username': user.username, 'password': password}
#         response = client.post(url, form_data)
#         assert response.status_code == 302
#         assert response.url == '/admin'
#
#
# @pytest.mark.django_db
# class TestModPasswordChangeView:
#     pytestmark = pytest.mark.django_db
#
#     def test_mod_password_change_view_get(self, client: Client, faker: Faker) -> None:
#         url = reverse('shop:registration')
#         password = faker.pystr(min_chars=15, max_chars=20)
#         username = faker.user_name()
#         form_data = {
#             'username': username, 'password1': password, 'password2': password
#         }
#         client.post(url, form_data)
#         client.login(username=username, password=password)
#         url = reverse('shop:password_change')
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert isinstance(response.context['form'], PasswordChangeForm)
#         assert response.context['title'] == 'Зміна паролю'
#
#
# @pytest.mark.django_db
# class TestModPasswordResetFormView:
#     pytestmark = pytest.mark.django_db
#
#     def test_mod_password_reset_form_view_get(self, client: Client) -> None:
#         url = reverse('shop:password_reset')
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert isinstance(response.context['form'], PasswordResetForm)
#         assert response.context['title'] == 'Скидання паролю'
#
#     def test_mod_password_reset_form_view_post(
#             self, client: Client, faker: Faker
#     ):
#         user = User.objects.create_user(
#             faker.user_name(), faker.email(), faker.pystr(min_chars=15, max_chars=20)
#         )
#         url = reverse('shop:password_reset')
#         form_data = {'email': user.email}
#         response = client.post(url, form_data)
#         assert response.status_code == 302
#         assert response.url == reverse('shop:password_reset_done')
#
#
# @pytest.mark.django_db
# class TestModPasswordResetDoneView:
#     pytestmark = pytest.mark.django_db
#
#     def test_mod_password_reset_done_view(self, client: Client) -> None:
#         url = reverse('shop:password_reset_done')
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert response.context['title'] == 'Пароль скинутий'
#
#
# @pytest.mark.django_db
# class TestModPasswordResetConfirmView:
#     pytestmark = pytest.mark.django_db
#
#     def test_mod_password_reset_confirm_view_get(
#             self, client: Client, faker: Faker
#     ) -> None:
#         user = User.objects.create_user(
#             faker.user_name(), faker.email(), faker.pystr(min_chars=15, max_chars=20)
#         )
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         token_generator = PasswordResetTokenGenerator()
#         token = token_generator.make_token(user)
#         url = reverse(
#             'shop:password_reset_confirm',
#             kwargs={'uidb64': uid, 'token': token}
#         )
#         response = client.get(url)
#         assert response.status_code == 302
#         assert response.url == f'/accounts/reset/{uid}/set-password/'
#         url = reverse(
#             'shop:password_reset_confirm',
#             kwargs={'uidb64': uid, 'token': 'set-password'}
#         )
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert isinstance(response.context['form'], SetPasswordForm)
#         assert response.context['title'] == 'Підтвердження скидання паролю'
#
#     def test_mod_password_reset_confirm_view_post(
#             self, client: Client, faker: Faker
#     ) -> None:
#         user = User.objects.create_user(
#             faker.user_name(), faker.email(), faker.pystr(min_chars=15, max_chars=20)
#         )
#         uid = urlsafe_base64_encode(force_bytes(user.pk))
#         token_generator = PasswordResetTokenGenerator()
#         token = token_generator.make_token(user)
#         url = reverse(
#             'shop:password_reset_confirm',
#             kwargs={'uidb64': uid, 'token': token}
#         )
#         response = client.get(url)
#         assert response.status_code == 302
#         assert response.url == f'/accounts/reset/{uid}/set-password/'
#         url = reverse(
#             'shop:password_reset_confirm',
#             kwargs={'uidb64': uid, 'token': 'set-password'}
#         )
#         new_password = faker.pystr(min_chars=15, max_chars=20)
#         post_data = {'new_password1': new_password, 'new_password2': new_password}
#         response = client.post(url, post_data)
#         assert response.status_code == 302
#         assert response.url == reverse('shop:password_reset_complete')
#
#
# @pytest.mark.django_db
# class TestModPasswordResetCompleteView:
#     pytestmark = pytest.mark.django_db
#
#     def test_mod_password_reset_complete_view(self, client: Client) -> None:
#         url = reverse('shop:password_reset_complete')
#         response = client.get(url)
#         check_data_mixin(response)
#         assert response.status_code == 200
#         assert response.context['title'] == 'Скидання паролю виконано'


@pytest.mark.django_db
class TestUserAccountView:
    pytestmark = pytest.mark.django_db

    def test_user_account_view_get(self, client: Client, faker: Faker) -> None:
        cache.clear()
        user_id = faker.random_int(min=1, max=5)
        url = reverse('shop:user_account', kwargs={'pk': user_id})
        user = User.objects.get(id=user_id)
        buyer = Buyer.objects.get(user=user)
        orders = querysets.get_order_queryset_for_user_account_view(user)
        order_list = define_order_list(orders)
        client.login(username=f'username_{user_id}', password='fyukbqcrbq zpsr11')
        response = client.get(url)
        check_data_mixin(response)
        expected_form_data = response.context['form']
        assert response.status_code == 200
        for i, order in enumerate(response.context['order_list']):
            assert order[0] == order_list[i][0]
            assert order[1] == order_list[i][1]
            for j, orderitem in enumerate(order[2]):
                assert orderitem == order_list[i][2][j]
        assert expected_form_data['tel'].value() == buyer.tel
        assert expected_form_data['address'].value() == buyer.address
        assert expected_form_data['name'].value() == buyer.name
        assert expected_form_data['email'].value() == buyer.email
        assert response.context['title'] == 'Персональна інформація'

    def test_user_account_view_post(self, client: Client, faker: Faker) -> None:
        cache.clear()
        user_id = faker.random_int(min=1, max=5)
        url = reverse('shop:user_account', kwargs={'pk': user_id})
        user = User.objects.get(id=user_id)
        client.login(username=f'username_{user_id}', password='fyukbqcrbq zpsr11')
        form_data = {
            'name': faker.first_name(),
            'email': faker.email(),
            'tel': faker.pystr(min_chars=5, max_chars=12),
            'address': faker.pystr(min_chars=10, max_chars=30)
        }
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == reverse('shop:home')


@pytest.mark.django_db
class TestCategoryView:
    pytestmark = pytest.mark.django_db

    def test_category_view_get(self, client: Client, faker: Faker) -> None:
        cache.clear()
        categories_for_slug = Category.objects.only('name', 'slug')
        category_id = faker.random_int(max=len(categories_for_slug) - 1)
        slug = categories_for_slug[category_id].slug
        categories = querysets.get_category_queryset_for_data_mixin()
        category_list = define_category_list(slug, categories)
        products = querysets.get_product_queryset_for_category_view(slug)
        category, title, product_list = define_category_title_product_list(
            products, slug, categories
        )
        product_list = handling_brand_price_form(QueryDict(), product_list)
        brands = define_brand_list(products)
        url = reverse('shop:category', kwargs={'category_slug': slug})
        response = client.post(url)
        page_range = response.context['page_range']
        assert response.status_code == 200
        assert response.context['title'] == title
        assert response.context['category'] == category
        for i, product in enumerate(response.context['products']):
            assert product == product_list[i]
        assert response.context['category_flag'] is True
        for i, category in enumerate(response.context['categories']):
            assert category == category_list[i]
        assert isinstance(response.context['brand_filter_form'], BrandFilterForm)
        assert isinstance(response.context['price_filter_form'], PriceFilterForm)
        assert isinstance(page_range, List) if page_range else True
        for i, brand in enumerate(response.context['brands']):
            assert brand == brands[i]
        assert response.context['page_data'] is None

    def test_category_view_post(self, client: Client, faker: Faker) -> None:
        cache.clear()
        categories_for_slug = Category.objects.only('name', 'slug')
        category_id = faker.random_int(max=len(categories_for_slug)-1)
        slug = categories_for_slug[category_id].slug
        categories = querysets.get_category_queryset_for_data_mixin()
        category_list = define_category_list(slug, categories)
        products = querysets.get_product_queryset_for_category_view(slug)
        category, title, product_list = define_category_title_product_list(
            products, slug, categories
        )
        brands = define_brand_list(products)
        brand = brands[faker.random_int(max=len(brands)-1)][0]
        product_list = handling_brand_price_form(
            QueryDict(f'brand={brand}'), product_list
        )
        form_data = {'brand': brand}
        url = reverse('shop:category', kwargs={'category_slug': slug})
        response = client.post(url, form_data)
        page_range = response.context['page_range']
        assert response.status_code == 200
        assert response.context['title'] == title
        assert response.context['category'] == category
        for i, product in enumerate(response.context['products']):
            assert product == product_list[i]
        assert response.context['category_flag'] is True
        for i, category in enumerate(response.context['categories']):
            assert category == category_list[i]
        assert isinstance(response.context['brand_filter_form'], BrandFilterForm)
        assert isinstance(response.context['price_filter_form'], PriceFilterForm)
        assert isinstance(page_range, List) if page_range else True
        for i, brand in enumerate(response.context['brands']):
            assert brand == brands[i]
        assert response.context['page_data'] is None


@pytest.mark.django_db
class TestProductView:
    pytestmark = pytest.mark.django_db

    def test_product_view_get(self, client: Client, faker: Faker) -> None:
        products = Product.objects.only('slug')
        slug = products[faker.random_int(max=len(products)-1)].slug
        product = querysets.get_product_queryset_for_product_view().get(slug=slug)
        access_number = product.access_number
        last_access_at = product.last_access_at
        title = product.name
        product_features = querysets.get_product_features_queryset_for_product_view(
            product=product
        )
        product_images = querysets.get_product_image_queryset_for_product_view(product)
        product_review = querysets.get_review_queryset_for_product_view(product)
        product_eval = define_product_eval(product_review)
        url = reverse('shop:product', kwargs={'product_slug': slug})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context['product'] == product
        for i, feature in enumerate(response.context['product_features']):
            assert feature == product_features[i]
        for i, image in enumerate(response.context['product_images']):
            assert image == product_images[i]
        for i, review in enumerate(response.context['product_review']):
            assert review == product_review[i]
        assert response.context['title'] == title
        assert response.context['review_form'] == ReviewForm
        assert response.context['product_eval'] == product_eval
        assert response.context['super_category'] == product.category.super_category
        assert response.context['product'].last_access_at != last_access_at
        assert Product.objects.get(slug=slug).access_number == access_number + 1


@pytest.mark.django_db
class TestReviewFormView:
    pytestmark = pytest.mark.django_db

    def test_review_form_view(self, client: Client, faker: Faker) -> None:
        products = Product.objects.only('slug')
        product = products[faker.random_int(max=len(products)-1)]
        user_id = faker.random_int(min=1, max=5)
        client.login(username=f'username_{user_id}', password='fyukbqcrbq zpsr11')
        url = reverse('shop:product_form', kwargs={'product_slug': product.slug})
        form_data = {
            'grade': faker.random_int(min=1, max=5),
            'review_text': faker.pystr(min_chars=1, max_chars=255),
            'product': product.id,
            'review_author': user_id,
        }
        response = client.post(url, form_data)
        expected_review = Review.objects.last()
        assert response.status_code == 302
        assert response.url == reverse(
            'shop:product', kwargs={'product_slug': product.slug}
        )
        assert expected_review.product.id == product.id
        assert expected_review.grade == form_data['grade']
        assert expected_review.review_text == form_data['review_text']
        assert expected_review.review_author.id == user_id
