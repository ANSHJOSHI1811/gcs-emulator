"""
IAM CLI commands for gcloud compatibility
Provides command-line interface for managing IAM resources
"""
import click
from flask import current_app
from app.services.iam_service import ServiceAccountService, RoleService, IAMPolicyService
from tabulate import tabulate


@click.group()
def iam():
    """IAM commands for managing service accounts, roles, and policies"""
    pass


@iam.group()
def service_accounts():
    """Manage service accounts"""
    pass


@service_accounts.command('list')
@click.option('--project', default='my-project', help='Project ID')
def list_service_accounts(project):
    """List service accounts"""
    service = ServiceAccountService()
    accounts = service.list_service_accounts(project)
    
    if not accounts:
        click.echo("No service accounts found.")
        return
    
    table_data = [
        [
            sa.email,
            sa.display_name or '',
            'DISABLED' if sa.disabled else 'ACTIVE',
            sa.unique_id
        ]
        for sa in accounts
    ]
    
    headers = ['EMAIL', 'DISPLAY NAME', 'STATUS', 'UNIQUE ID']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))


@service_accounts.command('create')
@click.argument('account_id')
@click.option('--project', default='my-project', help='Project ID')
@click.option('--display-name', help='Display name for the service account')
@click.option('--description', help='Description of the service account')
def create_service_account(account_id, project, display_name, description):
    """Create a service account"""
    service = ServiceAccountService()
    
    try:
        account = service.create_service_account(
            project_id=project,
            account_id=account_id,
            display_name=display_name,
            description=description
        )
        click.echo(f"Created service account: {account.email}")
        click.echo(f"Unique ID: {account.unique_id}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@service_accounts.command('delete')
@click.argument('email')
def delete_service_account(email):
    """Delete a service account"""
    service = ServiceAccountService()
    
    if not click.confirm(f"Delete service account {email}?"):
        return
    
    try:
        service.delete_service_account(email)
        click.echo(f"Deleted service account: {email}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@service_accounts.command('describe')
@click.argument('email')
def describe_service_account(email):
    """Describe a service account"""
    service = ServiceAccountService()
    
    try:
        account = service.get_service_account(email)
        if not account:
            click.echo(f"Service account {email} not found.", err=True)
            return 1
        
        click.echo(f"Email: {account.email}")
        click.echo(f"Display Name: {account.display_name or 'N/A'}")
        click.echo(f"Description: {account.description or 'N/A'}")
        click.echo(f"Project ID: {account.project_id}")
        click.echo(f"Unique ID: {account.unique_id}")
        click.echo(f"OAuth2 Client ID: {account.oauth2_client_id or 'N/A'}")
        click.echo(f"Status: {'DISABLED' if account.disabled else 'ACTIVE'}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@service_accounts.command('disable')
@click.argument('email')
def disable_service_account(email):
    """Disable a service account"""
    service = ServiceAccountService()
    
    try:
        service.disable_service_account(email)
        click.echo(f"Disabled service account: {email}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@service_accounts.command('enable')
@click.argument('email')
def enable_service_account(email):
    """Enable a service account"""
    service = ServiceAccountService()
    
    try:
        service.enable_service_account(email)
        click.echo(f"Enabled service account: {email}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@iam.group()
def keys():
    """Manage service account keys"""
    pass


@keys.command('list')
@click.argument('email')
def list_keys(email):
    """List service account keys"""
    service = ServiceAccountService()
    
    try:
        key_list = service.list_keys(email)
        
        if not key_list:
            click.echo("No keys found.")
            return
        
        table_data = [
            [
                key.id.split('/')[-1],
                key.key_algorithm,
                key.key_type,
                'DISABLED' if key.disabled else 'ACTIVE'
            ]
            for key in key_list
        ]
        
        headers = ['KEY ID', 'ALGORITHM', 'TYPE', 'STATUS']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@keys.command('create')
@click.argument('email')
@click.option('--key-file-type', default='json', help='Key file type (json)')
def create_key(email, key_file_type):
    """Create a service account key"""
    service = ServiceAccountService()
    
    try:
        key = service.create_key(email)
        click.echo(f"Created key: {key.id}")
        
        if key.private_key_data:
            import base64
            key_data = base64.b64decode(key.private_key_data).decode('utf-8')
            
            # Save to file
            filename = f"{email.split('@')[0]}-key.json"
            with open(filename, 'w') as f:
                f.write(key_data)
            
            click.echo(f"Private key saved to: {filename}")
            click.echo("WARNING: Keep this key secure and do not share it!")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@keys.command('delete')
@click.argument('key_id')
def delete_key(key_id):
    """Delete a service account key"""
    service = ServiceAccountService()
    
    if not click.confirm(f"Delete key {key_id}?"):
        return
    
    try:
        service.delete_key(key_id)
        click.echo(f"Deleted key: {key_id}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@iam.group()
def roles():
    """Manage IAM roles"""
    pass


@roles.command('list')
@click.option('--project', help='Project ID (for custom roles)')
def list_roles(project):
    """List IAM roles"""
    service = RoleService()
    
    try:
        role_list = service.list_roles(project)
        
        if not role_list:
            click.echo("No roles found.")
            return
        
        table_data = [
            [
                role.name,
                role.title,
                'Custom' if role.is_custom else 'Predefined',
                role.stage,
                len(role.included_permissions)
            ]
            for role in role_list
        ]
        
        headers = ['NAME', 'TITLE', 'TYPE', 'STAGE', 'PERMISSIONS']
        click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@roles.command('create')
@click.argument('role_id')
@click.option('--project', default='my-project', help='Project ID')
@click.option('--title', required=True, help='Role title')
@click.option('--description', help='Role description')
@click.option('--permissions', help='Comma-separated list of permissions')
def create_role(role_id, project, title, description, permissions):
    """Create a custom role"""
    service = RoleService()
    
    try:
        perm_list = []
        if permissions:
            perm_list = [p.strip() for p in permissions.split(',')]
        
        role = service.create_role(
            project_id=project,
            role_id=role_id,
            title=title,
            description=description,
            included_permissions=perm_list
        )
        click.echo(f"Created role: {role.name}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@roles.command('describe')
@click.argument('role_name')
def describe_role(role_name):
    """Describe a role"""
    service = RoleService()
    
    try:
        role = service.get_role(role_name)
        if not role:
            click.echo(f"Role {role_name} not found.", err=True)
            return 1
        
        click.echo(f"Name: {role.name}")
        click.echo(f"Title: {role.title}")
        click.echo(f"Description: {role.description or 'N/A'}")
        click.echo(f"Type: {'Custom' if role.is_custom else 'Predefined'}")
        click.echo(f"Stage: {role.stage}")
        click.echo(f"Deleted: {role.deleted}")
        click.echo(f"\nIncluded Permissions ({len(role.included_permissions)}):")
        for perm in role.included_permissions:
            click.echo(f"  - {perm}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


@roles.command('delete')
@click.argument('role_name')
def delete_role(role_name):
    """Delete a custom role"""
    service = RoleService()
    
    if not click.confirm(f"Delete role {role_name}?"):
        return
    
    try:
        service.delete_role(role_name)
        click.echo(f"Deleted role: {role_name}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return 1


def register_iam_commands(app):
    """Register IAM CLI commands with Flask app"""
    app.cli.add_command(iam)
