from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic import View, TemplateView, CreateView, FormView, DetailView
from.models import *
from django.urls import reverse_lazy
from .forms import registrar_cliente_form, ClienteEntrarForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.views import View
from django.http import Http404
from loja.services.pagarme import criar_pix_pagarme
import json
from django.views.decorators.csrf import csrf_exempt
from loja.services.estoque import baixar_estoque_por_lote, EstoqueInsuficiente




class lojaMixIn(object):
    def dispatch(self, request, *args, **kwargs):
        kart_id = request.session.get("kart_id")

        if kart_id:
            kart_obj = Kart.objects.get(id=kart_id)

            if request.user.is_authenticated:
                try:
                    kart_obj.cliente = request.user.cliente
                    kart_obj.save()
                except Cliente.DoesNotExist:
                    # Mercado autônomo / admin / PDV
                    pass

        return super().dispatch(request, *args, **kwargs)



class indexView (lojaMixIn, TemplateView):
    template_name = "index.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['produto_list']= Produto.objects.all()
        return context
    
class todosprodutosView(lojaMixIn, TemplateView):
    template_name = "todosprodutos.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['todascategorias']= Categoria.objects.all().order_by("-id")
        return context
    
class addKartView(lojaMixIn, TemplateView):
    template_name = "addkart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Recupera o ID do produto a partir da URL
        produto_id = self.kwargs.get('pro_id')
        produto_obj = Produto.objects.get(id=produto_id)

        # Obtém ou cria um carrinho associado à sessão
        kart_id = self.request.session.get('kart_id')
        if kart_id:
            # Tenta recuperar o carrinho existente
            try:
                kart_obj = Kart.objects.get(id=kart_id)
            except Kart.DoesNotExist:
                kart_obj = self._create_new_kart()
        else:
            kart_obj = self._create_new_kart()

        # Verifica se o produto já está no carrinho
        produto_no_kart = kart_obj.kartproduto_set.filter(produto=produto_obj)
        if produto_no_kart.exists():
            # Atualiza a quantidade e subtotal se o produto já estiver no carrinho
            kartproduto = produto_no_kart.last()
            kartproduto.quantidade += 1
            kartproduto.subtotal += produto_obj.preco_venda
            kartproduto.save()
        else:
            # Cria uma nova entrada para o produto no carrinho
            kartproduto = KartProduto.objects.create(
                kart=kart_obj,
                produto=produto_obj,
                quantidade=1,
                subtotal=produto_obj.preco_venda,
                total=produto_obj.preco_venda,
            )

        # Atualiza o total do carrinho
        kart_obj.total += produto_obj.preco_venda
        kart_obj.save()

        # Adiciona o carrinho ao contexto
        context['kart'] = kart_obj
        return context

    def _create_new_kart(self):
        """Cria um novo carrinho e associa à sessão."""
        kart_obj = Kart.objects.create(total=0)
        self.request.session['kart_id'] = kart_obj.id
        return kart_obj
  

class proudutoDetalheView(lojaMixIn, TemplateView):
    template_name = "produtodetalhe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtém o slug da URL
        url_slug = self.kwargs.get('slug')

        # Recupera o produto com base no slug ou lança erro 404 se não encontrado
        produto = get_object_or_404(Produto, slug=url_slug)

        # Incrementa a visualização do produto
        produto.visualizacao += 1
        produto.save()

        # Adiciona o produto ao contexto
        context['produto'] = produto

        return context

    
class meuKartView(lojaMixIn, TemplateView):
    template_name = "pdv/carrinho.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        kart_id = self.request.session.get("kart_id")
        kart = None

        if kart_id:
            kart = Kart.objects.filter(id=kart_id).first()

        context["kart"] = kart
        return context
    
    
