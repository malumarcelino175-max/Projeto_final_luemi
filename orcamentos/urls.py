from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("servicos/", views.servicos, name="servicos"),
    path("servicos/novo/", views.servico_criar, name="servico_criar"),
    path("servicos/<int:pk>/editar/", views.servico_editar, name="servico_editar"),
    path("servicos/<int:pk>/excluir/", views.servico_excluir, name="servico_excluir"),
    path("carrinho/", views.carrinho, name="carrinho"),
    path("carrinho/atualizar/", views.atualizar_carrinho, name="atualizar_carrinho"),
    path("evento/", views.evento, name="evento"),
    path("resumo/", views.resumo, name="resumo"),
    path("resumo/finalizar/", views.finalizar, name="finalizar"),
    path("contato/", views.contato, name="contato"),
    path("admin/", views.painel, name="painel"),
    path("admin/login/", views.painel_login, name="painel_login"),
    path("admin/logout/", views.painel_logout, name="painel_logout"),
]
