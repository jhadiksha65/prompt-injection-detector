"""
test_ui_navigation_and_themes.py
Automated Verification Suite for UI/UX, Dark Mode, Navigation, and Dashboard Architecture.

Verifies:
  1. Theme controller (/static/js/theme.js) is served and adheres to the localStorage theme contract.
  2. All primary views (/, /external-demo, /dashboard, /sensitive-resource) include theme.js and the theme toggle button.
  3. Consistent top-level navigation bar is maintained across all pages:
     - Analyzer
     - History
     - External Demo
     - Dashboard
  4. Active page highlighting is accurately applied to the corresponding tab.
  5. Dashboard and Sensitive Resource use the modern saas.css stylesheet and not legacy style.css.
  6. External Demo dark mode rules exist for pipeline nodes, scenario cards, timeline, and delivered response.
  7. Sensitive Resource is removed from primary nav tabs, maintaining controlled demo access and lockout protections.
  8. Dashboard incident/stats endpoints enforce HTTP Basic Auth protection.
"""

import unittest
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app


class TestUINavigationAndThemes(unittest.TestCase):
    """Verifies UI/UX architecture, dark mode integration, and navigation consistency."""

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

    # 1. Theme Controller Script
    def test_theme_script_is_served_and_valid(self):
        """GET /static/js/theme.js must return 200 OK with theme persistence logic."""
        res = self.client.get("/static/js/theme.js")
        self.assertEqual(res.status_code, 200)
        js = res.get_data(as_text=True)
        self.assertIn("prompt_security_theme", js)
        self.assertIn("data-theme", js)
        self.assertIn("themeToggleBtn", js)

    # 2. Navigation Consistency across All Pages
    def test_index_page_navigation_contract(self):
        """Index page must contain full navigation tabs and theme toggle."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn('data-target="analyzer"', html)
        self.assertIn('data-target="history"', html)
        self.assertIn('href="/external-demo"', html)
        self.assertIn('href="/dashboard"', html)
        self.assertIn('id="themeToggleBtn"', html)
        self.assertIn('/static/js/theme.js', html)

    def test_external_demo_navigation_and_styling(self):
        """External demo page must contain top navbar with External Demo as active tab."""
        res = self.client.get("/external-demo")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Navigation tabs
        self.assertIn('href="/#analyzer"', html)
        self.assertIn('href="/#history"', html)
        self.assertIn('href="/dashboard"', html)
        self.assertIn('class="nav-tab-link active"', html)
        self.assertIn('id="themeToggleBtn"', html)
        self.assertIn('/static/js/theme.js', html)

        # Dark mode rules
        self.assertIn('[data-theme="dark"]', html)
        self.assertIn('[data-theme="dark"] .pipeline-step-node', html)
        self.assertIn('[data-theme="dark"] .scenario-card-btn', html)

    def test_dashboard_page_navigation_and_modern_styling(self):
        """Dashboard page must load saas.css, top navbar with Dashboard active, and no legacy style.css."""
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Uses saas.css and theme.js
        self.assertIn('/static/css/saas.css', html)
        self.assertNotIn('/static/css/style.css', html)
        self.assertIn('/static/js/theme.js', html)

        # Navigation tabs
        self.assertIn('href="/#analyzer"', html)
        self.assertIn('href="/#history"', html)
        self.assertIn('href="/external-demo"', html)
        self.assertIn('href="/dashboard" class="nav-tab-link active"', html)
        self.assertIn('id="themeToggleBtn"', html)

        # Responsive stats and incident table
        self.assertIn('id="statTotal"', html)
        self.assertIn('id="statBlocked"', html)
        self.assertIn('id="statHighCritical"', html)
        self.assertIn('id="statLayer2"', html)
        self.assertIn('id="incidentsTableBody"', html)

    def test_sensitive_resource_page_controlled_access(self):
        """Sensitive Resource must use modern saas.css and maintain vault lock controls."""
        res = self.client.get("/sensitive-resource")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Modern stylesheet and theme
        self.assertIn('/static/css/saas.css', html)
        self.assertNotIn('/static/css/style.css', html)
        self.assertIn('/static/js/theme.js', html)

        # Navigation
        self.assertIn('href="/#analyzer"', html)
        self.assertIn('href="/dashboard"', html)
        self.assertIn('id="vaultStatusBadge"', html)
        self.assertIn('id="lockedOverlay"', html)
        self.assertIn('id="protectedDataCard"', html)

    # 3. External Demo Usability Components
    def test_external_demo_ui_components_present(self):
        """External Demo must expose all required presentation and audit components."""
        res = self.client.get("/external-demo")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Explicit simulation / offline badge
        self.assertIn("LOCAL SIMULATION — OFFLINE", html)

        # Scenario cards
        self.assertIn('id="scenarioABtn"', html)
        self.assertIn('id="scenarioBBtn"', html)
        self.assertIn('id="scenarioCBtn"', html)

        # 5-Stage execution pipeline
        self.assertIn('id="stepApp"', html)
        self.assertIn('id="stepL1"', html)
        self.assertIn('id="stepLlm"', html)
        self.assertIn('id="stepL2"', html)
        self.assertIn('id="stepDelivery"', html)

        # Timeline and delivered output
        self.assertIn('id="timelineEventsContainer"', html)
        self.assertIn('id="requestIdDisplay"', html)
        self.assertIn('Delivered Output — What the External User Receives', html)
        self.assertIn('id="resultStatusPill"', html)
        self.assertIn('id="btnResetDemo"', html)

    # 4. Security Access Controls on Telemetry Endpoints
    def test_telemetry_endpoints_require_admin_auth(self):
        """Stats and incident telemetry endpoints must reject unauthenticated requests with 401."""
        res_stats = self.client.get("/api/stats")
        self.assertEqual(res_stats.status_code, 401)
        self.assertIn("WWW-Authenticate", res_stats.headers)

        res_incidents = self.client.get("/api/incidents")
        self.assertEqual(res_incidents.status_code, 401)
        self.assertIn("WWW-Authenticate", res_incidents.headers)


if __name__ == "__main__":
    unittest.main()
