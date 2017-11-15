from django.db import models

from mep.common.models import Notable
from mep.people.models import Person, Address
from django.core.exceptions import ObjectDoesNotExist

class Account(models.Model):
    '''Central model for all account and related information, M2M explicity to
    :class:`people.Person`'''

    persons = models.ManyToManyField(Person, blank=True)  # ? how can this be optional?
    addresses = models.ManyToManyField(
        Address,
        through='AccountAddress',
        blank=True
    )

    def __repr__(self):
        return '<Account %s>' % self.__dict__

    def __str__(self):
        if not self.persons.exists() and not self.addresses.exists():
            return 'Account #%s' % self.pk
        if self.persons.exists():
            return 'Account #%s: %s' % (
                self.pk,
                ', '.join(person.name for person in self.persons.all())
            )
        if self.addresses.exists():
            return 'Account #%s: %s' % (
                self.pk,
                '; '.join(address.name if address.name else
                          address.street_address if address.street_address else
                          address.city for address in
                          self.addresses.all().order_by(
                          'city', 'street_address', 'name'))
        )

    class Meta:
        ordering = ('persons__sort_name',)

    def list_persons(self):
        '''List :class:`mep.people.models.Person` instances associated with this
        account.
        '''
        return ', '.join(person.name for
                         person in self.persons.all().order_by('name'))
    list_persons.short_description = 'Associated persons'

    def list_addresses(self):
        '''List :class:`mep.people.models.Address` instances associated with
        this account.
        '''
        return '; '.join(
            address.name if address.name
            else address.street_address if address.street_address
            else address.city for address in
            self.addresses.all().order_by('name', 'street_address')
        )
    list_addresses.short_description = 'Associated addresses'

    def add_event(self, etype='event', **kwargs):
        '''Helper function to add a :class:`Event` or subclass to an
        instance of :class:`Account`. Requires that the :class:`Account`
        object be saved first (so it has a set primary key).
        This provides functionality normally in the ``self.*_set``
        functionality of Django, but not provided with subclassed
        table inheritence.

       :param etype: ``str``
            One of ``borrow``, ``event``, ``subscribe``,
            ``purchase``, ``reimbursement``
        '''
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscribe',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscribe, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscribe': Subscribe
        }
        str_to_model[etype].objects.create(account=self, **kwargs)

    def get_events(self, etype='event', **kwargs):
        '''Helper function to retrieve related events of any valid type for
        :class:`Account.add_event()`. This provides functionality normally in the
        ``self.*_set`` functionality, but not provided with subclassed
        table inheritence.

        :param etype: ``str``
            One of ``borrow``, ``event``, ``subscribe``,
            ``purchase``, ``reimbursement``

        :Keyword Arguments:
            Any valid query kwargs for :class:`Account`, defaults to equivalent
            of ``Foo.objects.all()``.

        '''
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscribe',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscribe, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscribe': Subscribe
        }

        if not kwargs:
            return str_to_model[etype].objects.filter(account=self)

        return str_to_model[etype].objects.filter(account=self, **kwargs)


class AccountAddress(Notable):
    '''Through model for :class:`Account` and :class:`Address` that supplies
    start and end dates, as well as a c/o person.'''
    care_of_person = models.ForeignKey(Person, blank=True, null=True)
    account = models.ForeignKey(Account)
    address = models.ForeignKey(Address)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __repr__(self):
        return '<AccountAddress %s>' % self.__dict__

    def __str__(self):
        '''This is a through model, so the str representation is minimal'''
        return 'Account #%s - Address #%s' % (self.account.pk, self.address.pk)

    class Meta:
        verbose_name = 'Account-address association'


class Event(Notable):
    '''Base table for events in the Shakespeare and Co. Lending Library'''
    account = models.ForeignKey(Account)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # These provide generic string representation for the Event class
    # and its subclasses
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.__dict__)

    def __str__(self):
        return '%s for account #%s' % (self.__class__.__name__,
                                      self.account.pk)

    @property
    def event_type(self):
        try:
            subscribe = self.subscribe
            if subscribe.modification:
                return subscribe.get_modification_display()
            return 'Subscribe'
        except ObjectDoesNotExist:
            pass
        try:
            self.reimbursement
            return 'Reimbursement'
        except ObjectDoesNotExist:
            pass
        return 'Generic'


USD = 'USD'
FRF = 'FRF'
GBP = 'GBP'
# NOTE: Tentative set for testing
CURRENCY_CHOICES = (
    ('', '----'),
    (USD, 'US Dollar'),
    (FRF, 'French Franc'),
    (GBP, 'British Pound')
)


class Subscribe(Event):
    '''Records subscription events in the MEP database'''
    duration = models.DecimalField(
        max_digits=4, decimal_places=2,
        blank=True, null=True,
        help_text=('Duration in months. Weeks may be noted with '
                   'fractions in decimal form.')
    )
    volumes = models.DecimalField(blank=True, null=True, max_digits=4,
        decimal_places=2,
        help_text='Number of volumes for checkout')
    A = 'A'
    B = 'B'
    A_B = 'A+B'
    ADL = 'AdL'
    STU = 'Stu'
    PROF = 'Prof'
    OTHER = 'Oth'

    SUB_TYPE_CHOICES = (
        (A, 'A'),
        (B, 'B'),
        (A_B, 'A+B'),
        (ADL, 'AdL'),
        (STU, 'Student'),
        (PROF, 'Professor'),
        (OTHER, 'Other')
    )
    sub_type = models.CharField(max_length=255, verbose_name='type', blank=True,
        choices=SUB_TYPE_CHOICES)
    # NOTE: Using decimal field to take advantage of Python's decimal handling
    # Can store up to 99999999.99 -- which is *probably* safe.
    price_paid = models.DecimalField(max_digits=10, decimal_places=2,
        blank=True, null=True)
    deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    currency = models.CharField(max_length=3, blank=True, choices=CURRENCY_CHOICES)

    SUPPLEMENT = 'sup'
    RENEWAL = 'ren'

    MODIFICATION_CHOICES = (
        ('', '----'),
        (SUPPLEMENT, 'Supplement'),
        (RENEWAL, 'Renewal'),
    )
    modification = models.CharField(
        max_length=50,
        blank=True,
        choices=MODIFICATION_CHOICES,
        help_text='Use to indicate supplement or renewal.'
    )


class Borrow(Event):
    '''Inherited table indicating borrow events'''
    # NOTE: Renamed to avoid field conflict with the table inheritences
    # The related_name should keep related queries consistently framed
    purchase_id = models.ForeignKey(
        'Purchase',
        blank=True,
        null=True,
        verbose_name='purchase',
        related_name='purchase'
    )


class Purchase(Event):
    '''Inherited table indicating purchase events'''
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        blank=True,
        choices=CURRENCY_CHOICES
    )
    item = models.ForeignKey('books.Item')


class Reimbursement(Event):
    '''Inherited table indicating reimbursement events'''
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True,
        blank=True)
    currency = models.CharField(
        max_length=3,
        blank=True,
        choices=CURRENCY_CHOICES
    )
