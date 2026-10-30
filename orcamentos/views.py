import json
from functools import wraps
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from . import services
from .forms import ProdutoForm
from .models import ItemPedido, Pedido, Produto

PAINEL_SENHA = "admin123"  # troque por autenticação real em produção


def is_admin(request):
    """Mesma regra do painel: sessão liberada pela senha ou usuário staff do Django."""
    return bool(request.session.get("painel_ok")) or (
        request.user.is_authenticated and request.user.is_staff
    )


def painel_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not is_admin(request):
            messages.error(request, "Faça login no painel para gerenciar os serviços.")
            return redirect(f"{reverse('painel_login')}?next={request.get_full_path()}")
        return view(request, *args, **kwargs)
    return _wrapped


def home(request):
    destaques = Produto.objects.filter(ativo=True)[:3]
    return render(request, "orcamentos/home.html", {"destaques": destaques})


def servicos(request):
    admin = is_admin(request)
    produtos = Produto.objects.all() if admin else Produto.objects.filter(ativo=True)
    carrinho = services.get_carrinho(request)
    lista = [{"p": p, "qtd": carrinho.get(p.slug, 0)} for p in produtos]
    return render(request, "orcamentos/servicos.html", {"lista": lista, "is_admin": admin})


@painel_required
def servico_criar(request):
    form = ProdutoForm(request.POST, request.FILES) if request.method == "POST" else ProdutoForm()
    if request.method == "POST":
        if form.is_valid():
            produto = form.save()
            messages.success(request, f"Serviço “{produto.nome}” cadastrado com sucesso.")
            return redirect("servicos")
        messages.error(request, "Corrija os campos destacados.")
    return render(request, "orcamentos/servico_form.html", {"form": form, "titulo": "Adicionar serviço"})


@painel_required
def servico_editar(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = (
        ProdutoForm(request.POST, request.FILES, instance=produto)
        if request.method == "POST"
        else ProdutoForm(instance=produto)
    )
    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Serviço “{produto.nome}” atualizado.")
            return redirect("servicos")
        messages.error(request, "Corrija os campos destacados.")
    return render(
        request,
        "orcamentos/servico_form.html",
        {"form": form, "titulo": f"Editar {produto.nome}", "produto": produto},
    )


@painel_required
def servico_excluir(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == "POST":
        nome = produto.nome
        services.set_quantidade(request, produto.slug, 0)
        produto.delete()
        messages.success(request, f"Serviço “{nome}” excluído.")
        return redirect("servicos")
    return render(request, "orcamentos/servico_confirmar_exclusao.html", {"produto": produto})


def atualizar_carrinho(request):
    """Recebe {slug, quantidade} por POST (fetch) e devolve o resumo do carrinho."""
    if request.method != "POST":
        return JsonResponse({"erro": "método inválido"}, status=405)
    dados = json.loads(request.body or "{}")
    slug = dados.get("slug")
    quantidade = dados.get("quantidade", 0)
    get_object_or_404(Produto, slug=slug)
    services.set_quantidade(request, slug, quantidade)
    carrinho = services.get_carrinho(request)
    resumo = services.calcular(request)
    return JsonResponse(
        {
            "quantidade": carrinho.get(slug, 0),
            "itens_total": sum(carrinho.values()),
            "subtotal": float(resumo["subtotal"]),
        }
    )


def carrinho(request):
    return render(request, "orcamentos/carrinho.html", services.calcular(request))


def evento(request):
    if request.method == "POST":
        dados = {
            "nome": request.POST.get("nome", "").strip(),
            "telefone": request.POST.get("telefone", "").strip(),
            "data": request.POST.get("data", ""),
            "endereco": request.POST.get("endereco", "").strip(),
        }
        services.set_evento(request, dados)
        if all(dados.values()):
            return redirect("resumo")
        messages.error(request, "Preencha todos os campos para continuar.")
    ctx = services.calcular(request)
    return render(request, "orcamentos/evento.html", ctx)


def resumo(request):
    return render(request, "orcamentos/resumo.html", services.calcular(request))


def finalizar(request):
    if request.method != "POST":
        return redirect("resumo")

    ctx = services.calcular(request)
    ev = ctx["evento"]
    if not ctx["itens"] or not ev.get("data"):
        messages.error(request, "Complete o carrinho e os dados do evento.")
        return redirect("resumo")

    pedido = Pedido.objects.create(
        cliente_nome=ev.get("nome", ""),
        cliente_telefone=ev.get("telefone", ""),
        data_evento=ev.get("data"),
        endereco=ev.get("endereco", ""),
        distancia_km=ctx["distancia_km"],
        taxa_deslocamento=ctx["taxa"],
        subtotal=ctx["subtotal"],
        total=ctx["total"],
    )
    for item in ctx["itens"]:
        ItemPedido.objects.create(
            pedido=pedido,
            produto=item["produto"],
            nome=item["produto"].nome,
            preco=item["produto"].preco,
            quantidade=item["quantidade"],
        )

    pedido.refresh_from_db()
    data_fmt = pedido.data_evento.strftime('%d/%m/%Y')
    linhas = [
        "*Novo Orçamento — Delícias da Mari*",
        "",
        f"*Cliente:* {pedido.cliente_nome}",
        f"*Telefone:* {pedido.cliente_telefone}",
        f"*Data do evento:* {data_fmt}",
        f"*Endereço:* {pedido.endereco}",
        f"*Distância estimada:* {pedido.distancia_km} km",
        "",
        "*Itens:*",
    ]
    linhas += [
        f"• {i['produto'].nome} × {i['quantidade']} — R$ {i['subtotal']:.2f}".replace(".", ",")
        for i in ctx["itens"]
    ]
    linhas += [
        "",
        f"*Subtotal:* R$ {ctx['subtotal']:.2f}".replace(".", ","),
        f"*Taxa de deslocamento:* R$ {ctx['taxa']:.2f}".replace(".", ","),
        f"*Total:* R$ {ctx['total']:.2f}".replace(".", ","),
    ]
    url = f"https://wa.me/{settings.WHATSAPP_NUMBER}?text={quote(chr(10).join(linhas))}"

    services.limpar(request)
    return render(request, "orcamentos/enviado.html", {"whatsapp_url": url, "pedido": pedido})


def contato(request):
    return render(request, "orcamentos/contato.html", {"whatsapp": settings.WHATSAPP_NUMBER})


def painel_login(request):
    if request.method == "POST":
        if request.POST.get("senha") == PAINEL_SENHA:
            request.session["painel_ok"] = True
            destino = request.POST.get("next") or request.GET.get("next")
            if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}):
                return redirect(destino)
            return redirect("painel")
        messages.error(request, "Senha incorreta.")
    return render(request, "orcamentos/painel_login.html")


