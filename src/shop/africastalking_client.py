import logging

import africastalking
from django.conf import settings

from shop.constants import NOTIFICATION_TEMPLATES

logger = logging.getLogger(__name__)


class AfricasTalkingClient:
    def __init__(self):
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        self.sms = africastalking.SMS

    REQUIRED_KEYS = {"customer_name", "order_id"}

    def get_templated_message(self, template_name, to, order_id):
        """
        Returns a formatted message from a template
        """
        template = NOTIFICATION_TEMPLATES.get(template_name, "Hello {customer_name}.")

        message = template.format(customer_name=to, order_id=order_id)

        return message

    def send_sms(self, to, message):
        """Sends an SMS using the AfricasTalking API with error handling and logging."""
        try:
            response = self.sms.send(message, [to])
            logger.info(f"SMS sent to {to}. Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}. Error: {e}", exc_info=True)
            return None
