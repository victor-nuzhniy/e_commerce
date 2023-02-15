import math
from typing import Optional, Dict, List, Tuple, Union, Any

from django.conf.global_settings import AUTH_USER_MODEL
from django.contrib.auth.backends import ModelBackend, UserModel
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import MultipleObjectsReturned
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, prefetch_related_objects, F, QuerySet
from django.http import JsonResponse, QueryDict, HttpRequest, HttpResponseRedirect
from django.utils.functional import SimpleLazyObject

from .forms import *
from .models import *
from types import SimpleNamespace
from django.core.exceptions import ObjectDoesNotExist
import json
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings


class EmailBackend(ModelBackend):
    def authenticate(
            self,
            request: HttpRequest,
            username: str = None,
            password: str = None,
            **kwargs: Any,
    ) -> Optional[User]:
        """
            Make it possible of using email as username. Default behaviour is present.
        """
        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        except MultipleObjectsReturned:
            return User.objects.filter(email=username).order_by('id').first()
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def get_user(self, user_id: int) -> Optional[User]:
        """
            Additional changed method for EmailBackend functionality.
            Return user, if it can be authenticated, or None with ability to catch
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
            putting them in context dict and file cash.
            Additionally put user_creation_form, user_login_form in context dict
            to make it accessible from every view using Datamixin.
            Also put in context dict cartItem data received from request cookies.
        """
        context = kwargs
        context['user_creation_form'] = CustomUserCreationForm(auto_id=False)
        context['user_login_form'] = AuthenticationForm(auto_id=False)
        context['cartItem'] = get_cart_item_quantity(
            json.loads(self.request.COOKIES.get('cart', '{}'))
        )
        super_categories = cache.get('super_categories')
        category_list = cache.get('category_list')
        if not super_categories:
            super_categories = SuperCategory.objects.all().prefetch_related(
                'category_set'
            )
            cache.set('super_categories', super_categories, 1000)
        if not category_list:
            category_list = Category.objects.all().select_related('super_category')
            cache.set('category_list', category_list, 1000)
        context['super_categories'] = super_categories
        context['category_list'] = category_list
        return context


class NestedNamespace(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        """

        """
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)


def check_quantity_in_stock(
        items: List[NestedNamespace]
) -> Tuple[str, List[NestedNamespace]]:
    message, stock_list = '', []
    product_ids = [item.product.id for item in items]
    stock = Stock.objects.filter(product__in=product_ids).select_related('product')
    for item in items:
        quantity = 0
        if item:
            for x in stock:
                if x.product.id == item.product.id:
                    quantity += x.quantity
        if quantity < item.quantity or not item.quantity:
            item.quantity = quantity
            message = _("Нажаль, в одній позиції зі списку виникли зміни."
                        "Поки Ви оформлювали покупку, товар був придбаний"
                        " іншим покупцем."
                        "Приносимо свої вибачення.")
    return message, items


def decreasing_stock_items(items: List[OrderItem]) -> None:
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
        cart: Dict[Optional[int, Dict[str, int]]],
        index: str,
) -> NestedNamespace:
    return NestedNamespace({
        'product': {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'productimage': {'image': image},
        },
        'quantity': cart[index]['quantity'],
        'get_total': cart[index]['quantity'] * product.price,
    })


def define_cart(request: HttpRequest) -> Dict[Optional[int, Dict[str, int]]]:
    try:
        cart = json.loads(request.COOKIES['cart'].replace("'", '''"'''))
    except KeyError:
        cart = {}
    return cart


def get_cookies_cart(
        request: HttpRequest
) -> Tuple[List[NestedNamespace], Dict[str, int], int]:
    cart = define_cart(request)
    items, order = [], {'get_order_total': 0, 'get_order_items': 0}
    cartItems = order['get_order_items']
    products = Product.objects.filter(id__in=cart.keys()).prefetch_related(
        'productimage_set'
    )
    for product in products:
        try:
            i = str(product.id)
            cartItems += cart[i]["quantity"]
            total = product.price * cart[i]["quantity"]
            order['get_order_total'] += total
            order['get_order_items'] += cart[i]['quantity']
            try:
                image = product.productimage_set.first()
            except (AttributeError, IndexError) as e:
                image = None
            items.append(create_item(product, image, cart, i))
        except ObjectDoesNotExist:
            pass
    return items, order, cartItems


def correct_cart_order(
        items: List[NestedNamespace], order: Dict[str, int]
) -> Tuple[Dict[int, Dict[str, int]], Dict[str, int]]:
    cart, number, total = {}, 0, 0
    for item in items:
        if item.quantity:
            number += item.quantity
            item.get_total = item.quantity * item.product.price
            total += item.get_total
            cart[item.product.id] = {"quantity": item.quantity}
    order['get_order_items'] = number
    order['get_order_total'] = total
    return cart, order


