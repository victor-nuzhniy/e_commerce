import pytest

from shop.models import SuperCategory
from tests.bases import BaseModelFactory
from tests.e_commerce.factories import SuperCategoryFactory


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
