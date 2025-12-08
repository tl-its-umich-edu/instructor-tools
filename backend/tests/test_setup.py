# backend/test_setup.py
from django.test.runner import DiscoverRunner

class CustomTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)