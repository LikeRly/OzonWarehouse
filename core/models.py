# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        default='avatars/default.png'
    )

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Создаёт профиль при регистрации и сохраняет его при обновлении юзера.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()


class UserAction(models.Model):
    """
    Лог действий пользователя (добавление/редактирование/удаление/вход).
    """
    ACTION_TYPES = [
        ('add', 'Добавление'),
        ('edit', 'Редактирование'),
        ('delete', 'Удаление'),
        ('login', 'Вход в систему'),
    ]
    user = models.ForeignKey(
        User,
        related_name='actions',
        on_delete=models.CASCADE
    )
    action_type = models.CharField(
        max_length=16,
        choices=ACTION_TYPES
    )
    description = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ts = self.date.strftime('%d.%m.%Y %H:%M')
        return f"{self.user.username} — {self.get_action_type_display()}: {self.description} ({ts})"


class Product(models.Model):
    name = models.CharField("Название", max_length=255)
    category = models.CharField(
        "Категория",
        max_length=100,
        blank=True,
        null=True
    )
    quantity = models.IntegerField("Кол-во на складе", default=0)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    date_added = models.DateTimeField("Дата добавления", auto_now_add=True)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """
    Транзакция: списание (sale), приход (incoming) или другое.
    """
    TYPE_CHOICES = [
        ('sale', 'Продажа'),
        ('incoming', 'Поступление'),
        ('other', 'Другое'),
    ]

    product = models.ForeignKey(
        Product,
        verbose_name="Товар",
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )
    type = models.CharField(
        "Тип операции",
        max_length=20,
        choices=TYPE_CHOICES,
        default='other'
    )
    quantity = models.IntegerField("Количество")
    total_price = models.DecimalField(
        "Общая цена",
        max_digits=12,
        decimal_places=2
    )
    date = models.DateTimeField("Дата и время", auto_now_add=True)

    @property
    def item_name(self):
        # Возвращаем название товара, если он существует
        return self.product.name if self.product else ''

    @property
    def category(self):
        # Возвращаем категорию товара, если он существует и категория не пуста
        if self.product and self.product.category:
            return self.product.category
        return ''

    def get_type_display(self):
        # Чтобы можно было обращаться просто transaction.type_display()
        return dict(self.TYPE_CHOICES).get(self.type, self.type)

    def __str__(self):
        return f"#{self.pk} — {self.get_type_display()} {self.item_name}"
