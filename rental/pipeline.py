from django.contrib.auth import get_user_model, login
from .models import Role
from social_core.pipeline.user import get_username as social_get_username

User = get_user_model()

def get_username(strategy, details, backend, user=None, *args, **kwargs):
    """Get unique username for new user."""
    if user:
        return {'username': user.username}
        
    return {
        'username': social_get_username(strategy, details, backend, *args, **kwargs)
    }

def create_user(backend, strategy, details, user=None, *args, **kwargs):
    """
    Create user if it doesn't exist.
    This pipeline is called when a new user authenticates via social auth.
    """
    if user:
        return {'is_new': False}
    
    if not kwargs.get('email'):
        return None

    email = kwargs.get('email')
    username = kwargs.get('username', email.split('@')[0])
    
    # Check if user with this email already exists
    try:
        existing_user = User.objects.get(email=email)
        # Update the user's social auth details if needed
        if not existing_user.first_name and details.get('first_name'):
            existing_user.first_name = details.get('first_name')
        if not existing_user.last_name and details.get('last_name'):
            existing_user.last_name = details.get('last_name')
        existing_user.save()
        
        return {
            'user': existing_user,
            'is_new': False
        }
    except User.DoesNotExist:
        pass
    
    # Get customer role (default role for all users)
    customer_role, _ = Role.objects.get_or_create(role_name='customer')
    
    # Create new user with all available details
    user = User.objects.create_user(
        username=username,
        email=email,
        role=customer_role,
        first_name=details.get('first_name', ''),
        last_name=details.get('last_name', ''),
        is_active=True
    )
    
    # If we have additional details from Google, save them
    if 'picture' in kwargs.get('response', {}):
        user.profile_picture = kwargs['response']['picture']
        user.save()

    # Ensure the user is saved and the session is created
    strategy.session_set('user_id', user.id)
    
    return {
        'user': user,
        'is_new': True
    }

def update_user_details(backend, strategy, details, user=None, *args, **kwargs):
    """
    Update user details from social auth data and ensure session is maintained.
    """
    if not user or not details:
        return
        
    changed = False
    
    # Update user details if they're empty
    if not user.first_name and details.get('first_name'):
        user.first_name = details.get('first_name')
        changed = True
    
    if not user.last_name and details.get('last_name'):
        user.last_name = details.get('last_name')
        changed = True
    
    # Update profile picture if available
    if 'picture' in kwargs.get('response', {}) and not user.profile_picture:
        user.profile_picture = kwargs['response']['picture']
        changed = True
        
    if changed:
        user.save()
    
    # Ensure the session is maintained
    strategy.session_set('user_id', user.id)
    
    return {
        'user': user,
        'changed': changed
    } 