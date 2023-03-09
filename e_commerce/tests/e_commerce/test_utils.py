import json
import math
from decimal import Decimal
from typing import List, Tuple
import copy
import pytest
from django.db.models import Prefetch, Subquery, OuterRef, QuerySet
from django.urls import reverse
from faker import Faker
from tests.e_commerce.conftest import find_instance
from django.core.paginator import Paginator

from django.http import HttpRequest, QueryDict, HttpResponseRedirect, JsonResponse
from shop.utils import (
    EmailBackend,
    DataMixin,
    NestedNamespace,
    check_quantity_in_stock,
    decreasing_stock_items,
    create_item,
    define_cart_from_cookies,
    get_cookies_cart,
    correct_cart_order,
    handling_brand_price_form,
    get_product_list,
    get_cart_item_quantity,
    create_cookie_cart,
    cart_authorization_handler,
    define_cart,
    define_page_range,
    clear_not_completed_order,
    define_order_list,
    define_buyer_data,
    define_category_with_super_category,
    define_category_list,
    define_brand_list,
    define_category_title_product_list,
    define_product_eval,
    modify_like_with_response,
    check_buyer_existence,
    perform_orderItem_actions,
    get_order_with_cleaning,
    update_buyer,
    get_order,
    get_order_items_list,
    get_message_and_warning,
    get_checkout_form,
    get_response_dict_with_sale_creation,
    get_updated_response_dict,
)
from shop.forms import CheckoutForm, CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, AnonymousUser
from shop.querysets import querysets
from django.core.cache import cache
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
    UserFactory,
)