def handling_brand_price_form(
        data: QueryDict, product_list: List[Tuple[Product, str]]
) -> List[Tuple[Product, str]]:
    if data:
        filtered_brand_set = set(data.getlist('brand'))
        low = int(data['low']) if data['low'] else 0
        high = int(data['high']) if data['high'] else 100000000
        product_list = list(filter(lambda x: (low <= x[0].price <= high), product_list))
        if filtered_brand_set:
            product_list = list(
                filter(
                    lambda x: (str(x[0].brand.name) in filtered_brand_set), product_list
                )
            )
    return product_list


# def get_pagination(page, product_list, items_per_page):
#     paginator = Paginator(product_list, items_per_page)
#     page_range = paginator.get_elided_page_range(page, on_each_side=1, on_ends=1)
#     try:
#         page_obj = paginator.page(page)
#     except PageNotAnInteger:
#         page_obj = paginator.page(1)
#     except EmptyPage:
#         page_obj = paginator.page(paginator.num_pages)
#     return page_obj, paginator, page_obj.object_list, page_range, page_obj.has_other_pages()


def get_product_list(products: QuerySet) -> List[Tuple[Product, str]]:
    product_list = []
    for product in products:
        image = product.productimage_set.first()
        image = None if not image else image.image
        product_list.append((product, image))
    return product_list


def get_cart_item_quantity(data: Dict[int, Dict[str, int]]) -> int:
    quantity = 0
    for item in data.values():
        quantity += int(list(item.values())[0])
    return quantity


def create_cookie_cart(items: QuerySet) -> Dict[int, Dict[str, int]]:
    cart = {}
    for item in items:
        if item.quantity:
            cart[item.product.id] = {"quantity": item.quantity}
    return cart


def authorization_handler(
        request: HttpRequest,
        response: HttpResponseRedirect,
        user: AUTH_USER_MODEL,
) -> HttpResponseRedirect:
    cookie_cart = json.loads(request.COOKIES.get('cart'))
    if cookie_cart:
        buyer = Buyer.objects.get_or_create(user=user)
        order, created = Order.objects.get_or_create(buyer=buyer, complete=False)
        if not created:
            items = OrderItem.objects.filter(order=order)
            for item in items:
                item.delete()
        for item in cookie_cart.items():
            OrderItem.objects.create(
                product=Product.objects.get(id=int(item[0][0])),
                order=order,
                quantity=int(list(item[1].values())[0]),
            )
    else:
        response.set_cookie('flag', '1', max_age=1)
    return response


def define_cart(
        flag: Union[bool, str], user: Union[AUTH_USER_MODEL, AnonymousUser]
) -> Dict[int, Dict[str, int]]:
    cart = {}
    if flag:
        order = Order.objects.filter(buyer__user=user).last()
        if order and not order.complete:
            items = OrderItem.objects.filter(order=order)
            cart = create_cookie_cart(items)
    return cart


def define_page_range(context: Dict) -> Optional[Dict]:
    page_range = None
    if context['is_paginated']:
        page_range = context['paginator'].get_elided_page_range(
            context['page_obj'].number, on_each_side=1, on_ends=1
        )
    return page_range


def clear_not_completed_order(buyer: Optional[Buyer]) -> None:
    if buyer:
        lastOrder = Order.objects.filter(buyer=buyer).last()
        if lastOrder and not lastOrder.complete:
            order_items = OrderItem.objects.filter(order=lastOrder)
            for order_item in order_items:
                order_item.delete()
            lastOrder.delete()


def define_order_list(orders: QuerySet) -> List[Tuple[Order, Sale, QuerySet]]:
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
        'tel': buyer.tel,
        'address': buyer.address,
        'name': buyer.name,
        'email': buyer.email,
    }


def define_category_with_super_category(
        categories: QuerySet, sc_id: int
) -> List[Category]:
    category_list = []
    for category in categories:
        if category.super_category.id == sc_id:
            category_list.append(category)
    return category_list


def define_category_list(slug: str, categories: QuerySet) -> List[Category]:
    super_category_id = None
    for category in categories:
        if category.slug == slug:
            super_category_id = category.super_category.id
            break
    return define_category_with_super_category(categories, super_category_id)


def define_brand_list(products: QuerySet) -> List[Tuple[str, str]]:
    return list(
        {(product.brand.name, product.brand.name) for product in products}
    )


def define_category_title_product_list(
        products: QuerySet, slug: str, categories: QuerySet
) -> Tuple[Category, str, List[Tuple[Product, str]]]:
    try:
        category = products[0].category if products else categories.get(slug=slug)
        product_list, title = get_product_list(products), category.name
    except ObjectDoesNotExist:
        category, title, product_list = categories[0], categories[0].name, []
    return category, title, product_list


