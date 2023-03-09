import json
import math
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple, Union

from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth.backends import ModelBackend, UserModel
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models import F, Q, QuerySet
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse, QueryDict
from django.utils.translation import gettext_lazy as _

from .forms import CheckoutForm, CustomUserCreationForm
from .models import (
    Buyer,
    Category,
    Like,
    Order,
    OrderItem,
    Product,
    ProductImage,
    Review,
    Sale,
    Stock,
)
from .querysets import querysets


class EmailBackend(ModelBackend):
    def authenticate(
        self,
        request: HttpRequest,
        username: str = None,
        password: str = None,
        **kwargs: Any,
    ) -> Optional[User]:
        """
        Makes it possible of using email as username. Default behaviour is present.
        """
        try:
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        except MultipleObjectsReturned:
            return User.objects.filter(email=username).order_by("id").first()
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def get_user(self, user_id: int) -> Optional[User]:
        """
        Additionally changed method for EmailBackend functionality.
        Returns user, if it can be authenticated, or None with ability to catch
        UserModel.DoesNotExist exception.
        """
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None


class DataMixin:
    def get_user_context(self, **kwargs: Any) -> Dict:
        """
        Method for obtaining lists of super_categories and categories,
        putting them in context dictionary and file cash.
        Additionally puts user_creation_form, user_login_form in context dictionary
        to make it accessible from every view using DataMixin.
        Also puts in context dictionary cartItem data received
        from request cookies.
        """
        context = kwargs
        context["user_creation_form"] = CustomUserCreationForm(auto_id=False)
        context["user_login_form"] = AuthenticationForm(auto_id=False)
        context["cartItem"] = get_cart_item_quantity(
            json.loads(self.request.COOKIES.get("cart", "{}"))
        )
        super_categories = cache.get("super_categories")
        category_list = cache.get("category_list")
        if not super_categories:
            super_categories = querysets.get_super_category_queryset_for_data_mixin()
            cache.set("super_categories", super_categories, 1000)
        if not category_list:
            category_list = querysets.get_category_queryset_for_data_mixin()
            cache.set("category_list", category_list, 1000)
        context["super_categories"] = super_categories
        context["category_list"] = category_list
        return context


class NestedNamespace(SimpleNamespace):
    """
    Creates a dictionary like object with dot notation.
    Nested construction can be accessed via dot notation too.
    """

    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)


def check_quantity_in_stock(
    items: List[NestedNamespace],
) -> Tuple[str, List[NestedNamespace]]:
    """
    Takes as an argument list of NestedNamespace objects, checks quantity of
    products, which is mentioned in items, in stock, and if there is no such
    amount, decreases appropriate item quantity, adding special message to mention
    about it. If everything ok, the message is empty.
    """
    message, stock_list = "", []
    product_ids = {item.product.id for item in items}
    stock = Stock.objects.filter(product__in=product_ids).select_related("product")
    for item in items:
        quantity = 0
        if item:
            for x in stock:
                if x.product.id == item.product.id:
                    quantity += x.quantity
        if quantity < item.quantity or not item.quantity:
            item.quantity = quantity
            message = _(
                "Нажаль, в одній позиції зі списку виникли зміни."
                "Поки Ви оформлювали покупку, товар був придбаний"
                " іншим покупцем."
                "Приносимо свої вибачення."
            )
    return message, items


def decreasing_stock_items(items: List[OrderItem]) -> None:
    """
    Decreases quantity of stock products after sale is performed.
    If quantity of one product decreases to 0, sets product sold
    field to True.
    """
    for item in items:
        q = Stock.objects.filter(product=item.product.id)
        quantity = item.quantity
        if q:
            i = 0
            while q:
                if q[i].quantity < quantity:
                    quantity -= q[i].quantity
                    q[i].quantity = 0
                    q[i].delete()
                else:
                    if q[i].quantity == quantity:
                        q[i].quantity = 0
                        q[i].delete()
                    else:
                        q[i].quantity -= quantity
                        q[i].save()
                    break
                i += 1
        if all([not x.quantity for x in q]):
            item.product.sold = True
            item.product.save()


def create_item(
    product: Product,
    image: Optional[ProductImage],
    cart: Dict[Union[int, str], Dict[str, int]],
    index: str,
) -> NestedNamespace:
    """
    Returns created NestedNamespace object with appropriate characteristics.
    """
    return NestedNamespace(
        {
            "product": {
                "id": product.pk,
                "name": product.name,
                "price": product.price,
                "productimage": {"image": image},
            },
            "quantity": cart[index]["quantity"],
            "get_total": cart[index]["quantity"] * product.price,
        }
    )


