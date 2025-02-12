from celery import shared_task
from .africastalking_client import AfricasTalkingClient
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_sms_task(to, template_name, customer_id, order_id):
    """ Background task to send SMS with exception handling"""
    from shop.models import Notification  
    from django.contrib.auth import get_user_model
    
    User = get_user_model()

    try:
        client = AfricasTalkingClient()
        message = client.get_templated_message(
            template_name=template_name, 
            to=to, 
            order_id=order_id
            )
        response = client.send_sms(to, message)
        
        if response:
            customer = User.objects.get(pk=customer_id)
            Notification.objects.create(user=customer, message=message)
            logger.info(f"Notification created for customer {customer_id}.")
        else:
            logger.warning(f"Failed to send SMS to {to}. No response.")
    
    except Exception as e:
        logger.error(f"Error sending SMS to {to}. Exception: {e}", exc_info=True)