class editarMeuKartView(lojaMixIn, View):
    def get(self, request, *args, **kwargs):
        kp_id = self.kwargs["kp_id"]
        acao = request.GET.get('acao')
        
        try:
            kp_obj = KartProduto.objects.get(id=kp_id)
            kart_obj = kp_obj.kart
            
            if acao == 'adc':
                kp_obj.quantidade += 1
                kp_obj.subtotal += kp_obj.total
                kp_obj.save()
                kart_obj.total += kp_obj.total
                kart_obj.save()
                messages.success(request, "Quantidade atualizada com sucesso.")
            
            elif acao == 'rmv':
                if kp_obj.quantidade > 1:
                    kp_obj.quantidade -= 1
                    kp_obj.subtotal -= kp_obj.total
                    kp_obj.save()
                    kart_obj.total -= kp_obj.total
                    kart_obj.save()
                    messages.success(request, "Quantidade reduzida com sucesso.")
                else:
                    messages.error(request, "Quantidade não pode ser menor que 1.")
            
            elif acao == 'del':
                kart_obj.total -= kp_obj.subtotal
                kp_obj.delete()
                kart_obj.save()
                messages.success(request, "Produto removido com sucesso.")
            
            else:
                messages.error(request, "Ação inválida.")
        
        except KartProduto.DoesNotExist:
            messages.error(request, "Produto não encontrado no carrinho.")
        
        return redirect("loja:meukart")
    
class limparCarroView (lojaMixIn, View):
    def get(self, request, *args, **kargs):
        kart_id = request.session.get("kart_id", None)
        if kart_id:
            kart = Kart.objects.get(id=kart_id)
            kart.kartproduto_set.all().delete()
            kart.total = 0
            kart.save()
        return redirect("loja:meukart")

# class finalizarCompraView (lojaMixIn, CreateView):
#     template_name = "checkout.html"
#     # form_class = checar_ordem_Pedido
#     success_url = reverse_lazy('loja:index')
#     def dispatch(self, request, *args, **kwargs):
#         if not (request.user.is_authenticated and hasattr(request.user, 'cliente')):
#             return redirect("/clienteentrar/?next=/finalizarcompra")
#         return super().dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         kart_id = self.request.session.get('kart_id', None)
#         if kart_id:
#             kart_obj = Kart.objects.get(id=kart_id)
#         else:
#             kart_obj = None
#         context['kart'] = kart_obj
#         return context
    
#     def form_valid(self, form):
#         kart_id = self.request.session.get("kart_id")
#         if kart_id:
#             kart_obj = Kart.objects.get(id=kart_id)
#             form.instance.kart = kart_obj
#             form.instance.desconto = 0
#             form.instance.ordenado_por = self.request.user
#             form.instance.pedido_status = 'Pedido Recebido'
#             form.instance.total = kart_obj.total
#             form.instance.subtotal = kart_obj.total
#             del self.request.session['kart_id']
#         else:
#             return redirect("loja:index")
#         return super().form_valid(form)

class registrarView(CreateView):
    template_name = "registrar.html"
    form_class = registrar_cliente_form
    success_url = reverse_lazy('loja:index')

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")
        user = User.objects.create_user(username, email, password)
        form.instance.user = user
        login(self.request, user)
        return super().form_valid(form)
    
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url


class ClienteSairView(View):
    def get(self, request):
        logout(request)
        return redirect("loja:index")
    
class ClienteEntrarView(FormView):
    template_name = "entrar.html"
    form_class = ClienteEntrarForm
    success_url = reverse_lazy('loja:index')

    def form_valid(self, form):
        unome = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=unome, password=pword)
        if usr is not None and usr.cliente:
            login(self.request, usr)
        else: 
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Usuário ou Senha inválidos"})
        return super().form_valid(form)
    
    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url

class ClientePerfilView(TemplateView):
    template_name = "clienteperfil.html"
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and hasattr(request.user, 'cliente')):
            return redirect("/clienteentrar/?next=/clienteperfil")
        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.request.user.cliente
        context['cliente']=cliente
        pedidos = OrdemPedido.objects.filter(kart__cliente=cliente)
        context['pedidos']=pedidos
        return context

class ClientePedidoDetalheView(DetailView):
    template_name = "clientepedidodetalhe.html"
    model = OrdemPedido
    context_object_name = 'pedido_obj'
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_authenticated and hasattr(request.user, 'cliente')):
            return redirect("/clienteentrar/?next=/clienteperfil")
        return super().dispatch(request, *args, **kwargs)



class sobreView (lojaMixIn, TemplateView):
    template_name = "sobre.html"

class contatoView(lojaMixIn, TemplateView):
    template_name = "contato.html"

