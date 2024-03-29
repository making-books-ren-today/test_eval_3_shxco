import logging
from collections import defaultdict

from django.apps import apps
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Coalesce
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from djiffy.models import Canvas, Manifest
from parasolr.django.indexing import ModelIndexable

from mep.common.models import Named, Notable


logger = logging.getLogger(__name__)


class BibliographySignalHandlers:
    '''Signal handlers for indexing :class:`Bibliography` records when
    related records are saved or deleted.'''

    @staticmethod
    def debug_log(name, count, mode='save'):
        '''shared debug logging for card signal save handlers'''
        logger.debug('%s %s, reindexing %d related card%s',
                     mode, name, count, '' if count == 1 else 's')

    @staticmethod
    def person_save(sender=None, instance=None, raw=False, **kwargs):
        '''when a person is saved, reindex bibliography card records
        associated through an account'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # find any cards associated via an account
        cards = Bibliography.objects.filter(account__persons__pk=instance.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('person', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def person_delete(sender, instance, **kwargs):
        '''when a person is deleted, reindex any bibliography card
        records associated through an account'''
        card_ids = Bibliography.objects \
            .filter(account__persons__pk=instance.pk) \
            .values_list('id', flat=True)
        if card_ids:
            # find the items based on the list of ids to reindex
            cards = Bibliography.objects.filter(id__in=list(card_ids))

            # clear the assocation so items will index without this person
            instance.account_set.clear()
            BibliographySignalHandlers.debug_log('person', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def account_save(sender=None, instance=None, raw=False, **_kwargs):
        '''when an account is saved, reindex any associated library
        lending card.'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # find any cards associated with this account
        cards = Bibliography.objects.filter(account__pk=instance.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('account', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def account_delete(sender, instance, **kwargs):
        '''when an account is deleted, reindex any associated library
        lending card'''
        card_ids = Bibliography.objects.filter(account__pk=instance.pk) \
            .values_list('id', flat=True)

        if card_ids:
            # delete the assocation so cards will index without the account
            instance.card = None
            instance.save()
            # find the items based on the list of ids to reindex
            cards = Bibliography.objects.filter(id__in=list(card_ids))
            BibliographySignalHandlers.debug_log('account', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def manifest_save(sender=None, instance=None, raw=False, **kwargs):
        '''when a manifest is saved, reindex associated library
        lending card'''
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # find any cards associated with this account
        cards = Bibliography.objects.filter(manifest__pk=instance.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('manifest', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def manifest_delete(sender, instance, **kwargs):
        '''when a manifest is deleted, reindex associated library
        lending card'''
        card_ids = Bibliography.objects.filter(manifest__pk=instance.pk) \
            .values_list('id', flat=True)
        if card_ids:
            # delete the assocation so cards will index without the account
            instance.bibliography_set.clear()
            # find the items based on the list of ids to reindex
            cards = Bibliography.objects.filter(id__in=list(card_ids))
            BibliographySignalHandlers.debug_log('manifest', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def canvas_save(sender=None, instance=None, raw=False, **kwargs):
        '''when a canvas is saved, reindex library lending card
        associated via manifest'''

        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # find any cards associated with this canvas, via manifest
        cards = Bibliography.objects.filter(manifest__pk=instance.manifest.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('canvas', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def canvas_delete(sender, instance, **kwargs):
        '''when a canvas is deleted, reindex library lending card
        associated via manifest'''
        cards = Bibliography.objects.filter(manifest__pk=instance.manifest.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('canvas', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)

    @staticmethod
    def event_save(sender=None, instance=None, raw=False, **_kwargs):
        '''when an event is saved, reindex library lending card
        associated via account'''
        # NOTE: should this also/instead rely on footnote associatio?
        # raw = saved as presented; don't query the database
        if raw or not instance.pk:
            return
        # find any cards associated with this event, via account
        cards = Bibliography.objects.filter(account__pk=instance.account.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('event', cards.count())
            ModelIndexable.index_items(cards)

    @staticmethod
    def event_delete(sender, instance, **kwargs):
        '''when an event is deleted, reindex library lending card
        associated via account'''
        cards = Bibliography.objects.filter(account__pk=instance.account.pk)
        if cards.exists():
            BibliographySignalHandlers.debug_log('event', cards.count(),
                                                 mode='delete')
            ModelIndexable.index_items(cards)


class SourceType(Named, Notable):
    '''Type of source document.'''

    def item_count(self):
        '''number of associated bibliographic items'''
        return self.bibliography_set.count()
    item_count.short_description = '# items'


class Bibliography(Notable, ModelIndexable):
    # Note: citation might be better singular
    bibliographic_note = models.TextField(
        help_text='Full bibliographic citation')
    source_type = models.ForeignKey(SourceType,
                                    on_delete=models.CASCADE)

    #: digital version as instance of :class:`djiffy.models.Manifest`
    manifest = models.ForeignKey(
        Manifest, blank=True, null=True, on_delete=models.SET_NULL,
        help_text='Digitized version of lending card, if locally available')

    class Meta:
        verbose_name_plural = 'Bibliographies'
        ordering = ('bibliographic_note',)

    def __str__(self):
        return self.bibliographic_note

    def footnote_count(self):
        '''number of footnotes this item is referenced in'''
        return self.footnote_set.count()
    footnote_count.short_description = '# footnotes'

    @classmethod
    def index_item_type(cls):
        """Label for this kind of indexable item."""
        # override default behavior (using model verbose name)
        # since we are only care about indexing cards, and not
        # all bibliography records
        return 'card'

    @classmethod
    def items_to_index(cls):
        '''Custom logic for finding items for bulk indexing; only include
        records associated with an account and with a IIIF manifest.'''
        return cls.objects.filter(account__isnull=False,
                                  manifest__isnull=False)

    index_depends_on = {
        'account_set': {
            'post_save': BibliographySignalHandlers.account_save,
            'pre_delete': BibliographySignalHandlers.account_delete
        },
        'account_set__persons': {
            'post_save': BibliographySignalHandlers.person_save,
            'pre_delete': BibliographySignalHandlers.person_delete
        },
        # NOTE: using app.Model notation here because
        # parasolr doesn't currently support foreignkey relation lookup
        'djiffy.Manifest': {
            'post_save': BibliographySignalHandlers.manifest_save,
            'pre_delete': BibliographySignalHandlers.manifest_delete
        },
        'djiffy.Canvas': {
            'post_save': BibliographySignalHandlers.canvas_save,
            'post_delete': BibliographySignalHandlers.canvas_delete
        },
        'accounts.Event': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        # unfortunately the generic event signals aren't fired
        # when subclass types are edited directly, so bind the same signal
        'accounts.Borrow': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        'accounts.Purchase': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        'accounts.Subscription': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        },
        'accounts.Reimbursement': {
            'post_save': BibliographySignalHandlers.event_save,
            'post_delete': BibliographySignalHandlers.event_delete,
        }
    }

    def index_data(self):
        '''data for indexing in Solr'''
        index_data = super().index_data()
        # only library lending cards are indexed; if bibliography
        # does not have a manifest or is not associated with an account,
        # return id only.
        # This will blank out any previously indexed values, and item
        # will not be findable by any public searchable fields.
        account = self.account_set.all().first()
        if not self.manifest or not self.account_set.all().exists():
            del index_data['item_type']
            return index_data

        # we expect a thumbnail, but possible there is none
        if self.manifest.thumbnail:
            iiif_thumbnail = self.manifest.thumbnail.image

            # for now, store iiif thumbnail urls directly
            index_data['thumbnail_t'] = str(iiif_thumbnail.size(width=225))
            index_data['thumbnail2x_t'] = str(iiif_thumbnail.size(width=225 * 2))

        names = []
        account_years = set()
        for account in self.account_set.all():
            for person in account.persons.all():
                names.append(person.sort_name)
            account_years.update(set(date.year for date in
                                     account.event_dates))
        if names:
            index_data.update({
                'cardholder_t': names,
                'cardholder_sort_s': names[0],
            })

        if account_years:
            index_data.update({
                'years_is': list(account_years),
                'start_i': min(account_years),
                'end_i': max(account_years),
            })
        return index_data


class FootnoteQuerySet(models.QuerySet):
    '''Custom :class:`models.QuerySet` for :class:`Footnote`'''

    def on_events(self):
        '''Filter to footnotes that are associated with events'''
        return self.filter(
            content_type__app_label='accounts',
            content_type__model__in=['event', 'borrow', 'purchase'])

    def events(self):
        '''Return an Events queryset of any events (including borrows and
        purchases) associated with the current footnote queryset.'''

        # use get model to avoid circular import
        Event = apps.get_model('accounts', 'Event')

        # get event ids and content types from the current footnote queryset
        event_refs = self.on_events() \
                         .values('object_id', 'content_type__model')
        # group event ids by content type
        event_ids_by_type = defaultdict(list)
        for ref in event_refs:
            event_ids_by_type[ref['content_type__model']].append(ref['object_id'])
        # construct an OR filter query for each content type and list of ids
        # - look for nothing OR for events and event subtypes by id
        filter_q = models.Q(pk__in=[])
        for ctype, pk_list in event_ids_by_type.items():
            if ctype == 'borrow':
                filter_q |= models.Q(borrow__pk__in=pk_list)
            elif ctype == 'purchase':
                filter_q |= models.Q(purchase__pk__in=pk_list)
            elif ctype == 'event':
                filter_q |= models.Q(pk__in=pk_list)

        # find and return corresponding events
        return Event.objects.filter(filter_q)

    def event_date_range(self):
        '''Find earliest and latest dates for any events associated
        with footnotes in this queryset. Returns a tuple of earliest
        and latest dates, or None if no dates are found.'''

        # find corresponding events, filter out unknown years,
        # and aggregrate dates to get earliest and latest from this set
        # date_values = Event.objects.filter(filter_q).known_years() \
        date_values = self.events().known_years() \
            .annotate(
                start_dates=Coalesce('start_date', 'end_date'),
                end_dates=Coalesce('end_date', 'start_date')) \
            .aggregate(first=models.Min('start_dates'),
                       last=models.Max('end_dates'))
        # return earliest and latest dates, unless result is None
        if date_values['first']:
            return date_values['first'], date_values['last']


class Footnote(Notable):
    '''Footnote that can be associated with any other model via
    generic relationship.  Used to provide supporting documentation
    for or against information in the system.
    '''
    bibliography = models.ForeignKey(Bibliography, on_delete=models.CASCADE)
    location = models.TextField(
        blank=True,
        help_text='Page number for a book, URL for part of a website,' +
        ' or other location inside of a larger work.')
    snippet_text = models.TextField(blank=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        # restrict choices to "content" models (exclude django/admin models)
        # and models that are available in django admin
        # (otherwise, lookup is not possible)
        # TODO: add items here as the application expands
        limit_choices_to=models.Q(app_label='people',
            model__in=['country', 'person', 'address', 'profession']) |
            models.Q(
                app_label='accounts',
                model__in=['account', 'event', 'subscription', 'borrow',
                           'reimbursement', 'purchase']) |
            models.Q(app_label='books', model__in=['item'])
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    is_agree = models.BooleanField(
        'Supports', help_text='True if the evidence ' +
        'supports the information in the system, False if it contradicts.',
        default=True)

    image = models.ForeignKey(
        Canvas, blank=True, null=True, on_delete=models.SET_NULL,
        help_text='Image location from an imported manifest, if available.')

    # override default manager with customized version
    objects = FootnoteQuerySet.as_manager()

    def __str__(self):
        return 'Footnote on %s (%s)' % \
            (self.content_object,
             ' '.join([str(i) for i in [self.bibliography, self.location]
                       if i]))

    # NOTE: for convenient access from other models, add a
    # reverse generic relation
    #
    # from django.contrib.contenttypes.fields import GenericRelation
    # from mep.footnotes.models import Footnote
    #
    # footnotes = GenericRelation(Footnote)

    def image_thumbnail(self):
        '''Use admin thumbnail from image if available, but wrap
        in a link using rendering url from manifest when present'''
        if self.image:
            img = self.image.admin_thumbnail()
            if 'rendering' in self.image.manifest.extra_data:
                img = format_html(
                    '<a target="_blank" href="{}">{}</a>',
                    self.image.manifest.extra_data['rendering']['@id'],
                    mark_safe(img))
            return img
    image_thumbnail.allow_tags = True
