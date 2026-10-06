import pytest
import html
import logging
from unittest.mock import patch, MagicMock
import requests
from backend.app import create_app
from backend.app.services.contact_service import ContactService, EmailConfigError, EmailDeliveryError


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# ── Contact Endpoint Tests (High-Level Contract) ───────────────────────────────

def test_contact_submission_success(client):
    """Test valid contact submission when email service is properly configured."""
    with patch.object(ContactService, 'is_configured', return_value=True), \
         patch.object(ContactService, 'send_contact_email', return_value=True) as mock_send:
        
        response = client.post('/contact', data={
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'message': 'Hello PostureSense team'
        })
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert json_data['status'] == 'success'
        assert 'sent successfully' in json_data['message']
        mock_send.assert_called_once_with('Jane Doe', 'jane@example.com', 'Hello PostureSense team')


def test_contact_submission_json_payload(client):
    """Test contact submission accepting JSON content type."""
    with patch.object(ContactService, 'is_configured', return_value=True), \
         patch.object(ContactService, 'send_contact_email', return_value=True):
        
        response = client.post('/contact', json={
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'message': 'Enquiry via JSON'
        })
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True


def test_contact_submission_missing_name(client):
    """Test submission with missing name returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': '',
        'email': 'jane@example.com',
        'message': 'Enquiry'
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Name is required' in json_data['error']


def test_contact_submission_oversized_name(client):
    """Test submission with oversized name (>100 chars) returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'A' * 105,
        'email': 'jane@example.com',
        'message': 'Enquiry'
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'maximum length' in json_data['error']


def test_contact_submission_missing_email(client):
    """Test submission with missing email returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'Jane Doe',
        'email': '',
        'message': 'Enquiry'
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Email is required' in json_data['error']


def test_contact_submission_invalid_email(client):
    """Test submission with malformed email returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'Jane Doe',
        'email': 'not-an-email',
        'message': 'Enquiry'
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Valid email' in json_data['error']


def test_contact_submission_missing_message(client):
    """Test submission with missing message returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'message': '   '
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Message is required' in json_data['error']


def test_contact_submission_oversized_message(client):
    """Test submission with oversized message (>5000 chars) returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'message': 'X' * 5001
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'maximum length' in json_data['error']


def test_contact_submission_unconfigured_service(client):
    """Test response when email service lacks credentials (returns HTTP 503)."""
    with patch.object(ContactService, 'send_contact_email', side_effect=EmailConfigError("Not configured")):
        response = client.post('/contact', data={
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'message': 'Enquiry'
        })
        
        assert response.status_code == 503
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'Email service is temporarily unavailable' in json_data['error']


def test_contact_submission_provider_failure(client):
    """Test response when email provider delivery fails (returns HTTP 502)."""
    with patch.object(ContactService, 'send_contact_email', side_effect=EmailDeliveryError("Brevo API error: HTTP 500")):
        response = client.post('/contact', data={
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'message': 'Enquiry'
        })
        
        assert response.status_code == 502
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'Unable to deliver message' in json_data['error']


# ── Brevo Transactional Email Service Unit Tests ───────────────────────────────

@pytest.fixture(autouse=True)
def brevo_env(monkeypatch):
    """Set standard mock environment variables for Brevo."""
    monkeypatch.setenv('BREVO_API_KEY', 'xkeysib-test-secret-key-1234567890')
    monkeypatch.setenv('BREVO_SENDER_EMAIL', 'notifications@posturesense.ai')
    monkeypatch.setenv('BREVO_SENDER_NAME', 'PostureSense')
    monkeypatch.setenv('CONTACT_RECIPIENT_EMAIL', 'admin@posturesense.ai')
    monkeypatch.setenv('BREVO_TIMEOUT', '12.5')


def test_contact_service_is_configured(brevo_env):
    """Verify is_configured correctly checks required Brevo credentials."""
    assert ContactService.is_configured() is True


def test_contact_service_unconfigured_when_missing_key(monkeypatch):
    """Verify is_configured returns False if BREVO_API_KEY is missing."""
    monkeypatch.delenv('BREVO_API_KEY', raising=False)
    assert ContactService.is_configured() is False


