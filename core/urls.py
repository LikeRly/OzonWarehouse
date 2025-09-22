from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('analytics/', views.analytics, name='analytics'),

    # товары
    path('product/add/',         views.add_product,    name='add_product'),
    path('product/edit/',        views.edit_product,   name='edit_product'),
    path('product/<int:pk>/delete/', views.delete_product, name='delete_product'),

    # профиль
    path('profile/update/',      views.update_profile, name='update_profile'),
    path('profile/password/',    views.change_password, name='change_password'),
    path('profile/delete/',      views.delete_account, name='delete_account'),
    path('register/',            views.register,       name='register'),

    # транзакции
    path('transactions/',                 views.transactions_view,   name='transactions'),
    path('transactions/add/',             views.add_transaction,     name='add_transaction'),
    # <-- добавляем путь для редактирования:
    path('transactions/edit/',            views.edit_transaction,    name='edit_transaction'),
    path('transactions/<int:pk>/delete/', views.delete_transaction,  name='delete_transaction'),
]
