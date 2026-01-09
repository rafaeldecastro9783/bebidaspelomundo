from django.db import transaction
from django.utils import timezone
from loja.models import LoteProduto, Produto

class EstoqueInsuficiente(Exception):
    pass


@transaction.atomic
def baixar_estoque_por_lote(produto, quantidade):
    """
    Baixa estoque respeitando FIFO por data de vencimento.
    Operação atômica para evitar inconsistência.
    """

    lotes = (
        LoteProduto.objects
        .select_for_update()
        .filter(
            produto=produto,
            ativo=True,
            quantidade__gt=0,
            data_vencimento__gte=timezone.now().date()
        )
        .order_by("data_vencimento")
    )

    quantidade_restante = quantidade

    for lote in lotes:
        if quantidade_restante <= 0:
            break

        if lote.quantidade >= quantidade_restante:
            lote.quantidade -= quantidade_restante
            lote.save()
            quantidade_restante = 0
        else:
            quantidade_restante -= lote.quantidade
            lote.quantidade = 0
            lote.ativo = False
            lote.save()

    if quantidade_restante > 0:
        raise EstoqueInsuficiente(
            f"Estoque insuficiente para o produto {produto.titulo}"
        )

    # Atualiza estoque agregado do produto (campo derivado)
    produto.estoque = sum(
        l.quantidade for l in produto.lotes.filter(ativo=True)
    )
    produto.save()
