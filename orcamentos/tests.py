import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Produto


class ServicosTests(TestCase):
    def setUp(self):
        self.p = Produto.objects.create(slug="churros", nome="Churros", descricao="d", preco=Decimal("10"), imagem="churros.jpg")
        self.dados = {"nome": "Brigadeiro", "descricao": "Doce", "preco": "50.00", "unidade": "/ 100 un", "imagem": "churros.jpg", "ativo": "on"}

    def login(self):
        s = self.client.session; s["painel_ok"] = True; s.save()

    def test_visitante_nao_cadastra(self):
        r = self.client.post(reverse("servico_criar"), self.dados)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("painel_login"), r.url)
        self.assertFalse(Produto.objects.filter(nome="Brigadeiro").exists())

    def test_visitante_nao_exclui(self):
        self.client.post(reverse("servico_excluir", args=[self.p.pk]))
        self.assertTrue(Produto.objects.filter(pk=self.p.pk).exists())

    def test_admin_cadastra(self):
        self.login()
        r = self.client.post(reverse("servico_criar"), self.dados)
        self.assertRedirects(r, reverse("servicos"))
        b = Produto.objects.get(nome="Brigadeiro")
        self.assertEqual(b.slug, "brigadeiro")
        self.assertContains(self.client.get(reverse("servicos")), "Brigadeiro")

    def test_campos_obrigatorios(self):
        self.login()
        r = self.client.post(reverse("servico_criar"), {})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Informe o nome do serviço.")
        self.assertEqual(Produto.objects.count(), 1)

    def test_preco_invalido_e_nome_duplicado(self):
        self.login()
        r = self.client.post(reverse("servico_criar"), {**self.dados, "nome": "Churros", "preco": "0"})
        self.assertContains(r, "Já existe um serviço com esse nome.")
        self.assertContains(r, "O preço deve ser maior que zero.")

    def test_admin_edita(self):
        self.login()
        self.client.post(reverse("servico_editar", args=[self.p.pk]), {**self.dados, "nome": "Churros", "preco": "12.50"})
        self.p.refresh_from_db()
        self.assertEqual(self.p.preco, Decimal("12.50"))

    def test_admin_exclui_com_confirmacao(self):
        self.login()
        self.assertContains(self.client.get(reverse("servico_excluir", args=[self.p.pk])), "Tem certeza")
        self.client.post(reverse("servico_excluir", args=[self.p.pk]))
        self.assertFalse(Produto.objects.filter(pk=self.p.pk).exists())

    def test_oculto_so_para_admin(self):
        Produto.objects.create(slug="x", nome="Oculto X", descricao="d", preco=1, imagem="churros.jpg", ativo=False)
        self.assertNotContains(self.client.get(reverse("servicos")), "Oculto X")
        self.login()
        self.assertContains(self.client.get(reverse("servicos")), "Oculto X")
