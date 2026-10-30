from decimal import Decimal
from .models import Produto

def get_carrinho(request):
    """Retorna o dicionário {slug: quantidade} guardado na sessão."""
    return request.session.get('carrinho', {})

def set_quantidade(request, slug, quantidade):
    """Define ou atualiza a quantidade de um produto no carrinho."""
    carrinho = get_carrinho(request)
    qtd = int(quantidade)
    if qtd > 0:
        carrinho[slug] = qtd
    else:
        carrinho.pop(slug, None)
    request.session['carrinho'] = carrinho
    request.session.modified = True

def set_evento(request, dados):
    """Guarda os dados do evento na sessão."""
    request.session['evento'] = dados
    request.session.modified = True

def get_evento(request):
    """Retorna os dados do evento guardados na sessão."""
    return request.session.get('evento', {'nome': '', 'telefone': '', 'data': '', 'endereco': ''})

def calcular_taxa(distancia_km):
    """Calcula a taxa de deslocamento com base na distância em km."""
    base = Decimal('5.00')
    por_km = Decimal('2.00')
    return base + (Decimal(str(distancia_km)) * por_km)

def calcular(request):
    """Calcula subtotal, taxa de deslocamento e total geral do carrinho."""
    carrinho = get_carrinho(request)
    itens = []
    subtotal = Decimal('0.00')
    
    for slug, qtd in carrinho.items():
        try:
            produto = Produto.objects.get(slug=slug, ativo=True)
            sub = produto.preco * qtd
            subtotal += sub
            itens.append({
                'produto': produto,
                'quantidade': qtd,
                'subtotal': sub
            })
        except Produto.DoesNotExist:
            continue
            
    distancia_km = 10  # Valor padrão para cálculo de exemplo
    taxa = calcular_taxa(distancia_km)
    total = subtotal + taxa
    
    evento = get_evento(request)
    
    return {
        'itens': itens,
        'subtotal': subtotal,
        'distancia_km': distancia_km,
        'taxa': taxa,
        'total': total,
        'evento': evento
    }

def limpar(request):
    """Limpa o carrinho e os dados do evento da sessão após finalizar o pedido."""
    request.session.pop('carrinho', None)
    request.session.pop('evento', None)
    request.session.modified = True