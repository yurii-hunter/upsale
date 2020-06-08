"""
List of models that are used for telegram bot and admin panel
"""
from functools import reduce
from django.db import models


class Buyer(models.Model):
    """Describes a user that uses bot"""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, null=True)
    language_code = models.CharField(max_length=20)
    link = models.URLField(max_length=200, null=True)
    is_bot = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, null=True)

    def __str__(self):
        return self.full_name


class Product(models.Model):
    """Describes product that could be added to the shop"""

    name = models.CharField(max_length=500)
    description = models.TextField()
    image = models.URLField(max_length=500)

    def __min_price(self):
        return self.stockkeepingunit_set.order_by('price')[0].price

    def short_caption(self):
        return f'☕️ {self.name}\n💵 Цена: {self.__min_price()}'

    def long_caption(self):
        return f'☕️ {self.name}\n💵 Цена: {self.__min_price()}\n\n{self.description}'

    def __str__(self):
        return self.name


class Pack(models.Model):
    """Describes pack that could be used for a product"""

    unit = models.CharField(max_length=5)
    size = models.IntegerField()

    def __str__(self):
        return f'{self.size} {self.unit}'


class StockKeepingUnit(models.Model):
    """Describes unique item in the shop"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE)
    price = models.FloatField()

    def __str__(self):
        return f'{self.product} {self.pack} - {self.price} грн'


class Cart(models.Model):
    """Describes cart that is used by Bayer for keeping stock units"""

    buyer = models.OneToOneField(Buyer, on_delete=models.CASCADE, primary_key=True)
    items = models.ManyToManyField(StockKeepingUnit, through='CartItem')
    total_message_id = models.BigIntegerField(default=0)

    def __str__(self):
        return f'{self.buyer.full_name}'

    def contains(self, sku: StockKeepingUnit) -> bool:
        """Returns True if cart already contains pack"""
        return self.items.filter(id=sku.id).exists()

    def is_empty(self):
        """Returns True if no item present in the cart"""
        return not self.items.exists()

    def get_total_price(self):
        """Return the sum of prices of all items in the cart"""
        return reduce(lambda price, item: price + item.price, self.items.all(), 0)

    def add_sku(self, sku: StockKeepingUnit):
        """Creates CartItem with passed pack"""
        CartItem(cart=self, sku=sku).save()

    def clear_sku(self, sku: StockKeepingUnit):
        """Removes pack from the cart"""
        CartItem.objects.filter(sku=sku).delete()

    def remove_sku(self, sku: StockKeepingUnit):
        """Decrease count for specific pack"""
        CartItem.objects.filter(sku=sku)[0].delete()


class Order(models.Model):
    """Describes order from Buyer"""

    STATUS = [
        ('new', 'new'),
        ('in_progress', 'in progress'),
        ('done', 'done')
    ]
    status = models.CharField(max_length=32, choices=STATUS, default='new')
    user = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    city = models.CharField(max_length=50, null=True)
    branch_number = models.IntegerField(null=True)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'[{self.status}] {self.user.full_name} - {self.created}'


class CartItem(models.Model):
    """Used for many to many relationship"""
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    sku = models.ForeignKey(StockKeepingUnit, on_delete=models.CASCADE)
