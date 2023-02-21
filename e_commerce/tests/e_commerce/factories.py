import factory
from slugify import slugify
from pytz import utc
from shop.models import (
    SuperCategory,
    Category,
    CategoryFeatures,
    Brand,
    Supplier,
    Product,
    ProductFeature,
    ProductImage,
    Review,
    Like,
    Income,
    Buyer,
    Order,
    OrderItem,
    Sale,
    Stock,
    PageData,
)
from django.contrib.auth.models import User
from tests.bases import BaseModelFactory


class SuperCategoryFactory(BaseModelFactory):
    class Meta:
        model = SuperCategory
        exclude = ('category_set',)

    name = factory.Faker('pystr', min_chars=1, max_chars=50)
    icon = factory.django.ImageField(color="yellow")
    category_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.CategoryFactory',
        factory_related_name='category_set',
        size=0,
    )


class CategoryFactory(BaseModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('slug', 'super_category')
        exclude = ('category_feature_set', 'product_set')

    name = factory.Faker('pystr', min_chars=1, max_chars=100)
    slug = factory.LazyAttribute(function=lambda obj: slugify(str(obj.name)))
    super_category = factory.SubFactory(factory=SuperCategoryFactory)
    icon = factory.django.ImageField(color='yellow')
    category_feature_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.CategoryFeatureFactory',
        factory_related_name='category_feature_set',
        size=0,
    )
    product_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.ProductFactory',
        factory_related_name='product_set',
        size=0,
    )


class CategoryFeatureFactory(BaseModelFactory):
    class Meta:
        model = CategoryFeatures
        django_get_or_create = ('category',)
        exclude = ('product_feature_set',)

    category = factory.SubFactory(factory=CategoryFactory)
    feature_name = factory.Faker('pystr', min_chars=1, max_chars=100)
    product_feature_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.ProductFeatureFactory',
        factory_related_name='product_feature_set',
        size=0,
    )


class BrandFactory(BaseModelFactory):
    class Meta:
        model = Brand
        django_get_or_create = ('slug',)
        exclude = ('product_set',)

    name = factory.Faker('pystr', min_chars=1, max_chars=100)
    slug = factory.LazyAttribute(function=lambda obj: slugify(str(obj.name)))
    product_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.ProductFactory',
        factory_related_name='product_set',
        size=0
    )


class SupplierFactory(BaseModelFactory):
    class Meta:
        model = Supplier
        exclude = ('income_set', 'stock_set')

    name = factory.Faker('pystr', min_chars=1, max_chars=150)
    inn = factory.Faker('pystr', max_chars=15)
    pdv = factory.Faker('pystr', max_chars=15)
    egrpou = factory.Faker('pystr', max_chars=15)
    bank = factory.Faker('pystr', max_chars=50)
    mfo = factory.Faker('pystr', max_chars=8)
    checking_account = factory.Faker('pystr', max_chars=50)
    tel = factory.Faker('pystr', max_chars=15)
    email = factory.Faker('email')
    person = factory.Faker('first_name')
    creation_date = factory.Faker('date')
    income_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.IncomeFactory',
        factory_related_name='income_set',
        size=0,
    )
    stock_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.StockFactory',
        factory_related_name='stock_set',
        size=0,
    )


class ProductFactory(BaseModelFactory):
    class Meta:
        model = Product
        django_get_or_create = ('slug', 'brand', 'category')
        exclude = (
            'productfeature_set',
            'productimage_set',
            'review_set',
            'income_set',
            'orderitem_set',
            'stock_set',
        )

    name = factory.Faker('pystr', max_chars=150)
    model = factory.Faker('pystr', max_chars=50)
    slug = factory.LazyAttribute(function=lambda obj: slugify(str(obj.model)))
    brand = factory.SubFactory(factory=BrandFactory)
    description = factory.Faker('pystr', min_chars=1)
    category = factory.SubFactory(factory=CategoryFactory)
    vendor_code = factory.Faker('pystr', min_chars=1, max_chars=50)
    price = factory.Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    sold = factory.Faker('pybool')
    notes = factory.Faker('pystr', max_chars=200)
    last_accessed_at = factory.Faker('date_time', tzinfo=utc)
    access_number = factory.Faker('pyint')
    productfeature_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.ProductFeatureFactory',
        factory_related_name='productfeature_set',
        size=0,
    )
    productimage_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.ProductImageFactory',
        factory_related_name='productimage_set',
        size=0,
    )
    review_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.ReviewFactory',
        factory_related_name='review_set',
        size=0,
    )
    income_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.IncomeFactory',
        factory_related_name='income_set',
        size=0,
    )
    orderitem_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.OrderItemFactory',
        factory_related_name='orderitem_set',
        size=0,
    )
    stock_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.StockFactory',
        factory_related_name='stock_set',
        size=0,
    )

    @factory.post_generation
    def supplier(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for supplier in extracted:
                self.supplier.add(supplier)


class ProductFeatureFactory(BaseModelFactory):
    class Meta:
        model = ProductFeature
        django_get_or_create = ('product', 'feature_name')

    product = factory.SubFactory(factory=ProductFactory)
    feature_name = factory.SubFactory(factory=CategoryFeatureFactory)
    feature = factory.Faker('pystr', max_chars=100)


class ProductImageFactory(BaseModelFactory):
    class Meta:
        model = ProductImage
        django_get_or_create = ('product',)

    product = factory.SubFactory(factory=ProductFactory)
    image = factory.django.ImageField(color='red')


class ReviewFactory(BaseModelFactory):
    class Meta:
        model = Review
        django_get_or_create = ('product', 'review_author')

    product = factory.SubFactory(factory=ProductFactory)
    grade = factory.Faker('pyint', max_value=5)
    review_text = factory.Faker('pystr', max_chars=255)
    review_date = factory.Faker('date')
    review_author = factory.SubFactory(factory='tests.e_commerce.factories.UserFactory')
    like_num = factory.Faker('pyint', max_value=10000)
    dislike_num = factory.Faker('pyint', max_value=10000)


class UserFactory(BaseModelFactory):
    class Meta:
        model = User
        exclude = ('review_set', 'like_set', 'buyer')

    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    email = factory.Faker('email')
    is_staff = factory.Faker('pybool')
    is_active = factory.Faker('pybool')
    review_set = factory.RelatedFactoryList(
        factory=ReviewFactory,
        factory_related_name='review_set',
        size=0,
    )
    like_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.LikeFactory',
        factory_related_name='like_set',
        size=0,
    )
    buyer = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.BuyerFactory',
        factory_related_name='buyer',
        size=0,
    )


