from abc import ABC
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
import re


class ProductFeatureInline(admin.StackedInline):
    model = ProductFeature
    exclude = ('id',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    exclude = ('id',)


# @admin.action(description='Copy item')
# def duplicate_query_sets(modeladmin, request, queryset, **kwargs):
#     for p in queryset:
#         p.pk = None
#         p.slug = '1'
#         for i, v in kwargs.items():
#             setattr(p, i, v)
#         p.save()
#
#
# @admin.action(description='Copy p and i item')
# def duplicate_query_sets_1(modeladmin, request, queryset, **kwargs):
#     for p in queryset:
#         p.pk = None
#         product = Product.objects.get(id=p.product.id+1)
#         p.product = product
#         for i, v in kwargs.items():
#             setattr(p, i, v)
#         p.save()


class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'model', 'brand', 'category', 'sold')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    search_help_text = _('Поиск по наименованию товара')
    list_editable = ('sold',)
    list_filter = ('brand', 'category', 'sold',)
    list_per_page = 20
    prepopulated_fields = {"slug": ("model",)}
    inlines = [
        ProductFeatureInline,
        ProductImageInline,
    ]
    list_select_related = ['brand', 'category']
    # actions = [duplicate_query_sets]

    def get_formsets_with_inlines(self, request, obj=None):  # readable labels of product feature in admin.site
        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, ProductFeatureInline) and re.search(r'[0-9]+', request.path_info):
                product_pk = re.search(r'[0-9]+', request.path_info)[0]
                category = Product.objects.get(id=product_pk).category
                category_features = CategoryFeatures.objects.filter(category=category)
                if category_features:
                    product_features_names = list(
                        CategoryFeatures.objects.filter(category=category).values()[0].values())
                    label_dict = {}
                    for i in range(1, len(product_features_names) - 1):
                        label_dict['feature_' + str(i)] = product_features_names[i + 1]
                    formset_inline = inlineformset_factory(Product, ProductFeature,
                                                           exclude=('id', 'product'), labels=label_dict)
                    yield formset_inline, inline
                else:
                    yield inline.get_formset(request, obj), inline
            else:
                yield inline.get_formset(request, obj), inline


class CategoryFeatureInline(admin.StackedInline):
    model = CategoryFeatures
    exclude = ('id',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'super_category')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    search_help_text = _('Поиск по имени категории')
    list_filter = ('super_category__name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [
        CategoryFeatureInline
    ]
    list_select_related = ['categoryfeatures', 'super_category']


class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}


class BuyerInline(admin.StackedInline):
    model = Buyer


class BuyerListFilter(admin.SimpleListFilter, ABC):
    title = _('Покупатель')
    parameter_name = 'buyer'

    def lookups(self, request, model_admin):
        return ('Да', _('Да')), ('Нет', _('Нет'))

    def queryset(self, request, queryset):
        buyers = Buyer.objects.all()
        buyers_set = {buyer.user_id for buyer in buyers}
        if self.value() == 'Да':
            return queryset.filter(id__in=buyers_set)
        elif self.value() == 'Нет':
            return queryset.exclude(id__in=buyers_set)


class UserAdmin(BaseUserAdmin):
    inlines = [BuyerInline, ]
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff']
    list_filter = ('username', 'is_staff', BuyerListFilter)
    list_per_page = 20
    list_select_related = ['buyer']


class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'price', 'summ', 'income', 'supplier']
    readonly_fields = ['product', 'quantity', 'income', 'price', 'supplier']
    list_filter = ['supplier']
    search_fields = ['product__name']
    search_help_text = _('Поиск по наименованию товара')
    list_per_page = 20
    list_select_related = ['product', 'income', 'supplier']

    @admin.display(description=_('Сумма'))
    def summ(self, obj):
        return obj.price * obj.quantity


