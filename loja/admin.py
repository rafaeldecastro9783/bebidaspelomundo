from django.utils.html import format_html
from django.utils import timezone
from django.shortcuts import render, redirect
from datetime import timedelta
from .models import (
    Cliente,
    Categoria,
    Produto,
    LoteProduto,
    Kart,
    KartProduto,
    OrdemPedido,
)

import csv
from django.contrib import admin, messages
from django.utils.text import slugify
from django.shortcuts import redirect
from django.urls import path
from django import forms

class ImportarProdutoCSVForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo CSV")

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("titulo",)}
    search_fields = ("titulo",)

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "user", "data_on")
    search_fields = ("nome_completo", "user__username")


class LoteProdutoInline(admin.TabularInline):
    model = LoteProduto
    extra = 1
    fields = ("codigo_lote", "quantidade", "data_vencimento", "ativo")
    readonly_fields = ()

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "imagem_preview",
        "titulo",
        "codigo_barras",
        "categoria",
        "estoque",
        "estoque_status",
        "vencimento_status",
    )

    search_fields = ("titulo", "codigo_barras")
    list_filter = ("categoria",)
    readonly_fields = ("estoque", "imagem_preview")

    change_list_template = "admin/produto_changelist.html"

    fieldsets = (
        ("Informações Básicas", {
            "fields": (
                "titulo",
                "slug",
                "categoria",
                "codigo_barras",
            )
        }),
        ("Preços", {
            "fields": (
                "preco_compra",
                "preco_venda",
            )
        }),
        ("Imagens do Produto", {
            "fields": (
                "imagem",
                "imagem2",
                "imagem3",
                "imagem_preview",
            )
        }),
        ("Detalhes", {
            "fields": (
                "descricao",
                "devolucao",
                "avaliacao",
            )
        }),
        ("Estoque", {
            "fields": ("estoque",)
        }),
    )

    prepopulated_fields = {"slug": ("titulo",)}
    inlines = [LoteProdutoInline]

    # =============================
    # 📥 IMPORTAÇÃO CSV
    # =============================
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "importar-csv/",
                self.admin_site.admin_view(self.importar_csv),
                name="produto_importar_csv",
            ),
        ]
        return custom_urls + urls

    def importar_csv(self, request):
        if request.method == "POST":
            form = ImportarProdutoCSVForm(request.POST, request.FILES)

            if form.is_valid():
                arquivo = request.FILES["arquivo"]
                linhas = arquivo.read().decode("utf-8").splitlines()
                reader = csv.DictReader(linhas)

                criados = 0
                ignorados = 0

                for row in reader:
                    categoria, _ = Categoria.objects.get_or_create(
                        titulo=row["categoria"],
                        defaults={"slug": slugify(row["categoria"])}
                    )

                    produto, criado = Produto.objects.get_or_create(
                        codigo_barras=row["codigo_barras"],
                        defaults={
                            "titulo": row["titulo"],
                            "slug": slugify(row["titulo"]),
                            "categoria": categoria,
                            "preco_compra": int(row["preco_compra"]),
                            "preco_venda": int(row["preco_venda"]),
                            "descricao": row["descricao"],
                            "devolucao": row["devolucao"],
                        }
                    )

                    if criado:
                        LoteProduto.objects.create(
                            produto=produto,
                            quantidade=int(row["estoque"]),
                            data_vencimento=row["data_vencimento"],
                        )
                        produto.estoque += int(row["estoque"])
                        produto.save()
                        criados += 1
                    else:
                        ignorados += 1

                self.message_user(
                    request,
                    f"{criados} produtos importados | {ignorados} já existentes.",
                    messages.SUCCESS,
                )
                return redirect("..")

        else:
            form = ImportarProdutoCSVForm()

        context = {
            **self.admin_site.each_context(request),
            "form": form,
            "title": "Importar produtos via CSV",
        }

        return render(request, "admin/importar_csv.html", context)

    # =============================
    # 📸 PREVIEW DA IMAGEM
    # =============================
    def imagem_preview(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="width:80px;height:80px;object-fit:cover;border-radius:6px;" />',
                obj.imagem.url
            )
        return "-"

    imagem_preview.short_description = "Imagem"

    # =============================
    # 🔴🟡🟢 STATUS DE ESTOQUE
    # =============================
    def estoque_status(self, obj):
        if obj.estoque == 0:
            return format_html(
                '<span style="color:white;background:#d9534f;padding:3px 8px;border-radius:4px;">SEM ESTOQUE</span>'
            )
        elif obj.estoque < 5:
            return format_html(
                '<span style="color:black;background:#f0ad4e;padding:3px 8px;border-radius:4px;">BAIXO</span>'
            )
        return format_html(
            '<span style="color:white;background:#5cb85c;padding:3px 8px;border-radius:4px;">OK</span>'
        )

    estoque_status.short_description = "Estoque"

    # =============================
    # ⏰ STATUS DE VENCIMENTO
    # =============================
    def vencimento_status(self, obj):
        hoje = timezone.now().date()
        alerta = hoje + timedelta(days=7)
        lotes = obj.lotes.filter(ativo=True)

        if lotes.filter(data_vencimento__lt=hoje).exists():
            return format_html(
                '<span style="color:white;background:#000;padding:3px 8px;border-radius:4px;">VENCIDO</span>'
            )

        if lotes.filter(data_vencimento__lte=alerta).exists():
            return format_html(
                '<span style="color:black;background:#ffd966;padding:3px 8px;border-radius:4px;">VENCE EM BREVE</span>'
            )

        return format_html(
            '<span style="color:white;background:#5cb85c;padding:3px 8px;border-radius:4px;">OK</span>'
        )

    vencimento_status.short_description = "Validade"


@admin.register(LoteProduto)
class LoteProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "produto",
        "quantidade",
        "data_vencimento",
        "vencimento_status",
        "ativo",
    )

    list_filter = ("ativo", "data_vencimento")
    search_fields = ("produto__titulo", "codigo_lote")

    def vencimento_status(self, obj):
        hoje = timezone.now().date()
        if obj.data_vencimento < hoje:
            return format_html(
                '<span style="color:white;background:#d9534f;padding:3px 8px;border-radius:4px;">VENCIDO</span>'
            )
        elif obj.data_vencimento <= hoje + timedelta(days=7):
            return format_html(
                '<span style="color:black;background:#f0ad4e;padding:3px 8px;border-radius:4px;">ALERTA</span>'
            )
        return format_html(
            '<span style="color:white;background:#5cb85c;padding:3px 8px;border-radius:4px;">OK</span>'
        )

    vencimento_status.short_description = "Status"

@admin.register(OrdemPedido)
class OrdemPedidoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "pedido_status",
        "total",
        "criado_em",
    )

    list_filter = ("pedido_status",)
    search_fields = ("codigo",)


admin.site.register(Kart)
admin.site.register(KartProduto)
