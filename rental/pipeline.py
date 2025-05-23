from django.contrib.auth import get_user_model
from .models import Role

User = get_user_model()

def create_user(backend, user=None, *args, **kwargs):
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
        return {
            'user': existing_user,
            'is_new': False
        }
    except User.DoesNotExist:
        pass
    
    # Get customer role (default role for all users)
    customer_role, _ = Role.objects.get_or_create(role_name='customer')
    
    # Create new user
    user = User.objects.create_user(
        username=username,
        email=email,
        role=customer_role,
        # Extract first name and last name if provided by Google
        first_name=kwargs.get('details', {}).get('first_name', ''),
        last_name=kwargs.get('details', {}).get('last_name', ''),
    )

    return {
        'user': user,
        'is_new': True
    }

def update_user_details(backend, user=None, details=None, *args, **kwargs):
    """
    Update user details from social auth data.
    """
    if not user or not details:
        return
        
    changed = False
    
    # Update first_name if it's empty
    if not user.first_name and details.get('first_name'):
        user.first_name = details.get('first_name')
        changed = True
    
    # Update last_name if it's empty
    if not user.last_name and details.get('last_name'):
        user.last_name = details.get('last_name')
        changed = True
        
    if changed:
        user.save() 