from django.contrib import admin


from .models import ItemPedido, Pedido, Produto




@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "unidade", "ativo")
    list_editable = ("preco", "ativo")
    prepopulated_fields = {"slug": ("nome",)}




class ItemInline(admin.TabularInline):
    model = ItemPedido
    extra = 0




@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("cliente_nome", "data_evento", "total", "status", "criado_em")
    list_filter = ("status", "data_evento")
    search_fields = ("cliente_nome", "cliente_telefone", "endereco")
    inlines = [ItemInline]
