import factory
from slugify import slugify

from shop.models import (
    SuperCategory,
    Category,
    CategoryFeatures,
)
from tests.bases import BaseModelFactory


class SuperCategoryFactory(BaseModelFactory):
    class Meta:
        model = SuperCategory
        exclude = ('category_set',)

    name = factory.Faker('pystr', min_chars=1, max_chars=50)
    icon = factory.django.ImageField(color="blue")
    category_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.CategoryFactory',
        factory_related_name='category_set',
        size=0,
    )


class CategoryFactory(BaseModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug', 'super_category')
        exclude = ('category_feature_set', 'seq')

    seq = factory.Sequence(lambda x: x)
    name = factory.Faker('pystr', min_chars=1, max_chars=100)
    slug = factory.LazyAttribute(function=lambda obj: slugify(str(obj.name)))
    super_category = factory.SubFactory(factory=SuperCategoryFactory)
    icon = factory.django.ImageField(color='yellow')
    category_feature_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.CategoryFeatureFactory',
        factory_related_name='category_feature_set',
        size=0,
    )


class CategoryFeatureFactory(BaseModelFactory):
    class Meta:
        model = CategoryFeatures
        django_get_or_create = ('category',)

    category = factory.SubFactory(factory=CategoryFactory)
    feature_name = factory.Faker('pystr', min_chars=1, max_chars=100)


