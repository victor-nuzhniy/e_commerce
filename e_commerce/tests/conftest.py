import random
import pytest
from typing import Tuple, List, Union
from decimal import Decimal
from django.core.management import call_command
from faker import Faker
from django.contrib.auth.models import User

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


@pytest.fixture(scope="function", autouse=True)
def faker_seed() -> None:
    """Generate random seed for Faker instance."""
    return random.seed(version=3)


@pytest.fixture()
def products_preparation_for_view_testing(faker: Faker) -> None:
    """
    This fixture is used for creating 'data.json' file for creating initial
    data for test database. To invoke this fixture you have to set scope='function',
    autouse=True as fixture decorator argument and once run test with one test function.
    The 'data.json' file will be created in tests folder. It may be need to
    convert 'data.json' code to 'utf-8', use 'NotePad' for that. There is a
    need to comment custom django_db_setup fixture below.
    """
    super_categories: List[SuperCategory] = SuperCategoryFactory.create_batch(size=2)
    categories = [
        CategoryFactory(super_category=super_categories[0]) for _ in range(5)
    ] + [
        CategoryFactory(super_category=super_categories[1]) for _ in range(5)
    ]
    brands: List[Brand] = BrandFactory.create_batch(size=2)
    users = [
        User.objects.create_user(
            username=f'username_{i+1}',
            email=f'username_{i+1}@user.com',
            password='fyukbqcrbq zpsr11'
        ) for i in range(5)
    ]
    buyers = [BuyerFactory(user=user) for user in users]
    suppliers: List[Supplier] = SupplierFactory.create_batch(size=2)
    [CategoryFeatureFactory.create_batch(size=3, category=category) for category in categories]
    products = []
    for category in categories:
        for i, brand in enumerate(brands):
            products += ProductFactory.create_batch(
                size=2,
                category=category,
                brand=brand,
                sold=False,
            )
    for product in products:
        for category_feature in product.category.categoryfeatures_set.all():
            ProductFeatureFactory(
                product=product, feature_name=category_feature
            )
        ProductImageFactory.create_batch(size=3, product=product)
        reviews = ReviewFactory.create_batch(
            size=2, product=product, review_author=users[faker.random_int(min=0, max=4)]
        )
        for review in reviews:
            LikeFactory(
                review=review, like_author=users[faker.random_int(min=0, max=4)]
            )
        income = IncomeFactory(
            product=product,
            supplier=suppliers[faker.random_int(min=0, max=1)],
            income_quantity=10,
        )
        StockFactory(
            product=product,
            income=income,
            supplier=income.supplier,
            quantity=5,
        )
        order = OrderFactory(buyer=buyers[faker.random_int(min=0, max=4)], complete=True)
        OrderItemFactory(product=product, order=order, quantity=5)
        SaleFactory(order=order)
    call_command('dumpdata', exclude=['contenttypes'], output='data.json')


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    'data.json' file have to be created using
    product_preparation_for_view_testing fixture
    """
    with django_db_blocker.unblock():
        call_command('loaddata', 'data.json')

