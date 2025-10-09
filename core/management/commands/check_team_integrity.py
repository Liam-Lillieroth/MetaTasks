from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from services.cflows.models import TeamBooking
from core.models import Team


class Command(BaseCommand):
    help = 'Check for teams with bookings but no active members'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix teams with no members by assigning organization admins',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about affected bookings',
        )

    def handle(self, *args, **options):
        # Find teams that have bookings but no active members
        problematic_teams = Team.objects.annotate(
            booking_count=Count('cflows_bookings'),
            active_member_count=Count('members', filter=Q(members__is_active=True))
        ).filter(
            booking_count__gt=0,
            active_member_count=0
        )

        if not problematic_teams.exists():
            self.stdout.write(
                self.style.SUCCESS('✓ All teams with bookings have at least one active member')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'Found {problematic_teams.count()} teams with bookings but no active members:')
        )

        for team in problematic_teams:
            booking_count = TeamBooking.objects.filter(team=team).count()
            self.stdout.write(f'\n• Team: {team.name} (ID: {team.id})')
            self.stdout.write(f'  Organization: {team.organization.name}')
            self.stdout.write(f'  Bookings: {booking_count}')
            
            if options['verbose']:
                bookings = TeamBooking.objects.filter(team=team).order_by('-start_time')[:5]
                self.stdout.write('  Recent bookings:')
                for booking in bookings:
                    status = "Completed" if booking.is_completed else "Active/Upcoming"
                    self.stdout.write(f'    - {booking.start_time.strftime("%Y-%m-%d %H:%M")} ({status})')

            if options['fix']:
                # Try to find organization admins to add to the team
                org_admins = team.organization.members.filter(
                    is_organization_admin=True,
                    is_active=True
                )
                
                if org_admins.exists():
                    admin = org_admins.first()
                    team.members.add(admin)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Added {admin.user.username} to team {team.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ No organization admins found for {team.organization.name}')
                    )

        if not options['fix']:
            self.stdout.write(
                self.style.WARNING('\nRun with --fix to automatically add organization admins to these teams.')
            )