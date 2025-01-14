from django.urls import path

from.views import *

app_name = "loja"
urlpatterns = [
    path('', indexView.as_view(), name='index'),
    path('sobre/', sobreView.as_view(), name='sobre'),
    path('contato/', contatoView.as_view(), name='contato'),
    path('todos-produtos/', todosprodutosView.as_view(), name='todosprodutos'),
    path('produto/<slug:slug>/', proudutoDetalheView.as_view(), name='produtodetalhe'),
    path('addkart-<int:pro_id>/', addKartView.as_view(), name='addkart'),
    path('meukart/', meuKartView.as_view(), name='meukart'),
    path('editarmeukart/<int:kp_id>/', editarMeuKartView.as_view(), name='editarmeukart'),
    path('limparcarro', limparCarroView.as_view(), name='limparcarro'),
    path('finalizarcompra', finalizarCompraView.as_view(), name='finalizarcompra'),
    path('registrar/', registrarView.as_view(), name='registrar'),
    path('clientesair/', ClienteSairView.as_view(), name='clientesair'),
    path('clienteentrar/', ClienteEntrarView.as_view(), name='clienteentrar'),
    path('clienteperfil/', ClientePerfilView.as_view(), name='clienteperfil'),
    path('clienteperfil/pedido-<int:pk>', ClientePedidoDetalheView.as_view(), name='clientepedidodetalhe')
]