@pytest.mark.django_db
class TestEmailBackend:
    pytestmark = pytest.mark.django_db

    def test_email_backend_authenticate(self, faker: Faker) -> None:
        password = faker.pystr(min_chars=20, max_chars=40)
        user = User.objects.create_user(
            username=faker.user_name(),
            password=password,
            email=faker.email(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
        )
        email_backend = EmailBackend()
        assert user == email_backend.authenticate(
            request=HttpRequest(),
            username=user.username,
            password=password,
        )
        assert user == email_backend.authenticate(
            request=HttpRequest(),
            username=user.email,
            password=password,
        )
        assert email_backend.authenticate(
            request=HttpRequest(),
            username=user.username,
            password=str(faker.pyint())
        ) is None

    def test_email_backend_get_user(self, faker: Faker) -> None:
        password = faker.pystr(min_chars=20, max_chars=40)
        user = User.objects.create_user(
            username=faker.user_name(),
            password=password,
            email=faker.email(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
        )
        email_backend = EmailBackend()
        assert user == email_backend.get_user(user.id)
        assert email_backend.get_user(faker.pyint()) is None


@pytest.mark.django_db
class TestDataMixin:
    pytestmark = pytest.mark.django_db

    def test_data_mixin_get_user_context_without_cache(self, faker: Faker) -> None:
        keys = [faker.pystr() for _ in range(5)]
        context = {key: faker.pystr() for key in keys}
        SuperCategoryFactory.create_batch(size=4)
        CategoryFactory.create_batch(size=4)
        data_mixin = DataMixin()
        setattr(data_mixin, 'request', HttpRequest())
        cache.clear()
        expected_result = data_mixin.get_user_context(**context)
        assert expected_result['user_creation_form'].__class__ is CustomUserCreationForm
        assert expected_result['user_login_form'].__class__ is AuthenticationForm
        assert expected_result['cartItem'] == 0
        for key, value in context.items():
            assert expected_result[key] == value
        super_categories = querysets.get_super_category_queryset_for_data_mixin()
        for super_category in expected_result['super_categories']:
            assert super_category in super_categories
        categories = querysets.get_category_queryset_for_data_mixin()
        for category in expected_result['category_list']:
            assert category in categories

    def test_data_mixin_get_user_context_with_cache(self, faker: Faker) -> None:
        keys = [faker.pystr() for _ in range(5)]
        context = {key: faker.pystr() for key in keys}
        SuperCategoryFactory.create_batch(size=4)
        CategoryFactory.create_batch(size=4)
        data_mixin = DataMixin()
        setattr(data_mixin, 'request', HttpRequest())
        expected_result = data_mixin.get_user_context(**context)
        assert expected_result['user_creation_form'].__class__ is CustomUserCreationForm
        assert expected_result['user_login_form'].__class__ is AuthenticationForm
        assert expected_result['cartItem'] == 0
        for key, value in context.items():
            assert expected_result[key] == value
        super_categories = cache.get("super_categories")
        if not super_categories:
            super_categories = querysets.get_super_category_queryset_for_data_mixin()
        for super_category in expected_result['super_categories']:
            assert super_category in super_categories
        categories = cache.get("category_list")
        if not categories:
            categories = querysets.get_category_queryset_for_data_mixin()
        for category in expected_result['category_list']:
            assert category in categories


def test_nested_name_space(faker: Faker) -> None:
    name_space = NestedNamespace({
        'product': {
            'id': faker.pyint(),
            'name': faker.first_name(),
            'price': faker.pydecimal(),
        }
    })
    assert name_space.product.id.__class__ is int
    assert name_space.product.__class__ is NestedNamespace
    assert name_space.product.name.__class__ is str
    assert name_space.product.price.__class__ is Decimal


@pytest.mark.django_db
class TestCheckQuantityInStock:
    pytestmark = pytest.mark.django_db

    def test_check_quantity_in_stock_empty_message(self) -> None:
        stocks: List[Stock] = StockFactory.create_batch(size=5)
        items = []
        for stock in stocks:
            ProductImageFactory(product=stock.product)
            items.append(NestedNamespace({
                "product": {
                    "id": stock.product.id,
                    "name": stock.product.name,
                    "price": stock.product.price,
                    "productimage": {"image": stock.product.productimage_set},
                },
                "quantity": stock.quantity,
                "get_total": stock.quantity * stock.price,
            }))
        expected_result = check_quantity_in_stock(items)
        assert expected_result[0] == ''
        assert expected_result[1] == items

    def test_check_quantity_in_stock_lower_message(self) -> None:
        stocks: List[Stock] = StockFactory.create_batch(size=5)
        items, quantities = [], []
        for stock in stocks:
            ProductImageFactory(product=stock.product)
            items.append(NestedNamespace({
                "product": {
                    "id": stock.product.id,
                    "name": stock.product.name,
                    "price": stock.product.price,
                    "productimage": {"image": stock.product.productimage_set},
                },
                "quantity": stock.quantity + 1,
                "get_total": stock.quantity * stock.price,
            }))
            quantities.append(stock.quantity + 1)
        expected_result = check_quantity_in_stock(items)
        assert expected_result[0] == ("Нажаль, в одній позиції зі списку виникли зміни."
                                      "Поки Ви оформлювали покупку, товар був придбаний"
                                      " іншим покупцем."
                                      "Приносимо свої вибачення.")
        assert expected_result[1] == items
        for index, item in enumerate(expected_result[1]):
            assert item.quantity == quantities[index] - 1

    def test_check_quantity_in_stock_higher_message(self) -> None:
        stocks: List[Stock] = StockFactory.create_batch(size=5)
        items = []
        for stock in stocks:
            ProductImageFactory(product=stock.product)
            items.append(NestedNamespace({
                "product": {
                    "id": stock.product.id,
                    "name": stock.product.name,
                    "price": stock.product.price,
                    "productimage": {"image": stock.product.productimage_set.first()},
                },
                "quantity": stock.quantity - 1,
                "get_total": stock.quantity * stock.price,
            }))
        expected_result = check_quantity_in_stock(items)
        assert expected_result[0] == ''
        assert expected_result[1] == items


@pytest.mark.django_db
class TestDecreasingStockItems:
    pytestmark = pytest.mark.django_db

    def test_decreasing_stock_items_empty_many_products(self) -> None:
        order: Order = OrderFactory()
        OrderItemFactory.create_batch(size=5, order=order)
        orderitems = OrderItem.objects.all()
        for orderitem in orderitems:
            StockFactory(
                product=orderitem.product,
                quantity=orderitem.quantity,
                price=orderitem.product.price,
                income=IncomeFactory(product=orderitem.product)
            )
        decreasing_stock_items(orderitems)
        expected_stock_result = Stock.objects.count()
        expected_product_result = Product.objects.all()
        assert not expected_stock_result
        for product in expected_product_result:
            assert product.sold

    def test_decreasing_stock_items_empty_one_product(self) -> None:
        order: Order = OrderFactory()
        product: Product = ProductFactory()
        OrderItemFactory.create_batch(size=5, order=order, product=product)
        orderitems = OrderItem.objects.all()
        for orderitem in orderitems:
            StockFactory(
                product=product,
                quantity=orderitem.quantity,
                price=orderitem.product.price,
                income=IncomeFactory(product=product)
            )
        decreasing_stock_items(orderitems)
        expected_stock_result = Stock.objects.count()
        expected_product_result = Product.objects.all()
        assert not expected_stock_result
        for product in expected_product_result:
            assert product.sold

    def test_decreasing_stock_items_not_empty(self) -> None:
        order: Order = OrderFactory()
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(
            size=5, order=order
        )
        stock_quantity_list = []
        for i, orderitem in enumerate(orderitems):
            StockFactory(
                product=orderitem.product,
                quantity=orderitem.quantity + i + 1,
                price=orderitem.product.price,
            )
            stock_quantity_list.append(i+1)
        decreasing_stock_items(orderitems)
        expected_result = Stock.objects.all()
        for i, stock in enumerate(expected_result):
            assert stock.quantity == stock_quantity_list[i]


@pytest.mark.django_db
class TestCreateItem:
    pytestmark = pytest.mark.django_db

    def test_create_item(self, faker: Faker) -> None:
        product_image: ProductImage = ProductImageFactory()
        number = faker.pyint()
        cart = {product_image.product.id: {'quantity': number}}
        expected_result = create_item(
            product_image.product,
            product_image,
            cart,
            product_image.product.id
        )
        assert expected_result.product.id == product_image.product.id
        assert expected_result.product.name == product_image.product.name
        assert expected_result.product.price == product_image.product.price
        assert expected_result.product.productimage.image == product_image
        assert expected_result.quantity == number
        assert expected_result.get_total == number * product_image.product.price


@pytest.mark.django_db
class TestDefineCartFromCookies:
    pytestmark = pytest.mark.django_db

    def test_define_cart_from_cookies(self) -> None:
        request = HttpRequest()
        cart = {str(i): {'quantity': i + 1} for i in range(5)}
        request.COOKIES["cart"] = json.dumps(cart)
        expected_result = define_cart_from_cookies(request)
        assert expected_result == cart

    def test_define_cart_from_cookies_empty(self) -> None:
        request = HttpRequest()
        expected_result = define_cart_from_cookies(request)
        assert expected_result == {}


@pytest.mark.django_db
class TestGetCookiesCart:
    pytestmark = pytest.mark.django_db

    def test_get_cookies_cart(self, faker: Faker) -> None:
        products: List[Product] = ProductFactory.create_batch(size=5)
        [ProductImageFactory(product=product) for product in products]
        cart = {str(product.id): {'quantity': faker.pyint()} for product in products}
        items, order = [], {}
        order['get_order_items'] = sum(elem['quantity'] for elem in cart.values())
        order['get_order_total'] = sum(
            elem.price * cart[str(elem.id)]['quantity'] for elem in products
        )
        items = [
            create_item(
                product,
                product.productimage_set.first(),
                cart,
                str(product.id)
            ) for product in products]
        cartItem = order['get_order_items']
        request = HttpRequest()
        request.COOKIES["cart"] = json.dumps(cart)
        expected_items, expected_order, expected_cartItems = get_cookies_cart(request)
        assert expected_order == order
        assert expected_cartItems == cartItem
        for elem in expected_items:
            assert elem in items

    def test_get_cookies_cart_empty(self, faker: Faker) -> None:
        request = HttpRequest()
        expected_items, expected_order, expected_cartItems = get_cookies_cart(request)
        assert expected_items == []
        assert expected_order == {"get_order_total": 0, "get_order_items": 0}
        assert expected_cartItems == 0


@pytest.mark.django_db
class TestCorrectCartOrder:
    pytestmark = pytest.mark.django_db

    def test_correct_cart_order(self, faker: Faker) -> None:
        products: List[Product] = ProductFactory.create_batch(size=5)
        items, cart, order = [], {}, {"get_order_total": 0, "get_order_items": 0}
        for product in products:
            ProductImageFactory(product=product)
            items.append(NestedNamespace({
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "productimage": {"image": product.productimage_set.first()},
                },
                "quantity": (number := faker.pyint()),
                "get_total": number * product.price,
            }))
            cart[product.id] = {'quantity': number}
            order['get_order_items'] += number
            order['get_order_total'] += product.price * number
        expected_cart, expected_order = correct_cart_order(items)
        assert expected_cart == cart
        assert expected_order == order

    def test_correct_cart_order_empty(self, faker: Faker) -> None:
        items, order = [], {"get_order_total": 0, "get_order_items": 0}
        expected_cart, expected_order = correct_cart_order(items)
        assert expected_cart == {}
        assert expected_order == order


@pytest.mark.django_db
class TestHandlingBrandPriceForm:
    pytestmark = pytest.mark.django_db

    def test_handling_brand_price_form_all(
            self, preparation_for_filter_testing: Tuple[str, str, List[Tuple[Product, str]]]
    ) -> None:
        brand_1, brand_2, product_list = preparation_for_filter_testing
        data = QueryDict(f'brand={brand_1}&brand={brand_2}&low=2&high=70')
        expected_result = handling_brand_price_form(data, product_list)
        for elem in expected_result:
            assert elem[0].brand.name in {brand_1, brand_2}
            assert elem[0].price in {10, 20, 30, 40, 50}
        assert len(expected_result) == 10

    def test_handling_brand_price_form_one_brand(
            self, preparation_for_filter_testing: Tuple[str, str, List[Tuple[Product, str]]]
    ) -> None:
        brand_1, brand_2, product_list = preparation_for_filter_testing
        data = QueryDict(f'brand={brand_1}')
        expected_result = handling_brand_price_form(data, product_list)
        for elem in expected_result:
            assert elem[0].brand.name == brand_1
            assert elem[0].price in {10, 20, 30, 40, 50}
        assert len(expected_result) == 5

    def test_handling_brand_price_form_one_brand_one_price(
            self, preparation_for_filter_testing: Tuple[str, str, List[Tuple[Product, str]]]
    ) -> None:
        brand_1, brand_2, product_list = preparation_for_filter_testing
        data = QueryDict(f'brand={brand_2}&low=50')
        expected_result = handling_brand_price_form(data, product_list)
        assert expected_result[0][0].price == 50
        assert expected_result[0][0].brand.name == brand_2
        assert len(expected_result) == 1

    def test_handling_brand_price_form_empty_query(
            self, preparation_for_filter_testing: Tuple[str, str, List[Tuple[Product, str]]]
    ) -> None:
        brand_1, brand_2, product_list = preparation_for_filter_testing
        data = QueryDict()
        expected_result = handling_brand_price_form(data, product_list)
        assert len(expected_result) == 10

    def test_handling_brand_price_form_all_brands_and_high_price(
            self, preparation_for_filter_testing: Tuple[str, str, List[Tuple[Product, str]]]
    ) -> None:
        brand_1, brand_2, product_list = preparation_for_filter_testing
        data = QueryDict(f'brand={brand_1}&brand={brand_2}&low=100')
        expected_result = handling_brand_price_form(data, product_list)
        assert not len(expected_result)

    def test_handling_brand_price_form_brands_and_prices(
            self, preparation_for_filter_testing: Tuple[str, str, List[Tuple[Product, str]]]
    ) -> None:
        brand_1, brand_2, product_list = preparation_for_filter_testing
        data = QueryDict(f'brand={brand_1}&brand={brand_2}&low=20&high=40')
        expected_result = handling_brand_price_form(data, product_list)
        for elem in expected_result:
            assert elem[0].brand.name in {brand_1, brand_2}
            assert elem[0].price in {20, 30, 40}
        assert len(expected_result) == 6


@pytest.mark.django_db
class TestGetProductList:
    pytestmark = pytest.mark.django_db

    def test_get_product_list(self) -> None:
        products: List[Product] = ProductFactory.create_batch(size=5)
        [ProductImageFactory(product=product) for product in products]
        queryset = Product.objects.only("id", "name", "price").prefetch_related(
                Prefetch(
                    "productimage_set",
                    queryset=ProductImage.objects.filter(
                        id__in=Subquery(
                            ProductImage.objects.filter(
                                product=OuterRef("product_id")
                            ).values_list("id", flat=True)[:1]
                        )
                    ),
                )
            )
        expected_result = get_product_list(queryset)
        for i, elem in enumerate(expected_result):
            assert elem[0] == queryset[i]
            assert elem[1] == queryset[i].productimage_set.first().image

    def test_get_product_list_empty(self) -> None:
        queryset = Product.objects.all()
        expected_result = get_product_list(queryset)
        assert expected_result == []


class TestGetCartItemQuantity:

    def test_get_cart_item_quantity(self, faker: Faker) -> None:
        data = {i: {'quantity': faker.pyint()} for i in range(5)}
        data_summ = sum(elem.get('quantity') for elem in data.values())
        expected_result = get_cart_item_quantity(data)
        assert expected_result == data_summ

    def test_get_cart_item_quantity_empty(self) -> None:
        expected_result = get_cart_item_quantity({})
        assert expected_result == 0


@pytest.mark.django_db
class TestCreateCookieCart:
    pytestmark = pytest.mark.django_db

    def test_create_cookie_cart(self) -> None:
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(size=5)
        queryset = OrderItem.objects.all()
        expected_result = create_cookie_cart(queryset)
        for key, value in expected_result.items():
            instance = find_instance(orderitems, key, 'id')
            assert key == instance.product.id
            assert value.get('quantity') == instance.quantity

    def test_create_cookie_cart_empty(self) -> None:
        queryset = OrderItem.objects.all()
        expected_result = create_cookie_cart(queryset)
        assert expected_result == {}


@pytest.mark.django_db
class TestCartAuthorizationHandler:
    pytestmark = pytest.mark.django_db

    def test_cart_authorization_handler_existed_order(self) -> None:
        buyer: Buyer = BuyerFactory()
        order: Order = OrderFactory(buyer=buyer, complete=False)
        another_order: Order = OrderFactory(complete=True)
        OrderItemFactory.create_batch(size=5, order=another_order)
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(
            size=5, order=order
        )
        cart = {str(elem.product.id): {'quantity': elem.quantity - 1} for elem in orderitems}
        request = HttpRequest()
        request.COOKIES["cart"] = json.dumps(cart)
        expected_response = cart_authorization_handler(
            request, HttpResponseRedirect(reverse("shop:home")), buyer.user
        )
        expected_orderitems = OrderItem.objects.filter(order=order)
        assert not expected_response.cookies
        for orderitem in expected_orderitems:
            assert orderitem.quantity == cart[str(orderitem.product.id)]['quantity']

    def test_cart_authorization_handler_without_order_existed_buyer(
            self, faker: Faker
    ) -> None:
        buyer: Buyer = BuyerFactory()
        another_order: Order = OrderFactory(complete=True)
        OrderItemFactory.create_batch(size=5, order=another_order)
        products: List[Product] = ProductFactory.create_batch(size=5)
        cart = {str(product.id): {'quantity': faker.pyint()} for product in products}
        request = HttpRequest()
        request.COOKIES["cart"] = json.dumps(cart)
        expected_response = cart_authorization_handler(
            request, HttpResponseRedirect(reverse("shop:home")), buyer.user
        )
        expected_orderitems = OrderItem.objects.filter(order__buyer=buyer)
        assert not expected_response.cookies
        for orderitem in expected_orderitems:
            assert orderitem.quantity == cart[str(orderitem.product.id)]['quantity']

    def test_cart_authorization_handler_without_order_existed_user(
            self, faker: Faker
    ) -> None:
        user: User = UserFactory()
        another_order: Order = OrderFactory(complete=True)
        OrderItemFactory.create_batch(size=5, order=another_order)
        products: List[Product] = ProductFactory.create_batch(size=5)
        cart = {str(product.id): {'quantity': faker.pyint()} for product in products}
        request = HttpRequest()
        request.COOKIES["cart"] = json.dumps(cart)
        expected_response = cart_authorization_handler(
            request, HttpResponseRedirect(reverse("shop:home")), user
        )
        expected_orderitems = OrderItem.objects.filter(order__buyer__user=user)
        assert not expected_response.cookies
        for orderitem in expected_orderitems:
            assert orderitem.quantity == cart[str(orderitem.product.id)]['quantity']

    def test_cart_authorization_handler_empty_cart(self) -> None:
        user: User = UserFactory()
        cart = {}
        request = HttpRequest()
        request.COOKIES["cart"] = json.dumps(cart)
        expected_response = cart_authorization_handler(
            request, HttpResponseRedirect(reverse("shop:home")), user
        )
        expected_orderitems = OrderItem.objects.filter(order__buyer__user=user)
        assert not expected_orderitems
        assert expected_response.cookies['flag'].value == '1'
        assert expected_response.cookies['flag']['max-age'] == 1

    def test_cart_authorization_handler_without_cart(self) -> None:
        user: User = UserFactory()
        request = HttpRequest()
        expected_response = cart_authorization_handler(
            request, HttpResponseRedirect(reverse("shop:home")), user
        )
        expected_orderitems = OrderItem.objects.filter(order__buyer__user=user)
        assert not expected_orderitems
        assert expected_response.cookies['flag'].value == '1'
        assert expected_response.cookies['flag']['max-age'] == 1


@pytest.mark.django_db
class TestDefineCart:
    pytestmark = pytest.mark.django_db

    def test_define_cart(self) -> None:
        order: Order = OrderFactory(complete=False)
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(
            size=5, order=order
        )
        expected_result = define_cart('1', order.buyer.user)
        for key, value in expected_result.items():
            instance = find_instance(orderitems, int(key), 'id')
            assert int(key) == instance.product.id
            assert value.get('quantity') == instance.quantity

    def test_define_cart_complete_order(self) -> None:
        order: Order = OrderFactory(complete=True)
        OrderItemFactory.create_batch(
            size=5, order=order
        )
        expected_result = define_cart('1', order.buyer.user)
        assert expected_result == {}

    def test_define_cart_empty_flag(self) -> None:
        user: User = UserFactory()
        expected_result = define_cart(None, user)
        assert expected_result == {}

    def test_define_cart_anonymous_user(self) -> None:
        user = AnonymousUser()
        expected_result = define_cart('1', user)
        assert expected_result == {}


class TestDefinePageRange:

    def test_define_page_range(self) -> None:
        products = [1 for _ in range(500)]
        paginator = Paginator(products, 20)
        context = {
            'page_obj': paginator.page(5),
            'paginator': paginator,
            'is_paginated': True,
        }
        expected_result = list(define_page_range(context))
        assert expected_result == list(paginator.get_elided_page_range(
            paginator.page(5).number, on_each_side=1, on_ends=1
        ))

    def test_define_page_range_empty(self) -> None:
        context = {
            'is_paginated': False,
        }
        expected_result = define_page_range(context)
        assert expected_result is None


@pytest.mark.django_db
class TestClearNotCompletedOrder:
    pytestmark = pytest.mark.django_db

    def test_clear_not_completed_order_not_complete(self) -> None:
        order: Order = OrderFactory(complete=False)
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(
            size=5, order=order
        )
        clear_not_completed_order(order.buyer)
        expected_result = OrderItem.objects.filter(order=order)
        assert not expected_result

    def test_clear_not_completed_order_complete(self) -> None:
        order: Order = OrderFactory(complete=True)
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(
            size=5, order=order
        )
        clear_not_completed_order(order.buyer)
        expected_result = OrderItem.objects.filter(order=order)
        assert expected_result.count() == 5
        for expected_orderitem in expected_result:
            instance = find_instance(orderitems, expected_orderitem.product.id, 'id')
            assert expected_orderitem == instance

    def test_clear_not_completed_order_without_user(self) -> None:
        order: Order = OrderFactory(complete=True)
        OrderItemFactory.create_batch(size=5, order=order)
        clear_not_completed_order(None)
        expected_result = OrderItem.objects.filter(order=order)
        assert expected_result.count() == 5


@pytest.mark.django_db
class TestDefineOrderList:
    pytestmark = pytest.mark.django_db

    def test_define_order_list(self) -> None:
        buyer: Buyer = BuyerFactory()
        orders: List[Order] = OrderFactory.create_batch(
            size=3, buyer=buyer, complete=True
        )
        [SaleFactory(order=order) for order in orders]
        orders.append(OrderFactory(buyer=buyer, complete=False))
        for order in orders:
            OrderItemFactory.create_batch(size=5, order=order)
        queryset = querysets.get_order_queryset_for_user_account_view(buyer.user)
        expected_result = define_order_list(queryset)
        for i, elem in enumerate(expected_result):
            assert elem[0] == queryset[i]
            assert elem[1] == queryset[i].sale_set.first()
            for j, item in enumerate(elem[2]):
                assert item == queryset[i].orderitem_set.all()[j]


@pytest.mark.django_db
class TestDefineBuyerData:
    pytestmark = pytest.mark.django_db

    def test_define_buyer_data_buyer_exist(self) -> None:
        order: Order = OrderFactory()
        order_list = [(order, 'Не оплачений', QuerySet())]
        expected_result = define_buyer_data(order_list, order.buyer.user)
        user_data = {
            'tel': order.buyer.tel,
            'address': order.buyer.address,
            'name': order.buyer.name,
            'email': order.buyer.email
        }
        assert expected_result == user_data

    def test_define_buyer_data_buyer_doesnt_exist(self) -> None:
        user: User = UserFactory()
        expected_result = define_buyer_data([], user)
        user_data = {
            'tel': '',
            'address': '',
            'name': user.username,
            'email': user.email,
        }
        assert expected_result == user_data


@pytest.mark.django_db
class TestDefineCategoryWithSuperCategory:
    pytestmark = pytest.mark.django_db

    def test_define_category_with_super_category(self) -> None:
        CategoryFactory.create_batch(size=10)
        super_category: SuperCategory = SuperCategoryFactory()
        CategoryFactory.create_batch(size=5, super_category=super_category)
        categories = Category.objects.all()
        expected_result = define_category_with_super_category(
            categories, super_category.id
        )
        for elem in expected_result:
            assert elem.super_category.id == super_category.id
        assert len(expected_result) == 5


@pytest.mark.django_db
class TestDefineCategoryList:
    pytestmark = pytest.mark.django_db

    def test_define_category_list(self, faker: Faker) -> None:
        CategoryFactory.create_batch(size=10)
        super_category: SuperCategory = SuperCategoryFactory()
        samples: List[Category] = CategoryFactory.create_batch(
            size=5,
            super_category=super_category
        )
        slug = samples[faker.random_int(min=0, max=4)].slug
        categories = Category.objects.all()
        expected_result = define_category_list(slug, categories)
        for elem in expected_result:
            assert elem.super_category.id == super_category.id
        assert len(expected_result) == 5


@pytest.mark.django_db
class TestDefineBrandList:
    pytestmark = pytest.mark.django_db

    def test_define_brand_list(self) -> None:
        ProductFactory.create_batch(size=5)
        products = Product.objects.all()
        brands = {product.brand.name for product in products}
        expected_result = define_brand_list(products)
        assert len(expected_result) == len(brands)
        for elem in expected_result:
            assert type(elem) is tuple
            assert len(elem) == 2
            assert elem[0] in brands


@pytest.mark.django_db
class TestDefineCategoryTitleProductList:
    pytestmark = pytest.mark.django_db

    def test_define_category_title_product_list(self, faker: Faker) -> None:
        super_category: SuperCategory = SuperCategoryFactory()
        category_list: List[Category] = CategoryFactory.create_batch(
            size=5, super_category=super_category
        )
        product_list = []
        for category in category_list:
            product_list += ProductFactory.create_batch(size=5, category=category)
        index = faker.random_int(min=0, max=len(category_list)-1)
        slug = category_list[index].slug
        products = querysets.get_product_queryset_for_category_view(slug)
        categories = querysets.get_category_queryset_for_data_mixin()
        exp_category, exp_title, exp_product_list = define_category_title_product_list(
            products, slug, categories
        )
        assert exp_category == category_list[index]
        assert exp_title == category_list[index].name
        assert exp_product_list == get_product_list(products)

    def test_define_category_title_product_list_empty_cat_slug(
            self, faker: Faker
    ) -> None:
        super_category: SuperCategory = SuperCategoryFactory()
        category_list: List[Category] = CategoryFactory.create_batch(
            size=5, super_category=super_category
        )
        index = faker.random_int(min=0, max=len(category_list)-1)
        slug = category_list[index].slug
        products = querysets.get_product_queryset_for_category_view(slug)
        categories = querysets.get_category_queryset_for_data_mixin()
        exp_category, exp_title, exp_product_list = define_category_title_product_list(
            products, slug, categories
        )
        assert exp_category == category_list[index]
        assert exp_title == category_list[index].name
        assert exp_product_list == get_product_list(products)

    def test_define_category_title_product_list_empty_cat_slug_dif(
            self, faker: Faker
    ) -> None:
        super_category: SuperCategory = SuperCategoryFactory()
        category_list: List[Category] = CategoryFactory.create_batch(
            size=5, super_category=super_category
        )
        index = faker.random_int(min=0, max=len(category_list)-1)
        slug = category_list[index].slug[:-2]
        products = querysets.get_product_queryset_for_category_view(slug)
        categories = querysets.get_category_queryset_for_data_mixin()
        exp_category, exp_title, exp_product_list = define_category_title_product_list(
            products, slug, categories
        )
        assert exp_category == categories[0]
        assert exp_title == categories[0].name
        assert exp_product_list == get_product_list(products)


@pytest.mark.django_db
class TestDefineProductEval:
    pytestmark = pytest.mark.django_db

    def test_define_product_eval(self) -> None:
        product: Product = ProductFactory()
        reviews: List[Review] = ReviewFactory.create_batch(size=5, product=product)
        product_review = querysets.get_review_queryset_for_product_view(product)
        product_eval = 0
        for review in product_review:
            product_eval += review.grade
        product_eval = str(int(math.ceil(2 * product_eval / product_review.count())))
        expected_result = define_product_eval(product_review)
        assert expected_result == product_eval

    def test_define_product_eval_empty(self) -> None:
        product: Product = ProductFactory()
        product_review = querysets.get_review_queryset_for_product_view(product)
        expected_result = define_product_eval(product_review)
        assert expected_result == 0


@pytest.mark.django_db
class TestModifyLikeWithResponse:
    pytestmark = pytest.mark.django_db

    def test_modify_like_with_response_like(self) -> None:
        review: Review = ReviewFactory()
        request = HttpRequest()
        request.COOKIES['review'] = json.dumps(review.id)
        request.COOKIES['author'] = json.dumps(review.review_author.id)
        request.COOKIES['like'] = json.dumps('True')
        like_num, dislike_num = review.like_num, review.dislike_num
        expected_result = modify_like_with_response(
            review, review.review_author, True, False
        )
        expected_like = Like.objects.get(
            like_author=review.review_author, review=review
        )
        expected_review = Review.objects.get(id=review.id)
        assert type(expected_result) is JsonResponse
        assert expected_like
        assert expected_review.like_num == like_num + 1
        assert expected_review.dislike_num == dislike_num

    def test_modify_like_with_response_dislike(self) -> None:
        review: Review = ReviewFactory()
        request = HttpRequest()
        request.COOKIES['review'] = json.dumps(review.id)
        request.COOKIES['author'] = json.dumps(review.review_author.id)
        request.COOKIES['like'] = json.dumps('False')
        like_num, dislike_num = review.like_num, review.dislike_num
        expected_result = modify_like_with_response(
            review, review.review_author, False, True
        )
        expected_like = Like.objects.get(
            like_author=review.review_author, review=review
        )
        expected_review = Review.objects.get(id=review.id)
        assert type(expected_result) is JsonResponse
        assert expected_like
        assert expected_review.like_num == like_num
        assert expected_review.dislike_num == dislike_num + 1

    def test_modify_like_with_response_like_not_added(self) -> None:
        review: Review = ReviewFactory()
        request = HttpRequest()
        request.COOKIES['review'] = json.dumps(review.id)
        request.COOKIES['author'] = json.dumps(review.review_author.id)
        request.COOKIES['like'] = json.dumps('True')
        like_num, dislike_num = review.like_num, review.dislike_num
        modify_like_with_response(
            review, review.review_author, True, False
        )
        expected_result = modify_like_with_response(
            review, review.review_author, True, False
        )
        expected_like = Like.objects.get(
            like_author=review.review_author, review=review
        )
        expected_review = Review.objects.get(id=review.id)
        assert type(expected_result) is JsonResponse
        assert expected_like
        assert expected_review.like_num == like_num + 1
        assert expected_review.dislike_num == dislike_num

    def test_modify_like_with_response_dislike_not_added(self) -> None:
        review: Review = ReviewFactory()
        request = HttpRequest()
        request.COOKIES['review'] = json.dumps(review.id)
        request.COOKIES['author'] = json.dumps(review.review_author.id)
        request.COOKIES['like'] = json.dumps('False')
        like_num, dislike_num = review.like_num, review.dislike_num
        modify_like_with_response(
            review, review.review_author, False, True
        )
        expected_result = modify_like_with_response(
            review, review.review_author, False, True
        )
        expected_like = Like.objects.get(
            like_author=review.review_author, review=review
        )
        expected_review = Review.objects.get(id=review.id)
        assert type(expected_result) is JsonResponse
        assert expected_like
        assert expected_review.like_num == like_num
        assert expected_review.dislike_num == dislike_num + 1


@pytest.mark.django_db
class TestCheckBuyerExistence:
    pytestmark = pytest.mark.django_db

    def test_check_buyer_existence(self) -> None:
        buyer: Buyer = BuyerFactory()
        expected_result = check_buyer_existence(buyer.user)
        assert expected_result == buyer

    def test_check_buyer_existence_empty(self) -> None:
        user: User = UserFactory()
        expected_result = check_buyer_existence(user)
        assert not expected_result



@pytest.mark.django_db
class TestPerformOrderItemActions:
    pytestmark = pytest.mark.django_db

    def test_perform_orderItem_actions_add(self, faker: Faker) -> None:
        order: Order = OrderFactory(complete=False)
        products: List[Product] = ProductFactory.create_batch(size=5, sold=False)
        order_items = [
            OrderItemFactory(order=order, product=product) for product in products
        ]
        index = faker.random_int(min=0, max=4)
        product_id = order_items[index].product.id
        quantity = order_items[index].quantity
        perform_orderItem_actions(product_id, 'add', order.buyer)
        expected_result = OrderItem.objects.get(id=order_items[index].id).quantity
        assert expected_result == quantity + 1

    def test_perform_orderItem_actions_remove(self, faker: Faker) -> None:
        order: Order = OrderFactory(complete=False)
        products: List[Product] = ProductFactory.create_batch(size=5, sold=False)
        order_items = [
            OrderItemFactory(order=order, product=product) for product in products
        ]
        index = faker.random_int(min=0, max=4)
        product_id = order_items[index].product.id
        quantity = order_items[index].quantity
        perform_orderItem_actions(product_id, 'remove', order.buyer)
        expected_result = OrderItem.objects.get(id=order_items[index].id).quantity
        assert expected_result == quantity - 1

    def test_perform_orderItem_actions_add_product_sold(self, faker: Faker) -> None:
        order: Order = OrderFactory(complete=False)
        products: List[Product] = ProductFactory.create_batch(size=5, sold=True)
        order_items = [
            OrderItemFactory(order=order, product=product) for product in products
        ]
        index = faker.random_int(min=0, max=4)
        product_id = order_items[index].product.id
        quantity = order_items[index].quantity
        perform_orderItem_actions(product_id, 'add', order.buyer)
        expected_result = OrderItem.objects.get(id=order_items[index].id).quantity
        assert expected_result == quantity

    def test_perform_orderItem_actions_add_create_orderitem(
            self, faker: Faker
    ) -> None:
        buyer: Buyer = BuyerFactory()
        products: List[Product] = ProductFactory.create_batch(size=5, sold=False)
        index = faker.random_int(min=0, max=4)
        product_id = products[index].id
        orderitem = OrderItem.objects.filter(product=products[index]).first()
        perform_orderItem_actions(product_id, 'add', buyer)
        expected_result = OrderItem.objects.get(product=products[index]).quantity
        assert expected_result == 1
        assert not orderitem

    def test_perform_orderItem_actions_remove_zero(self, faker: Faker) -> None:
        order: Order = OrderFactory(complete=False)
        products: List[Product] = ProductFactory.create_batch(size=5, sold=False)
        order_items = [
            OrderItemFactory(
                order=order, product=product, quantity=1
            ) for product in products
        ]
        index = faker.random_int(min=0, max=4)
        product_id = order_items[index].product.id
        perform_orderItem_actions(product_id, 'remove', order.buyer)
        expected_result = OrderItem.objects.filter(id=order_items[index].id)
        assert not expected_result


@pytest.mark.django_db
class TestGetOrderWithCleaning:
    pytestmark = pytest.mark.django_db

    def test_get_order_with_cleaning(self) -> None:
        order: Order = OrderFactory(complete=False)
        OrderItemFactory.create_batch(size=5, order=order)
        expected_order = get_order_with_cleaning(order.buyer.user)
        expected_orderitems = OrderItem.objects.filter(order=expected_order)
        assert not expected_orderitems
        assert expected_order == order

    def test_get_order_with_cleaning_without_order(self) -> None:
        buyer: Buyer = BuyerFactory()
        expected_order = get_order_with_cleaning(buyer.user)
        expected_orderitems = OrderItem.objects.filter(order=expected_order)
        assert not expected_orderitems
        assert expected_order.buyer == buyer


@pytest.mark.django_db
class TestUpdateBuyer:
    pytestmark = pytest.mark.django_db

    def test_update_buyer(self, faker: Faker) -> None:
        buyer: Buyer = BuyerFactory()
        data = {
            "tel": faker.pystr(min_chars=10, max_chars=15),
            "address": faker.pystr(min_chars=2, max_chars=30),
            "name": faker.first_name(),
            "email": faker.email(),
        }
        update_buyer(buyer.user, data)
        assert buyer.tel == data.get('tel')
        assert buyer.address == data.get('address')
        assert buyer.name == data.get('name')
        assert buyer.email == data.get('email')


@pytest.mark.django_db
class TestGetOrder:
    pytestmark = pytest.mark.django_db

    def test_get_order_with_order(self, faker: Faker) -> None:
        order: Order = OrderFactory(complete=False)
        OrderItemFactory.create_batch(size=5, order=order)
        data = {
            "tel": faker.pystr(min_chars=10, max_chars=15),
            "address": faker.pystr(min_chars=2, max_chars=30),
            "name": faker.first_name(),
            "email": faker.email(),
        }
        expected_result = get_order(order.buyer.user, data)
        expected_orderitems = OrderItem.objects.filter(order=expected_result)
        assert expected_result == order
        assert not expected_orderitems

    def test_get_order_anonymous_user(self, faker: Faker) -> None:
        user = AnonymousUser()
        data = {
            "tel": faker.pystr(min_chars=10, max_chars=15),
            "address": faker.pystr(min_chars=2, max_chars=30),
            "name": faker.first_name(),
            "email": faker.email(),
        }
        expected_result = get_order(user, data)
        expected_buyer = Buyer.objects.get(id=expected_result.buyer.id)
        assert expected_result
        assert expected_buyer.tel == data.get('tel')
        assert expected_buyer.address == data.get('address')
        assert expected_buyer.name == data.get('name')
        assert expected_buyer.email == data.get('email')


@pytest.mark.django_db
class TestGetOrderItemsList:
    pytestmark = pytest.mark.django_db

    def test_get_order_items_list(self, faker: Faker) -> None:
        order: Order = OrderFactory()
        products: List[Product] = ProductFactory.create_batch(size=5)
        items = []
        for product in products:
            quantity = faker.pyint(min_value=1)
            items.append(NestedNamespace({
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "productimage": {"image": None},
                },
                "quantity": quantity,
                "get_total": quantity * product.price,
            }))
        expected_result = get_order_items_list(items, order)
        for item in expected_result:
            instance = [elem for elem in items if elem.product.id == item.product.id][0]
            assert item.product.id == instance.product.id
            assert item.product.name == instance.product.name
            assert item.product.price == instance.product.price
            assert item.product.productimage_set.first() is None
            assert item.quantity == instance.quantity
            assert item.get_total == instance.get_total


