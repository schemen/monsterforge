from django.core.management.base import BaseCommand, CommandError
from paperminis.models import User, Creature, Bestiary

class Command(BaseCommand):
    help = 'List a number of stats'

    def handle(self, *args, **options):
            # Get all users
            total_users = User.objects.count()

            # Get all temp Users
            temp_users = User.objects.filter(groups__name='temp').count()

            # Get all monsters
            total_creatures = Creature.objects.count()
            ddb_creature = Creature.objects.filter(from_ddb=True).count()
            # Get all bestiaries
            total_bestiary = Bestiary.objects.count()
            ddb_bestiary = Bestiary.objects.filter(from_ddb=True).count()



            self.stdout.write(self.style.SUCCESS('USER STATS'))
            self.stdout.write(self.style.SUCCESS('Signed up users: %s' % str(total_users - temp_users)))
            self.stdout.write(self.style.SUCCESS('Temporary Users: %s' % str(temp_users)))
            self.stdout.write(self.style.SUCCESS('Total: %i\n' % total_users))
            self.stdout.write(self.style.SUCCESS('BESTIARY STATS'))
            self.stdout.write(self.style.SUCCESS('Total: %i' % total_bestiary))
            self.stdout.write(self.style.SUCCESS('From D&DBeyond: %i\n' % ddb_bestiary))
            self.stdout.write(self.style.SUCCESS('CREATURE STATS'))
            self.stdout.write(self.style.SUCCESS('Total: %i' % total_creatures))
            self.stdout.write(self.style.SUCCESS('From D&DBeyond: %i\n' % ddb_creature))