class LikeFactory(BaseModelFactory):
    class Meta:
        model = Like
        django_get_or_create = ('review', 'like_author')

    review = factory.SubFactory(factory=ReviewFactory)
    like = factory.Faker('pybool')
    dislike = factory.Faker('pybool')
    like_author = factory.SubFactory(factory=UserFactory)


class IncomeFactory(BaseModelFactory):
    class Meta:
        model = Income
        django_get_or_create = ('product', 'supplier')
        exclude = ('stock_set',)

    product = factory.SubFactory(factory=ProductFactory)
    income_quantity = factory.Faker('pyint', min_value=1, max_value=10000)
    income_price = factory.Faker(
        'pydecimal', left_digits=8, right_digits=2, positive=True
    )
    supplier = factory.SubFactory(factory=SupplierFactory)
    income_date = factory.Faker('date')
    stock_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.StockFactory',
        factory_related_name='stock_set',
        size=0,
    )


class BuyerFactory(BaseModelFactory):
    class Meta:
        model = Buyer
        django_get_or_create = ('user',)
        exclude = ('order_set',)

    user = factory.SubFactory(factory='tests.e_commerce.factories.UserFactory')
    name = factory.Faker('first_name')
    email = factory.Faker('email')
    tel = factory.Faker('pystr', min_chars=12, max_chars=15)
    address = factory.Faker('pystr', max_chars=30)
    order_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.OrderFactory',
        factory_related_name='order_set',
        size=0,
    )


class OrderFactory(BaseModelFactory):
    class Meta:
        model = Order
        django_get_or_create = ('buyer',)
        exclude = ('orderitem_set', 'sale_set')

    buyer = factory.SubFactory(factory=BuyerFactory)
    ordered_at = factory.Faker('date_time', tzinfo=utc)
    complete = factory.Faker('pybool')
    orderitem_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.OrderItemFactory',
        factory_related_name='orderitem_set',
        size=0,
    )
    sale_set = factory.RelatedFactoryList(
        factory='tests.e_commerce.factories.SaleFactory',
        factory_related_name='sale_set',
        size=0,
    )


class OrderItemFactory(BaseModelFactory):
    class Meta:
        model = OrderItem
        django_get_or_create = ('product', 'order')

    product = factory.SubFactory(factory=ProductFactory)
    order = factory.SubFactory(factory=OrderFactory)
    quantity = factory.Faker('pyint')
    added_at = factory.Faker('date_time', tzinfo=utc)


class SaleFactory(BaseModelFactory):
    class Meta:
        model = Sale
        django_get_or_create = ('order',)

    order = factory.SubFactory(factory=OrderFactory)
    sale_date = factory.Faker('date')
    region = factory.Faker('pystr', max_chars=80)
    city = factory.Faker('pystr', max_chars=80)
    department = factory.Faker('pystr', max_chars=6)


class StockFactory(BaseModelFactory):
    class Meta:
        model = Stock
        django_get_or_create = ('product',)

    product = factory.SubFactory(factory=ProductFactory)
    income = factory.SubFactory(factory=IncomeFactory)
    quantity = factory.Faker('pyint', min_value=1)
    price = factory.Faker('pydecimal', left_digits=8, right_digits=2, positive=True)
    supplier = factory.SubFactory(factory=SupplierFactory)


class PageDataFactory(BaseModelFactory):
    class Meta:
        model = PageData

    page_name = factory.Faker('pystr', min_chars=1, max_chars=50)
    banner = factory.django.ImageField(color='black')
    image_1 = factory.django.ImageField(color='green')
    image_2 = factory.django.ImageField(color='blue')
    image_3 = factory.django.ImageField(color='white')
    header_1 = factory.Faker('pystr', max_chars=255)
    header_2 = factory.Faker('pystr', max_chars=255)
    header_3 = factory.Faker('pystr', max_chars=255)
    text_1 = factory.Faker('pystr')
    text_2 = factory.Faker('pystr')
    text_3 = factory.Faker('pystr')