def test_brevo_api_request_structure(brevo_env):
    """Verify exact endpoint, headers, sender, recipient, replyTo and body structure."""
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"messageId": "<test-msg-id@brevo>"}

    with patch('requests.post', return_value=mock_response) as mock_post:
        success = ContactService.send_contact_email(
            name='Alice Wonderland',
            email='alice@example.com',
            message='Need help with Warrior II pose.'
        )

        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args

        # 1. Correct Endpoint URL
        assert args[0] == "https://api.brevo.com/v3/smtp/email"

        # 2. Correct Headers
        headers = kwargs.get('headers', {})
        assert headers['api-key'] == 'xkeysib-test-secret-key-1234567890'
        assert headers['Content-Type'] == 'application/json'
        assert headers['Accept'] == 'application/json'

        # 3. Correct Timeout
        assert kwargs.get('timeout') == 12.5

        # 4. Correct JSON Payload
        payload = kwargs.get('json', {})
        assert payload['sender']['name'] == 'PostureSense'
        assert payload['sender']['email'] == 'notifications@posturesense.ai'
        assert payload['to'] == [{'email': 'admin@posturesense.ai'}]
        assert payload['replyTo']['name'] == 'Alice Wonderland'
        assert payload['replyTo']['email'] == 'alice@example.com'
        assert payload['subject'] == 'New contact form submission from Alice Wonderland'
        assert 'Need help with Warrior II pose.' in payload['textContent']
        assert 'Alice Wonderland' in payload['htmlContent']
        assert 'alice@example.com' in payload['htmlContent']


def test_brevo_html_escaping_prevents_xss(brevo_env):
    """Verify user input is safely escaped in htmlContent."""
    mock_response = MagicMock()
    mock_response.status_code = 201

    with patch('requests.post', return_value=mock_response) as mock_post:
        ContactService.send_contact_email(
            name='<script>alert("hacked")</script>',
            email='test<xss>@example.com',
            message='<b>Bold & Dangerous</b>'
        )

        _, kwargs = mock_post.call_args
        payload = kwargs.get('json', {})
        html_content = payload['htmlContent']

        assert '<script>' not in html_content
        assert '&lt;script&gt;alert(&quot;hacked&quot;)&lt;/script&gt;' in html_content
        assert '&lt;b&gt;Bold &amp; Dangerous&lt;/b&gt;' in html_content


def test_brevo_api_authentication_error(brevo_env):
    """Verify Brevo 401 Unauthorized raises EmailDeliveryError."""
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch('requests.post', return_value=mock_response):
        with pytest.raises(EmailDeliveryError) as exc_info:
            ContactService.send_contact_email('Alice', 'alice@example.com', 'Hello')
        assert '401' in str(exc_info.value)


def test_brevo_api_server_error(brevo_env):
    """Verify Brevo 500 Internal Server Error raises EmailDeliveryError."""
    mock_response = MagicMock()
    mock_response.status_code = 500

    with patch('requests.post', return_value=mock_response):
        with pytest.raises(EmailDeliveryError) as exc_info:
            ContactService.send_contact_email('Alice', 'alice@example.com', 'Hello')
        assert '500' in str(exc_info.value)


def test_brevo_api_timeout_error(brevo_env):
    """Verify requests Timeout exception raises EmailDeliveryError."""
    with patch('requests.post', side_effect=requests.exceptions.Timeout("Connection timed out")):
        with pytest.raises(EmailDeliveryError) as exc_info:
            ContactService.send_contact_email('Alice', 'alice@example.com', 'Hello')
        assert 'Timeout' in str(exc_info.value)


def test_brevo_api_connection_error(brevo_env):
    """Verify requests ConnectionError raises EmailDeliveryError."""
    with patch('requests.post', side_effect=requests.exceptions.ConnectionError("Network is unreachable")):
        with pytest.raises(EmailDeliveryError) as exc_info:
            ContactService.send_contact_email('Alice', 'alice@example.com', 'Hello')
        assert 'ConnectionError' in str(exc_info.value)


def test_brevo_api_key_not_leaked_in_logs(brevo_env, caplog):
    """Verify secret API key is never logged upon delivery failure."""
    caplog.set_level(logging.DEBUG)
    mock_response = MagicMock()
    mock_response.status_code = 401

    with patch('requests.post', return_value=mock_response):
        try:
            ContactService.send_contact_email('Alice', 'alice@example.com', 'Hello')
        except EmailDeliveryError:
            pass

    log_text = caplog.text
    assert 'xkeysib-test-secret-key-1234567890' not in log_text
    assert 'api-key' not in log_text


def test_newsletter_subscription_brevo(brevo_env):
    """Verify newsletter subscription sends notification via Brevo API."""
    mock_response = MagicMock()
    mock_response.status_code = 201

    with patch('requests.post', return_value=mock_response) as mock_post:
        success = ContactService.send_subscription_email('newsletter.user@example.com')
        assert success is True

        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.brevo.com/v3/smtp/email"
        payload = kwargs.get('json', {})
        assert payload['to'] == [{'email': 'admin@posturesense.ai'}]
        assert payload['replyTo']['email'] == 'newsletter.user@example.com'
        assert 'newsletter.user@example.com' in payload['textContent']
