import pytest
from django.test import Client
from django.urls import reverse
import json
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


@pytest.mark.django_db
class TestHomeView:
    pytestmark = pytest.mark.django_db

    def test_home_view(
            self, client: Client
    ) -> None:
        cache.clear()
        url = reverse('shop:home')
        products = get_product_list(
            querysets.get_product_queryset_for_shop_home_view()
        )
        response = client.get(url)
        check_data_mixin(response)
        assert response.status_code == 200
        assert len(response.context['products']) == 20
        for i, product in enumerate(response.context['products']):
            assert product == products[i]
        assert response.context['super_category_flag'] is True
        assert response.context['cartJson'] == json.dumps({})
        assert not response.context['flag']
        assert response.context['page_data'] == PageData.objects.filter(name='home').first()

    def test_home_view_next_page(
            self, client: Client
    ) -> None:
        cache.clear()
        url = reverse('shop:home')
        products = get_product_list(
            querysets.get_product_queryset_for_shop_home_view()
        )
        response = client.get(url, {'page': 2})
        check_data_mixin(response)
        assert response.status_code == 200
        assert len(response.context['products']) == 20
        for i, product in enumerate(response.context['products']):
            assert product == products[i+20]
        assert response.context['super_category_flag'] is True
        assert response.context['cartJson'] == json.dumps({})
        assert not response.context['flag']
        assert response.context['page_data'] == PageData.objects.filter(name='home').first()


# @pytest.mark.django_db
# class TestRegisterUser:
#     pytestmark = pytest.django_db
