from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


def user_directory_path_1(instance, filename):
    return 'super_category_{0}/{1}'.format(instance.name, filename)


class SuperCategory(models.Model):
    name = models.CharField(max_length=50, verbose_name="Загальна категорія")
    icon = models.ImageField(upload_to=user_directory_path_1, blank=True, verbose_name="Іконка")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:super_category", kwargs={'super_category_pk': self.pk})

    class Meta:
        verbose_name = "Загальна категорія"
        verbose_name_plural = "Загальні категорії"


def user_directory_path_2(instance, filename):
    return 'category_{0}/{1}'.format(instance.name, filename)


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Категорія")
    slug = models.SlugField(unique=True, verbose_name="URL")
    super_category = models.ForeignKey(SuperCategory, on_delete=models.CASCADE)
    icon = models.ImageField(upload_to=user_directory_path_2, blank=True, null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("shop:category", kwargs={"category_slug": self.slug})

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"


class CategoryFeatures(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    feature_name = models.CharField(max_length=100, verbose_name='Характеристика категорії')

    def __str__(self):
        return self.feature_name

    class Meta:
        verbose_name = "Характеристика категорії"
        verbose_name_plural = "Характеристики категорії"


class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name="Найменування бренда")
    slug = models.SlugField(unique=True, verbose_name='URL')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренди"


class Supplier(models.Model):
    name = models.CharField(max_length=150, verbose_name="Назва постачальника")
    inn = models.CharField(max_length=15, blank=True, verbose_name="ІПН")
    pdv = models.CharField(max_length=15, blank=True, verbose_name="Номер свідоцтва ПДВ")
    egrpou = models.CharField(max_length=15, blank=True, verbose_name="ЄДРПОУ")
    bank = models.CharField(max_length=50, blank=True, verbose_name="Банк")
    mfo = models.CharField(max_length=8, blank=True, verbose_name="Банк")
    checking_account = models.CharField(max_length=50, blank=True, verbose_name="Розрахунковий рахунок")
    tel = models.CharField(max_length=15, verbose_name="Телефон")
    email = models.EmailField(verbose_name="Електронна адреса")
    person = models.CharField(max_length=20, verbose_name="Контактна особа")
    date_creation = models.DateField(auto_now_add=True, verbose_name="Дата внесення в базу")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Постачальник"
        verbose_name_plural = "Постачальники"


class Product(models.Model):
    name = models.CharField(max_length=150, verbose_name="Найменування продукту")
    model = models.CharField(max_length=50, verbose_name="Модель")
    slug = models.SlugField(unique=True, verbose_name='URL')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, verbose_name="Найменування бренду")
    description = models.TextField(verbose_name="Опис")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категорія")
    vendor_code = models.CharField(max_length=50, verbose_name="Артикул")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    supplier = models.ManyToManyField(Supplier, verbose_name="Постачальник")
    sold = models.BooleanField(verbose_name="Проданий")
    notes = models.CharField(max_length=200, blank=True, verbose_name="Додаткова інформація")
    last_accessed = models.DateTimeField(blank=True, null=True, verbose_name="Дата останнього відвідування")
    access_number = models.PositiveBigIntegerField(verbose_name="Кількість переглядів", default=0)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product', kwargs={'product_slug': self.slug})

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукти"


class ProductFeature(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="Товар"
    )
    feature_name = models.ForeignKey(
        CategoryFeatures,
        on_delete=models.CASCADE,
        verbose_name="Найменування характеристики",
    )
    feature = models.CharField(max_length=100, blank=True, null=True, verbose_name='Характеристика товара')

    def __str__(self):
        return self.feature

    class Meta:
        verbose_name = "Характеристики товару"
        verbose_name_plural = "Характеристики товарів"


def user_directory_path(instance, filename):
    return 'product_{0}/{1}'.format(instance.product.slug, filename)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    image = models.ImageField(upload_to=user_directory_path, blank=True, verbose_name="Зображення")

    def __str__(self):
        return 'Image'

    class Meta:
        verbose_name = "Зображення товару"
        verbose_name_plural = "Зображення товарів"


class Review(models.Model):
    MARKS = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Відгук на продукт")
    grade = models.PositiveSmallIntegerField(blank=True, choices=MARKS, verbose_name="Оцінка")
    review_text = models.CharField(max_length=255, blank=True, verbose_name="Текст відгуку")
    review_date = models.DateField(auto_now_add=True, verbose_name="Дата створення")
    review_author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор відгуку", blank=True,
                                      null=True)
    like_num = models.SmallIntegerField(blank=True, null=True, verbose_name="Кількість лайків")
    dislike_num = models.SmallIntegerField(blank=True, null=True, verbose_name="Кількість дизлайків")

    def __str__(self):
        return self.product.name + '-review'

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"


