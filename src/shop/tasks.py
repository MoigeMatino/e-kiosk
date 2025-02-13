from celery import shared_task
from .africastalking_client import AfricasTalkingClient
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_sms_task(to, template_name, order_id):
    """ Background task to send SMS with exception handling"""
    from shop.models import Notification  
    
    try:
        client = AfricasTalkingClient()
        message = client.get_templated_message(
            template_name=template_name, 
            to=to, 
            order_id=order_id
            )
        response = client.send_sms(to, message)
        
        if response:
            Notification.objects.create(message=message)
            logger.info(f"Notification created for order {order_id}.")
        else:
            logger.warning(f"Failed to send SMS to {to}. No response.")
    
    except Exception as e:
        logger.error(f"Error sending SMS to {to}. Exception: {e}", exc_info=True)
        

@shared_task
def send_email_task(subject, message, recipient_list):
    """ Sends an email to admin asynchronously"""
    from shop.models import Notification  
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='admin@ekiosk.com',
            recipient_list=recipient_list,
            fail_silently=False,
        )
        Notification.objects.create(message=message)
    except Exception as e:
        logger.error(f"Error sending email. Exception: {e}", exc_info=True)