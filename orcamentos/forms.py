from pathlib import Path

from django import forms
from django.conf import settings
from django.utils.text import slugify

from .models import Produto, Pedido


EXTENSOES = (".jpg", ".jpeg", ".png", ".webp")
IGNORAR = {"logo.png", "hero-quem-somos.jpg"}


def pasta_imagens():
    return Path(settings.BASE_DIR) / "static" / "img"


def imagens_disponiveis():
    pasta = pasta_imagens()
    if not pasta.exists():
        return []
    return sorted(
        f.name for f in pasta.iterdir()
        if f.suffix.lower() in EXTENSOES and f.name not in IGNORAR
    )


class ProdutoForm(forms.ModelForm):
    """Cadastro/edição de serviços usando o model Produto existente."""

    imagem = forms.ChoiceField(
        label="Foto do catálogo",
        required=False,
        help_text="Escolha uma foto já existente ou envie uma nova abaixo.",
    )
    nova_imagem = forms.ImageField(
        label="Enviar nova foto",
        required=False,
        help_text="JPG, PNG ou WEBP de até 3 MB. A foto é salva em static/img.",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    class Meta:
        model = Produto
        fields = ["nome", "descricao", "preco", "unidade", "imagem", "ativo"]
        labels = {
            "nome": "Nome do serviço",
            "descricao": "Descrição",
            "preco": "Preço (R$)",
            "unidade": "Unidade",
            "ativo": "Exibir no catálogo",
        }
        widgets = {
            "nome": forms.TextInput(attrs={"placeholder": "Ex.: Brigadeiro gourmet", "maxlength": 80}),
            "descricao": forms.Textarea(attrs={"rows": 3, "placeholder": "Descreva o serviço em poucas palavras"}),
            "preco": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "placeholder": "0,00"}),
            "unidade": forms.TextInput(attrs={"placeholder": "Ex.: / 100 un, / hora, / evento"}),
        }
        error_messages = {
            "nome": {"required": "Informe o nome do serviço."},
            "descricao": {"required": "Escreva uma descrição curta."},
            "preco": {"required": "Informe o preço.", "invalid": "Digite um valor válido."},
            "unidade": {"required": "Informe a unidade de venda."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        opcoes = imagens_disponiveis()
        atual = self.instance.imagem if self.instance and self.instance.pk else ""
        if atual and atual not in opcoes:
            opcoes.append(atual)
        self.fields["imagem"].choices = [("", "— selecione —")] + [(o, o) for o in opcoes]

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if len(nome) < 3:
            raise forms.ValidationError("O nome precisa ter pelo menos 3 caracteres.")
        qs = Produto.objects.filter(slug=slugify(nome))
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Já existe um serviço com esse nome.")
        return nome

    def clean_preco(self):
        preco = self.cleaned_data["preco"]
        if preco is not None and preco <= 0:
            raise forms.ValidationError("O preço deve ser maior que zero.")
        return preco

    def clean_nova_imagem(self):
        arquivo = self.cleaned_data.get("nova_imagem")
        if arquivo:
            if arquivo.size > 3 * 1024 * 1024:
                raise forms.ValidationError("A foto deve ter no máximo 3 MB.")
            if Path(arquivo.name).suffix.lower() not in EXTENSOES:
                raise forms.ValidationError("Use uma foto JPG, PNG ou WEBP.")
        return arquivo

    def clean(self):
        dados = super().clean()
        if not dados.get("imagem") and not dados.get("nova_imagem") and "imagem" not in self.errors:
            self.add_error("imagem", "Escolha uma foto ou envie uma nova.")
        return dados

    def save(self, commit=True):
        produto = super().save(commit=False)
        if not produto.slug or "nome" in self.changed_data:
            produto.slug = slugify(produto.nome)
        arquivo = self.cleaned_data.get("nova_imagem")
        if arquivo:
            pasta = pasta_imagens()
            pasta.mkdir(parents=True, exist_ok=True)
            ext = Path(arquivo.name).suffix.lower()
            nome = f"{produto.slug}{ext}"
            n = 1
            while (pasta / nome).exists():
                nome = f"{produto.slug}-{n}{ext}"
                n += 1
            with open(pasta / nome, "wb") as destino:
                for parte in arquivo.chunks():
                    destino.write(parte)
            produto.imagem = nome
        if commit:
            produto.save()
        return produto


class PedidoForm(forms.ModelForm):
    """Formulário para cadastro e atualização de pedidos de orçamento."""

    class Meta:
        model = Pedido
        fields = [
            "cliente_nome",
            "cliente_telefone",
            "data_evento",
            "endereco",
            "distancia_km",
            "taxa_deslocamento",
            "status",
        ]
        labels = {
            "cliente_nome": "Nome do Cliente",
            "cliente_telefone": "Telefone / WhatsApp",
            "data_evento": "Data do Evento",
            "endereco": "Endereço do Evento",
            "distancia_km": "Distância (km)",
            "taxa_deslocamento": "Taxa de Deslocamento (R$)",
            "status": "Status do Pedido",
        }
        widgets = {
            "cliente_nome": forms.TextInput(attrs={"placeholder": "Ex.: João Silva"}),
            "cliente_telefone": forms.TextInput(attrs={"placeholder": "(00) 00000-0000"}),
            "data_evento": forms.DateInput(attrs={"type": "date"}),
            "endereco": forms.TextInput(attrs={"placeholder": "Rua, Número, Bairro, Cidade"}),
            "distancia_km": forms.NumberInput(attrs={"min": "0"}),
            "taxa_deslocamento": forms.NumberInput(attrs={"step": "0.01", "min": "0.00"}),
            "status": forms.Select(),
        }