def define_cart_from_cookies(request: HttpRequest) -> Dict[int, Dict[str, int]]:
    """
    Defines cart from request cookies returning empty dictionary in case of
    its absence and returns it.
    """
    try:
        cart = json.loads(request.COOKIES["cart"].replace("'", '''"'''))
    except KeyError:
        cart = {}
    return cart


def get_cookies_cart(
    request: HttpRequest,
) -> Tuple[List[NestedNamespace], Dict[str, int], int]:
    """
    Creates cart dictionary from request cookies, creates cart items number,
    creates items list with NestedNamespace objects in it. The constructions
    are used for cart templates info transfer.
    """
    cart = define_cart_from_cookies(request)
    items, order = [], {"get_order_total": 0, "get_order_items": 0}
    cartItems = order["get_order_items"]
    products = Product.objects.filter(id__in=cart.keys()).prefetch_related(
        "productimage_set"
    )
    for product in products:
        try:
            i = str(product.id)
            cartItems += cart[i]["quantity"]
            total = product.price * cart[i]["quantity"]
            order["get_order_total"] += total
            order["get_order_items"] += cart[i]["quantity"]
            try:
                image = product.productimage_set.first()
            except (AttributeError, IndexError):
                image = None
            items.append(create_item(product, image, cart, i))
        except ObjectDoesNotExist:
            pass
    return items, order, cartItems


def correct_cart_order(
    items: List[NestedNamespace],
) -> Tuple[Dict[int, Dict[str, int]], Dict[str, int]]:
    """
    Takes NestedNamespace objects list as argument
    and corrects cart and order data.
    """
    cart, number, total, order = {}, 0, 0, {}
    for item in items:
        if item.quantity:
            number += item.quantity
            item.get_total = item.quantity * item.product.price
            total += item.get_total
            cart[item.product.id] = {"quantity": item.quantity}
    order["get_order_items"] = number
    order["get_order_total"] = total
    return cart, order


def handling_brand_price_form(
    data: QueryDict, product_list: List[Tuple[Product, str]]
) -> List[Tuple[Product, str]]:
    """
    Creates filter logic. Filter uses brand and prise as parameters
    for filtering output product list.
    """
    filtered_brand_set = {}
    if data:
        filtered_brand_set = set(data.getlist("brand"))
        low = int(data["low"]) if data.get("low") else 0
        high = int(data["high"]) if data.get("high") else 100000000
        product_list = list(filter(lambda x: (low <= x[0].price <= high), product_list))
        if filtered_brand_set:
            product_list = list(
                filter(
                    lambda x: (str(x[0].brand.name) in filtered_brand_set), product_list
                )
            )
    return product_list


def get_product_list(products: QuerySet) -> List[Tuple[Product, str]]:
    """
    Creates list of tuple with product and images objects.
    """
    product_list = []
    for product in products:
        image = product.productimage_set.first()
        image = None if not image else image.image
        product_list.append((product, image))
    return product_list


def get_cart_item_quantity(data: Dict[int, Dict[str, int]]) -> int:
    """
    Gets quantity of elements in items.
    """
    quantity = 0
    for item in data.values():
        quantity += int(list(item.values())[0])
    return quantity


def create_cookie_cart(items: QuerySet) -> Dict[int, Dict[str, int]]:
    """
    Creates cart for coolies from QuerySet objects list.
    """
    cart = {}
    for item in items:
        if item.quantity:
            cart[item.product.id] = {"quantity": item.quantity}
    return cart


def cart_authorization_handler(
    request: HttpRequest,
    response: HttpResponseRedirect,
    user: AUTH_USER_MODEL,
) -> HttpResponseRedirect:
    """
    Gets cart data from cookies, checks if authenticated buyer has
    not completed order, deletes this order and its data,
    creates new order using cookies cart data.
    If cart is empty, return flag in cookies with 1 sec lifetime.
    """
    cart = request.COOKIES.get("cart")
    cookie_cart = json.loads(cart) if cart else None
    if cookie_cart:
        buyer, created = Buyer.objects.get_or_create(user=user)
        order, created = Order.objects.get_or_create(buyer=buyer, complete=False)
        if not created:
            items = OrderItem.objects.filter(order=order)
            for item in items:
                item.delete()
        for key, value in cookie_cart.items():
            OrderItem.objects.create(
                product=Product.objects.get(id=int(key)),
                order=order,
                quantity=int(value.get("quantity")),
            )
    else:
        response.set_cookie("flag", "1", max_age=1)
    return response