class IncomeAdmin(admin.ModelAdmin):
    list_display = ['income_date', 'product', 'income_quantity', 'supplier']
    search_fields = ('product__name', 'income_date')
    search_help_text = _('Поиск по наименованию товара и дате прихода')
    list_filter = ['supplier']
    list_per_page = 20
    list_select_related = ['product', 'supplier']

    def save_model(self, request, obj, form, change):
        stock, prev_quantity = Stock.objects.filter(income=obj), 0
        if stock:
            prev_quantity = Income.objects.get(id=obj.id).income_quantity
        super().save_model(request, obj, form, change)
        if stock:
            dif = prev_quantity - obj.income_quantity
            if stock[0].quantity <= dif:
                stock[0].delete()
                obj.product.sold = True
                obj.product.save()
            else:
                stock[0].quantity -= dif
                stock[0].save()
        else:
            Stock.objects.create(product=obj.product, income=obj,
                                 quantity=obj.income_quantity, price=obj.income_price, supplier=obj.supplier)
            obj.product.sold = False
            obj.product.save()


class SaleAdmin(admin.ModelAdmin):
    readonly_fields = ['order']
    list_display = ['sale_date', 'sold_product', 'sale_buyer']
    search_fields = ['sale_date']
    search_help_text = _('Поиск по дате продажи')
    list_per_page = 20
    list_select_related = ['order', 'order__buyer']

    @admin.display(description=_('Проданный товар'))
    def sold_product(self, obj):
        return list(obj.order.orderitem_set.all())

    @admin.display(description=_('Покупатель'))
    def sale_buyer(self, obj):
        return obj.order.buyer

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('order__orderitem_set', 'order__orderitem_set__product')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'order', 'quantity', 'date_added', 'get_total']
    extra = 0


class SaleInline(admin.TabularInline):
    model = Sale
    readonly_fields = ['sale_date', 'region', 'city', 'department']
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, SaleInline]
    list_display = ['id', 'buyer', 'date_ordered', 'complete', 'get_order_items', 'get_order_total']
    list_display_links = ['id', 'buyer']
    search_fields = ['date_ordered', 'buyer__user__username', 'buyer__user__first_name', 'buyer__user__last_name']
    search_help_text = _('Поиск по дате заказа, нику, имени и фамилии пользователя')
    list_per_page = 20
    list_select_related = ['buyer', 'buyer__user']

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('orderitem_set', 'orderitem_set__product')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'order', 'product', 'quantity', 'get_total']
    list_display_links = ['order_id', 'order']
    search_fields = ['order__date_ordered', 'product__name']
    search_help_text = _('Поиск по дате заказа и наименованию товара')
    list_per_page = 20
    list_select_related = ['product', 'order']

    @admin.display(description=_('Порядковый номер заказа'))
    def order_id(self, obj):
        return obj.order.id


class LikeAdmin(admin.ModelAdmin):
    list_display = ['review_product', 'review_author', 'like_author', 'like', 'dislike']
    search_fields = ['review__product__name', 'review__review_author__username']
    search_help_text = _('Поиск по наименованию продукта, автору отзыва')
    list_per_page = 20
    list_select_related = ['review__review_author', 'review__product', 'like_author']

    @admin.display(description=_('Автор отзыва'))
    def review_author(self, obj):
        return obj.review.review_author

    @admin.display(description=_('Оцениваемый товар'))
    def review_product(self, obj):
        return obj.review.product


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['review_date', 'product', 'grade', 'review_author']
    list_filter = ['grade']
    search_fields = ['review_date', 'product__name', 'review_author__username']
    search_help_text = _('Поиск по дате отзыва, наименованию товара, юзернейму автора')
    list_per_page = 20
    list_select_related = ['product', 'review_author']


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'person', 'tel', 'email']
    search_fields = ['name']
    search_help_text = _('Поиск по наименованию предприятия')
    list_per_page = 20


class BuyerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'tel']


class SuperCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


# class ProductFeatureAdmin(admin.ModelAdmin):
#     list_display = ['id', 'product']
#     actions = [duplicate_query_sets_1]
#
#
# class ProductImageAdmin(admin.ModelAdmin):
#     list_display = ['id', 'product']
#     actions = [duplicate_query_sets_1]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(SuperCategory, SuperCategoryAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Like, LikeAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(Income, IncomeAdmin)
admin.site.register(Buyer, BuyerAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Stock, StockAdmin)
admin.site.register(CategoryFeatures)
# admin.site.register(ProductFeature, ProductFeatureAdmin)
# admin.site.register(ProductImage, ProductImageAdmin)
