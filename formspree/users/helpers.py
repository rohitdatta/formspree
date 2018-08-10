from flask import render_template, g
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
import zipcodes

from formspree import settings
from formspree.stuff import celery
from formspree.utils import send_email


def hash_pwd(password):
    return generate_password_hash(password)


def check_password(hashed, password):
    return check_password_hash(hashed, password)

@celery.task()
def send_downgrade_email(customer_email):
    send_email(
        to=customer_email,
        subject='Successfully downgraded from {} {}'.format(settings.SERVICE_NAME,
                                                            settings.UPGRADED_PLAN_NAME),
        text=render_template('email/downgraded.txt'),
        html=render_template('email/downgraded.html'),
        sender=settings.DEFAULT_SENDER
    )

def normal_payment(customer, source_id):
    customer.subscriptions.create(
        plan='gold',
        source=source_id,
        tax_percent=8.25 if card_state(source_id) == 'TX' else None
    )

def card_state(source_id=None, source=None):
    if source_id is None and source is None:
        raise ValueError('Either source_id or source must be passed in')
    if source is None:
        source = stripe.Source.retrieve(source_id)

    state = None
    if source.owner.address.country == 'US':
        try:
            state = zipcodes.matching(str(source.owner.address.postal_code.zfill(5)))[0]['state']
        except Exception as e:
            g.log.error('Failed to gather zip code data for US billing address', error=e)

    return state