@pytest.mark.django_db
class TestGetMessageAndWarning:
    pytestmark = pytest.mark.django_db

    def test_get_message_and_warning(self) -> None:
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(size=3)
        exp_message, exp_warning = get_message_and_warning(orderitems)
        assert exp_message == 'Оплата пройшла успішно'
        assert exp_warning == ':)'

    def test_get_message_and_warning_empty(self) -> None:
        exp_message, exp_warning = get_message_and_warning([])
        assert exp_message == ''
        assert exp_warning is None


@pytest.mark.django_db
class TestGetCheckoutForm:
    pytestmark = pytest.mark.django_db

    def test_get_checkout_form(self, faker: Faker) -> None:
        user: User = UserFactory()
        expected_result = get_checkout_form(user)
        assert expected_result.initial.get('name') == user.username
        assert expected_result.initial.get('email') == user.email
        assert expected_result.initial.get('tel') == ''
        assert expected_result.initial.get('address') == ''

    def test_get_checkout_form_anonymous(self) -> None:
        user = AnonymousUser()
        expected_result = get_checkout_form(user)
        assert isinstance(expected_result, CheckoutForm)
        assert expected_result.initial == {}


@pytest.mark.django_db
class TestGetResponseDictWithSaleCreation:
    pytestmark = pytest.mark.django_db

    def test_get_response_dict_with_sale_creation(self, faker: Faker) -> None:
        order: Order = OrderFactory(complete=False)
        orderitems: List[OrderItem] = OrderItemFactory.create_batch(
            size=5, order=order
        )
        incomes = []
        items = []
        for orderitem in orderitems:
            quantity = faker.pyint(min_value=1)
            items.append(NestedNamespace({
                "product": {
                    "id": orderitem.product.id,
                    "name": orderitem.product.name,
                    "price": orderitem.product.price,
                    "productimage": {"image": None},
                },
                "quantity": quantity,
                "get_total": quantity * orderitem.product.price,
            }))
            incomes.append(
                IncomeFactory(
                    product=orderitem.product,
                    income_quantity=quantity,
                    income_price=orderitem.product.price,
                )
            )
        income_id_set = {income.id for income in incomes}
        initial = define_buyer_data(order_list=None, user=order.buyer.user)
        initial.update({
            'order': order.id,
            'region': faker.pystr(min_chars=2, max_chars=80),
            'city': faker.pystr(min_chars=2, max_chars=80),
            'department': faker.pystr(min_chars=1, max_chars=6)
        })
        form = CheckoutForm(initial=initial)
        expected_result = get_response_dict_with_sale_creation(
            form, order.buyer.user, items
        )
        expected_stock = Stock.objects.filter(id__in=income_id_set)
        expected_sale = Sale.objects.get(order=order)
        assert expected_result.get('items') == []
        assert expected_result.get('order') == {
            "get_order_total": 0, "get_order_items": 0
        }
        assert expected_result.get('message') == 'Оплата пройшла успішно'
        assert expected_result.get('warning') == ':)'
        assert expected_result.get('cartJson') == json.dumps({})
        assert expected_sale
        assert not expected_stock

    def test_get_response_dict_with_sale_creation_anon_user(
            self, faker: Faker
    ) -> None:
        incomes: List[Income] = IncomeFactory.create_batch(size=5)
        items = []
        for income in incomes:
            items.append(NestedNamespace({
                "product": {
                    "id": income.product.id,
                    "name": income.product.name,
                    "price": income.product.price,
                    "productimage": {"image": None},
                },
                "quantity": income.income_quantity,
                "get_total": income.income_quantity * income.product.price,
            }))
        initial = {
            'name': faker.user_name(),
            'email': faker.email(),
            'tel': faker.pystr(min_chars=12, max_chars=15),
            'address': faker.pystr(min_chars=12, max_chars=30),
            'region': faker.pystr(min_chars=2, max_chars=80),
            'city': faker.pystr(min_chars=2, max_chars=80),
            'department': faker.pystr(min_chars=1, max_chars=6),
        }
        form = CheckoutForm(initial=initial)
        expected_result = get_response_dict_with_sale_creation(
            form, AnonymousUser(), items
        )
        expected_sale = Sale.objects.last()
        expected_buyer = Buyer.objects.last()
        assert expected_result.get('items') == []
        assert expected_result.get('order') == {
            "get_order_total": 0, "get_order_items": 0
        }
        assert expected_result.get('message') == 'Оплата пройшла успішно'
        assert expected_result.get('warning') == ':)'
        assert expected_result.get('cartJson') == json.dumps({})
        assert expected_sale
        assert not Stock.objects.all()
        assert expected_buyer.name == initial.get('name')
        assert expected_buyer.email == initial.get('email')
        assert expected_buyer.address == initial.get('address')
        assert expected_buyer.tel == initial.get('tel')
        assert expected_sale.region == initial.get('region')
        assert expected_sale.city == initial.get('city')
        assert expected_sale.department == initial.get('department')


