"""
Manage.py command to import logbooks from MEP XML. Example usage::

    python manage.py import_logbooks /path/to/logbooks/

Accounts are created for any existing or new people not already imported
into the personography. Any new people are also created with a stub entry that
can later be manually expanded.

See :meth:`mep.accounts.xml_models.XmlEvent.to_db_event` for detailed info
on the import process.
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from mep.accounts.xml_models import LogBook
from mep.accounts.models import Event, Subscribe, Reimbursement

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Import logbooks from XML documents"""
    help = __doc__

    def add_arguments(self, parser):

        parser.add_argument('file_list', nargs="*",
            help='list of path names containting XML logbooks')

    def get_totals(self):
        return {
            'events': Event.objects.count(),
            'subscriptions': Subscribe.objects.exclude(modification=Subscribe.RENEWAL).exclude(
                modification=Subscribe.SUPPLEMENT).count(),
            'renewals': Subscribe.objects.filter(modification=Subscribe.RENEWAL).count(),
            'reimbursements': Reimbursement.objects.count(),
            'supplements': Subscribe.objects.filter(modification=Subscribe.SUPPLEMENT).count()
        }

    def summarize(self, start_totals):
        new_totals = self.get_totals()
        for i in ['events', 'subscriptions', 'renewals', 'reimbursements',
                  'supplements']:
            self.stdout.write('%d %s added (%d total)\n' %
                (new_totals[i] - start_totals[i], i, new_totals[i]))

    def handle(self, *args, **kwargs):
        totals = self.get_totals()
        files = kwargs['file_list']
        for f in files:
            log = LogBook.from_file(f)
            self.stdout.write('%s: %s' % (f, len(log.days)))
            for day in log.days:
                for event in day.events:
                    try:
                        event.to_db_event(day.date)
                    except Exception as err:
                        self.stdout.write(
                        self.style.WARNING(
                            '%s, on %s' % (err, day.date)
                        )
                    )
        self.summarize(totals)

