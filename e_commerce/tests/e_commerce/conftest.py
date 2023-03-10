from typing import Tuple, List, Union
from decimal import Decimal
from faker import Faker
from django.contrib.auth.models import User
import pytest
from shop.querysets import querysets
from shop.forms import CheckoutForm, CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from shop.models import (
    Category,
    Brand,
    SuperCategory,
    ProductImage,
    Product,
    OrderItem,
    Supplier,
)
from tests.e_commerce.factories import (
    SuperCategoryFactory,
    CategoryFactory,
    CategoryFeatureFactory,
    BrandFactory,
    ProductFactory,
    ProductFeatureFactory,
    ProductImageFactory,
    SupplierFactory,
    UserFactory,
    BuyerFactory,
    ReviewFactory,
    LikeFactory,
    IncomeFactory,
    StockFactory,
    OrderFactory,
    OrderItemFactory,
    SaleFactory,
)


@pytest.fixture(scope="function")
def preparation_for_filter_testing() -> Tuple[str, str, List[Tuple[Product, str]]]:
    super_category: SuperCategory = SuperCategoryFactory()
    category: Category = CategoryFactory(super_category=super_category)
    brand_1: Brand = BrandFactory()
    brand_2: Brand = BrandFactory()
    products = [
                   ProductFactory(
                       category=category, price=Decimal(i), brand=brand_1
                   ) for i in range(10, 60, 10)
               ] + [
                   ProductFactory(
                       category=category, price=Decimal(i), brand=brand_2
                   ) for i in range(10, 60, 10)
               ]
    [ProductImage(product=product) for product in products]
    product_list = [
        (
            product, ProductImageFactory(product=product).image
        ) for product in products
    ]
    return brand_1.name, brand_2.name, product_list


def find_instance(
        elements: List[OrderItem], value: Union[str, int], attr: str
) -> OrderItem:
    for elem in elements:
        if getattr(elem.product, attr) == value:
            return elem


def check_data_mixin(response: HttpResponse) -> None:
    super_categories = querysets.get_super_category_queryset_for_data_mixin()
    category_list = querysets.get_category_queryset_for_data_mixin().order_by('id')
    for i, category in enumerate(response.context['category_list']):
        assert category == category_list[i]
    for i, super_category in enumerate(response.context['super_categories']):
        assert super_category == super_categories[i]
    assert isinstance(response.context['user_creation_form'], CustomUserCreationForm)
    assert isinstance(response.context['user_login_form'], AuthenticationForm)
    assert response.context['cartItem'] == 0

