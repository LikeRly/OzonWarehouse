# core/views.py

from decimal import Decimal
from datetime import timedelta, date

from django.db.models import Q, Sum, F
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone

from .forms import UserForm, ProfileForm, CustomRegisterForm
from .models import Product, Transaction, UserAction
from django.contrib.auth.forms import PasswordChangeForm


def index(request):
    """Главная страница: товары и транзакции"""
    products = Product.objects.all()
    transaction_list = (
        Transaction.objects
        .select_related('product')
        .all()
        .order_by('-date')
    )
    return render(request, 'index.html', {
        'products': products,
        'transactions': transaction_list,
    })


@login_required
def analytics(request):
    """Страница аналитики с данными"""

    # Получаем и валидируем даты из GET-параметров
    today = timezone.localdate()
    raw_from = request.GET.get('date_from')
    raw_to = request.GET.get('date_to')

    try:
        date_from = date.fromisoformat(raw_from) if raw_from else today - timedelta(days=30)
    except ValueError:
        date_from = today - timedelta(days=30)

    try:
        date_to = date.fromisoformat(raw_to) if raw_to else today
    except ValueError:
        date_to = today

    # Если даты перепутаны, меняем местами
    if date_to < date_from:
        date_from, date_to = date_to, date_from

    # Базовый queryset только по продажам в диапазоне
    qs = Transaction.objects.filter(
        type='sale',
        date__date__gte=date_from,
        date__date__lte=date_to
    )

    # Группировка по дате (для графика)
    daily = (
        qs
        .annotate(day=TruncDate('date'))
        .values('day')
        .annotate(total=Sum('total_price'))
        .order_by('day')
    )
    sales_chart_labels = [entry['day'].strftime('%d.%m') for entry in daily]
    sales_chart_data   = [float(entry['total']) for entry in daily]

    # Всего продаж за период и средний чек
    period_total = qs.aggregate(total=Sum('total_price'))['total'] or 0
    tx_count     = qs.count()
    avg_check    = (period_total / tx_count) if tx_count else 0

    # Топ-5 товаров по количеству проданных единиц
    top5 = (
        qs
        .values(name=F('product__name'))
        .annotate(sold=Sum('quantity'))
        .order_by('-sold')[:5]
    )
    top_5_products = [{'name': p['name'], 'sold': p['sold']} for p in top5]

    analytics_ctx = {
        'sales_chart_labels': sales_chart_labels,
        'sales_chart_data':   sales_chart_data,
        'period_total':       int(period_total),
        'avg_check':          int(avg_check),
        'top_5_products':     top_5_products,
        'date_from':          date_from.isoformat(),
        'date_to':            date_to.isoformat(),
    }
    return render(request, 'analytics.html', {'analytics': analytics_ctx})


@login_required
def transactions_view(request):
    """
    Список транзакций с регистрационно-независимым AJAX-поиском.
    """
    q = request.GET.get('q', '').strip()
    qs = Transaction.objects.select_related('product').all()
    if q:
        # Для SQLite: делаем фильтрацию в Python
        q_lower = q.lower()
        qs = [
            tx for tx in qs
            if q_lower in (tx.product.name or '').lower()
               or q_lower in (tx.product.category or '').lower()
               or q_lower in (tx.type or '').lower()
        ]
        qs = sorted(qs, key=lambda x: x.date, reverse=True)
    else:
        qs = qs.order_by('-date')

    products = Product.objects.all()
    context = {'transactions': qs, 'products': products, 'q': q}

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/_transactions_rows.html', context)
    return render(request, 'transactions.html', context)


@login_required
@require_POST
def add_product(request):
    name     = request.POST.get('name')
    category = request.POST.get('category') or None
    quantity = int(request.POST.get('quantity') or 0)
    price    = Decimal(request.POST.get('price') or 0)

    product = Product.objects.create(
        name=name, category=category,
        quantity=quantity, price=price
    )
    UserAction.objects.create(
        user=request.user,
        action_type='add',
        description=f"Добавил товар: {product.name}"
    )
    messages.success(request, 'Товар добавлен.')
    return redirect('index')


@login_required
@require_POST
def edit_product(request):
    pid      = request.POST.get('id')
    product  = get_object_or_404(Product, pk=pid)
    product.name     = request.POST.get('name')
    product.category = request.POST.get('category') or None
    product.quantity = int(request.POST.get('quantity') or 0)
    product.price    = Decimal(request.POST.get('price') or 0)
    product.save()

    UserAction.objects.create(
        user=request.user,
        action_type='edit',
        description=f"Отредактировал товар: {product.name}"
    )
    messages.success(request, 'Товар обновлён.')
    return redirect('index')


