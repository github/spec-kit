"""Simple Playwright tests for Google"""
from playwright.sync_api import Page, expect


def test_google_homepage_loads(page: Page):
    """Test that Google homepage loads correctly"""
    page.goto("https://www.google.com")
    expect(page).to_have_title(lambda title: "Google" in title)


def test_google_search_box_visible(page: Page):
    """Test that Google search box is visible"""
    page.goto("https://www.google.com")
    search_box = page.locator('textarea[name="q"]')
    expect(search_box).to_be_visible()


def test_google_search_works(page: Page):
    """Test that Google search functionality works"""
    page.goto("https://www.google.com")
    page.fill('textarea[name="q"]', "Playwright")
    page.press('textarea[name="q"]', "Enter")
    page.wait_for_load_state("networkidle")
    expect(page).to_have_url(lambda url: "search" in url)
