from django.db import models

class Buyer(models.Model):
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
    name = models.CharField(max_length=500)
    description = models.TextField()
    image = models.URLField(max_length=500)

    def __min_price(self):
        return self.pack_set.order_by('price')[0].price

    def short_caption(self):
        return f'☕️ {self.name}\n💵 Цена: {self.__min_price()}'

    def long_caption(self):
        return f'☕️ {self.name}\n💵 Цена: {self.__min_price()}\n\n{self.description}'

    def __str__(self):
        return self.name


class Pack(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit = models.CharField(max_length=5)
    size = models.IntegerField()
    price = models.FloatField()

    def __str__(self):
        return f'{self.product.name} {self.size} {self.unit}'


class Cart(models.Model):
    user = models.OneToOneField(Buyer, on_delete=models.CASCADE, primary_key=True)
    total_message_id = models.BigIntegerField(default=0)

    def __str__(self):
        return f'{self.user.full_name}'

    def contains(self, pack: Pack) -> bool:
        """Returns True if cart already contains pack"""
        return bool(self.cartitem_set.all().filter(pack=pack.id))

    def is_empty(self):
        """Returns True if no item present in the cart"""
        return not self.cartitem_set.all()

    def get_total_price(self):
        """Return the sum of prices of all items in the cart"""
        price = 0
        for item in self.cartitem_set.all():
            price = price + (item.pack.price * item.count)
        return price

    def add_pack(self, pack: Pack):
        """Creates CartItem with passed pack"""
        self.cartitem_set.create(
            pack=pack,
            count=1
        )

    def remove_pack(self, pack: Pack):
        """Removes pack from the cart"""
        cart_item = self.cartitem_set.get(pack=pack)
        cart_item.delete()

    def increase_pack_count(self, pack: Pack):
        """Increase count for specific pack"""
        cart_item = self.cartitem_set.get(pack=pack)
        # the maximum pack count is 10
        cart_item.count = min(cart_item.count + 1, 10)
        cart_item.save()

    def decrease_pack_count(self, pack: Pack):
        """Decrease count for specific pack"""
        cart_item = self.cartitem_set.get(pack=pack)
        # the minimum count is 1
        cart_item.count = max(cart_item.count - 1, 1)
        cart_item.save()


class Order(models.Model):
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
    count = models.IntegerField()
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True)
    pack = models.ForeignKey(Pack, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.count} x {self.pack}'
