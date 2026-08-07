from flask import Blueprint, render_template, request, jsonify, redirect
from backend.app.services.contact_service import ContactService

contact_bp = Blueprint('contact', __name__)


@contact_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        try:
            ContactService.send_contact_email(name, email, message)
            return jsonify({'status': 'success', 'message': 'Thank you for contacting us!'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'An error occurred while processing your contact form. Please try again later.'}), 500

    return redirect('/#contact')


@contact_bp.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        try:
            ContactService.send_contact_email(name, email, message)
            return jsonify({'status': 'success', 'message': 'Thank you for contacting us!'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'An error occurred while processing your contact form. Please try again later.'}), 500

    return redirect('/#contact')


@contact_bp.route('/subscribe', methods=['POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form.get('email')

        try:
            ContactService.send_subscription_email(email)
            return jsonify({'status': 'success', 'message': 'Thank you for subscribing to our newsletter!'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': 'An error occurred while processing your subscription. Please try again later.'}), 500
