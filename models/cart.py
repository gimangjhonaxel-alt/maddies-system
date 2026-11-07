from models.product import Product

MAX_PER_ITEM = 20


class Cart:
    """A visitor's shopping cart, kept in their session.
    Stores only product ids and quantities. Names and prices are looked up
    from the database each time, so they can't be tampered with."""

    def __init__(self, session):
        self._session = session
        self._session.setdefault("cart", {})

    @property
    def _data(self):
        return self._session["cart"]

    def add(self, product_id, quantity=1):
        key = str(product_id)
        self._data[key] = min(self._data.get(key, 0) + quantity, MAX_PER_ITEM)
        self._session.modified = True

    def set_quantity(self, product_id, quantity):
        key = str(product_id)
        if quantity <= 0:
            self._data.pop(key, None)
        else:
            self._data[key] = min(quantity, MAX_PER_ITEM)
        self._session.modified = True

    def remove(self, product_id):
        self._data.pop(str(product_id), None)
        self._session.modified = True

    def clear(self):
        self._session["cart"] = {}
        self._session.modified = True

    def count(self):
        return sum(self._data.values())

    def items(self):
        """Cart lines with current product details.
        Products that were removed from the menu are dropped automatically."""
        lines = []
        for key, quantity in list(self._data.items()):
            product = Product.find_by_id(int(key))
            if product is None or not product.is_active:
                self._data.pop(key, None)
                self._session.modified = True
                continue
            lines.append({
                "product": product,
                "quantity": quantity,
                "subtotal": product.price * quantity,
            })
        return lines

    def total(self):
        return sum(line["subtotal"] for line in self.items())