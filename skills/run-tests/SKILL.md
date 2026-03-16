---
name: run-tests
description: Use when writing tests, running the test suite, creating test fixtures, or understanding test conventions including ComplianceCheckTestBase, factory patterns, and Django TestCase usage in the Appendix K project
---

# Run Tests

## Overview

pytest with Django TestCase. SQLite in tests, PostgreSQL in prod. Celery tasks run synchronously via `CELERY_TASK_ALWAYS_EAGER`. No factories — direct ORM creation in `setUp`. All test files follow `test_*.py` naming.

## Configuration

**`setup.cfg`:**
```
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests/*.py test_*.py
python_classes = Test*
python_functions = test_*
```

**`config/settings/test.py`:**
- SQLite (fast, no PostgreSQL needed)
- `MD5PasswordHasher` (faster than bcrypt)
- `CELERY_TASK_ALWAYS_EAGER = True` (sync execution)
- `CELERY_TASK_EAGER_PROPAGATES = True` (exceptions propagate)

## Running Tests

```bash
# All tests
pytest

# Single app
pytest apps/compliance/

# Single file
pytest apps/compliance/tests/test_checks.py

# Single test class
pytest apps/compliance/tests/test_checks.py::TestBiennialRefresher

# Single test
pytest apps/compliance/tests/test_checks.py::TestBiennialRefresher::test_warning_within_90_days

# With verbosity
pytest -v

# With output
pytest -s
```

## Test Base Pattern

The project uses `django.test.TestCase` (not pytest fixtures). The standard pattern:

```python
from django.test import TestCase
from apps.tenants.models import Company
from apps.accounts.models import User
from apps.operators.models import Operator


class ComplianceCheckTestBase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co', slug='test-co')
        self.user = User.objects.create_user(
            username='testop', password='testpass123',
            first_name='Test', last_name='Operator',
            company=self.company, role='operator',
        )
        self.operator = Operator.objects.create(
            company=self.company,
            user=self.user,
            employee_id='EMP001',
            qualification_status='qualified',
        )
```

**Key objects created in setUp:**
1. `Company` — the tenant
2. `User` — with company and role
3. `Operator` — linked to user and company

Subclasses inherit the base and add test-specific data.

## Writing Tests for This Project

### Step 1: Create test file in the app's tests/ directory

```
apps/myapp/tests/test_myfeature.py
```

Ensure `apps/myapp/tests/__init__.py` exists.

### Step 2: Use the standard setUp pattern

Always create Company → User → Operator chain. Every TenantModel needs a company.

### Step 3: Test conventions

```python
class TestMyFeature(TestCase):
    def setUp(self):
        # Create minimal fixture data
        self.company = Company.objects.create(name='Test Co', slug='test-co')
        # ... more setup

    def test_descriptive_name(self):
        """Docstring explaining what is being tested."""
        # Arrange — set up test-specific state
        # Act — call the function under test
        # Assert — verify the result
```

### Step 4: Use `Decimal` for hours

```python
from decimal import Decimal
self.operator.career_survey_hours = Decimal('1450.5')
```

Never use `float` for hours — the project uses `DecimalField` throughout.

### Step 5: Use `date` and `timedelta` for dates

```python
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# 90 days ago
date.today() - timedelta(days=90)

# 2 years ago
date.today() - relativedelta(years=2)
```

## API / View Tests

```python
from rest_framework.test import APITestCase, APIClient

class TestMyViewSet(APITestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co', slug='test-co')
        self.user = User.objects.create_user(
            username='admin', password='pass',
            company=self.company, role='company_admin',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_returns_company_data_only(self):
        """Verify tenant isolation — only own company data returned."""
        other = Company.objects.create(name='Other', slug='other')
        MyModel.objects.create(company=self.company, ...)
        MyModel.objects.create(company=other, ...)
        response = self.client.get('/api/v1/my-endpoint/')
        self.assertEqual(len(response.data['results']), 1)
```

**Always test tenant isolation** — create data in another company and verify it's not returned.

## Celery Task Tests

Tasks run synchronously in tests. No mocking needed:

```python
def test_nightly_check_creates_alerts(self):
    # Arrange — set up operator with overdue training
    self.operator.last_classroom_training_date = date.today() - relativedelta(years=3)
    self.operator.save()

    # Act — call task directly (runs synchronously)
    from apps.compliance.tasks import run_nightly_compliance_checks
    run_nightly_compliance_checks()

    # Assert
    self.assertEqual(ComplianceAlert.objects.filter(operator=self.operator).count(), 1)
```

## Signal Tests

Signals fire automatically on `.save()` and `.create()`. Test the side effects:

```python
def test_survey_save_updates_operator_hours(self):
    Survey.objects.create(
        company=self.company,
        operator=self.operator,
        facility=self.facility,
        survey_date=date.today(),
        total_survey_hours=Decimal('5.0'),
    )
    self.operator.refresh_from_db()
    self.assertEqual(self.operator.career_survey_hours, Decimal('5.0'))
```

**Note:** `bulk_create` does NOT trigger signals. If testing import handlers that use bulk_create, verify the manual post-processing calls happen.

## Common Mistakes

- **Using `pytest` fixtures instead of `setUp`** — the project convention is Django TestCase with setUp
- **Forgetting `refresh_from_db()`** — after signals modify the operator, the in-memory object is stale
- **Using `float` instead of `Decimal`** for hour values — causes assertion failures due to precision
- **Not creating the Company/User/Operator chain** — TenantModel objects require a company FK
- **Testing API endpoints without `force_authenticate`** — returns 401
- **Assuming `bulk_create` triggers signals** — it doesn't; test the manual handler calls instead
- **Not testing tenant isolation** — create data in two companies, verify each only sees their own


## Amendments
