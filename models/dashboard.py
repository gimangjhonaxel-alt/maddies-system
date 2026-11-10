from models.database import Database

db = Database()


class Dashboard:
    """Numbers shown on the owner, manager, and customer dashboards.
    Cancelled orders are not counted as sales."""

    @staticmethod
    def _branch_filter(branch_id, column):
        if branch_id is None:
            return "", ()
        return f" AND {column} = %s", (branch_id,)

    @staticmethod
    def totals(branch_id=None):
        clause, params = Dashboard._branch_filter(branch_id, "o.branch_id")
        return db.fetch_one(
            "SELECT COALESCE(SUM(COALESCE(o.status, 'pending') <> 'cancelled'), 0) AS total_orders, "
            "COALESCE(SUM(CASE WHEN COALESCE(o.status, 'pending') <> 'cancelled' "
            "THEN o.total END), 0) AS sales, "
            "COALESCE(SUM(COALESCE(o.status, 'pending') = 'pending'), 0) AS pending_orders, "
            "COALESCE(SUM(DATE(o.created_at) = CURDATE()), 0) AS today_orders "
            "FROM orders o WHERE 1 = 1" + clause,
            params,
        )

    @staticmethod
    def sales_by_branch():
        return db.fetch_all(
            "SELECT b.id, b.name, COUNT(o.id) AS orders, "
            "COALESCE(SUM(o.total), 0) AS sales "
            "FROM branches b "
            "LEFT JOIN orders o ON o.branch_id = b.id "
            "AND COALESCE(o.status, 'pending') <> 'cancelled' "
            "GROUP BY b.id, b.name ORDER BY b.id"
        )

    @staticmethod
    def top_products(branch_id=None, limit=5):
        clause, params = Dashboard._branch_filter(branch_id, "o.branch_id")
        return db.fetch_all(
            "SELECT p.name, SUM(oi.quantity) AS sold "
            "FROM order_items oi "
            "JOIN orders o ON o.id = oi.order_id "
            "JOIN products p ON p.id = oi.product_id "
            "WHERE COALESCE(o.status, 'pending') <> 'cancelled'" + clause +
            " GROUP BY p.id, p.name ORDER BY sold DESC LIMIT %s",
            params + (limit,),
        )

    @staticmethod
    def low_stock(branch_id=None):
        clause, params = Dashboard._branch_filter(branch_id, "bs.branch_id")
        return db.fetch_all(
            "SELECT b.name AS branch_name, p.name, bs.quantity, "
            "bs.low_stock_threshold "
            "FROM branch_stock bs "
            "JOIN products p ON p.id = bs.product_id "
            "JOIN branches b ON b.id = bs.branch_id "
            "WHERE bs.quantity <= bs.low_stock_threshold "
            "AND COALESCE(p.is_active, 1) = 1" + clause +
            " ORDER BY bs.quantity, p.name",
            params,
        )