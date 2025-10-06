import os
import sys
import json
import django
from django.conf import settings
from django.db.models import Q

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nacos.settings')
django.setup()

from nacos_app.models import CustomUser

def import_users(json_file):
    total_imported = 0
    total_skipped = 0
    total_existing = 0
    
    try:
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)
            members = data.get('Members', {})
            for index, user_data in members.items():
                reg = user_data.get('reg')
                email = user_data.get('email')
                matric = user_data.get('matric')
                
                if not reg:
                    print(f'Skipping user {index}: No NACOS ID provided')
                    total_skipped += 1
                    continue
                
                # Check if user exists by reg, email, or matric
                existing_user = CustomUser.objects.filter(
                    Q(membership_id=reg) | Q(email=email) | Q(matric=matric)
                ).first()
                
                if existing_user:
                    print(f'User with reg {reg}, email {email}, or matric {matric} already exists: {existing_user.username}')
                    total_existing += 1
                    continue
                
                user = CustomUser(
                    username=reg,  # Use reg as username
                    email=email or '',
                    first_name=user_data.get('firstname', ''),
                    surname=user_data.get('surname', ''),
                    other_names=user_data.get('othernames', ''),
                    membership_id=reg,
                    firebase_uid=user_data.get('index', ''),
                    is_migrated=True,
                    matric=matric or '',
                    level=user_data.get('level', ''),
                    course=user_data.get('course', ''),
                    clubs=user_data.get('clubs', []),
                    phone=user_data.get('phone', ''),
                    address=user_data.get('address', ''),
                    lga=user_data.get('LGA', ''),
                    state=user_data.get('state', ''),
                    sex=user_data.get('sex', ''),
                    hobby=user_data.get('hubby', ''),
                    denomination=user_data.get('denom', ''),
                    parent_phone=user_data.get('parentphone', ''),
                    mother_name=user_data.get('mother', ''),
                    room=user_data.get('room', ''),
                )
                user.set_unusable_password()  # Set unusable password for lazy migration
                user.save()
                print(f'Imported user: {user.username}')
                total_imported += 1
    
        print('\nImport Summary:')
        print(f'Total users imported: {total_imported}')
        print(f'Total users skipped (no NACOS ID): {total_skipped}')
        print(f'Total users already existing: {total_existing}')
        print(f'Total users in database: {CustomUser.objects.count()}')
        print(f'Total migrated users: {CustomUser.objects.filter(is_migrated=True).count()}')
    
    except FileNotFoundError:
        print(f'Error: File {json_file} not found')
    except json.JSONDecodeError:
        print(f'Error: Invalid JSON format in {json_file}')
    except Exception as e:
        print(f'Error: {str(e)}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python import_users.py <path_to_json_file>')
        sys.exit(1)
    import_users(sys.argv[1])