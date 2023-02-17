from django.contrib.auth.views import LogoutView
from django.urls import path
from .views import *

app_name = 'shop'

urlpatterns = [
    path('', ShopHome.as_view(), name='home'),
    path('accounts/register/', RegisterUser.as_view(template_name='shop/register/register.html'), name='registration'),
    path('accounts/login/', ModLoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page='shop:home'), name='logout'),
    path('accounts/password_change/', ModPasswordChangeView.as_view(), name='password_change'),
    path('accounts/password_reset/', ModPasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', ModPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', ModPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done', ModPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/<int:pk>', UserAccount.as_view(), name='user_account'),
    path('category/<slug:category_slug>/', CategoryView.as_view(), name='category'),
    path('super_category/<int:super_category_pk>/', SuperCategoryView.as_view(), name='super_category'),
    path('search/', SearchResultView.as_view(), name='search_results'),
    path('about', AboutView.as_view(), name='about'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('contacts/', ContactView.as_view(), name='contacts'),
    path('help/', HelpView.as_view(), name='help'),
    path('delivery/', DeliveryView.as_view(), name='delivery'),
    path('credit/', CreditView.as_view(), name='credit'),
    path('return-products/', ReturnProductsView.as_view(), name='return_products'),
    path('service-centers/', ServiceCentersView.as_view(), name='service_centers'),
    path('for-partners/', ForPartnersView.as_view(), name='for_partners'),
    path('product/<slug:product_slug>/', ProductView.as_view(), name='product'),
    path('product-form/<slug:product_slug>/', ReviewFormView.as_view(), name='product_form'),
    path('update_item/', updateItem, name='update_item'),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('update_like/', updateLike, name='update_like'),
]
