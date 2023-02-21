import tempfile
from django.test import override_settings
import pytest

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
from tests.bases import BaseModelFactory
from tests.e_commerce.factories import (
    SuperCategoryFactory,
    CategoryFactory,
    CategoryFeatureFactory,
    BrandFactory,
    SupplierFactory,
    ProductFactory,
    ProductFeatureFactory,
    ProductImageFactory,
    ReviewFactory,
    LikeFactory,
    IncomeFactory,
    BuyerFactory,
    OrderFactory,
    OrderItemFactory,
    SaleFactory,
    StockFactory,
    PageDataFactory,
)


@pytest.mark.django_db
class TestSuperCategory:
    pytestmark = pytest.mark.django_db

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=SuperCategoryFactory, model=SuperCategory
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test__str__(self) -> None:
        obj: SuperCategory = SuperCategoryFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestCategory:
    pytestmark = pytest.mark.django_db

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=CategoryFactory, model=Category
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
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

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=BrandFactory, model=Brand
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test__str__(self) -> None:
        obj: Brand = BrandFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestSupplier:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=SupplierFactory, model=Supplier
        )

    def test__str__(self) -> None:
        obj: Supplier = SupplierFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestProduct:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=ProductFactory, model=Product
        )

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

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=ProductImageFactory, model=ProductImage
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test__str__(self) -> None:
        obj: ProductImage = ProductImageFactory()
        expected_result = "Image"
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestReview:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=ReviewFactory, model=Review
        )

    def test__str__(self) -> None:
        obj: Review = ReviewFactory()
        expected_result = obj.product.name + "-review"
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestLike:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=LikeFactory, model=Like
        )

    def test__str__(self) -> None:
        obj: Like = LikeFactory()
        expected_result = "Likes"
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestIncome:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=IncomeFactory, model=Income
        )

    def test__str__(self) -> None:
        obj: Income = IncomeFactory()
        expected_result = str(obj.income_date)
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestBuyer:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=BuyerFactory, model=Buyer
        )

    def test__str__(self) -> None:
        obj: Buyer = BuyerFactory()
        expected_result = obj.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestOrder:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=OrderFactory, model=Order
        )

    def test__str__(self) -> None:
        obj: Order = OrderFactory()
        expected_result = str(obj.ordered_at)
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestOrderItem:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=OrderItemFactory, model=OrderItem
        )

    def test__str__(self) -> None:
        obj: OrderItem = OrderItemFactory()
        expected_result = obj.product.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestSale:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=SaleFactory, model=Sale
        )

    def test__str__(self) -> None:
        obj: Sale = SaleFactory()
        expected_result = str(obj.sale_date)
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestStock:
    pytestmark = pytest.mark.django_db

    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=StockFactory, model=Stock
        )

    def test__str__(self) -> None:
        obj: Stock = StockFactory()
        expected_result = obj.product.name
        assert expected_result == obj.__str__()


@pytest.mark.django_db
class TestPageData:
    pytestmark = pytest.mark.django_db

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_factory(self) -> None:
        BaseModelFactory.check_factory(
            factory_class=PageDataFactory, model=PageData
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test__str__(self) -> None:
        obj: PageData = PageDataFactory()
        expected_result = obj.page_name
        assert expected_result == obj.__str__()

