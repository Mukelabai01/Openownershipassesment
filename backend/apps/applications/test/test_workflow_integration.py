import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.applications.models import Application
from apps.audits.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
def test_full_workflow():
    # create users
    alice = User.objects.create_user(username='alice', password='pass')
    bob = User.objects.create_user(username='bob', password='pass', is_staff=True)

    client = APIClient()

    # login as alice
    r = client.post('/api/v1/accounts/token/', {'username': 'alice', 'password': 'pass'}, format='json')
    assert r.status_code == 200
    assert 'access' in r.data
    assert 'refresh' in client.cookies

    access = r.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

    # create application
    resp = client.post('/api/v1/applications/', {'title': 'My app', 'content': {}}, format='json')
    assert resp.status_code == 201
    app_id = resp.data['id']

    # submit as owner via transitions endpoint
    r2 = client.post(f'/api/v1/applications/{app_id}/transitions/', {'target': Application.Status.SUBMITTED, 'comment': 'please review'}, format='json')
    assert r2.status_code == 200

    # audit log exists
    assert AuditLog.objects.filter(application_id=app_id, to_status=Application.Status.SUBMITTED).exists()

    # now bob (reviewer) logs in
    client.credentials()  # clear credentials
    r3 = client.post('/api/v1/accounts/token/', {'username': 'bob', 'password': 'pass'}, format='json')
    assert r3.status_code == 200
    bob_access = r3.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {bob_access}')

    # move to under review
    r4 = client.post(f'/api/v1/applications/{app_id}/transitions/', {'target': Application.Status.UNDER_REVIEW}, format='json')
    assert r4.status_code == 200
    assert AuditLog.objects.filter(application_id=app_id, to_status=Application.Status.UNDER_REVIEW).exists()

    # approve
    r5 = client.post(f'/api/v1/applications/{app_id}/transitions/', {'target': Application.Status.APPROVED}, format='json')
    assert r5.status_code == 200
    assert AuditLog.objects.filter(application_id=app_id, to_status=Application.Status.APPROVED).exists()


@pytest.mark.django_db
def test_applicant_cannot_approve():
    """Authorization test: alice (applicant) tries to approve → 403 Forbidden"""
    alice = User.objects.create_user(username='alice', password='pass')
    bob = User.objects.create_user(username='bob', password='pass', is_staff=True)
    
    # Create application owned by alice, move to UNDER_REVIEW
    app = Application.objects.create(owner=alice, title='Test', status=Application.Status.UNDER_REVIEW)
    
    client = APIClient()
    r = client.post('/api/v1/accounts/token/', {'username': 'alice', 'password': 'pass'}, format='json')
    access = r.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    
    # alice tries to approve (should fail)
    resp = client.post(f'/api/v1/applications/{app.id}/transitions/', {
        'target': Application.Status.APPROVED,
        'comment': 'I approve myself!'
    }, format='json')
    
    assert resp.status_code == 403
    assert 'reviewer' in resp.json()['error']['message'].lower()
    
    # Status should remain unchanged
    app.refresh_from_db()
    assert app.status == Application.Status.UNDER_REVIEW


@pytest.mark.django_db
def test_reject_without_comment():
    """Validation test: reviewer rejects without required comment → 400 Bad Request"""
    alice = User.objects.create_user(username='alice', password='pass')
    bob = User.objects.create_user(username='bob', password='pass', is_staff=True)
    
    # Create application owned by alice, move to UNDER_REVIEW
    app = Application.objects.create(owner=alice, title='Test', status=Application.Status.UNDER_REVIEW)
    
    client = APIClient()
    r = client.post('/api/v1/accounts/token/', {'username': 'bob', 'password': 'pass'}, format='json')
    access = r.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    
    # bob tries to reject without comment (should fail)
    resp = client.post(f'/api/v1/applications/{app.id}/transitions/', {
        'target': Application.Status.REJECTED
        # Missing 'comment'!
    }, format='json')
    
    assert resp.status_code == 400
    assert 'comment' in resp.json()['error']['message'].lower()
    
    # Status should remain unchanged
    app.refresh_from_db()
    assert app.status == Application.Status.UNDER_REVIEW


@pytest.mark.django_db
def test_illegal_transition_blocked():
    """Workflow test: cannot transition APPROVED → DRAFT (illegal) → 400"""
    alice = User.objects.create_user(username='alice', password='pass')
    bob = User.objects.create_user(username='bob', password='pass', is_staff=True)
    
    # Create application owned by alice, set to APPROVED
    app = Application.objects.create(owner=alice, title='Test', status=Application.Status.APPROVED)
    
    client = APIClient()
    r = client.post('/api/v1/accounts/token/', {'username': 'bob', 'password': 'pass'}, format='json')
    access = r.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    
    # bob tries to transition back to DRAFT (illegal)
    resp = client.post(f'/api/v1/applications/{app.id}/transitions/', {
        'target': Application.Status.DRAFT,
        'comment': 'Oops, mistake!'
    }, format='json')
    
    assert resp.status_code == 400
    assert 'illegal' in resp.json()['error']['message'].lower()
    
    # Status should remain unchanged
    app.refresh_from_db()
    assert app.status == Application.Status.APPROVED
