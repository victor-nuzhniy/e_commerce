import pytest
from django.test import Client
from django.urls import reverse
import json
from django.contrib import admin
from faker import Faker
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
from django.contrib.auth.forms import AuthenticationForm
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
        # user.is_staff = True
        # user.save()
        form_data = {'username': user.username, 'password': password}
        response = client.post(url, form_data)
        assert response.status_code == 302
        assert response.url == '/admin'
