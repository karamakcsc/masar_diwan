# Copyright (c) 2026, Masar and Contributors
# See license.txt

# import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]
IGNORE_TEST_RECORD_DEPENDENCIES = []  # eg. ["User"]


class IntegrationTestConfidentialityLevel(IntegrationTestCase):
	"""
	Integration tests for ConfidentialityLevel.
	Use this class for testing interactions between multiple components.
	"""

	pass
