from typing import Tuple, List, Union
from decimal import Decimal
from faker import Faker
from django.contrib.auth.models import User
import pytest
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


@pytest.fixture(scope="function")
def products_preparation_for_view_testing(faker: Faker) -> None:
    super_categories: List[SuperCategory] = SuperCategoryFactory.create_batch(size=2)
    categories = [
        CategoryFactory(super_category=super_categories[0]) for _ in range(5)
    ] + [
        CategoryFactory(super_category=super_categories[1]) for _ in range(5)
    ]
    brands: List[Brand] = BrandFactory.create_batch(size=2)
    users: List[User] = UserFactory.create_batch(size=5)
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
