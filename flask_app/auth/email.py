from typing import List

from flask_mail import Message
from flask import render_template

from . import mail, auth, models


def send_email(
    subject: str,
    sender: str,
    recipients: List[str],
    text_body: str,
    html_body: str
) -> None:
    """
    Wrapper for Flask-Mail in one function.

    Parameters
    ----------
    subject
        Subject for the e-mail.
    sender
        Sender of the e-mail.
    recipients
        List of recipients of the e-mail.
    text_body
        Text body for the e-mail.
    html_body
        HTML body for the e-mail.

    Returns
    -------
    None
        Just sends the specified e-mail.

    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(user: models.User) -> None:
    """
    Sends an e-mail to the user with password reset link.

    Parameters
    ----------
    user
        User to send an e-mail to.

    Returns
    -------
    None
        Just sends the reset e-mail.

    """
    token = user.get_reset_password_token()
    send_email(
        'Slip app reset password',
        sender=auth.config['MAIL_USERNAME'],
        recipients=[user.email],
        text_body=render_template('reset_password_mail.txt',
                                  user=user, token=token),
        html_body=render_template('reset_password_mail.html',
                                  user=user, token=token)
    )


def send_mail_verification_email(user: models.User) -> None:
    """
    Sends an e-mail to the user with verification link.

    Parameters
    ----------
    user
        User to send an e-mail to.

    Returns
    -------
    None
        Just sends the verification e-mail.

    """
    token = user.get_mail_verification_token()
    send_email(
        'Slip app verificate email',
        sender=auth.config['MAIL_USERNAME'],
        recipients=[user.email],
        text_body=render_template('verificate_mail.txt',
                                  user=user, token=token),
        html_body=render_template('verificate_mail.html',
                                  user=user, token=token)
    )
