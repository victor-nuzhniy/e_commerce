from decimal import Decimal
from typing import List
import copy
import pytest
from faker import Faker

from django.http import HttpRequest
from shop.utils import (
    EmailBackend,
    DataMixin,
    NestedNamespace,
    check_quantity_in_stock,
)
from shop.forms import CheckoutForm, CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from shop.querysets import querysets
from django.core.cache import cache
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


@pytest.mark.django_db
def test_email_backend_authenticate(faker: Faker) -> None:
    password = faker.pystr(min_chars=20, max_chars=40)
    user = User.objects.create_user(
        username=faker.user_name(),
        password=password,
        email=faker.email(),
        first_name=faker.first_name(),
        last_name=faker.last_name(),
    )
    email_backend = EmailBackend()
    assert user == email_backend.authenticate(
        request=HttpRequest(),
        username=user.username,
        password=password,
    )
    assert user == email_backend.authenticate(
        request=HttpRequest(),
        username=user.email,
        password=password,
    )
    assert email_backend.authenticate(
        request=HttpRequest(),
        username=user.username,
        password=str(faker.pyint())
    ) is None


@pytest.mark.django_db
def test_email_backend_get_user(faker: Faker) -> None:
    password = faker.pystr(min_chars=20, max_chars=40)
    user = User.objects.create_user(
        username=faker.user_name(),
        password=password,
        email=faker.email(),
        first_name=faker.first_name(),
        last_name=faker.last_name(),
    )
    email_backend = EmailBackend()
    assert user == email_backend.get_user(user.id)
    assert email_backend.get_user(faker.pyint()) is None


@pytest.mark.django_db
def test_data_mixin_get_user_context_without_cache(faker: Faker) -> None:
    keys = [faker.pystr() for _ in range(5)]
    context = {key: faker.pystr() for key in keys}
    SuperCategoryFactory.create_batch(size=4)
    CategoryFactory.create_batch(size=4)
    data_mixin = DataMixin()
    setattr(data_mixin, 'request', HttpRequest())
    cache.clear()
    expected_result = data_mixin.get_user_context(**context)
    assert expected_result['user_creation_form'].__class__ is CustomUserCreationForm
    assert expected_result['user_login_form'].__class__ is AuthenticationForm
    assert expected_result['cartItem'] == 0
    for key, value in context.items():
        assert expected_result[key] == value
    super_categories = querysets.get_super_category_queryset_for_data_mixin()
    for super_category in expected_result['super_categories']:
        assert super_category in super_categories
    categories = querysets.get_category_queryset_for_data_mixin()
    for category in expected_result['category_list']:
        assert category in categories


@pytest.mark.django_db
def test_data_mixin_get_user_context_with_cache(faker: Faker) -> None:
    keys = [faker.pystr() for _ in range(5)]
    context = {key: faker.pystr() for key in keys}
    SuperCategoryFactory.create_batch(size=4)
    CategoryFactory.create_batch(size=4)
    data_mixin = DataMixin()
    setattr(data_mixin, 'request', HttpRequest())
    expected_result = data_mixin.get_user_context(**context)
    assert expected_result['user_creation_form'].__class__ is CustomUserCreationForm
    assert expected_result['user_login_form'].__class__ is AuthenticationForm
    assert expected_result['cartItem'] == 0
    for key, value in context.items():
        assert expected_result[key] == value
    super_categories = cache.get("super_categories")
    if not super_categories:
        super_categories = querysets.get_super_category_queryset_for_data_mixin()
    for super_category in expected_result['super_categories']:
        assert super_category in super_categories
    categories = cache.get("category_list")
    if not categories:
        categories = querysets.get_category_queryset_for_data_mixin()
    for category in expected_result['category_list']:
        assert category in categories


def test_nested_name_space(faker: Faker) -> None:
    name_space = NestedNamespace({
        'product': {
            'id': faker.pyint(),
            'name': faker.first_name(),
            'price': faker.pydecimal(),
        }
    })
    assert name_space.product.id.__class__ is int
    assert name_space.product.__class__ is NestedNamespace
    assert name_space.product.name.__class__ is str
    assert name_space.product.price.__class__ is Decimal


@pytest.mark.django_db
def test_check_quantity_in_stock_empty_message() -> None:
    stocks: List[Stock] = StockFactory.create_batch(size=5)
    items = []
    for stock in stocks:
        ProductImageFactory(product=stock.product)
        items.append(NestedNamespace({
            "product": {
                "id": stock.product.id,
                "name": stock.product.name,
                "price": stock.product.price,
                "productimage": {"image": stock.product.productimage_set},
            },
            "quantity": stock.quantity,
            "get_total": stock.quantity * stock.price,
        }))
    expected_result = check_quantity_in_stock(items)
    assert expected_result[0] == ''
    assert expected_result[1] == items


@pytest.mark.django_db
def test_check_quantity_in_stock_lower_message() -> None:
    stocks: List[Stock] = StockFactory.create_batch(size=5)
    items, quantities = [], []
    for stock in stocks:
        ProductImageFactory(product=stock.product)
        items.append(NestedNamespace({
            "product": {
                "id": stock.product.id,
                "name": stock.product.name,
                "price": stock.product.price,
                "productimage": {"image": stock.product.productimage_set},
            },
            "quantity": stock.quantity + 1,
            "get_total": stock.quantity * stock.price,
        }))
        quantities.append(stock.quantity + 1)
    expected_result = check_quantity_in_stock(items)
    assert expected_result[0] == ("Нажаль, в одній позиції зі списку виникли зміни."
                                  "Поки Ви оформлювали покупку, товар був придбаний"
                                  " іншим покупцем."
                                  "Приносимо свої вибачення.")
    assert expected_result[1] == items
    for index, item in enumerate(expected_result[1]):
        assert item.quantity == quantities[index] - 1


@pytest.mark.django_db
def test_check_quantity_in_stock_higher_message() -> None:
    stocks: List[Stock] = StockFactory.create_batch(size=5)
    items = []
    for stock in stocks:
        ProductImageFactory(product=stock.product)
        items.append(NestedNamespace({
            "product": {
                "id": stock.product.id,
                "name": stock.product.name,
                "price": stock.product.price,
                "productimage": {"image": stock.product.productimage_set},
            },
            "quantity": stock.quantity - 1,
            "get_total": stock.quantity * stock.price,
        }))
    expected_result = check_quantity_in_stock(items)
    assert expected_result[0] == ''
    assert expected_result[1] == items