@login_required
@require_POST
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name    = product.name
    product.delete()

    UserAction.objects.create(
        user=request.user,
        action_type='delete',
        description=f"Удалил товар: {name}"
    )
    messages.info(request, 'Товар удалён.')
    return redirect('index')


@login_required
@require_POST
def add_transaction(request):
    item_id  = request.POST.get('item_id')
    tx_type  = request.POST.get('type')
    quantity = int(request.POST.get('quantity') or 0)
    product  = get_object_or_404(Product, pk=item_id)

    if quantity <= 0:
        messages.error(request, 'Количество должно быть положительным.')
        return redirect('transactions')
    if tx_type == 'sale' and product.quantity < quantity:
        messages.error(request, 'Недостаточно товара на складе для продажи.')
        return redirect('transactions')

    total_price = product.price * quantity
    tx = Transaction.objects.create(
        product=product,
        type=tx_type,
        quantity=quantity,
        total_price=total_price,
    )
    # Обновляем остаток
    if tx_type == 'sale':
        product.quantity -= quantity
    else:
        product.quantity += quantity
    product.save()

    UserAction.objects.create(
        user=request.user,
        action_type='add',
        description=f"Добавил транзакцию №{tx.id} для товара «{product.name}»"
    )
    messages.success(request, 'Транзакция добавлена.')
    return redirect('transactions')


@login_required
@require_POST
def edit_transaction(request):
    tid      = request.POST.get('id')
    tx       = get_object_or_404(Transaction, pk=tid)
    old_prod = tx.product
    old_qty  = tx.quantity

    # Откат старого влияния
    if tx.type == 'sale':
        old_prod.quantity += old_qty
    else:
        old_prod.quantity = max(old_prod.quantity - old_qty, 0)
    old_prod.save()

    new_prod = get_object_or_404(Product, pk=request.POST.get('item_id'))
    new_type = request.POST.get('type')
    new_qty  = int(request.POST.get('quantity') or 0)

    if new_qty <= 0:
        messages.error(request, 'Количество должно быть положительным.')
        return redirect('transactions')
    if new_type == 'sale' and new_prod.quantity < new_qty:
        messages.error(request, 'Недостаточно товара на складе для продажи.')
        return redirect('transactions')

    new_total = new_prod.price * new_qty
    if new_type == 'sale':
        new_prod.quantity -= new_qty
    else:
        new_prod.quantity += new_qty
    new_prod.save()

    tx.product     = new_prod
    tx.type        = new_type
    tx.quantity    = new_qty
    tx.total_price = new_total
    tx.save()

    UserAction.objects.create(
        user=request.user,
        action_type='edit',
        description=f"Отредактировал транзакцию №{tx.id}"
    )
    messages.success(request, 'Транзакция обновлена.')
    return redirect('transactions')


@login_required
@require_POST
def delete_transaction(request, pk):
    tx   = get_object_or_404(Transaction, pk=pk)
    prod = tx.product
    qty  = tx.quantity

    if tx.type == 'sale':
        prod.quantity += qty
    else:
        prod.quantity = max(prod.quantity - qty, 0)
    prod.save()

    tx.delete()
    UserAction.objects.create(
        user=request.user,
        action_type='delete',
        description=f"Удалил транзакцию №{pk} для товара «{prod.name}»"
    )
    messages.info(request, 'Транзакция удалена.')
    return redirect('transactions')


def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = CustomRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def update_profile(request):
    user    = request.user
    profile = user.profile

    if request.method == 'POST':
        uf = UserForm(request.POST, instance=user)
        pf = ProfileForm(request.POST, request.FILES, instance=profile)
        if uf.is_valid() and pf.is_valid():
            uf.save()
            pf.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('index')
    else:
        uf = UserForm(instance=user)
        pf = ProfileForm(instance=profile)

    return render(request, 'profile_update.html', {
        'user_form':    uf,
        'profile_form': pf,
    })


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён.')
            return redirect('index')
        else:
            messages.error(request, 'Ошибка при изменении пароля.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'profile_change_password.html', {'form': form})


@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        messages.info(request, 'Аккаунт удалён.')
    return redirect('index')
