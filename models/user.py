import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import Database

db = Database()

CODE_MINUTES = 15      # how long a code works
MAX_ATTEMPTS = 5       # wrong tries before the code is cancelled
RESEND_SECONDS = 60    # wait before a new code can be requested


class User:
    """Base class for every account in Maddie's System."""

    role = "user"

    def __init__(self, id, name, email, password_hash,
                 branch_id=None, profile_photo=None, email_verified=True):
        self.id = id
        self.name = name
        self.email = email
        self._password_hash = password_hash  # private: never shown or exposed
        self.branch_id = branch_id
        self.profile_photo = profile_photo
        self.email_verified = bool(email_verified)

    # ---------- behavior ----------
    def check_password(self, password):
        return check_password_hash(self._password_hash, password)

    def can_manage_inventory(self):
        return False

    def can_view_all_sales(self):
        return False

    # ---------- email verification ----------
    def start_verification(self):
        """Create a new 6-digit code, store only its hash, and return the code."""
        code = f"{secrets.randbelow(1000000):06d}"
        db.execute(
            "UPDATE users SET verification_code_hash = %s, "
            "verification_expires = DATE_ADD(NOW(), INTERVAL %s MINUTE), "
            "verification_attempts = 0, verification_sent_at = NOW() "
            "WHERE id = %s",
            (generate_password_hash(code), CODE_MINUTES, self.id),
        )
        return code

    def seconds_until_resend(self):
        row = db.fetch_one(
            "SELECT GREATEST(0, %s - TIMESTAMPDIFF(SECOND, verification_sent_at, NOW())) "
            "AS wait FROM users WHERE id = %s",
            (RESEND_SECONDS, self.id),
        )
        if row is None or row["wait"] is None:
            return 0
        return int(row["wait"])

    def check_verification(self, code):
        """Check a typed code. Returns 'ok', 'wrong', 'expired' or 'locked'."""
        row = db.fetch_one(
            "SELECT verification_code_hash, verification_attempts, "
            "(verification_expires IS NOT NULL AND verification_expires > NOW()) "
            "AS still_valid FROM users WHERE id = %s",
            (self.id,),
        )
        if row is None or not row["verification_code_hash"] or not row["still_valid"]:
            return "expired"
        if row["verification_attempts"] >= MAX_ATTEMPTS:
            return "locked"

        if check_password_hash(row["verification_code_hash"], code):
            db.execute(
                "UPDATE users SET email_verified = 1, "
                "verification_code_hash = NULL, verification_expires = NULL, "
                "verification_attempts = 0 WHERE id = %s",
                (self.id,),
            )
            self.email_verified = True
            return "ok"

        attempts = row["verification_attempts"] + 1
        db.execute(
            "UPDATE users SET verification_attempts = %s WHERE id = %s",
            (attempts, self.id),
        )
        return "locked" if attempts >= MAX_ATTEMPTS else "wrong"

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
                          row["profile_photo"], row.get("email_verified", 1))

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
    def remove_unverified(email):
        """Delete an old, never-verified sign-up so the email can be used again.
        Verified accounts are never touched."""
        db.execute(
            "DELETE FROM users WHERE email = %s AND email_verified = 0",
            (email,),
        )

    @staticmethod
    def register_customer(name, email, password):
        """Create a customer account that must verify its email before login."""
        hashed = generate_password_hash(password)
        new_id = db.execute(
            "INSERT INTO users (name, email, password_hash, role, email_verified) "
            "VALUES (%s, %s, %s, 'customer', 0)",
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