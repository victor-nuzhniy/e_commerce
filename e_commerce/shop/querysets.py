from django.conf.global_settings import AUTH_USER_MODEL
from django.db.models import OuterRef, Prefetch, QuerySet, Subquery
from django.http import QueryDict

from .models import (
    Category,
    Order,
    OrderItem,
    Product,
    ProductFeature,
    ProductImage,
    Review,
    Sale,
    SuperCategory,
)


class ShopQuerySets:
    @staticmethod
    def get_product_queryset_for_shop_home_view() -> QuerySet:
        return (
            Product.objects.only("id", "name", "price", "sold")
            .order_by("access_number").select_related("category").only(
                'category__name', 'category__slug'
            ).prefetch_related(
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
            .reverse()[:100]
        )

    @staticmethod
    def get_order_queryset_for_user_account_view(user: AUTH_USER_MODEL) -> QuerySet:
        return (
            Order.objects.filter(buyer__user=user)
            .select_related("buyer")
            .prefetch_related(
                Prefetch(
                    "sale_set",
                    queryset=Sale.objects.only("sale_date"),
                ),
                Prefetch(
                    "orderitem_set",
                    queryset=OrderItem.objects.only("product", "quantity"),
                ),
                Prefetch(
                    "orderitem_set__product",
                    queryset=Product.objects.only("name", "price"),
                ),
            )
            .order_by("ordered_at")
            .reverse()
        )

    @staticmethod
    def get_product_queryset_for_category_view(slug: str) -> QuerySet:
        return (
            Product.objects.filter(category__slug=slug)
            .select_related("category", "brand", "category__super_category")
            .only("name", "price", "brand", "category")
            .defer("category__slug", "brand__slug")
            .prefetch_related("productimage_set")
        )

    @staticmethod
    def get_product_queryset_for_product_view() -> QuerySet:
        return Product.objects.select_related(
            "category", "category__super_category"
        ).only(
            "name",
            "description",
            "category",
            "vendor_code",
            "price",
            "sold",
            "category__name",
            "category__super_category",
            "category__super_category__name",
        )

    @staticmethod
    def get_product_features_queryset_for_product_view(product: Product) -> QuerySet:
        return (
            ProductFeature.objects.filter(product=product)
            .defer("feature_name__category")
            .select_related("feature_name")
        )

    @staticmethod
    def get_product_image_queryset_for_product_view(product: Product) -> QuerySet:
        return ProductImage.objects.filter(product=product)

    @staticmethod
    def get_review_queryset_for_product_view(product: Product) -> QuerySet:
        return (
            Review.objects.filter(product=product)
            .select_related("review_author")
            .only(
                "product",
                "grade",
                "review_text",
                "review_date",
                "review_author",
                "like_num",
                "dislike_num",
                "review_author__username",
            )
        )

    @staticmethod
    def get_product_for_search_result_view(query: QueryDict) -> QuerySet:
        return (
            Product.objects.filter(name__icontains=query)
            .only(
                "name",
                "price",
            )
            .prefetch_related("productimage_set")
            .order_by("access_number")
            .reverse()[:100]
        )

    @staticmethod
    def get_super_category_queryset_for_data_mixin() -> QuerySet:
        return SuperCategory.objects.all().prefetch_related(
            Prefetch("category_set", queryset=Category.objects.defer("slug"))
        )

    @staticmethod
    def get_category_queryset_for_data_mixin() -> QuerySet:
        return Category.objects.defer("slug").select_related("super_category")


querysets = ShopQuerySets()
