from .services import get_carrinho


def carrinho_resumo(request):
    carrinho = get_carrinho(request)
    return {"carrinho_qtd": sum(carrinho.values())}
