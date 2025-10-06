import json
from django.core.management.base import BaseCommand
from nacos_app.models import CustomUser

class Command(BaseCommand):
    help = 'Import users from Firebase JSON export'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to Firebase JSON export')

    def handle(self, *args, **options):
        with open(options['json_file'], encoding='utf-8') as f:
            data = json.load(f)
            members = data.get('Members', {})
            for index, user_data in members.items():
                email = user_data.get('email')
                if not email:
                    self.stdout.write(self.style.WARNING(f'Skipping user {index}: No email provided'))
                    continue
                
                user, created = CustomUser.objects.get_or_create(
                    username=email,  # Use email as username
                    defaults={
                        'email': email,
                        'first_name': user_data.get('firstname', ''),
                        'last_name': user_data.get('surname', ''),
                        'membership_id': user_data.get('reg', ''),
                        'firebase_uid': user_data.get('index', ''),
                        'is_migrated': True,
                        'matric': user_data.get('matric', ''),
                        'level': user_data.get('level', ''),
                        'course': user_data.get('course', ''),
                        'clubs': user_data.get('clubs', []),
                        'phone': user_data.get('phone', ''),
                        'address': user_data.get('address', ''),
                        'lga': user_data.get('LGA', ''),
                        'state': user_data.get('state', ''),
                        'sex': user_data.get('sex', ''),
                        'hobby': user_data.get('hubby', ''),
                        'denomination': user_data.get('denom', ''),
                        'parent_phone': user_data.get('parentphone', ''),
                        'mother_name': user_data.get('mother', ''),
                        'room': user_data.get('room', ''),
                    }
                )
                if created:
                    user.set_unusable_password()  # Set unusable password for lazy migration
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'Imported user: {user.username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'User {user.username} already exists'))