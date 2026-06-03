from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CartItem:
    produto: str
    quantidade: int
    cor: str | None = None
    tamanho: str | None = None
    valor_unitario: Decimal | None = None

    @property
    def subtotal(self):
        if self.valor_unitario is None:
            return Decimal("0")
        return self.valor_unitario * self.quantidade


class Cart:
    def __init__(self):
        self._items = []
        self.ultimo_item_index = None

    def adicionar_item(self, item):
        self._items.append(item)
        self.ultimo_item_index = len(self._items) - 1

    def adicionar_itens(self, itens):
        for item in itens:
            self.adicionar_item(item)

    def trocar_ultimo_item(self, item):
        indice = self._indice_ultimo_valido()
        if indice is None:
            return False
        self._items[indice] = item
        self.ultimo_item_index = indice
        return True

    def remover_ultimo_item(self):
        indice = self._indice_ultimo_valido()
        if indice is None:
            return None
        item = self._items.pop(indice)
        self.ultimo_item_index = len(self._items) - 1 if self._items else None
        return item

    def limpar(self):
        self._items.clear()
        self.ultimo_item_index = None

    def esta_vazio(self):
        return not self._items

    def subtotal(self):
        return sum((item.subtotal for item in self._items), Decimal("0"))

    def listar_itens(self):
        return list(self._items)

    def ultimo_item(self):
        indice = self._indice_ultimo_valido()
        return self._items[indice] if indice is not None else None

    def atualizar_quantidade_ultimo(self, quantidade):
        item = self.ultimo_item()
        if item is None:
            return False
        item.quantidade = quantidade
        return True

    def atualizar_valor_ultimo(self, valor_unitario):
        item = self.ultimo_item()
        if item is None:
            return False
        item.valor_unitario = valor_unitario
        return True

    def _indice_ultimo_valido(self):
        if self.ultimo_item_index is not None and 0 <= self.ultimo_item_index < len(self._items):
            return self.ultimo_item_index
        return len(self._items) - 1 if self._items else None
