from django.test import TestCase
from django.urls import reverse

from mep.accounts.models import Account, Address
from mep.people.models import Person, Location

class TestAccountsViews(TestCase):

    def test_account_autocomplete(self):
        url = reverse('accounts:autocomplete')
        res = self.client.get(url)

        # getting the view returns 200
        assert res.status_code == 200
        data = res.json()
        # there is a results list in the JSON
        assert 'results' in data
        # it is empty because there are no accounts or query
        assert not data['results']

        # - test search and sort

        # search by pk
        acc1 = Account.objects.create()
        acc2 = Account.objects.create()
        res = self.client.get(url, {'q': acc1.pk})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert data['results'][0]['text'] == 'Account #%s' % acc1.pk

        # search by persons
        pers1 = Person.objects.create(name='Mlle Foo')
        pers2 = Person.objects.create(name='Msr Foo')
        acc2.persons.add(pers1, pers2)
        res = self.client.get(url, {'q': 'Mlle'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert data['results'][0]['text'] == \
            'Account #%s: Mlle Foo, Msr Foo' % acc2.pk

        # search by address
        loc1 = Location.objects.create(street_address='1 Rue St.')
        Address.objects.create(account=acc1, location=loc1)
        res = self.client.get(url, {'q': 'Rue'})
        data = res.json()
        assert res.status_code == 200
        assert 'results' in data
        assert data['results'][0]['text'] == 'Account #%s: 1 Rue St.' % acc1.pk
