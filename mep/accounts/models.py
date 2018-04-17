# -*- coding: utf-8 -*-
import re
import datetime

from cached_property import cached_property
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import ValidationError
from django.db import models
from django.template.defaultfilters import pluralize
from flags import Flags

from mep.books.models import Item
from mep.common.models import Named, Notable
from mep.people.models import Person, Location


class Account(models.Model):
    '''Central model for all account and related information, M2M explicity to
    :class:`people.Person`'''

    persons = models.ManyToManyField(Person, blank=True,
        verbose_name='Account holder(s)')
    # convenience access to associated locations, although
    # we will probably use Address for most things
    locations = models.ManyToManyField(Location, through='Address', blank=True)

    def __repr__(self):
        return '<Account %s>' % self.__dict__

    def __str__(self):
        if not self.persons.exists() and not self.locations.exists():
            return 'Account #%s' % self.pk
        if self.persons.exists():
            return 'Account #%s: %s' % (
                self.pk,
                ', '.join(person.name for person in self.persons.all())
            )
        if self.locations.exists():
            return 'Account #%s: %s' % (
                self.pk,
                '; '.join(address.name if address.name else
                          address.street_address if address.street_address else
                          address.city for address in
                          self.locations.all().order_by(
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
    list_persons.short_description = 'Account holder(s)'

    def earliest_date(self):
        '''Earliest known date from all events associated with this account'''
        evt = self.event_set.order_by('start_date').first()
        if evt:
            return evt.start_date

    def last_date(self):
        '''Last known date from all events associated with this account'''

        # sort by end date then start date; if end dates are missing this
        # may not be quite right...
        evt = self.event_set.order_by('end_date', 'start_date').last()
        if evt:
            # if no end date is present, return start date
            return evt.end_date or evt.start_date

    @property
    def subscription_set(self):
        '''associated subscription events, as queryset of :class:`Subscription`'''
        return Subscription.objects.filter(account_id=self.id)

    def list_locations(self):
        '''List of associated :class:`mep.people.models.Location` '''
        return '; '.join([str(loc) for loc in self.locations.distinct()])
    list_locations.short_description = 'Locations'

    def add_event(self, etype='event', **kwargs):
        '''Helper function to add a :class:`Event` or subclass to an
        instance of :class:`Account`. Requires that the :class:`Account`
        object be saved first (so it has a set primary key).
        This provides functionality normally in the ``self.*_set``
        functionality of Django, but not provided with subclassed
        table inheritence.

       :param etype: ``str``
            One of ``borrow``, ``event``, ``subscription``,
            ``purchase``, ``reimbursement``
        '''
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscription',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscription, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscription': Subscription
        }
        str_to_model[etype].objects.create(account=self, **kwargs)

    def get_events(self, etype='event', **kwargs):
        '''Helper function to retrieve related events of any valid type for
        :class:`Account.add_event()`. This provides functionality normally in the
        ``self.*_set`` functionality, but not provided with subclassed
        table inheritence.

        :param etype: ``str``
            One of ``borrow``, ``event``, ``subscription``,
            ``purchase``, ``reimbursement``

        :Keyword Arguments:
            Any valid query kwargs for :class:`Account`, defaults to equivalent
            of ``Foo.objects.all()``.

        '''
        # Catch an invalid class of event or subevent
        etype = etype.lower()
        if etype not in ['borrow', 'event', 'subscription',
                         'purchase', 'reimbursement']:
            raise ValueError('etype must be one of borrow, event, purchase,'
                             ' subscription, or reimbursement')

        str_to_model = {
            'borrow': Borrow,
            'reimbursement': Reimbursement,
            'event': Event,
            'purchase': Purchase,
            'subscription': Subscription
        }

        if not kwargs:
            return str_to_model[etype].objects.filter(account=self)

        return str_to_model[etype].objects.filter(account=self, **kwargs)


class Address(Notable):
    '''Address associated with an :class:`Account` or
    a :class:`~mep.people.models.Person`.  Used to associate locations with
    people and accounts, with optional start and end dates and a care/of person.'''
    location = models.ForeignKey(Location)
    account = models.ForeignKey(Account, blank=True, null=True,
        help_text='Associated library account')
    person = models.ForeignKey(Person, blank=True, null=True,
        help_text='For personal addresses not associated with library accounts.')
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    care_of_person = models.ForeignKey(Person, blank=True, null=True,
        related_name='care_of_addresses')

    class Meta:
        verbose_name_plural = 'Addresses'

    def __repr__(self):
        return '<Address %s>' % self.__dict__

    def __str__(self):
        dates = care_of = ''
        if self.start_date or self.end_date:
            dates = ' (%s)' % '-'.join([date.strftime('%Y') if date else ''
                for date in [self.start_date, self.end_date]])
        if self.care_of_person:
            care_of = ' c/o %s' % self.care_of_person

        # NOTE: this is potentially redundant if account has only a
        # location and not a name
        return '%s - %s%s%s' % (self.location, self.account or self.person,
            dates, care_of)

    def clean(self):
        '''Validate to require one and only one of :class:`Account` or
        :class:`~mep.people.models.Person`'''
        if not self.account and not self.person:
            raise ValidationError('Address must be associated with an account or person')
        if self.account and self.person:
            raise ValidationError('Address must only be associated with one of account or person')


class Event(Notable):
    '''Base table for events in the Shakespeare and Co. Lending Library'''
    account = models.ForeignKey(Account)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ('start_date', 'account__persons__sort_name')

    # These provide generic string representation for the Event class
    # and its subclasses
    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.__dict__)

    def __str__(self):
        return '%s for account #%s' % (self.__class__.__name__,
                                      self.account.pk)

    @cached_property
    def event_type(self):
        try:
            return self.subscription.get_subtype_display()
        except ObjectDoesNotExist:
            pass
        try:
            self.reimbursement
            return 'Reimbursement'
        except ObjectDoesNotExist:
            pass
        try:
            self.borrow
            return 'Borrow'
        except ObjectDoesNotExist:
            pass
        try:
            self.purchase
            return 'Purchase'
        except ObjectDoesNotExist:
            pass
        return 'Generic'


class SubscriptionType(Named, Notable):
    '''Type of subscription'''
    pass


class CurrencyMixin(models.Model):
    '''Mixin for currency field with currency symbol display'''

    USD = 'USD'
    FRF = 'FRF'
    GBP = 'GBP'
    # NOTE: Preliminary currency set for now
    CURRENCY_CHOICES = (
        ('', '----'),
        (USD, 'US Dollar'),
        (FRF, 'French Franc'),
        (GBP, 'British Pound')
    )

    symbols = {
        FRF: '₣',
        USD: '$',
        GBP: '£'
    }

    currency = models.CharField(max_length=3, blank=True,
        choices=CURRENCY_CHOICES, default=FRF)

    class Meta:
        abstract = True

    def currency_symbol(self):
        '''symbol for the selected currency'''
        return self.symbols.get(self.currency, self.currency)
    # NOTE: could use ¤ (generic currency), but probably not that well known
    currency_symbol.short_description = '$'
    currency_symbol.admin_order_field = 'currency'


class Subscription(Event, CurrencyMixin):
    '''Records subscription events in the MEP database'''
    duration = models.PositiveIntegerField('Days',
        blank=True, null=True,
        help_text='Subscription duration in days. Automatically calculated from start and end date.')
    volumes = models.DecimalField(blank=True, null=True, max_digits=4,
        decimal_places=2,
        help_text='Number of volumes for checkout')
    category = models.ForeignKey(SubscriptionType, null=True, blank=True,
        help_text='Code to indicate the kind of subscription')

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

    SUPPLEMENT = 'sup'
    RENEWAL = 'ren'
    OTHER = 'oth'

    EVENT_TYPE_CHOICES = (
        ('', 'Subscription'),
        (SUPPLEMENT, 'Supplement'),
        (RENEWAL, 'Renewal'),
        (OTHER, 'Other'),
    )
    subtype = models.CharField(verbose_name='Type', max_length=50, blank=True,
        choices=EVENT_TYPE_CHOICES,
        help_text='Type of subscription event, e.g. supplement or renewal.')

    def save(self, *args, **kwargs):
        # recalculate duration on save if dates are available,
        # so that duration is always accurate even if dates change
        if self.start_date and self.end_date:
            self.calculate_duration()
        super(Subscription, self).save(*args, **kwargs)

    def calculate_duration(self):
        '''calculate and set subscription duration based on start and end
        date, when both are known'''
        if self.start_date and self.end_date:
            # calculate duration in days as timedelta from end to start
            self.duration = (self.end_date - self.start_date).days

    def validate_unique(self, *args, **kwargs):
        '''Validation check to prevent duplicate events from being
        added to the system.  Does not allow more than one subscription
        for the same account and date.'''
        super(Subscription, self).validate_unique(*args, **kwargs)

        # check to prevent duplicate event
        # should not have same date + account + event subtype
        # (can't use unique_together because of multi-table inheritance)

        # adapted from https://stackoverflow.com/questions/7366363/adding-custom-django-model-validation
        qs = Subscription.objects.filter(start_date=self.start_date,
            account=self.account, subtype=self.subtype)

        # if current item is already saved, exclude it from the queryset
        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError('Subscription event is not unique')

    def readable_duration(self):
        '''Generate a human-readable version of the subscription duration.
        Intended to follow Beach's conventions, e.g. 1 year rather than
        12 months; 1 week rather than 7 days.'''

        # simple case - days/weeks less than a month
        if self.duration and self.duration < 28:
            # weeks are sets of 7 days exactly
            if self.duration % 7 == 0:
                weeks = self.duration / 7
                return '%d week%s' % (weeks, pluralize(weeks))
            # days less than a week
            if self.duration < 7:
                return '%d day%s' % (self.duration, pluralize(self.duration))

        # otherwise, use relativedelta to generate duration in years/months/days
        # and aggregate the different units
        parts = []
        rel_dur = relativedelta(self.end_date, self.start_date)
        if rel_dur.years:
            parts.append('%d year%s' % (rel_dur.years, pluralize(rel_dur.years)))
        if rel_dur.months:
            parts.append('%d month%s' % (rel_dur.months, pluralize(rel_dur.months)))
        if rel_dur.days:
            parts.append('%d day%s' % (rel_dur.days, pluralize(rel_dur.days)))

        # if there are multiple parts (e.g., 1 month and 11 days) and
        # duration is evenly divisible by 7, display as weeks
        # NOTE: this could potentially match 1 year + some number of months;
        # unclear what behavior would be preferred in that case,
        # but unlikely to happen with current MEP data
        if len(parts) > 1 and self.duration % 7 == 0:
            weeks = self.duration / 7
            return '%d week%s' % (weeks, pluralize(weeks))

        # otherwise, combine months & days
        return ', '.join(parts)
    readable_duration.short_description = 'Duration'
    readable_duration.admin_order_field = 'duration'


class DatePrecision(Flags):
    # flag class to indicate which date values are known
    year = ()
    month = ()
    day = ()


class DatePrecisionField(models.PositiveSmallIntegerField):

    DATE_FORMATS = {
        DatePrecision.year: '%Y',
        DatePrecision.month: '%Y-%m',
        DatePrecision.day: '%Y-%m-%d'
    }

    partial_date_re = re.compile(
       r'^(?P<year>\d{4})?(?:-(?P<month>[01]\d))?(?:-(?P<day>[0-3]\d))?$'
    )

    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            # default is full precision
            # NOTE: needs to be cast as int or it breaks django migrations
            kwargs['default'] = int(DatePrecision.all_flags)
        super(DatePrecisionField, self).__init__(*args, **kwargs)

    @classmethod
    def parse_date(cls, value):
        '''Parse a partial date string and return a :class:`datetime.date`
        and precision value.'''
        # partial date parsing adapted in part from django_partial_date
        # https://github.com/ktowen/django_partial_date
        match = cls.partial_date_re.match(value)
        if match:
            match_info = match.groupdict()

            # turn matched values into numbers for initializing date object;
            # default to 1 for any values not present
            date_values = {k: int(v) if v else 1 for k, v in match_info.items()}

            # determine known date parts based on regex match values
            # and initialize pecision flags accordingly
            date_parts = [key for key, val in match_info.items() if val]
            precision = DatePrecision.from_simple_str('|'.join(date_parts))
            return (datetime.date(**date_values), precision)

        else:
            raise ValidationError('%s is not a recognized partial date''' % value)

    @classmethod
    def date_format(cls, value):
        '''Return a format string for use with :meth:`datetime.date.strftime`
        to output a date with the appropriate precision'''
        parts = []
        # cast integer to date precision flag for comparison
        value = DatePrecision(value)
        if value & DatePrecision.year:
            parts.append('%Y')
        else:
            # if no year, indicate with --
            parts.append('-')
        if value & DatePrecision.month:
            parts.append('%m')
        if value & DatePrecision.day:
            parts.append('%d')

        # this is potentially ambiguous in some cases, but those cases
        # may not be meaningful anywya
        return '-'.join(parts)


class Borrow(Event):
    '''Inherited table indicating borrow events'''
    #: :class:`~mep.books.models.Item` that was borrowed;
    #: optional to account for unclear titles
    item = models.ForeignKey(Item, null=True, blank=True)
    start_date_precision = DatePrecisionField()
    end_date_precision = DatePrecisionField()
    bought = models.BooleanField(default=False,
        help_text='Item was bought instead of returned')

    def set_partial_start_date(self, value):
        '''parse a partial date and set :attr:`start_date` and
        :attr:`start_date_precision` accordingly'''
        self.start_date, \
            self.start_date_precision = DatePrecisionField.parse_date(value)

    def set_partial_end_date(self, value):
        '''parse a partial date and set :attr:`end_date` and
        :attr:`end_date_precision` accordingly'''
        self.end_date, \
            self.end_date_precision = DatePrecisionField.parse_date(value)

    def display_start_date(self):
        if self.start_date:
            return self.start_date.strftime(DatePrecisionField.date_format(self.start_date_precision))
    display_start_date.short_description = 'start_date'
    display_start_date.admin_order_field = 'start_date'

    def display_end_date(self):
        if self.end_date:
            return self.end_date.strftime(DatePrecisionField.date_format(self.end_date_precision))
    display_end_date.short_description = 'end_date'
    display_end_date.admin_order_field = 'end_date'


class Purchase(Event, CurrencyMixin):
    '''Inherited table indicating purchase events'''
    price = models.DecimalField(max_digits=8, decimal_places=2)
    item = models.ForeignKey(Item)


class Reimbursement(Event, CurrencyMixin):
    '''Reimbursement event; extends :class:`Event`'''
    refund = models.DecimalField(max_digits=8, decimal_places=2, null=True,
        blank=True)

    def date(self):
        '''alias of :attr:`start_date` for display, since reimbersument
        is a single-day event'''
        return self.start_date
    date.admin_order_field = 'start_date'

    def save(self, *args, **kwargs):
        '''Reimbursement is a single-day event; populate end date on save
        to make that explicit and simplify any generic event date
        range searching and filtering.'''
        self.end_date = self.start_date
        super(Reimbursement, self).save(*args, **kwargs)

    def validate_unique(self, *args, **kwargs):
        '''Validation check to prevent duplicate events from being
        added to the system.  Does not allow more than one reimbursement
        for the account and date.'''
        super(Reimbursement, self).validate_unique(*args, **kwargs)

        # check to prevent duplicate event (reimbursement + date + account)
        # should not have same date + account
        qs = Reimbursement.objects.filter(start_date=self.start_date,
            account=self.account)

        # if current item is already saved, exclude it from the queryset
        if not self._state.adding and self.pk is not None:
            qs = qs.exclude(pk=self.pk)

        if qs.exists():
            raise ValidationError('Reimbursement event is not unique')