def painel_logout(request):
    request.session.pop("painel_ok", None)
    return redirect("painel_login")


def painel(request):
    if not is_admin(request):
        return redirect("painel_login")
    pedidos = Pedido.objects.prefetch_related("itens").all()
    total = sum(p.total for p in pedidos)
    return render(
        request,
        "orcamentos/painel.html",
        {"pedidos": pedidos, "qtd": len(pedidos), "faturamento": total},
    )

@painel_required
def item_pedido_adicionar(request, pedido_id):
    """Adiciona um novo produto como item de um pedido existente no painel."""
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == "POST":
        produto_id = request.POST.get("produto_id")
        quantidade = int(request.POST.get("quantidade", 1))
        
        produto = get_object_or_404(Produto, pk=produto_id)
        
        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            nome=produto.nome,
            preco=produto.preco,
            quantidade=quantidade
        )
        
        # Recalcula o subtotal e o total do pedido
        pedido.subtotal = sum(item.subtotal for item in pedido.itens.all())
        pedido.total = pedido.subtotal + pedido.taxa_deslocamento
        pedido.save()
        
        messages.success(request, f"Item “{produto.nome}” adicionado ao pedido #{pedido.pk}.")
    return redirect("painel")


@painel_required
def item_pedido_remover(request, item_id):
    """Remove um item do pedido e atualiza os totais."""
    item = get_object_or_404(ItemPedido, pk=item_id)
    pedido = item.pedido
    nome_item = item.nome
    
    item.delete()
    
    # Recalcula os valores após remoção
    pedido.subtotal = sum(i.subtotal for i in pedido.itens.all())
    pedido.total = pedido.subtotal + pedido.taxa_deslocamento
    pedido.save()
    
    messages.success(request, f"Item “{nome_item}” removido do pedido.")
    return redirect("painel")