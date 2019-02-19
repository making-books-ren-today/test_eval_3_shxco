'''
Manage command to import lending card data from MEP XML.  Example usage::

    python manage.py import_cards  /path/to/transcriptions/cards/

The command expects to be given the cards directory in the MEP XML
GitHub data, and will find all xml files under it, including in
subdirectories.

Finds associated people and their accounts (if no account exists,
it will be created if possible) and then processes xml borrowing events
and adds them to the account.

'''


from collections import defaultdict
import glob
import os.path

from django.core.management.base import BaseCommand
from eulxml import xmlmap

from mep.accounts.models import Account
from mep.accounts.xml_models import LendingCard
from mep.people.models import Person
from mep.footnotes.models import SourceType, Bibliography


class Command(BaseCommand):
    """Import lending card data from XML documents"""
    help = __doc__

    v_normal = 1

    stats = defaultdict(int)

    #: base path for image urls referenced in the xml
    image_base_url = 'https://diglib.princeton.edu/tools/ib/'

    def add_arguments(self, parser):
        parser.add_argument('path',
            help='base path containing folders of lending card XML files')

    def handle(self, *args, **kwargs):
        search_path = os.path.join(kwargs['path'], '**', '*.xml')
        verbosity = kwargs['verbosity']

        cardfiles = glob.iglob(search_path, recursive=True)

        # initialize values that might not get set, for use in format output
        self.stats['accounts_created'] = 0
        self.stats['skipped'] = 0

        self.lending_card_sourcetype = SourceType.objects \
            .get_or_create(name='Lending Library Card')[0]

        for i, card_file in enumerate(cardfiles):
            self.stats['files'] += 1

            lcard = xmlmap.load_xmlobject_from_file(card_file, LendingCard)

            # special cases (mostly for organizations not tagged as persons, no ids)
            if not lcard.cardholders:
                self.stdout.write(self.style.WARNING(
                    'No cardholder found - %s' % card_file))
                self.stats['skipped'] += 1
                continue
            elif not lcard.cardholders[0].mep_id:
                # id missing for libraries des deux lycee...
                self.stdout.write(self.style.WARNING(
                    'No MEP id for cardholder %s - %s' %
                    (lcard.cardholders[0].name, card_file)))
                self.stats['skipped'] += 1
                continue

            # output file name, cardholders, and number of borrowing events
            # when running in verbose mode
            cardholders = ', '.join(['%s %s' % (cardholder.mep_id, cardholder.name)
                                     for cardholder in lcard.cardholders])
            if verbosity > self.v_normal:
                self.stdout.write('%s: %s' % (card_file, cardholders))
                self.stdout.write('%d borrowing events' % len(lcard.borrowing_events))
            self.stats['card_holders'] += len(lcard.cardholders)
            self.stats['borrow_events'] += len(lcard.borrowing_events)

            account = None
            # more than one cardholder in a single file means there are
            # multiple accounts represented and the accound needs to be
            # determined based on person name on each side
            multiple_cardholders = len(lcard.cardholders) > 1

            # get account records for all cardholders in the file
            # create dictionary of accounts keyed on mepid to handle multiple
            accounts = {}
            for cardholder in lcard.cardholders:
                account = self.get_account(cardholder.mep_id, card_file)
                if account:
                    self.add_card_citation(account, cardholder)
                    accounts[cardholder.mep_id] = account

            # if all cardholders are not found, skip
            if not len(accounts.values()) == len(lcard.cardholders):
                self.stdout.write(self.style.WARNING('Couldn\'t find or generate accounts for all cardholders' \
                        % (lcard.cardholders[0].name, card_file)))
                self.stats['skipped'] += 1
                continue

            # if not dealing with a file with multiple card holders,
            # set the default account
            if not multiple_cardholders:
                account = list(accounts.values())[0]

            # document expected number of borrowing events as a sanity
            # check to make sure they are all found when iterating card by card
            expected = len(lcard.borrowing_events)
            current = self.stats['borrow_created']
            # iterate through card sides
            for side in lcard.sides:
                # if there are multiple card holders for this file,
                # get the account based on the person name on the card
                # print(side.facsimile_id)
                # print(lcard.image_path(page.facsimile_id))

                if multiple_cardholders and side.cardholders:
                    account = accounts[side.cardholders[0].mep_id]
                    # if multiple and no card holders on this side,
                    # continue with previous account

                # add image path to the notes for the appropriate account
                account.card.notes += '\n%s%s' % \
                    (self.image_base_url, lcard.image_path(side.facsimile_id))

                # then iterate through borrowing events and associate with the acount
                for xml_borrow in side.borrowing_events:
                    borrow = xml_borrow.to_db_event(account)
                    borrow.save()
                    borrow.footnotes.create(bibliography=account.card,
                        location=''.join([self.image_base_url,
                                          lcard.image_path(side.facsimile_id)]),
                        is_agree=True)
                    self.stats['borrow_created'] += 1

            # save account citation with image paths
            for account in accounts.values():
                account.card.save()

            # check that we found the expected number of borrowing events
            if self.stats['borrow_created'] - current != expected:
                self.stdout.write(self.style.WARNING(
                    'Borrowing event mismatch for %s; expected %d but got %d' \
                    % (card_file, expected, self.stats['borrow_created'] - current)))

            # skip after processing max number
            # NOTE: could add configurable max records option for testing
            # if i > 30:
                # break

        # summarize what was done
        self.stdout.write('''\nSummary:
{files:,} files processed
{card_holders:,} card holders
{accounts:,} accounts found; {accounts_created:,} accounts created
{borrow_events:,} borrowing events found in XML
{borrow_created:,} borrowing events created
{skipped:,} files skipped
'''.format(**self.stats))

    def get_account(self, mep_id, card_file):
        '''Find a library account for a person based on MEP id.  If the account
         does not exist, find the person and create it.  If the person does not
         exist, print a warning.'''
        try:
            account = Account.objects.get(persons__mep_id=mep_id)
            self.stats['accounts'] += 1
            return account
        except Account.DoesNotExist:
            # if account does not exist, find person and create the account
            try:
                person = Person.objects.get(mep_id=mep_id)
                account = Account.objects.create()
                account.persons.add(person)
                self.stats['accounts_created'] += 1
                return account
            except Person.DoesNotExist:
                self.stdout.write(self.style.WARNING('Person not found for %s\n%s' \
                            % (mep_id, card_file)))
                return
        except Account.MultipleObjectsReturned:
            self.stdout.write(self.style.ERROR('Multiple accounts found for %s\n%s' \
                            % (mep_id, card_file)))
            return

    def add_card_citation(self, account, cardholder):
        # if account already has a card, do nothing
        if account.card:
            return

        # construct new reference bibliography and associate with the account
        reference = 'Sylvia Beach, %s Lending Library Card' % cardholder.name + \
            ', Box 43, Sylvia Beach Papers, Department of Rare Books ' + \
            'and Special Collections, Princeton University Library.'

        # add images label; actual image paths will be added when
        # iterating through the sections of the file
        notes = 'Images:'

        account.card = Bibliography.objects.create(bibliographic_note=reference,
            source_type=self.lending_card_sourcetype, notes=notes)
        account.save()


