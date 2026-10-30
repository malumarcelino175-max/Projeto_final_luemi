from decimal import Decimal

from django.conf import settings

from .models import Produto

CARRINHO_KEY = "carrinho"
EVENTO_KEY = "evento"


def get_carrinho(request):
    """Retorna {slug: quantidade} guardado na sessão."""
    return {k: int(v) for k, v in request.session.get(CARRINHO_KEY, {}).items() if int(v) > 0}


def set_quantidade(request, slug, quantidade):
    carrinho = request.session.get(CARRINHO_KEY, {})
    quantidade = max(0, int(quantidade))
    if quantidade == 0:
        carrinho.pop(slug, None)
    else:
        carrinho[slug] = quantidade
    request.session[CARRINHO_KEY] = carrinho
    request.session.modified = True


def limpar(request):
    request.session.pop(CARRINHO_KEY, None)
    request.session.pop(EVENTO_KEY, None)
    request.session.modified = True


def get_evento(request):
    return request.session.get(EVENTO_KEY, {})


def set_evento(request, dados):
    request.session[EVENTO_KEY] = dados
    request.session.modified = True


def distancia_estimada(endereco: str) -> int:
    """Estimativa simples e determinística a partir do endereço.

    Substitua por uma chamada à API de geocodificação (ex.: Google Distance
    Matrix) quando tiver a chave disponível.
    """
    endereco = (endereco or "").strip()
    if not endereco:
        return 0
    h = 0
    for ch in endereco:
        h = (h * 31 + ord(ch)) % (2**32)
    return (h % 90) + 5


def calcular(request):
    carrinho = get_carrinho(request)
    produtos = {p.slug: p for p in Produto.objects.filter(slug__in=carrinho.keys())}
    itens = []
    subtotal = Decimal("0")
    for slug, qtd in carrinho.items():
        produto = produtos.get(slug)
        if not produto:
            continue
        total_item = produto.preco * qtd
        subtotal += total_item
        itens.append({"produto": produto, "quantidade": qtd, "subtotal": total_item})

    evento = get_evento(request)
    km = distancia_estimada(evento.get("endereco", ""))
    livre = settings.FREE_DELIVERY_KM
    taxa = Decimal("0")
    if km > livre:
        taxa = Decimal(str((km - livre) * settings.DELIVERY_FEE_PER_KM))
    taxa = taxa.quantize(Decimal("0.01"))

    return {
        "itens": itens,
        "subtotal": subtotal,
        "distancia_km": km,
        "km_extras": max(0, km - livre),
        "taxa": taxa,
        "total": subtotal + taxa,
        "evento": evento,
    }
