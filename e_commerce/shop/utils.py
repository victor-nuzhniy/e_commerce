from django.contrib.auth.backends import ModelBackend, UserModel
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import MultipleObjectsReturned
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from .forms import *
from .models import *
from types import SimpleNamespace
from django.core.exceptions import ObjectDoesNotExist
import json
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            UserModel().set_password(password)
        except MultipleObjectsReturned:
            return User.objects.filter(email=username).order_by('id').first()
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None


class DataMixin:
    def get_user_context(self, **kwargs):
        context = kwargs
        context['user_creation_form'] = CustomUserCreationForm(auto_id=False)
        context['user_login_form'] = AuthenticationForm(auto_id=False)
        context['cartItem'] = get_cart_item_quantity(json.loads(self.request.COOKIES.get('cart', '{}')))
        super_categories = cache.get('super_categories')
        category_list = cache.get('category_list')
        if not super_categories:
            super_categories = SuperCategory.objects.all().prefetch_related('category_set')
            cache.set('super_categories', super_categories, 1000)
        if not category_list:
            category_list = Category.objects.all().select_related('super_category')
            cache.set('category_list', category_list, 1000)
        context['super_categories'], context['category_list'] = super_categories, category_list
        return context


class NestedNamespace(SimpleNamespace):
    def __init__(self, dictionary, **kwargs):
        super().__init__(**kwargs)
        for key, value in dictionary.items():
            if isinstance(value, dict):
                self.__setattr__(key, NestedNamespace(value))
            else:
                self.__setattr__(key, value)


def check_quantity_in_stock(items):
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
            message = _("К сожалению, в одной позиции из списка товаров произошли изменения."
                        " Пока Вы оформляли покупку, товар был приобретен другим покупателем."
                        " Приносим свои извинения.")
    return message, items


def decreasing_stock_items(items):
    product_ids = [item.product.id for item in items]
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


def get_cookies_cart(request):
    try:
        cart = json.loads(request.COOKIES['cart'].replace("'", '''"'''))
    except KeyError:
        cart = {}
    items, order = [], {'get_order_total': 0, 'get_order_items': 0}
    cartItems, products_id_list = order['get_order_items'], []
    products = Product.objects.filter(id__in=cart.keys()).select_related('productimage')
    for product in products:
        try:
            i = str(product.id)
            cartItems += cart[i]["quantity"]
            total = product.price * cart[i]["quantity"]
            order['get_order_total'] += total
            order['get_order_items'] += cart[i]['quantity']
            try:
                image = product.productimage.image_1
            except AttributeError:
                image = None
            item = NestedNamespace({
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'productimage': {'image_1': image},
                },
                'quantity': cart[i]['quantity'],
                'get_total': cart[i]['quantity'] * product.price,
            })
            items.append(item)
        except ObjectDoesNotExist:
            pass
    return items, order, cartItems


def correct_cart_order(items, order):
    cart, number, total, cookie_value = {}, 0, 0, ''
    for item in items:
        if item.quantity:
            number += item.quantity
            item.get_total = item.quantity * item.product.price
            total += item.get_total
            cart[item.product.id] = {"quantity": item.quantity}
    order['get_order_items'] = number
    order['get_order_total'] = total
    return cart, order


def handling_brand_price_form(data, product_list):
    filtered_brand_set = set(data.getlist('brand'))
    low = int(data['low']) if data['low'] else 0
    high = int(data['high']) if data['high'] else 100000000
    product_list = list(filter(lambda x: (low <= x[0].price <= high), product_list))
    if filtered_brand_set:
        product_list = list(filter(lambda x: (str(x[0].brand.name) in filtered_brand_set), product_list))
    return product_list


def get_pagination(page, product_list, items_per_page):
    paginator = Paginator(product_list, items_per_page)
    page_range = paginator.get_elided_page_range(page, on_each_side=1, on_ends=1)
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj, paginator, page_obj.object_list, page_range, page_obj.has_other_pages()


def get_product_list(products):
    product_list = []
    for product in products:
        image = None if not hasattr(product, 'productimage') else product.productimage.image[0]
        product_list.append((product, image))
    return product_list


def get_cart_item_quantity(data):
    quantity = 0
    for item in data.values():
        quantity += int(list(item.values())[0])
    return quantity


def create_cookie_cart(items):
    cart = {}
    for item in items:
        if item.quantity:
            cart[item.product.id] = {"quantity": item.quantity}
    return cart


def authorization_handler(request, response, user):
    cookie_cart = json.loads(request.COOKIES.get('cart'))
    if cookie_cart:
        buyer = Buyer.objects.get_or_create(user=user)
        order, created = Order.objects.get_or_create(buyer=user.buyer, complete=False)
        if not created:
            items = OrderItem.objects.filter(order=order)
            for item in items:
                item.delete()
        for item in cookie_cart.items():
            OrderItem.objects.create(product=Product.objects.get(id=int(item[0][0])), order=order,
                                     quantity=int(list(item[1].values())[0]))
    else:
        response.set_cookie('flag', 1, max_age=1)
    return response


def switch_lang_code(path, language):
    # Get the supported language codes
    lang_codes = [c for (c, name) in settings.LANGUAGES]

    # Validate the inputs
    if path == '':
        raise Exception('URL path for language switch is empty')
    elif path[0] != '/':
        raise Exception('URL path for language switch does not start with "/"')
    elif language not in lang_codes:
        raise Exception('%s is not a supported language code' % language)

    # Split the parts of the path
    parts = path.split('/')

    # Add or substitute the new language prefix
    if parts[1] in lang_codes:
        parts[1] = language
    else:
        parts[0] = "/" + language

    # Return the full new path
    return '/'.join(parts)
