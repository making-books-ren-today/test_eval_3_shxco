
from django.db import models

from mep.common.models import AliasIntegerField, DateRange, Named, Notable


class Person(Notable, DateRange):
    """Model for people in the MEP dataset"""

    # Identifiers
    mep_id = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    # QUESTION: This is listed as integer on draft 004
    # Do we want that?
    # May be obviated by the need for other URLs anyway
    viaf_id = models.URLField(blank=True)

    # Vital statistics
    # QUESTION: These are aliased with the reusable logic of AliasIntegerField
    # and the DateRange class. Worth it even though the SQL column name will
    # be a bit less clear?
    birth_year = AliasIntegerField(db_column='start_year',
        blank=True, null=True)
    death_year = AliasIntegerField(db_column='end_year',
        blank=True, null=True)

    MALE = 'M'
    FEMALE = 'F'
    SEX_CHOICES = (
        ('', '----'),
        (FEMALE, 'Female'),
        (MALE, 'Male'),
    )
    sex = models.CharField(blank=True, max_length=1, choices=SEX_CHOICES)
    # QUESTION: Do we want this to be constrained vocabulary? Probably not,
    # but want to ask.
    title = models.CharField(blank=True, max_length=255)
    profession = models.ForeignKey('Profession', blank=True, null=True)
    nationalities = models.ManyToManyField('Country', blank=True)

    def __repr__(self):
        return '<Person %s>' % self.__dict__

    def __str__(self):
        entry_name = '%s, %s' % (self.last_name, self.first_name)
        return entry_name.strip()

    @property
    def full_name(self):
        return ('%s %s' % (self.first_name, self.last_name)).strip()

    class Meta:
        verbose_name_plural = 'People'


class Country(Named):
    """Django model for countries"""

    code = models.CharField(max_length=3, blank=True)

    def __repr__(self):
        return '<Country %s>' % self.__dict__

    def __str_(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Countries'


class Profession(Named, Notable):
    """Model holder for named professions"""
    pass

    def __repr__(self):
        return '<Profession %s>' % self.__dict__

    def __str__(self):
        return self.name


class Relationship(models.Model):
    """Through model for ``Person.relationships``"""
    from_person = models.ForeignKey('RelationshipType')
    to_person = models.ForegnKey('RelationshipType')
    relationship_type = models.ForeignKey('RelationshipType')

    def __str__(self):
        return '%s is a %s to %s' % (
            self.from_person.full_name,
            self.relationship_type.name,
            self.to_person.full_name
            )


class RelationshipType(Named, Notable):
    """ Stock model for relationship types"""
