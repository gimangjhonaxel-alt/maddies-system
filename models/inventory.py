from models.database import Database

db = Database()


class Inventory:
    """Stock levels of every product at one Maddie's branch."""

    @staticmethod
    def all_branches():
        return db.fetch_all("SELECT id, name FROM branches ORDER BY id")

    @staticmethod
    def get_branch(branch_id):
        return db.fetch_one(
            "SELECT id, name FROM branches WHERE id = %s", (branch_id,)
        )

    @staticmethod
    def for_branch(branch_id):
        """Every active product with this branch's stock, low items flagged."""
        rows = db.fetch_all(
            "SELECT p.id AS product_id, p.name, p.image, "
            "c.name AS category_name, bs.quantity, bs.low_stock_threshold "
            "FROM branch_stock bs "
            "JOIN products p ON p.id = bs.product_id "
            "JOIN categories c ON c.id = p.category_id "
            "WHERE bs.branch_id = %s AND COALESCE(p.is_active, 1) = 1 "
            "ORDER BY c.name, p.name",
            (branch_id,),
        )
        for row in rows:
            row["is_low"] = row["quantity"] <= row["low_stock_threshold"]
        return rows

    @staticmethod
    def update(branch_id, product_id, quantity, low_stock_threshold):
        db.execute(
            "UPDATE branch_stock SET quantity = %s, low_stock_threshold = %s "
            "WHERE branch_id = %s AND product_id = %s",
            (quantity, low_stock_threshold, branch_id, product_id),
        )