def define_cart(
    flag: Union[bool, str], user: Union[AUTH_USER_MODEL, AnonymousUser]
) -> Dict[int, Dict[str, int]]:
    """
    If cookies cart is empty after login buyer creates cart from existing
    order data. It uses flag var from cookies. With empty flag returns
    empty cart.
    """
    cart = {}
    if flag and not isinstance(user, AnonymousUser):
        order = Order.objects.filter(buyer__user=user).last()
        if order and not order.complete:
            items = OrderItem.objects.filter(order=order)
            cart = create_cookie_cart(items)
    return cart


def define_page_range(context: Dict) -> Optional[Dict]:
    """
    Define page range from paginator in context data.
    """
    page_range = None
    if context["is_paginated"]:
        page_range = context["paginator"].get_elided_page_range(
            context["page_obj"].number, on_each_side=1, on_ends=1
        )
    return page_range


def clear_not_completed_order(buyer: Optional[Buyer]) -> None:
    """
    Clear not completed order if buyer and such order exists.
    """
    if buyer:
        lastOrder = Order.objects.filter(buyer=buyer).last()
        if lastOrder and not lastOrder.complete:
            order_items = OrderItem.objects.filter(order=lastOrder)
            for order_item in order_items:
                order_item.delete()
            lastOrder.delete()


def define_order_list(orders: QuerySet) -> List[Tuple[Order, Sale, QuerySet]]:
    """
    Creates info list with order, sale and order items info for buyer
    account representation.
    """
    order_list = []
    for order in orders:
        sale = order.sale_set.all().first() if order.complete else "Не оплачений"
        orderItems = order.orderitem_set.all()
        order_list.append((order, sale, orderItems))
    return order_list


def define_buyer_data(
    order_list: Optional[List[Tuple]],
    user: Union[AUTH_USER_MODEL, AnonymousUser],
) -> Dict[str, str]:
    """
    Defines buyer and returns data for initializing form.
    """
    if order_list:
        buyer = order_list[0][0].buyer
    else:
        try:
            buyer = user.buyer
        except ObjectDoesNotExist:
            buyer = Buyer.objects.create(
                user=user,
                name=user.username,
                email=user.email,
            )
    return {
        "tel": buyer.tel,
        "address": buyer.address,
        "name": buyer.name,
        "email": buyer.email,
    }


def define_category_with_super_category(
    categories: QuerySet, sc_id: int
) -> List[Category]:
    """
    Defines category list for given super category id.
    """
    category_list = []
    for category in categories:
        if category.super_category.id == sc_id:
            category_list.append(category)
    return category_list


def define_category_list(slug: str, categories: QuerySet) -> List[Category]:
    """
    Finds out super category id and defines category list
    for this id.
    """
    super_category_id = None
    for category in categories:
        if category.slug == slug:
            super_category_id = category.super_category.id
            break
    return define_category_with_super_category(categories, super_category_id)


def define_brand_list(products: QuerySet) -> List[Tuple[str, str]]:
    """
    Defines unique tuple list with double brand name for
    products in given queryset.
    """
    return list({(product.brand.name, product.brand.name) for product in products})


def define_category_title_product_list(
    products: QuerySet, slug: str, categories: QuerySet
) -> Tuple[Category, str, List[Tuple[Product, str]]]:
    """
    Defines category, title name and product list from given data.
    """
    try:
        category = products[0].category if products else categories.get(slug=slug)
        product_list, title = get_product_list(products), category.name
    except ObjectDoesNotExist:
        category, title, product_list = categories[0], categories[0].name, []
    return category, title, product_list


def define_product_eval(product_review: QuerySet) -> Union[str, int]:
    """
    Calculates product evaluation.
    """
    product_eval = 0
    for review in product_review:
        product_eval += review.grade
    product_eval = (
        str(int(math.ceil(2 * product_eval / product_review.count())))
        if product_review.count()
        else 0
    )
    return product_eval


def modify_like_with_response(
    review: Review, author: User, like: bool, dislike: bool
) -> JsonResponse:
    """
    Creates Like objects if not exists, modifies and saves like
    data. If Like objects exists for this author, nothing happens.
    """
    if not Like.objects.filter(review=review, like_author=author).count():
        Like.objects.create(
            review=review, like_author=author, like=like, dislike=dislike
        )
        if like:
            review.like_num = F("like_num") + 1 if review.like_num else 1
        else:
            review.dislike_num = F("dislike_num") + 1 if review.dislike_num else 1
        review.save()
        return JsonResponse("Like was added", safe=False)
    return JsonResponse("Like was not added", safe=False)


