import requests
import datetime
import calendar
import urlparse
import string
import uuid
import re
from datetime import timedelta
from flask import make_response, current_app, request, url_for, jsonify
from importlib import import_module
import sendgrid
from sendgrid.helpers.mail import *

from formspree import settings, log

IS_VALID_EMAIL = lambda x: re.match(r"[^@]+@[^@]+\.[^@]+", x)

# decorators

def request_wants_json():
    if request.headers.get('X_REQUESTED_WITH','').lower() == 'xmlhttprequest' or \
       request.headers.get('X-REQUESTED-WITH','').lower() == 'xmlhttprequest':
        return True
    if accept_better('json', 'html'):
        return True
    if 'json' in request.headers.get('Content-Type', '') and \
            not accept_better('html', 'json'):
        return True


def accept_better(subject, against):
    if 'Accept' in request.headers:
        accept = request.headers['Accept'].lower()
        try:
            isub = accept.index(subject)
        except ValueError:
            return False

        try:
            iaga = accept.index(against)
        except ValueError:
            return True

        return isub < iaga
    else:
        return False


def jsonerror(code, *args, **kwargs):
    resp = jsonify(*args, **kwargs)
    resp.status_code = code
    return resp


def uuidslug():
    return uuid2slug(uuid.uuid4())


def uuid2slug(uuidobj):
    return uuidobj.bytes.encode('base64').rstrip('=\n').replace('/', '_')


def slug2uuid(slug):
    return str(uuid.UUID(bytes=(slug + '==').replace('_', '/').decode('base64')))


def get_url(endpoint, secure=False, **values):   
    ''' protocol preserving url_for '''
    path = url_for(endpoint, **values)
    if secure:
        url_parts = request.url.split('/', 3)
        path = "https://" + url_parts[2] + path
    return path


def unix_time_for_12_months_from_now(now=None):
    now = now or datetime.date.today()
    month = now.month - 1 + 12
    next_year = now.year + month / 12
    next_month = month % 12 + 1
    start_of_next_month = datetime.datetime(next_year, next_month, 1, 0, 0)
    return calendar.timegm(start_of_next_month.utctimetuple())


def next_url(referrer=None, next=None):
    referrer = referrer if referrer is not None else ''
    next = next if next is not None else ''

    if not next:
      return url_for('thanks')

    if urlparse.urlparse(next).netloc:  # check if next_url is an absolute url
      return next

    parsed = list(urlparse.urlparse(referrer))  # results in [scheme, netloc, path, ...]
    parsed[2] = next

    return urlparse.urlunparse(parsed)


def send_email(to=None, subject=None, text=None, html=None, sender=None, cc=None, reply_to=None):
    '''
    Sends email using SendGrid's REST-api
    '''

    if None in [to, subject, text, sender]:
        raise ValueError('to, subject text and sender are required to send email')

    sg = sendgrid.SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
    mail = Mail()

    # parse 'fromname' from 'sender' if it is formatted like "Name <name@email.com>"
    try:
        bracket = sender.index('<')
        mail.set_from(Email(sender[bracket+1:-1], sender[:bracket].strip()))
    except ValueError:
        mail.set_from(Email(sender))

    mail.set_subject(subject)
    personalization = Personalization()
    personalization.add_to(Email(to))
    if cc:
        valid_emails = [email for email in cc if IS_VALID_EMAIL(email)]
        map(lambda valid_email: personalization.add_cc(Email(valid_email)), valid_emails)
    mail.add_personalization(personalization)
    mail.add_content(Content('text/plain', text))
    mail.add_content(Content('text/html', html))
    if reply_to:
        mail.set_reply_to(Email(reply_to))

    log.info('Queuing message to %s' % str(to))

    result = sg.client.mail.send.post(request_body=mail.get())

    log.info('Queued message to %s' % str(to))
    errmsg = ""
    if result.status_code / 100 != 2:
        try:
            errmsg = '; \n'.join(result.json().get("errors"))
        except ValueError:
            errmsg = result.text
        log.warning(errmsg)

    return result.status_code / 100 == 2, errmsg, result.status_code
