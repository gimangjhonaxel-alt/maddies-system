from models.database import Database

db = Database()


class Product:
    """A bakery item sold at every Maddie's branch."""

    def __init__(self, id, category_id, name, description, price,
                 image=None, is_active=True, category_name=None):
        self.id = id
        self.category_id = category_id
        self.name = name
        self.description = description
        self.price = price
        self.image = image
        self.is_active = is_active
        self.category_name = category_name

    @staticmethod
    def _from_row(row):
        if row is None:
            return None
        return Product(
            row["id"], row["category_id"], row["name"], row["description"],
            row["price"], row.get("image"), row["is_active"] != 0,
            row.get("category_name"),
        )

    # ---------- reading ----------
    @staticmethod
    def all_categories():
        return db.fetch_all("SELECT id, name FROM categories ORDER BY name")

    @staticmethod
    def get_all(include_inactive=False):
        query = (
            "SELECT p.*, c.name AS category_name "
            "FROM products p JOIN categories c ON c.id = p.category_id "
        )
        if not include_inactive:
            query += "WHERE COALESCE(p.is_active, 1) = 1 "
        query += "ORDER BY c.name, p.name"
        return [Product._from_row(r) for r in db.fetch_all(query)]

    @staticmethod
    def find_by_id(product_id):
        row = db.fetch_one(
            "SELECT p.*, c.name AS category_name "
            "FROM products p JOIN categories c ON c.id = p.category_id "
            "WHERE p.id = %s",
            (product_id,),
        )
        return Product._from_row(row)

    # ---------- writing ----------
    @staticmethod
    def create(category_id, name, description, price, image=None):
        new_id = db.execute(
            "INSERT INTO products (category_id, name, description, price, image, is_active) "
            "VALUES (%s, %s, %s, %s, %s, 1)",
            (category_id, name, description, price, image),
        )
        # Give the new product a stock row (0 pcs) in every branch.
        db.execute(
            "INSERT INTO branch_stock (branch_id, product_id, quantity, low_stock_threshold) "
            "SELECT id, %s, 0, 5 FROM branches",
            (new_id,),
        )
        return Product.find_by_id(new_id)

    def update(self, category_id, name, description, price, image=None):
        """If image is None, the current image is kept."""
        db.execute(
            "UPDATE products SET category_id = %s, name = %s, "
            "description = %s, price = %s, image = COALESCE(%s, image) "
            "WHERE id = %s",
            (category_id, name, description, price, image, self.id),
        )

    def archive(self):
        db.execute("UPDATE products SET is_active = 0 WHERE id = %s", (self.id,))

    def restore(self):
        db.execute("UPDATE products SET is_active = 1 WHERE id = %s", (self.id,))