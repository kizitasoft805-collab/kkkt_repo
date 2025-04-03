from django.db import migrations

def update_phone_numbers(apps, schema_editor):
    ChurchMember = apps.get_model('members', 'ChurchMember')
    for member in ChurchMember.objects.all():
        # Remove the '+' sign from phone numbers
        if member.phone_number.startswith('+'):
            member.phone_number = member.phone_number[1:]
        if member.emergency_contact_phone.startswith('+'):
            member.emergency_contact_phone = member.emergency_contact_phone[1:]
        member.save()

class Migration(migrations.Migration):
    dependencies = [
        ('members', '0009_churchmember_apostolic_movement_and_more'),  # Replace with the correct parent migration
    ]

    operations = [
        migrations.RunPython(update_phone_numbers),
    ]
