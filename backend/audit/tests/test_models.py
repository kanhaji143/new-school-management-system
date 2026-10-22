"""Audit model tests."""
import pytest
from django.test import TestCase


pytestmark = pytest.mark.django_db


class AuditConfigModelTests(TestCase):
    def test_placeholder(self):
        self.assertTrue(True)
