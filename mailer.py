from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


class Mailer:
    """Sends emails for Maddie's System.
    A failed email is logged and never stops an order from going through."""

    @staticmethod
    def send_verification_code(name, email, code):
        body = (
            f"Hi {name},\n\n"
            f"Welcome to Maddie's! Your verification code is:\n\n"
            f"    {code}\n\n"
            f"It expires in 15 minutes. "
            f"If you didn't create an account, you can ignore this email.\n\n"
            f"- Maddie's Bakeshop"
        )
        message = Message(
            subject="Your Maddie's verification code",
            recipients=[email],
            body=body,
        )
        try:
            mail.send(message)
            return True
        except Exception as error:
            current_app.logger.error("Could not send verification email: %s", error)
            return False

    @staticmethod
    def send_order_confirmation(order):
        item_lines = "\n".join(
            f"  {item['quantity']} x {item['name']} - PHP {item['subtotal']:.2f}"
            for item in order["items"]
        )
        if order["fulfillment"] == "delivery":
            how = f"Delivery to: {order['delivery_address']}"
        else:
            how = "Pickup at the branch"
        if order["payment_method"] == "gcash":
            payment = f"GCash (reference: {order['gcash_reference']})"
        else:
            payment = "Cash"

        body = (
            f"Hi {order['customer_name']},\n\n"
            f"Thank you for ordering from Maddie's! "
            f"We received your order {order['order_number']}.\n\n"
            f"Branch: {order['branch_name']}\n"
            f"{how}\n"
            f"Payment: {payment}\n\n"
            f"Your items:\n{item_lines}\n\n"
            f"Total: PHP {order['total']:.2f}\n\n"
            f"We'll start preparing your order soon. "
            f"Please keep your order number handy.\n\n"
            f"- Maddie's Bakeshop"
        )

        message = Message(
            subject=f"Your Maddie's order {order['order_number']}",
            recipients=[order["customer_email"]],
            body=body,
        )
        try:
            mail.send(message)
            return True
        except Exception as error:
            current_app.logger.error("Could not send order email: %s", error)
            return False