class AdicionarPorCodigoBarrasView(lojaMixIn, View):
    def post(self, request):
        codigo = request.POST.get("codigo_barras")

        if not codigo:
            messages.error(request, "Código de barras inválido.")
            return redirect("loja:meukart")

        try:
            produto = Produto.objects.get(codigo_barras=codigo)
        except Produto.DoesNotExist:
            messages.error(request, "Produto não encontrado.")
            return redirect("loja:meukart")

        # Obtém ou cria carrinho
        kart_id = request.session.get("kart_id")
        if kart_id:
            kart = Kart.objects.get(id=kart_id)
        else:
            kart = Kart.objects.create(total=0)
            request.session["kart_id"] = kart.id

        # Adiciona ou incrementa produto
        item, criado = KartProduto.objects.get_or_create(
            kart=kart,
            produto=produto,
            defaults={
                "quantidade": 1,
                "total": produto.preco_venda,
                "subtotal": produto.preco_venda,
            }
        )

        if not criado:
            item.quantidade += 1
            item.subtotal += produto.preco_venda
            item.save()
        else:
            item.save()

        kart.total += produto.preco_venda
        kart.save()

        return redirect("loja:meukart")


class FinalizarPagamentoPIXView(lojaMixIn, View):
    template_name = "pdv/pagamento_pix.html"

    def get(self, request):
        kart_id = request.session.get("kart_id")
        if not kart_id:
            return redirect("loja:index")

        kart = get_object_or_404(Kart, id=kart_id)

        pedido, _ = OrdemPedido.objects.get_or_create(
            kart=kart,
            defaults={
                "cliente": kart.cliente,
                "subtotal": kart.total,
                "total": kart.total,
                "pedido_status": STATUS_AGUARDANDO,
                "metodo_pagamento": "PIX",
            }
        )

        pagamento, _ = Pagamento.objects.get_or_create(
            pedido=pedido,
            defaults={
                "gateway": "pagarme",
                "status": "PENDENTE",
            }
        )

        # 🔒 IDMPOTÊNCIA PIX
        if not pagamento.gateway_id:
            data = criar_pix_pagarme(pedido)

            charge = data["charges"][0]
            transaction = charge.get("last_transaction")

            if not transaction or transaction.get("status") != "waiting_payment":
                messages.error(request, "PIX não disponível.")
                return redirect("loja:meukart")

            pagamento.gateway_id = data["id"]                     # order id
            pagamento.txid = transaction["id"]                    # transaction id
            pagamento.pix_qr_code = transaction["qr_code"]        # string
            pagamento.pix_qr_code_url = transaction["qr_code_url"]
            pagamento.pix_expira_em = timezone.make_aware(
                timezone.datetime.fromisoformat(
                    transaction["expires_at"].replace("Z", "")
                )
            )
            pagamento.save()

        return render(request, self.template_name, {
            "pedido": pedido,
            "pagamento": pagamento
        })


@csrf_exempt
def webhook_pagarme(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    if not request.body:
        # Webhook vazio (teste do pagar.me ou ping)
        return HttpResponse(status=200)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    # DEBUG TEMPORÁRIO (recomendo deixar agora)
    print("WEBHOOK RECEBIDO:", payload)

    if payload.get("type") != "order.paid":
        return HttpResponse(status=200)

    order_id = payload["data"]["id"]

    try:
        pagamento = Pagamento.objects.select_related("pedido").get(
            gateway_id=order_id
        )
    except Pagamento.DoesNotExist:
        return HttpResponse(status=404)

    # Idempotência
    if pagamento.status == "PAGO":
        return HttpResponse(status=200)

    pagamento.status = "PAGO"
    pagamento.confirmado_em = timezone.now()
    pagamento.save()

    pedido = pagamento.pedido
    pedido.pedido_status = STATUS_PAGO
    pedido.pago_em = timezone.now()
    pedido.save()

    # 🔻 Baixa de estoque por lote
    try:
        for item in pedido.kart.kartproduto_set.all():
            baixar_estoque_por_lote(
                produto=item.produto,
                quantidade=item.quantidade
            )
    except EstoqueInsuficiente as e:
        print("ERRO ESTOQUE:", e)

    # 🔻 Limpar carrinho
    pedido.kart.kartproduto_set.all().delete()
    pedido.kart.total = 0
    pedido.kart.save()

    return HttpResponse(status=200)

