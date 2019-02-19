from wagtail.core.models import Page, Site
from wagtail.tests.utils import WagtailPageTests
from wagtail.tests.utils.form_data import (nested_form_data, rich_text,
                                           streamfield)

from mep.pages.models import ContentPage, HomePage, LandingPage


class TestHomePage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        root = Page.objects.get(title='Root')
        self.assertCanCreate(root, HomePage, nested_form_data({
            'title': 'S&Co.',
            'slug': 'newhome',
            'body': streamfield([
                ('paragraph', rich_text('homepage body text')),
                ('footnotes', rich_text('homepage footnotes')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(HomePage, [Page])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(HomePage, [LandingPage, Page])

    def test_template(self):
        site = Site.objects.first()
        home = HomePage.objects.first()
        response = self.client.get(home.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/home_page.html')


class TestLandingPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        home = HomePage.objects.first()
        self.assertCanCreate(home, LandingPage, nested_form_data({
            'title': 'Sources 2',
            'slug': 'sources2',
            'tagline': 'like sources, but better',
            'body': streamfield([
                ('paragraph', rich_text('the new sources landing page')),
                ('footnotes', rich_text('some landing page footnotes')),
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(LandingPage, [HomePage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(LandingPage, [ContentPage, Page])

    def test_template(self):
        site = Site.objects.first()
        landing_page = LandingPage.objects.first()
        response = self.client.get(landing_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/landing_page.html')


class TestContentPage(WagtailPageTests):
    fixtures = ['wagtail_pages']

    def test_can_create(self):
        landing_page = LandingPage.objects.first()
        self.assertCanCreate(landing_page, ContentPage, nested_form_data({
            'title': 'A newly discovered content source',
            'slug': 'new-source',
            'body': streamfield([
                ('paragraph', rich_text('this page lives under sources'))
            ]),
        }))

    def test_parent_pages(self):
        self.assertAllowedParentPageTypes(ContentPage, [LandingPage])

    def test_subpages(self):
        self.assertAllowedSubpageTypes(ContentPage, [Page])

    def test_template(self):
        site = Site.objects.first()
        content_page = ContentPage.objects.first()
        response = self.client.get(content_page.relative_url(site))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'pages/content_page.html')