@pytest.mark.django_db
class TestGetUpdatedResponseDict:
    pytestmark = pytest.mark.django_db

    def test_get_updated_response_dict(self, faker: Faker) -> None:
        incomes: List[Income] = IncomeFactory.create_batch(size=5)
        items = []
        for income in incomes:
            items.append(NestedNamespace({
                "product": {
                    "id": income.product.id,
                    "name": income.product.name,
                    "price": income.product.price,
                    "productimage": {"image": None},
                },
                "quantity": income.income_quantity,
                "get_total": income.income_quantity * income.product.price,
            }))
        initial = {
            'name': faker.user_name(),
            'email': faker.email(),
            'tel': faker.pystr(min_chars=12, max_chars=15),
            'address': faker.pystr(min_chars=12, max_chars=30),
            'region': faker.pystr(min_chars=2, max_chars=80),
            'city': faker.pystr(min_chars=2, max_chars=80),
            'department': faker.pystr(min_chars=1, max_chars=6),
        }
        context, message = dict(), 'Hello'
        args = QueryDict('', mutable=True)
        args.update(initial)
        cart, order = correct_cart_order(items)
        expected_result = get_updated_response_dict(
            context, message, items, CheckoutForm(args)
        )
        form = expected_result.get('checkout_form')
        expected_form_data = {key: form[key].value() for key in form.fields.keys()}
        assert isinstance(expected_result.get('checkout_form'), CheckoutForm)
        assert expected_result.get('message') == message
        assert expected_result.get('cartJson') == json.dumps(cart)
        assert expected_result.get('order') == order
        for key, value in initial.items():
            assert expected_form_data[key] == value
