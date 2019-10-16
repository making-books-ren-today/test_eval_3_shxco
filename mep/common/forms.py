from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.text import mark_safe


class SelectDisabledMixin():
    '''
    Mixin for :class:`django.forms.RadioSelect` or :class:`django.forms.CheckboxSelect`
    classes to set an option as disabled. To disable, the widget's choice
    label option should be passed in as a dictionary with `disabled` set
    to True::

        {'label': 'option', 'disabled': True}.
    '''

    # Using a solution at https://djangosnippets.org/snippets/2453/
    def create_option(self, name, value, label, selected, index, subindex=None,
                      attrs=None):
        disabled = None

        if isinstance(label, dict):
            label, disabled = label['label'], label.get('disabled', False)
        option_dict = super().create_option(
            name, value, label, selected, index,
            subindex=subindex, attrs=attrs
        )
        if disabled:
            option_dict['attrs'].update({'disabled': 'disabled'})
        return option_dict


class RadioSelectWithDisabled(SelectDisabledMixin, forms.RadioSelect):
    '''
    Subclass of :class:`django.forms.RadioSelect` with option to mark
    a choice as disabled.
    '''


class SelectWithDisabled(SelectDisabledMixin, forms.Select):
    '''
    Subclass of :class:`django.forms.Select` with option to mark
    a choice as disabled.
    '''


class CheckboxFieldset(forms.CheckboxSelectMultiple):
    '''Override of :class:`~django.forms.CheckboxSelectMultiple`
    that renders as a fieldset with checkbox inputs.'''
    template_name = 'common/widgets/checkbox_fieldset.html'
    facet_counts = None

    def get_context(self, name, value, attrs):
        '''Pass custom legend property into context dictionary for widget.'''
        context = super().get_context(name, value, attrs)
        context['widget']['legend'] = self.legend
        # add facet counts to context if available
        # used to conditionally hide facets based on count
        context['facet_counts'] = self.facet_counts
        return context


class FacetChoiceField(forms.MultipleChoiceField):
    '''Add CheckboxSelectMultiple field with facets taken from solr query.'''
    # Borrowed from https://github.com/Princeton-CDH/derrida-django/blob/develop/derrida/books/forms.py
    # customize multiple choice field for use with facets.
    # - turn off choice validation (shouldn't fail if facets don't get loaded)
    # - default to not required
    # - use CheckboxFieldset widget for rendering facet

    widget = CheckboxFieldset

    def __init__(self, hide_threshold=None, *args, **kwargs):
        # default required to false
        if 'required' not in kwargs:
            kwargs['required'] = False

        # get custom kwarg and remove before passing to MultipleChoiceField
        # super method, which would cause an error
        self.widget.legend = None
        if 'legend' in kwargs:
            self.widget.legend = kwargs['legend']
            del kwargs['legend']

        super().__init__(*args, **kwargs)

        # if no custom legend, set it from label
        if not self.widget.legend:
            self.widget.legend = self.label

        # if present, set hide threshold as widget data attribute
        if hide_threshold is not None:
            self.widget.attrs['data-hide-threshold'] = hide_threshold

    def valid_value(self, value):
        return True


# RangeWidget and RangeField adapted from Derrida & PPA, but
# returns a two-tuple instead of a string

class RangeWidget(forms.MultiWidget):
    '''date range widget, for two numeric inputs'''

    #: template to use to render range multiwidget
    # (based on multiwidget, but adds "to" between dates)
    template_name = 'common/widgets/rangewidget.html'

    def __init__(self, *args, **kwargs):
        widgets = [
            forms.NumberInput(attrs={'aria-label': 'start'}),
            forms.NumberInput(attrs={'aria-label': 'end'})
        ]
        super().__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return [int(val) if val else None for val in value]
        return [None, None]


class RangeField(forms.MultiValueField):
    '''Date range field, for two numeric inputs. Compresses to a tuple of
    two values for the start and end of the range; tuple values set to
    None for no input.'''
    widget = RangeWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.IntegerField(
                error_messages={'invalid': 'Enter a number'},
                validators=[
                    RegexValidator(r'^[0-9]*$', 'Enter a valid number.'),
                ],
                required=False
            ),
            forms.IntegerField(
                error_messages={'invalid': 'Enter a number'},
                validators=[
                    RegexValidator(r'^[0-9]*$', 'Enter a valid number.'),
                ],
                required=False
            ),
        )
        kwargs['fields'] = fields
        super().__init__(require_all_fields=False, *args, **kwargs)

    def compress(self, data_list):
        '''Compress into a single value; returns a two-tuple of range end,
        start.'''

        # If neither values is set, return None
        if not any(data_list):
            return None

        # if both values are set and the first is greater than the second,
        # raise a validation error
        if all(data_list) and len(data_list) == 2 and data_list[0] > data_list[1]:
            raise ValidationError('Invalid range (%s - %s)' % (data_list[0], data_list[1]))

        return (data_list[0], data_list[1])

    def set_min_max(self, min_val, max_val):
        '''Set a min and max value for :class:`RangeWidget` attributes
        and placeholders.

        :param min_value: minimum value to set on widget
        :type min_value: int
        :param max_value: maximum value to set on widget
        :type max_value: int
        :rtype: None
        '''
        start_widget, end_widget = self.widget.widgets
        # set placeholders for widgets individually
        start_widget.attrs['placeholder'] = min_val
        end_widget.attrs['placeholder'] = max_val
        # valid min and max for both via multiwidget
        self.widget.attrs.update({
            'min': min_val,
            'max': max_val
        })


class FacetForm(forms.Form):
    '''Form mixin to support mapping facet fields to
    :class`FacetChoiceField` fields.'''

    #: A mapping of facets fields to form fields.
    solr_facet_fields = {}

    def set_choices_from_facets(self, facets):
        '''Render a set of choices based on a mapping of facets to counts.'''
        # configure field choices based on facets returned from Solr
        # (adapted from derrida and winthrop codebase)
        for facet, counts in facets.items():
            # use field from facet fields map or else field name as is
            formfield = self.solr_facet_fields.get(facet, facet)
            if formfield in self.fields:
                self.fields[formfield].choices = [
                    # iterate over val and counts in counts dictionary
                    # and format as a lable and comma separated integer
                    (val, mark_safe('{}<span class="count">{:,}</span>'\
                                    .format(val if val else 'Unknown', count)))
                    for val, count in counts.items()
                ]
                self.fields[formfield].widget.facet_counts = counts