def define_product_eval(product_review: QuerySet) -> Union[str, int]:
    product_eval = 0
    for review in product_review:
        product_eval += review.grade
    product_eval = str(int(
        math.ceil(2 * product_eval / product_review.count())
    )) if product_review.count() else 0
    return product_eval


def modify_like_with_response(
        review: Review, author: User, like: bool, dislike: bool
) -> JsonResponse:
    if not Like.objects.filter(review=review, like_author=author):
        Like.objects.create(
            review=review, like_author=author, like=like, dislike=dislike
        )
        if like:
            review.like_num = review.like_num + 1 if review.like_num else 1
        else:
            review.dislike_num = review.dislike_num + 1 if review.dislike_num else 1
        review.save()
        return JsonResponse('Like was added', safe=False)
    return JsonResponse('Like was not added', safe=False)


def check_buyer_existence(user: Union[AUTH_USER_MODEL, AnonymousUser]) -> Optional[Buyer]:
    try:
        buyer = Buyer.objects.get(user=user)
    except ObjectDoesNotExist:
        buyer = None
    return buyer


def perform_orderItem_actions(product_id: int, action: str, buyer: Buyer) -> None:
    product = Product.objects.get(id=product_id)
    if not product.sold:
        order, created = Order.objects.get_or_create(buyer=buyer, complete=False)
        orderItem, created = OrderItem.objects.get_or_create(
            order=order, product=product
        )
        if action == 'add':
            orderItem.quantity = F('quantity') + 1
        elif action == 'remove':
            orderItem.quantity = F('quantity') + 1
        orderItem.save()
        if orderItem.quantity <= 0:
            orderItem.delete()


def get_order_with_cleaning(user: Union[AUTH_USER_MODEL, AnonymousUser]) -> Order:
    order, created = Order.objects.get_or_create(buyer=user.buyer, complete=False)
    if not created:
        orderItems = OrderItem.objects.filter(order=order)
        for orderItem in orderItems:
            orderItem.delete()
        order.complete = True
        order.save()
    return order


def update_buyer(user: Union[AUTH_USER_MODEL, AnonymousUser], data: Dict) -> None:
    user.buyer.name, user.buyer.email = data['name'], data['email']
    user.buyer.tel, user.buyer.address = data['tel'], data['address']
    user.buyer.save()


def get_order(user: Union[AUTH_USER_MODEL, AnonymousUser], data: Dict) -> Order:
    if user.is_authenticated:
        order = get_order_with_cleaning(user)
        update_buyer(user, data)
        return order
    buyer = Buyer.objects.create(
        name=data['name'],
        email=data['email'],
        tel=data['tel'],
        address=data['address'],
    )
    return Order.objects.create(buyer=buyer, complete=True)


def get_order_items_list(
        items: List[NestedNamespace], order: Order
) -> List[OrderItem]:
    order_item_list = []
    for item in items:
        orderItem = OrderItem.objects.create(
            product=Product.objects.get(id=int(item.product.id)),
            order=order,
            quantity=int(item.quantity)
        )
        order_item_list.append(orderItem)
    return order_item_list


def get_message_and_warning(items: List[OrderItem]) -> Tuple[str, Optional[str]]:
    message, warning = '', None
    if items:
        message, warning = 'Оплата пройшла успішно', ':)'
    return message, warning


def get_checkout_form(user: Union[AUTH_USER_MODEL, AnonymousUser]) -> CheckoutForm:
    if user.is_authenticated:
        return CheckoutForm(
            initial=define_buyer_data(order_list=None, user=user)
        )
    return CheckoutForm()


def get_response_dict_with_sale_creation(
        form: CheckoutForm,
        user: Union[AUTH_USER_MODEL, AnonymousUser],
        items: List[NestedNamespace],
) -> Dict[str, Union[str, List, Dict[str, int]]]:
    data = form.cleaned_data
    order = get_order(user, data)
    items = get_order_items_list(items, order)
    Sale.objects.create(
        order=order,
        region=data['region'],
        city=data['city'],
        department=data['department']
    )
    decreasing_stock_items(items)
    message, warning = get_message_and_warning(items)
    return {
        'items': [],
        'order': {'get_order_total': 0, 'get_order_items': 0},
        'message': message,
        'warning': warning,
        'cartJson': json.dumps({}),
    }


def get_updated_response_dict(
        context: Dict,
        message: Optional[str],
        items: List[NestedNamespace],
        order: Dict[str, int],
        args: QueryDict,
) -> Dict:
    cart = {}
    if message:
        cart, order = correct_cart_order(items, order)
    context.update({
        'checkout_form': CheckoutForm(args),
        'message': message,
        'cartJson': json.dumps(cart)
    })
    return context
