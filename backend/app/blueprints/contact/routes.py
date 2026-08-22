import re
from flask import Blueprint, request, jsonify, redirect
from backend.app.services.contact_service import ContactService, EmailConfigError, EmailDeliveryError

contact_bp = Blueprint('contact', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def _extract_request_data():
    """Extract parameters whether sent as JSON or multipart/form-data."""
    if request.is_json:
        data = request.get_json(silent=True) or {}
    else:
        data = request.form.to_dict()
    return data


def _process_contact_submission():
    data = _extract_request_data()
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()

    # Input Validation
    if not name:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Invalid contact form data: Name is required'
        }), 400

    if len(name) > 100:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Invalid contact form data: Name exceeds maximum length of 100 characters'
        }), 400

    if not email:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Invalid contact form data: Email is required'
        }), 400

    if len(email) > 254 or not EMAIL_REGEX.match(email):
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Invalid contact form data: Valid email address is required'
        }), 400

    if not message:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Invalid contact form data: Message is required'
        }), 400

    if len(message) > 5000:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Invalid contact form data: Message exceeds maximum length of 5000 characters'
        }), 400

    try:
        ContactService.send_contact_email(name, email, message)
        return jsonify({
            'success': True,
            'status': 'success',
            'message': 'Message sent successfully. We\'ll get back to you soon.'
        }), 200
    except EmailConfigError:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Email service is temporarily unavailable'
        }), 503
    except EmailDeliveryError:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Unable to deliver message. Please try again later.'
        }), 502
    except Exception:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'An internal error occurred while processing your contact request'
        }), 500


@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        return _process_contact_submission()
    return redirect('/#contact')


@contact_bp.route('/submit', methods=['POST'])
def submit():
    return _process_contact_submission()


@contact_bp.route('/subscribe', methods=['POST'])
def subscribe():
    data = _extract_request_data()
    email = (data.get('email') or '').strip()

    if not email or len(email) > 254 or not EMAIL_REGEX.match(email):
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Valid email address is required'
        }), 400

    try:
        ContactService.send_subscription_email(email)
        return jsonify({
            'success': True,
            'status': 'success',
            'message': 'Thank you for subscribing to our newsletter!'
        }), 200
    except EmailConfigError:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Email service is temporarily unavailable'
        }), 503
    except EmailDeliveryError:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Unable to process subscription. Please try again later.'
        }), 502
    except Exception:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'An internal error occurred'
        }), 500