class Like(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, verbose_name="Відгук")
    like = models.BooleanField(verbose_name="Лайк")
    dislike = models.BooleanField(verbose_name="Дизлайк", blank=True, null=True)
    like_author = models.ForeignKey(User, on_delete=models.CASCADE,
                                    blank=True, null=True, verbose_name="Автор лайку")

    def __str__(self):
        return 'Likes'

    class Meta:
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"


class Income(models.Model):
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL, verbose_name="Найменування товару")
    income_quantity = models.PositiveSmallIntegerField(verbose_name="Кількість")
    income_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Вхідна ціна")
    supplier = models.ForeignKey(Supplier, null=True, on_delete=models.SET_NULL, verbose_name="Постачальник")
    income_date = models.DateField(auto_now_add=True, verbose_name="Дата поставки")

    def __str__(self):
        return str(self.income_date)

    class Meta:
        verbose_name = "Поставка"
        verbose_name_plural = "Поставки"


class Buyer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Користувач")
    name = models.CharField(max_length=50, null=True, blank=True, verbose_name="Ім'я")
    email = models.EmailField(null=True, blank=True, verbose_name="Електронна адреса")
    tel = models.CharField(max_length=15, blank=True, verbose_name="Телефон")
    address = models.CharField(max_length=30, blank=True, verbose_name="Адреса")

    class Meta:
        verbose_name = "Покупець"
        verbose_name_plural = "Покупці"

    def __str__(self):
        return str(self.name)


class Order(models.Model):
    buyer = models.ForeignKey(Buyer, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Замовлення")
    date_ordered = models.DateTimeField(auto_now_add=True, verbose_name="Дата замовлення")
    complete = models.BooleanField(default=False, verbose_name="Виконання")

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    def __str__(self):
        return str(self.date_ordered)

    @property
    @admin.display(description="Загальна сума")
    def get_order_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    @admin.display(description="Загальна кількість")
    def get_order_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total


class OrderItem(models.Model):
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Товар")
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Замовлення")
    quantity = models.IntegerField(default=0, verbose_name="Кількість")
    date_added = models.DateTimeField(auto_now_add=True, verbose_name="Дата додавання")

    class Meta:
        verbose_name = "Замовлений товар"
        verbose_name_plural = "Замовлені товари"

    def __str__(self):
        return self.product.name

    @property
    @admin.display(description="Сума замовлення")
    def get_total(self):
        total = self.product.price * self.quantity
        return total


class Sale(models.Model):
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Замовлення")
    sale_date = models.DateField(auto_now_add=True, verbose_name="Дата продажу")
    region = models.CharField(max_length=80, blank=True, verbose_name="Регіон")
    city = models.CharField(max_length=80, blank=True, verbose_name="Місто")
    department = models.CharField(max_length=6, blank=True, verbose_name="Номер відділення")

    def __str__(self):
        return str(self.sale_date)

    class Meta:
        verbose_name = "Продаж"
        verbose_name_plural = "Продажі"


class Stock(models.Model):
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Товар")
    income = models.OneToOneField(Income, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Поставка")
    quantity = models.IntegerField(verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Постачальник")

    def __str__(self):
        return self.product.name

    class Meta:
        verbose_name = "Склад"
        verbose_name_plural = "Склади"

    @property
    def get_price_total(self):
        total = self.quantity * self.price
        return total


def user_directory_path_3(instance, filename):
    return 'page_{0}/{1}'.format(instance.slug, filename)


class PageData(models.Model):
    page_name = models.CharField(max_length=50, verbose_name='Назва сторінки')
    slug = models.SlugField(unique=True, verbose_name='Назва сторінки англійською')
    banner = models.ImageField(upload_to=user_directory_path, blank=True, verbose_name="Баннер")
    image_1 = models.ImageField(upload_to=user_directory_path, blank=True, verbose_name="Зображення 1")
    image_2 = models.ImageField(upload_to=user_directory_path, blank=True, verbose_name="Зображення 2")
    image_3 = models.ImageField(upload_to=user_directory_path, blank=True, verbose_name="Зображення 3")
    header_1 = models.CharField(max_length=255, verbose_name='Заголовок 1')
    header_2 = models.CharField(max_length=255, verbose_name='Заголовок 2')
    header_3 = models.CharField(max_length=255, verbose_name='Заголовок 3')
    text_1 = models.TextField(verbose_name="Текстове поле 1")
    text_2 = models.TextField(verbose_name="Текстове поле 2")
    text_3 = models.TextField(verbose_name="Текстове поле 3")

