import pytest
from services.auth_service import authenticate_admin

def test_authenticate_admin_success(db_path):
    """Test authenticating testadmin credentials."""
    admin = authenticate_admin('testadmin', 'TestPassword123!', db_path=db_path)
    assert admin is not None
    assert admin['username'] == 'testadmin'

def test_authenticate_admin_failure(db_path):
    """Test incorrect password rejects authentication."""
    admin = authenticate_admin('testadmin', 'WrongPassword!', db_path=db_path)
    assert admin is None

def test_unauthorized_access_redirect(client):
    """Ensure protected admin endpoints redirect anonymous users to login."""
    protected_urls = [
        '/admin/dashboard',
        '/admin/books',
        '/admin/members',
        '/admin/circulation',
        '/admin/history',
        '/admin/analytics'
    ]
    for url in protected_urls:
        response = client.get(url, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

def test_admin_login_and_logout_flow(client):
    """Test full login, access to dashboard, and logout workflow."""
    # 1. Login with valid credentials
    login_resp = client.post('/login', data={
        'username': 'testadmin',
        'password': 'TestPassword123!'
    }, follow_redirects=True)
    assert login_resp.status_code == 200
    assert b'Command Overview' in login_resp.data

    # 2. Access dashboard as authenticated user
    dash_resp = client.get('/admin/dashboard')
    assert dash_resp.status_code == 200
    assert b'Unique Book Titles' in dash_resp.data or b'TOTAL TITLES' in dash_resp.data

    # 3. Logout
    logout_resp = client.get('/logout', follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b'You have been securely logged out' in logout_resp.data

    # 4. Attempt dashboard again -> should redirect to login
    re_attempt = client.get('/admin/dashboard', follow_redirects=False)
    assert re_attempt.status_code == 302
    assert '/login' in re_attempt.headers['Location']
