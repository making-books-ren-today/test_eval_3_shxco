import pytest
import re

from django.test import TestCase
from .models import Account, AccountAddress, Address
from .models import Borrow, Event, Purchase, Reimbursement, Subscribe
from mep.books.models import Item


class TestAccount(TestCase):

    def test_repr(self):
        account = Account()
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>""
        overall = re.compile(r"<Account \{.+\}>")
        assert re.search(overall, repr(account))

    def test_str(self):
        account = Account()
        assert str(account) == "Account #%s" % account.pk

    def test_add_event(self):

        # Make a saved Account object
        account = Account.objects.create()
        account.add_event('reimbursement', **{'price': 2.32})

        # Look at the relationship from the other side via Reimbursement
        # should find the event we just saved
        reimbursement = Reimbursement.objects.get(account=account)
        assert float(reimbursement.price) == 2.32

        # Saving with a not saved object should raise ValueError
        with pytest.raises(ValueError):
            unsaved_account = Account()
            unsaved_account.add_event('reimbursement', **{'price': 2.32})

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event('foo')

    def test_get_events(self):
        # Make a saved Account object
        account = Account.objects.create()
        account.add_event('reimbursement', **{'price': 2.32})
        account.add_event(
            'subscribe',
            **{'duration': 1, 'volumes': 2, 'price_paid': 4.56}
        )

        # Access them as events only
        assert len(account.get_events()) == 2
        assert isinstance(account.get_events()[0], Event)

        # Now access as a subclass with related properties
        reimbursements = account.get_events('reimbursement')
        assert len(reimbursements) == 1
        assert float(reimbursements[0].price) == 2.32

        # Try filtering so that we get no reimbursements and empty qs
        reimbursements = account.get_events('reimbursement', price=2.45)
        assert not reimbursements

        # Providing a dud event type should raise ValueError
        with pytest.raises(ValueError):
            account.add_event('foo')



class TestAccountAddress(TestCase):

    def setUp(self):
        self.address = Address.objects.create()
        self.account = Account.objects.create()

        self.account_address = AccountAddress.objects.create(
            address=self.address,
            account=self.account
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<AccountAddress \{.+\}>")
        assert re.search(overall, repr(self.account_address))

    def test_str(self):
        assert str(self.account_address) == (
            'Account #%s - Address #%s' %
            (self.account.pk, self.address.pk)
        )


class TestEvent(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.event = Event.objects.create(account=self.account)

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Event \{.+\}>")
        assert re.search(overall, repr(self.event))

    def test_str(self):
        assert str(self.event) == 'Event for account #%s' % self.account.pk


class TestSubscribe(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.subscribe = Subscribe.objects.create(
            account=self.account,
            duration=1,
            volumes=2,
            price_paid=3.20
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Subscribe \{.+\}>")
        assert re.search(overall, repr(self.subscribe))

    def test_str(self):
        assert str(self.subscribe) == ('Subscribe for account #%s' %
                                       self.subscribe.account.pk)


class TestPurchase(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.item = Item.objects.create(
            title='Foobar'
        )
        self.purchase = Purchase.objects.create(
            account=self.account,
            price=2.30,
            currency='USD',
            item=self.item,
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Purchase \{.+\}>")
        assert re.search(overall, repr(self.purchase))

    def test_str(self):
        assert str(self.purchase) == ('Purchase for account #%s' %
                                      self.purchase.account.pk)


class TestReimbursement(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.reimbursement = Reimbursement.objects.create(
            account=self.account,
            price=2.30,
            currency='USD'
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Reimbursement \{.+\}>")
        assert re.search(overall, repr(self.reimbursement))

    def test_str(self):
        assert str(self.reimbursement) == ('Reimbursement for account #%s' %
                                           self.reimbursement.account.pk)


class TestBorrow(TestCase):

    def setUp(self):
        self.account = Account.objects.create()
        self.borrow = Borrow.objects.create(
            account=self.account
        )

    def test_repr(self):
        # Using self.__dict__ so relying on method being correct
        # Testing for form of "<Account {"k":v, ...}>"
        overall = re.compile(r"<Borrow \{.+\}>")
        assert re.search(overall, repr(self.borrow))

    def test_str(self):
        assert str(self.borrow) == ('Borrow for account #%s' %
                                    self.borrow.account.pk)