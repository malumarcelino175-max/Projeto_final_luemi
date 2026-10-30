from django.db import models


class Produto(models.Model):
    slug = models.SlugField(unique=True)
    nome = models.CharField(max_length=80)
    descricao = models.TextField()
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    unidade = models.CharField(max_length=40, default="/ 100 un")
    imagem = models.CharField(
        max_length=120,
        help_text="Nome do arquivo em static/img, ex.: churros.jpg",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    STATUS = [
        ("novo", "Novo"),
        ("em_contato", "Em contato"),
        ("confirmado", "Confirmado"),
        ("cancelado", "Cancelado"),
    ]

    criado_em = models.DateTimeField(auto_now_add=True)
    cliente_nome = models.CharField(max_length=120)
    cliente_telefone = models.CharField(max_length=40)
    data_evento = models.DateField()
    endereco = models.CharField(max_length=255)
    distancia_km = models.PositiveIntegerField(default=0)
    taxa_deslocamento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="novo")

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"{self.cliente_nome} — {self.data_evento}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name="itens", on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, null=True, on_delete=models.SET_NULL)
    nome = models.CharField(max_length=80)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.preco * self.quantidade

    def __str__(self):
        return f"{self.nome} x{self.quantidade}"