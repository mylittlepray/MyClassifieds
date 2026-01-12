from django.template.loader import render_to_string
from django.core.signing import Signer, BadSignature, loads
from django.conf import settings 

from django.core.mail import EmailMultiAlternatives

from datetime import datetime 
from os.path import splitext 

signer = Signer()

def send_activation_notification(user):
    host = "https://" + settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "http://localhost:8000"
    context = {"user": user, "host": host, "sign": signer.sign(user.username)}

    subject = render_to_string("email/activation_letter_subject.txt", context).strip()
    text_body = render_to_string("email/activation_letter_body.txt", context)
    html_body = render_to_string("email/activation_letter_body.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        to=[user.email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)

def send_new_comment_notification(comment):
    host = "https://" + settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else "http://localhost:8000"

    author = comment.bb.author
    context = {"author": author, "host": host, "comment": comment}

    subject = render_to_string("email/new_comment_letter_subject.txt", context).strip()
    text_body = render_to_string("email/new_comment_letter_body.txt", context)
    html_body = render_to_string("email/new_comment_letter_body.html", context)

    msg = EmailMultiAlternatives(subject=subject, body=text_body, to=[author.email])
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)

def get_timestamp_path(instance, filename): 
    return '%s%s' % (datetime.now().timestamp(), splitext(filename)[1])

def get_anon_author_from_cookie(request, cookie_key, cookie_salt, cookie_max_age):
    raw = request.COOKIES.get(cookie_key)
    if not raw:
        return None
    try:
        return loads(raw, salt=cookie_salt, max_age=cookie_max_age)
    except BadSignature:
        return None

def get_signed_cookie(request, key: str) -> str | None:
    value = request.COOKIES.get(key)
    if not value:
        return None
    try:
        return signer.unsign(value)
    except BadSignature:
        return None

def set_signed_cookie(response, key: str, plain_value: str, *, max_age: int, secure: bool):
    response.set_cookie(
        key,
        signer.sign(plain_value),
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=secure,
    )