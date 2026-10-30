from django.urls import path
from . import views

urlpatterns = [
    # Páginas Públicas, Catálogo e Carrinho
    path('', views.home, name='home'),
    path('servicos/', views.servicos, name='servicos'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('carrinho/atualizar/', views.atualizar_carrinho, name='atualizar_carrinho'),
    path('evento/', views.evento, name='evento'),
    path('resumo/', views.resumo, name='resumo'),
    path('finalizar/', views.finalizar, name='finalizar'),
    path('contato/', views.contato, name='contato'),

    # Painel Administrativo e Gestão de Serviços
    path('painel/', views.painel, name='painel'),
    path('painel/login/', views.painel_login, name='painel_login'),
    path('painel/logout/', views.painel_logout, name='painel_logout'),
    path('servicos/novo/', views.servico_criar, name='servico_criar'),
    path('servicos/editar/<int:pk>/', views.servico_editar, name='servico_editar'),
    path('servicos/excluir/<int:pk>/', views.servico_excluir, name='servico_excluir'),
    # Gestão de Itens do Pedido (US07)
    path('painel/pedido/<int:pedido_id>/item/adicionar/', views.item_pedido_adicionar, name='item_pedido_adicionar'),
    path('painel/item/<int:item_id>/remover/', views.item_pedido_remover, name='item_pedido_remover'),
]
