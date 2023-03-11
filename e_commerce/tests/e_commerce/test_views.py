import pytest
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
from tests.e_commerce.conftest import check_data_mixin
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
from shop.forms import CheckoutForm, CustomUserCreationForm
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

@pytest.mark.django_db
class TestModLoginView:
    pytestmark = pytest.mark.django_db

    def test_mod_login_view_get(self, client: Client, faker: Faker) -> None:
        cache.clear()
        url = reverse('shop:login')
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert isinstance(response.context['form'], AuthenticationForm)
        assert response.context['title'] == 'Авторизація'

    def test_mod_login_view_post(self, client: Client, faker: Faker) -> None:
        url = reverse('shop:login')
        password = faker.pystr(min_chars=15, max_chars=20)
        user = User.objects.create_user(
            faker.user_name(),
            faker.email(),
            password
        )
        form_data = {'username': user.username, 'password': password}
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == reverse('shop:home')


@pytest.mark.django_db
class TestAdminLoginView:
    pytestmark = pytest.mark.django_db

    def test_admin_login_view_get(self, client: Client, faker: Faker) -> None:
        cache.clear()
        url = reverse('login')
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert isinstance(response.context['form'], AuthenticationForm)

    def test_admin_login_view_post(self, client: Client, faker: Faker) -> None:
        url = reverse('login')
        password = faker.pystr(min_chars=15, max_chars=20)
        user = User.objects.create_user(
            faker.user_name(),
            faker.email(),
            password
        )
        user.is_staff = True
        user.save()
        form_data = {'username': user.username, 'password': password}
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == '/admin'


@pytest.mark.django_db
class TestModPasswordChangeView:
    pytestmark = pytest.mark.django_db

    def test_mod_password_change_view_get(self, client: Client, faker: Faker) -> None:
        url = reverse('shop:registration')
        password = faker.pystr(min_chars=15, max_chars=20)
        username = faker.user_name()
        form_data = {
            'username': username, 'password1': password, 'password2': password
        }
        client.post(url, form_data)
        client.login(username=username, password=password)
        url = reverse('shop:password_change')
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert isinstance(response.context['form'], PasswordChangeForm)
        assert response.context['title'] == 'Зміна паролю'


@pytest.mark.django_db
class TestModPasswordResetFormView:
    pytestmark = pytest.mark.django_db

    def test_mod_password_reset_form_view_get(self, client: Client) -> None:
        url = reverse('shop:password_reset')
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert isinstance(response.context['form'], PasswordResetForm)
        assert response.context['title'] == 'Скидання паролю'

    def test_mod_password_reset_form_view_post(
            self, client: Client, faker: Faker
    ):
        user = User.objects.create_user(
            faker.user_name(), faker.email(), faker.pystr(min_chars=15, max_chars=20)
        )
        url = reverse('shop:password_reset')
        form_data = {'email': user.email}
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == reverse('shop:password_reset_done')


@pytest.mark.django_db
class TestModPasswordResetDoneView:
    pytestmark = pytest.mark.django_db

    def test_mod_password_reset_done_view(self, client: Client) -> None:
        url = reverse('shop:password_reset_done')
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert response.context['title'] == 'Пароль скинутий'


@pytest.mark.django_db
class TestModPasswordResetConfirmView:
    pytestmark = pytest.mark.django_db

    def test_mod_password_reset_confirm_view_get(
            self, client: Client, faker: Faker
    ) -> None:
        user = User.objects.create_user(
            faker.user_name(), faker.email(), faker.pystr(min_chars=15, max_chars=20)
        )
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        url = reverse(
            'shop:password_reset_confirm',
            kwargs={'uidb64': uid, 'token': token}
        )
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f'/accounts/reset/{uid}/set-password/'
        url = reverse(
            'shop:password_reset_confirm',
            kwargs={'uidb64': uid, 'token': 'set-password'}
        )
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert isinstance(response.context['form'], SetPasswordForm)
        assert response.context['title'] == 'Підтвердження скидання паролю'
