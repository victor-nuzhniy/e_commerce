from typing import Tuple, List, Union
from decimal import Decimal

import pytest
from shop.models import Category, Brand, SuperCategory, ProductImage, Product, OrderItem
from tests.e_commerce.factories import (
    SuperCategoryFactory,
    CategoryFactory,
    BrandFactory,
    ProductFactory,
    ProductImageFactory,
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
