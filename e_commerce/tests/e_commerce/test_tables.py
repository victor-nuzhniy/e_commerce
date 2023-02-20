import pytest

from shop.models import SuperCategory, Category
from tests.bases import BaseModelFactory
from tests.e_commerce.factories import (
    SuperCategoryFactory,
    CategoryFactory,
)


@pytest.mark.django_db
class TestSuperCategory:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=SuperCategoryFactory, model=SuperCategory
        )

    def test__str__(self) -> None:
        obj: SuperCategory = SuperCategoryFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestCategory:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=CategoryFactory, model=Category
        )

    def test__str__(self) -> None:
        obj: Category = CategoryFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()
