import uuid
from decimal import Decimal

from models.database import Database

db = Database()

STATUSES = ["pending", "preparing", "ready", "completed", "cancelled"]
PAYMENT_STATUSES = ["unpaid", "paid"]


class OutOfStockError(Exception):
    """Raised when a branch doesn't have enough of a product."""


class Order:
    """Orders placed by customers at a Maddie's branch."""

    @staticmethod
    def place(lines, branch_id, user_id, customer_name, customer_phone,
              customer_email, fulfillment, delivery_address,
              payment_method, gcash_reference):
        """Save an order and subtract stock, all or nothing.
        `lines` come from Cart.items(). Returns the new order's id."""
        total = sum(
            (line["product"].price * line["quantity"] for line in lines),
            Decimal("0"),
        )

        with db.transaction() as cursor:
            # 1. Lock and check the stock of every item at this branch.
            for line in lines:
                product = line["product"]
                cursor.execute(
                    "SELECT quantity FROM branch_stock "
                    "WHERE branch_id = %s AND product_id = %s FOR UPDATE",
                    (branch_id, product.id),
                )
                row = cursor.fetchone()
                available = row["quantity"] if row else 0
                if available < line["quantity"]:
                    if available <= 0:
                        raise OutOfStockError(
                            f"Sorry, {product.name} is out of stock at this branch."
                        )
                    raise OutOfStockError(
                        f"Sorry, only {available} of {product.name} left at this branch."
                    )

            # 2. Save the order (temporary number, replaced right after).
            cursor.execute(
                "INSERT INTO orders (order_number, branch_id, user_id, "
                "customer_name, customer_phone, customer_email, fulfillment, "
                "delivery_address, payment_method, gcash_reference, "
                "payment_status, status, total) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                "'unpaid', 'pending', %s)",
                (uuid.uuid4().hex[:20], branch_id, user_id, customer_name,
                 customer_phone, customer_email, fulfillment,
                 delivery_address, payment_method, gcash_reference, total),
            )
            order_id = cursor.lastrowid
            cursor.execute(
                "UPDATE orders SET order_number = %s WHERE id = %s",
                (f"MD-{order_id:05d}", order_id),
            )

            # 3. Save the items and subtract the stock.
            for line in lines:
                product = line["product"]
                cursor.execute(
                    "INSERT INTO order_items "
                    "(order_id, product_id, quantity, unit_price) "
                    "VALUES (%s, %s, %s, %s)",
                    (order_id, product.id, line["quantity"], product.price),
                )
                cursor.execute(
                    "UPDATE branch_stock SET quantity = quantity - %s "
                    "WHERE branch_id = %s AND product_id = %s",
                    (line["quantity"], branch_id, product.id),
                )

        return order_id

    @staticmethod
    def find_by_id(order_id):
        order = db.fetch_one(
            "SELECT o.*, b.name AS branch_name FROM orders o "
            "JOIN branches b ON b.id = o.branch_id WHERE o.id = %s",
            (order_id,),
        )
        if order is None:
            return None
        order["items"] = db.fetch_all(
            "SELECT oi.quantity, oi.unit_price, p.name "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "WHERE oi.order_id = %s",
            (order_id,),
        )
        for item in order["items"]:
            item["subtotal"] = item["quantity"] * item["unit_price"]
        return order

    @staticmethod
    def for_user(user_id):
        return db.fetch_all(
            "SELECT o.*, b.name AS branch_name FROM orders o "
            "JOIN branches b ON b.id = o.branch_id "
            "WHERE o.user_id = %s ORDER BY o.created_at DESC",
            (user_id,),
        )

    @staticmethod
    def for_branch(branch_id=None):
        """Orders for one branch, or for every branch when branch_id is None."""
        query = (
            "SELECT o.*, b.name AS branch_name FROM orders o "
            "JOIN branches b ON b.id = o.branch_id "
        )
        params = ()
        if branch_id is not None:
            query += "WHERE o.branch_id = %s "
            params = (branch_id,)
        query += "ORDER BY o.created_at DESC"
        return db.fetch_all(query, params)

    @staticmethod
    def update_status(order_id, status, payment_status):
        """Change an order's status.
        Cancelling an order puts its items back into the branch's stock.
        A cancelled order is final and can't be changed again."""
        if status not in STATUSES or payment_status not in PAYMENT_STATUSES:
            raise ValueError("Invalid status.")

        with db.transaction() as cursor:
            cursor.execute(
                "SELECT branch_id, status FROM orders WHERE id = %s FOR UPDATE",
                (order_id,),
            )
            order = cursor.fetchone()
            if order is None:
                raise ValueError("Order not found.")
            if order["status"] == "cancelled":
                raise ValueError("A cancelled order can't be changed.")

            if status == "cancelled":
                cursor.execute(
                    "SELECT product_id, quantity FROM order_items "
                    "WHERE order_id = %s",
                    (order_id,),
                )
                for item in cursor.fetchall():
                    cursor.execute(
                        "UPDATE branch_stock SET quantity = quantity + %s "
                        "WHERE branch_id = %s AND product_id = %s",
                        (item["quantity"], order["branch_id"],
                         item["product_id"]),
                    )

            cursor.execute(
                "UPDATE orders SET status = %s, payment_status = %s "
                "WHERE id = %s",
                (status, payment_status, order_id),
            )