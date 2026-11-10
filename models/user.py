from werkzeug.security import generate_password_hash, check_password_hash
from models.database import Database

db = Database()


class User:
    """Base class for every account in Maddie's System."""

    role = "user"

    def __init__(self, id, name, email, password_hash,
                 branch_id=None, profile_photo=None):
        self.id = id
        self.name = name
        self.email = email
        self._password_hash = password_hash  # private: never shown or exposed
        self.branch_id = branch_id
        self.profile_photo = profile_photo

    # ---------- behavior ----------
    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    def can_manage_inventory(self):
        return False

    def can_view_all_sales(self):
        return False

    # ---------- profile changes ----------
    def update_details(self, name, email):
        db.execute(
            "UPDATE users SET name = %s, email = %s WHERE id = %s",
            (name, email, self.id),
        )
        self.name = name
        self.email = email

    def change_password(self, new_password):
        hashed = generate_password_hash(new_password)
        db.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hashed, self.id),
        )
        self._password_hash = hashed

    def set_photo(self, photo_path):
        db.execute(
            "UPDATE users SET profile_photo = %s WHERE id = %s",
            (photo_path, self.id),
        )
        self.profile_photo = photo_path

    # ---------- database ----------
    @staticmethod
    def _from_row(row):
        if row is None:
            return None
        user_class = ROLE_CLASSES.get(row["role"], Customer)
        return user_class(row["id"], row["name"], row["email"],
                          row["password_hash"], row["branch_id"],
                          row["profile_photo"])

    @staticmethod
    def find_by_email(email):
        row = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        return User._from_row(row)

    @staticmethod
    def find_by_id(user_id):
        row = db.fetch_one("SELECT * FROM users WHERE id = %s", (user_id,))
        return User._from_row(row)

    @staticmethod
    def email_taken(email, exclude_id=None):
        """True if another account already uses this email."""
        row = db.fetch_one("SELECT id FROM users WHERE email = %s", (email,))
        return row is not None and row["id"] != exclude_id

    @staticmethod
    def register_customer(name, email, password):
        hashed = generate_password_hash(password)
        new_id = db.execute(
            "INSERT INTO users (name, email, password_hash, role) "
            "VALUES (%s, %s, %s, 'customer')",
            (name, email, hashed),
        )
        return User.find_by_id(new_id)


class Customer(User):
    role = "customer"


class Manager(User):
    role = "manager"

    def can_manage_inventory(self):
        return True


class Owner(User):
    role = "owner"

    def can_manage_inventory(self):
        return True

    def can_view_all_sales(self):
        return True


ROLE_CLASSES = {
    "customer": Customer,
    "manager": Manager,
    "owner": Owner,
}