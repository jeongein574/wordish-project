from django.test import TestCase

# Create your tests here.
from django.urls import reverse
import re
import os

class HiddenFieldTests(TestCase):
    def test_malformed_game_over_bounces_to_start(self):
        resp = self.client.post(reverse("game"), {"target_text": "delve"})
        self.assertContains(resp, "Game started", status_code=200)

        payload = {
            "target": "DELVE",
            "grid_json": '[{"letters":"","classes":["state-empty"]*5}]*6'.replace("*5","").replace("*6",""),
            "row_index": "0",
            "game_over": "blahblah", 
            "guess_text": "first",
        }
        resp = self.client.post(reverse("game"), payload)
        self.assertTemplateUsed(resp, "wordish/start.html")
        self.assertContains(resp, "error", status_code=200)
        self.assertContains(resp, "invalid", status_code=200)

class InvalidTargetTests(TestCase):
    def _post_target(self, txt):
        """Helper to hit the start form."""
        return self.client.post(reverse("game"), {"target_text": txt})

    def test_target_too_short_shows_invalid_input(self):
        resp = self._post_target("test")
        self.assertTemplateUsed(resp, "wordish/start.html")
        self.assertContains(resp, "invalid input")   

    def test_target_with_non_letters_shows_invalid_input(self):
        resp = self._post_target("we<3u")
        self.assertTemplateUsed(resp, "wordish/start.html")
        self.assertContains(resp, "invalid input")

    def test_valid_target_starts_game(self):
        resp = self._post_target("delve")
        self.assertTemplateUsed(resp, "wordish/game.html")
        self.assertContains(resp, "Game started")     

class InitialContactTests(TestCase):
    def test_start_page_has_message_area_and_welcome_text(self):
        """
        GET / should render start.html, include a #message element,
        and the message text should contain 'welcome'.
        """
        resp = self.client.get(reverse("start")) 
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "wordish/start.html")
        self.assertContains(resp, 'id="message"', html=False)
        self.assertTrue(
            re.search(r"welcome", resp.content.decode("utf-8"), re.IGNORECASE),
            "Start page should contain the word 'welcome' in the #message area.",
        )

    def test_start_button_leads_to_game_and_status_contains_start(self):
        """
        POST a valid target_text; game page should render with #status
        containing the word 'start' (e.g., 'Game started...').
        """
        resp = self.client.post(reverse("game"), {"target_text": "delve"})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "wordish/game.html")
        self.assertContains(resp, 'id="status"', html=False)
        self.assertTrue(
            re.search(r"start", resp.content.decode("utf-8"), re.IGNORECASE),
            "Game page status should include 'start' (e.g., 'Game started...').",
        )

    def test_structure_ids_present(self):
        """
        Smoke test for required IDs: #message on start; #status on game.
        """
        r1 = self.client.get(reverse("start"))
        self.assertContains(r1, 'id="message"', html=False)

        r2 = self.client.post(reverse("game"), {"target_text": "delve"})
        self.assertContains(r2, 'id="status"', html=False)


class CSSMessageStyleTests(TestCase):
    def test_message_has_background_color_rule(self):
        css_path = os.path.join(os.path.dirname(__file__), "static", "wordish", "wordish.css")
        with open(css_path) as f:
            css = f.read()

        self.assertIn("#message", css)
        self.assertIn("background-color", css)

class MalformedGridJsonTests(TestCase):
    def test_malformed_grid_json_bounces_to_start(self):
        resp = self.client.post(reverse("game"), {"target_text": "delve"})
        self.assertContains(resp, "Game started")

        payload = {
            "target": "DELVE",
            "grid_json": "blahblah",  
            "row_index": "0",
            "game_over": "0",
            "guess_text": "first",
        }

        resp = self.client.post(reverse("game"), payload)

        self.assertTemplateUsed(resp, "wordish/start.html")

        self.assertContains(resp, 'id="message"', html=False)
        content = resp.content.decode("utf-8").lower()
        self.assertIn("error", content)
        self.assertIn("invalid", content)