def check_buyer_existence(user: AUTH_USER_MODEL) -> Optional[Buyer]:
    """
    Check buyer existence for given user. This can happen for
    admin workers, that became users not via buyer registration
    view.
    """
    try:
        buyer = Buyer.objects.get(user=user)
    except ObjectDoesNotExist:
        buyer = None
    return buyer


def perform_orderItem_actions(product_id: int, action: str, buyer: Buyer) -> None:
    """
    Modifies order items data in dependence from command.
    """
    product = Product.objects.get(id=product_id)
    if not product.sold:
        order, created = Order.objects.get_or_create(buyer=buyer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(
            order=order, product=product
        )
        if action == "add":
            orderItem.quantity = F("quantity") + 1
        elif action == "remove":
            orderItem.quantity = F("quantity") - 1
        orderItem.save()
        orderItem.refresh_from_db()
        if orderItem.quantity <= 0:
            orderItem.delete()


def get_order_with_cleaning(user: AUTH_USER_MODEL) -> Order:
    """
    Gets or creates order. If order was got and not completed,
    clears its data.
    """
    order, created = Order.objects.get_or_create(buyer=user.buyer, complete=False)
    if not created:
        orderItems = OrderItem.objects.filter(order=order)
        for orderItem in orderItems:
            orderItem.delete()
        order.complete = True
        order.save()
    return order


def update_buyer(user: Union[AUTH_USER_MODEL, AnonymousUser], data: Dict) -> None:
    """
    Updates buyer with given info.
    """
    user.buyer.name, user.buyer.email = data["name"], data["email"]
    user.buyer.tel, user.buyer.address = data["tel"], data["address"]
    user.buyer.save()


def get_order(user: Union[AUTH_USER_MODEL, AnonymousUser], data: Dict) -> Order:
    """
    Gets order, if user is authenticated, otherwise creates buyer and
    its order.
    """
    if user.is_authenticated:
        order = get_order_with_cleaning(user)
        update_buyer(user, data)
        return order
    buyer = Buyer.objects.create(
        name=data["name"],
        email=data["email"],
        tel=data["tel"],
        address=data["address"],
    )
    return Order.objects.create(buyer=buyer, complete=True)


def get_order_items_list(items: List[NestedNamespace], order: Order) -> List[OrderItem]:
    """
    Creates order items list from NestedNamespace objects
    list for specific order.
    """
    order_item_list = []
    for item in items:
        orderItem = OrderItem.objects.create(
            product=Product.objects.get(id=int(item.product.id)),
            order=order,
            quantity=int(item.quantity),
        )
        order_item_list.append(orderItem)
    return order_item_list


def get_message_and_warning(items: List[OrderItem]) -> Tuple[str, Optional[str]]:
    """
    Defines message and warning.
    """
    message, warning = "", None
    if items:
        message, warning = "Оплата пройшла успішно", ":)"
    return message, warning


def get_checkout_form(user: Union[AUTH_USER_MODEL, AnonymousUser]) -> CheckoutForm:
    """
    Returns Checkout form with initial data, if user
    is authenticated.
    """
    if user.is_authenticated:
        return CheckoutForm(initial=define_buyer_data(order_list=None, user=user))
    return CheckoutForm()


def get_response_dict_with_sale_creation(
    form: CheckoutForm,
    user: Union[AUTH_USER_MODEL, AnonymousUser],
    items: List[NestedNamespace],
) -> Dict[str, Union[str, List, Dict[str, int]]]:
    """
    Creates response dict with Sale creation after
    approving buying.
    """
    data = {key: form[key].value() for key in form.fields.keys()}
    order = get_order(user, data)
    items = get_order_items_list(items, order)
    Sale.objects.create(
        order=order,
        region=data["region"],
        city=data["city"],
        department=data["department"],
    )
    decreasing_stock_items(items)
    message, warning = get_message_and_warning(items)
    return {
        "items": [],
        "order": {"get_order_total": 0, "get_order_items": 0},
        "message": message,
        "warning": warning,
        "cartJson": json.dumps({}),
    }


def get_updated_response_dict(
    context: Dict,
    message: Optional[str],
    items: List[NestedNamespace],
    checkout_form: CheckoutForm,
) -> Dict:
    """
    Updating context dict after some problems with products
    availability (for example, if there is no such quantity),
    updates cart in accordance with available amount of
    products.
    """
    cart, order = correct_cart_order(items)
    context.update(
        {
            "checkout_form": checkout_form,
            "message": message,
            "cartJson": json.dumps(cart),
            "order": order,
        }
    )
    return context
