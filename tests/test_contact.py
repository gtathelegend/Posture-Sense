import pytest
from unittest.mock import patch, MagicMock
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


def test_contact_submission_success(client):
    """Test valid contact submission when email service is properly configured."""
    with patch.object(ContactService, 'is_configured', return_value=True), \
         patch.object(ContactService, 'send_contact_email', return_value=True) as mock_send:
        
        response = client.post('/contact', data={
            'name': 'A EON Core',
            'email': 'info@aeoncore.in',
            'message': 'Enquiry message'
        })
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True
        assert json_data['status'] == 'success'
        assert 'sent successfully' in json_data['message']
        mock_send.assert_called_once_with('A EON Core', 'info@aeoncore.in', 'Enquiry message')


def test_contact_submission_json_payload(client):
    """Test contact submission accepting JSON content type."""
    with patch.object(ContactService, 'is_configured', return_value=True), \
         patch.object(ContactService, 'send_contact_email', return_value=True):
        
        response = client.post('/contact', json={
            'name': 'A EON Core',
            'email': 'info@aeoncore.in',
            'message': 'Enquiry via JSON'
        })
        
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data['success'] is True


def test_contact_submission_missing_name(client):
    """Test submission with missing name returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': '',
        'email': 'info@aeoncore.in',
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
        'email': 'info@aeoncore.in',
        'message': 'Enquiry'
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'maximum length' in json_data['error']


def test_contact_submission_missing_email(client):
    """Test submission with missing email returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'A EON Core',
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
        'name': 'A EON Core',
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
        'name': 'A EON Core',
        'email': 'info@aeoncore.in',
        'message': '   '
    })
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['success'] is False
    assert 'Message is required' in json_data['error']


def test_contact_submission_oversized_message(client):
    """Test submission with oversized message (>5000 chars) returns 400 Bad Request."""
    response = client.post('/contact', data={
        'name': 'A EON Core',
        'email': 'info@aeoncore.in',
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
            'name': 'A EON Core',
            'email': 'info@aeoncore.in',
            'message': 'Enquiry'
        })
        
        assert response.status_code == 503
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'Email service is temporarily unavailable' in json_data['error']


def test_contact_submission_provider_failure(client):
    """Test response when SMTP delivery fails (returns HTTP 502)."""
    with patch.object(ContactService, 'send_contact_email', side_effect=EmailDeliveryError("SMTP connection timeout")):
        response = client.post('/contact', data={
            'name': 'A EON Core',
            'email': 'info@aeoncore.in',
            'message': 'Enquiry'
        })
        
        assert response.status_code == 502
        json_data = response.get_json()
        assert json_data['success'] is False
        assert 'Unable to deliver message' in json_data['error']


def test_contact_service_smtp_timeout_configuration(monkeypatch):
    """Verify ContactService get_smtp_config parses timeouts and settings correctly."""
    monkeypatch.setenv('EMAIL_USER', 'test@example.com')
    monkeypatch.setenv('EMAIL_PASSWORD', 'secretpass')
    monkeypatch.setenv('ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setenv('SMTP_TIMEOUT', '15.5')
    
    assert ContactService.is_configured() is True
    config = ContactService.get_smtp_config()
    assert config['timeout'] == 15.5
    assert config['user'] == 'test@example.com'
    assert config['password'] == 'secretpass'


def test_contact_service_header_sanitization():
    """Verify header injection characters are stripped."""
    dirty_header = "Subject\r\nBcc: hacker@example.com"
    clean = ContactService._sanitize_header(dirty_header)
    assert "\r" not in clean
    assert "\n" not in clean
    assert clean == "SubjectBcc: hacker@example.com"
