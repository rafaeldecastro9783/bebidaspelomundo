from django.db import models
from django.contrib.auth.models import User

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
    imagem = models.ImageField(upload_to='produtos')
    imagem2 = models.ImageField(upload_to='produtos')
    imagem3 = models.ImageField(upload_to='produtos')
    preco_compra = models.PositiveIntegerField()
    preco_venda = models.PositiveIntegerField()
    descricao = models.TextField()
    visualizacao = models.PositiveIntegerField(default=0)
    garantia = models.CharField(max_length=200, null=True, blank=True)
    devolucao = models.CharField(max_length=200)
    estoque = models.PositiveIntegerField(default=0)
    avaliacao = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.titulo
    
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
    
PEDIDO_STATUS = (
    ("Pedido Recebido", "Pedido Recebido"),
    ("Aguardando Pagamento", "Aguardando Pagamento"),
    ("Pagamento Aprovado", "Pagamento Aprovado"),
    ("Pedido Enviado", "Pedido Enviado"),
    ("Pedido Entregue", "Pedido Entregue"),
    ("Pedido Cancelado", "Pedido Cancelado"),
)

class ordemPedido(models.Model):
    kart = models.OneToOneField(Kart, on_delete=models.CASCADE)
    endereco_de_entrega = models.CharField(max_length=200)
    ordenado_por = models.CharField(max_length=200)
    telefone = models.CharField(max_length=11, null=True, blank=True)
    email = models.CharField(max_length=200, null=True, blank=True)
    cpf = models.CharField(max_length=11, null=True, blank=True)
    desconto = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    subtotal = models.PositiveIntegerField(default=0)
    pedido_status = models.CharField(max_length=50, choices=PEDIDO_STATUS)
    data_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return 'ordemPedido:' + str(self.id)

