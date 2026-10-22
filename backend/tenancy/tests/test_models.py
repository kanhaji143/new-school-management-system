"""Tenancy model tests."""
import pytest
from django.test import TestCase


pytestmark = pytest.mark.django_db


class TenancyConfigModelTests(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)
