import factory

from shop.models import SuperCategory
from tests.bases import BaseModelFactory


class SuperCategoryFactory(BaseModelFactory):
    class Meta:
        model = SuperCategory

    name = factory.Faker('pystr', max_chars=50)
    icon = factory.django.ImageField(color="blue")

