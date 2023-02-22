from faker import Faker
import pytest
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
from slugify import slugify
from tests.bases import BaseModelFactory
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
)


@pytest.mark.django_db
class TestSuperCategory:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=SuperCategoryFactory, model=SuperCategory
        )

    def test_get_absolute_url(self) -> None:
        super_category: SuperCategory = SuperCategoryFactory()
        expected_result = f'/super_category/{super_category.id}/'
        assert expected_result == super_category.get_absolute_url()

    def test__str__(self) -> None:
        obj: SuperCategory = SuperCategoryFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestCategory:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=CategoryFactory, model=Category)

    def test_get_absolute_url(self) -> None:
        category: SuperCategory = CategoryFactory()
        expected_result = f'/category/{category.slug}/'
        assert expected_result == category.get_absolute_url()

    def test__str__(self) -> None:
        obj: Category = CategoryFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestCategoryFeature:
    pystestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=CategoryFeatureFactory, model=CategoryFeatures
        )

    def test__str__(self) -> None:
        obj: CategoryFeatures = CategoryFeatureFactory()
        expected_result = obj.feature_name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestBrand:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=BrandFactory, model=Brand)

    def test__str__(self) -> None:
        obj: Brand = BrandFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestSupplier:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=SupplierFactory, model=Supplier)

    def test__str__(self) -> None:
        obj: Supplier = SupplierFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestProduct:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=ProductFactory, model=Product)

    def test_get_absolute_url(self) -> None:
        product: Product = ProductFactory()
        expected_result = f'/product/{product.slug}/'
        assert expected_result == product.get_absolute_url()

    def test__str__(self) -> None:
        obj: Product = ProductFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestProductFeature:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=ProductFeatureFactory, model=ProductFeature
        )

    def test__str__(self) -> None:
        obj: ProductFeature = ProductFeatureFactory()
        expected_result = obj.feature
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestProductImage:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=ProductImageFactory, model=ProductImage
        )

    def test__str__(self) -> None:
        obj: ProductImage = ProductImageFactory()
        expected_result = "Image"
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestReview:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=ReviewFactory, model=Review)

    def test__str__(self) -> None:
        obj: Review = ReviewFactory()
        expected_result = obj.product.name + "-review"
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestLike:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=LikeFactory, model=Like)

    def test__str__(self) -> None:
        obj: Like = LikeFactory()
        expected_result = "Likes"
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestIncome:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=IncomeFactory, model=Income)

    def test__str__(self) -> None:
        obj: Income = IncomeFactory()
        expected_result = str(obj.income_date)
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestBuyer:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=BuyerFactory, model=Buyer)

    def test__str__(self) -> None:
        obj: Buyer = BuyerFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestOrder:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=OrderFactory, model=Order)

    def test__str__(self) -> None:
        obj: Order = OrderFactory()
        expected_result = str(obj.ordered_at)
        assert expected_result == obj.__str__()

    def test_get_order_total(self) -> None:
        order: Order = OrderFactory()
        orderitems = [OrderItemFactory(order=order) for _ in range(5)]
        expected_result = sum([item.get_total for item in orderitems])
        assert expected_result == order.get_order_total

    def test_get_order_items(self) -> None:
        order: Order = OrderFactory()
        orderitems = [OrderItemFactory(order=order) for _ in range(5)]
        expected_result = sum([item.quantity for item in orderitems])
        assert expected_result == order.get_order_items


@pytest.mark.django_db
class TestOrderItem:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=OrderItemFactory, model=OrderItem)

    def test__str__(self) -> None:
        obj: OrderItem = OrderItemFactory()
        expected_result = obj.product.name
        assert expected_result == obj.__str__()

    def test_get_total(self) -> None:
        orderitem: OrderItem = OrderItemFactory()
        expected_result = orderitem.product.price * orderitem.quantity
        assert expected_result == orderitem.get_total


@pytest.mark.django_db
class TestSale:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=SaleFactory, model=Sale)

    def test__str__(self) -> None:
        obj: Sale = SaleFactory()
        expected_result = str(obj.sale_date)
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestStock:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=StockFactory, model=Stock)

    def test__str__(self) -> None:
        obj: Stock = StockFactory()
        expected_result = obj.product.name
        assert expected_result == obj.__str__()

    def test_get_price_total(self) -> None:
        stock: Stock = StockFactory()
        expected_result = stock.quantity * stock.price
        assert expected_result == stock.get_price_total


@pytest.mark.django_db
class TestPageData:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(factory_class=PageDataFactory, model=PageData)

    def test__str__(self) -> None:
        obj: PageData = PageDataFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
def test_user_directory_path(faker: Faker) -> None:
    objects = [(obj(), faker.pystr(min_chars=10, max_chars=15)) for obj in (
        SuperCategoryFactory, CategoryFactory, ProductImageFactory, PageDataFactory
    )]
    for obj, filename in objects:
        name = obj.product.name if isinstance(obj, ProductImage) else obj.name
        expected_result = "{0}_{1}/{2}".format(
            obj.__class__.__name__.lower(), slugify(name), filename
        )
        assert expected_result == user_directory_path(obj, filename)
