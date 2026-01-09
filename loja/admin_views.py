from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from .models import *
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

@staff_member_required
def admin_produto_pdv(request):
    produto = None

    # 🔍 BUSCA POR CÓDIGO DE BARRAS
    if "barcode" in request.GET:
        codigo = request.GET.get("barcode")
        produto = Produto.objects.filter(codigo_barras=codigo).first()

        if not produto:
            messages.info(
                request,
                "Produto não encontrado. Cadastre um novo abaixo."
            )

    # 💾 SALVAR PRODUTO
    if request.method == "POST" and "salvar_produto" in request.POST:
        codigo = request.POST["codigo_barras"]

        produto, _ = Produto.objects.get_or_create(
            codigo_barras=codigo
        )

        produto.titulo = request.POST["titulo"]
        produto.preco_compra = request.POST["preco_compra"]
        produto.preco_venda = request.POST["preco_venda"]
        produto.descricao = request.POST.get("descricao", "")
        produto.devolucao = request.POST.get("devolucao", "")
        produto.categoria_id = request.POST["categoria"]

        produto.save()

        messages.success(request, "Produto salvo com sucesso!")

    # 📦 ADICIONAR LOTE
    if request.method == "POST" and "add_lote" in request.POST:
        produto = get_object_or_404(
            Produto, id=request.POST["produto_id"]
        )

        LoteProduto.objects.create(
            produto=produto,
            codigo_lote=request.POST.get("codigo_lote"),
            quantidade=int(request.POST["quantidade"]),
            data_vencimento=request.POST["data_vencimento"],
        )

        messages.success(request, "Lote adicionado!")
        return redirect(
            f"/admin/produtos/?barcode={produto.codigo_barras}"
        )

    categorias = Categoria.objects.all()

    return render(
        request,
        "admin/produto_pdv.html",
        {
            "produto": produto,
            "categorias": categorias,
        }
    )


@staff_member_required
def dashboard_admin(request):
    hoje = timezone.now().date()
    alerta = hoje + timedelta(days=7)

    context = {
        "produtos_sem_estoque": Produto.objects.filter(estoque=0).count(),
        "produtos_estoque_baixo": Produto.objects.filter(estoque__gt=0, estoque__lt=5).count(),
        "lotes_vencidos": LoteProduto.objects.filter(data_vencimento__lt=hoje, ativo=True).count(),
        "lotes_vencendo": LoteProduto.objects.filter(
            data_vencimento__gte=hoje,
            data_vencimento__lte=alerta,
            ativo=True
        ).count(),
        "pix_pagos_hoje": Pagamento.objects.filter(
            status="PAGO",
            confirmado_em__date=hoje
        ).count(),
    }

    return render(request, "admin/dashboard.html", context)
