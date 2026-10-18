import pytest
from services.member_service import (
    add_member, update_member, delete_member,
    get_member_by_id, get_all_members
)
from services.borrowing_service import issue_book

def test_add_member_success(db_path):
    """Test registering a new member."""
    member_id = add_member({
        'full_name': 'Samantha Ray',
        'email': 'samantha.ray@matrix.org',
        'phone': '+1 (555) 777-8888',
        'membership_status': 'Active',
        'registration_date': '2026-02-01'
    }, db_path=db_path)

    assert member_id is not None
    member = get_member_by_id(member_id, db_path=db_path)
    assert member['full_name'] == 'Samantha Ray'
    assert member['membership_status'] == 'Active'

def test_prevent_duplicate_email(db_path):
    """Test duplicate member email rejection."""
    with pytest.raises(ValueError, match="already registered"):
        add_member({
            'full_name': 'Duplicate User',
            'email': 'samantha.ray@matrix.org',  # Duplicate!
            'phone': '+1 (555) 000-0000',
            'membership_status': 'Active'
        }, db_path=db_path)

def test_invalid_email_format(db_path):
    """Test validation rejection on malformed email address."""
    with pytest.raises(ValueError, match="Invalid email"):
        add_member({
            'full_name': 'Bad Email User',
            'email': 'not-an-email',
            'phone': '+1 234',
            'membership_status': 'Active'
        }, db_path=db_path)

def test_update_member_success(db_path, sample_member_id):
    """Test updating member details."""
    update_member(sample_member_id, {
        'full_name': 'Test Reader Updated',
        'email': 'test.member@example.com',
        'phone': '+1 (555) 999-0000',
        'membership_status': 'Suspended',
        'registration_date': '2026-01-01'
    }, db_path=db_path)

    updated = get_member_by_id(sample_member_id, db_path=db_path)
    assert updated['full_name'] == 'Test Reader Updated'
    assert updated['membership_status'] == 'Suspended'
    assert updated['phone'] == '+1 (555) 999-0000'
