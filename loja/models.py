from django.db import models
from django.contrib.auth.models import User
import uuid
from decimal import Decimal


# Create your models here.

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=200, null=True, blank=True)
    endereco = models.CharField(max_length=200, null=True, blank=True)
    data_on = models.DateField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.nome_completo

class Categoria(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    
    def __str__(self) -> str:
        return self.titulo
    
class Produto(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    codigo_barras = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Código de barras / QRCode do produto"
    )

    imagem = models.ImageField(upload_to='produtos')
    imagem2 = models.ImageField(upload_to='produtos')
    imagem3 = models.ImageField(upload_to='produtos')
    preco_compra = models.DecimalField(
    max_digits=10,
    decimal_places=2
)

    preco_venda = models.DecimalField(
    max_digits=10,
    decimal_places=2
)
    descricao = models.TextField()
    visualizacao = models.PositiveIntegerField(default=0)
    devolucao = models.CharField(max_length=200)
    estoque = models.PositiveIntegerField(
    default=0,
    help_text="Estoque calculado a partir dos lotes"
)
    avaliacao = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.titulo} ({self.codigo_barras})"

class LoteProduto(models.Model):
    produto = models.ForeignKey(
        Produto, on_delete=models.CASCADE, related_name="lotes"
    )

    codigo_lote = models.CharField(
        max_length=50, blank=True, null=True
    )

    quantidade = models.PositiveIntegerField()
    data_vencimento = models.DateField()

    criado_em = models.DateTimeField(auto_now_add=True)

    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.produto.titulo} - Vence em {self.data_vencimento}"


    
class Kart(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL,null=True, blank=True)
    total = models.PositiveIntegerField(default=0)
    criado_em = models.DateField(auto_now_add=True)

    def __str__(self):
        return 'Kart:'+ str(self.id)
    
class KartProduto(models.Model):
    kart = models.ForeignKey(Kart, on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    subtotal = models.PositiveIntegerField(default=0)

    def __str__(self):
        return 'Kart:' + str(self.id) + "KartProduto:" + str(self.id)
    
STATUS_CRIADO = "Pedido Criado"
STATUS_AGUARDANDO = "Aguardando Pagamento"
STATUS_PAGO = "Pagamento Aprovado"
STATUS_CANCELADO = "Pedido Cancelado"

PEDIDO_STATUS = (
    (STATUS_CRIADO, "Pedido Criado"),
    (STATUS_AGUARDANDO, "Aguardando Pagamento"),
    (STATUS_PAGO, "Pagamento Aprovado"),
    (STATUS_CANCELADO, "Pedido Cancelado"),
)


class OrdemPedido(models.Model):
    kart = models.OneToOneField(Kart, on_delete=models.CASCADE)

    # Identificação da venda
    codigo = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Cliente (opcional no mercado autônomo)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, blank=True
    )

    # Totais
    subtotal = models.PositiveIntegerField(default=0)
    desconto = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    # Pagamento
    pedido_status = models.CharField(
    max_length=50,
    choices=PEDIDO_STATUS,
    default=STATUS_AGUARDANDO,
    db_index=True
)
    metodo_pagamento = models.CharField(
        max_length=30, default="PIX"
    )

    # Datas
    criado_em = models.DateTimeField(auto_now_add=True)
    pago_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.codigo}"

PAGAMENTO_STATUS = (
    ("PENDENTE", "Pendente"),
    ("PAGO", "Pago"),
    ("EXPIRADO", "Expirado"),
    ("CANCELADO", "Cancelado"),
    ("ERRO", "Erro"),
)

class Pagamento(models.Model):
    pedido = models.OneToOneField(
        OrdemPedido, on_delete=models.CASCADE, related_name="pagamento"
    )

    # Gateway
    gateway = models.CharField(
        max_length=50,
        default="pagarme"
    )

    # Identificadores do gateway
    gateway_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    txid = models.CharField(
        max_length=100, blank=True, null=True
    )

    # PIX
    pix_qr_code = models.TextField(
        blank=True, null=True
    )
    pix_qr_code_url = models.TextField(blank=True, null=True)
    pix_expira_em = models.DateTimeField(
        blank=True, null=True
    )

    # Status
    status = models.CharField(
        max_length=30,
        choices=PAGAMENTO_STATUS,
        default="PENDENTE",
        db_index=True
    )

    # Datas
    criado_em = models.DateTimeField(auto_now_add=True)
    confirmado_em = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pagamento {self.id} - {self.status}"



