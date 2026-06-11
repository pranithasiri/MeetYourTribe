import unittest
from fastapi.testclient import TestClient
import os
import database
import matcher
from main import app

class TestMatchmakerBackend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Initialize/Verify database is seeded
        database.init_db()
        cls.client = TestClient(app)
        
    def test_database_seeding(self):
        """Test if the database seeded the mock profiles and groups successfully."""
        profiles = database.get_profiles()
        self.assertGreaterEqual(len(profiles), 8)
        
        groups = database.get_groups()
        self.assertGreaterEqual(len(groups), 3)
        
        # Verify first seed profile
        elena = database.get_profile(1)
        self.assertEqual(elena['name'], "Dr. Elena Rostova")
        self.assertEqual(elena['company'], "DeepMind Technologies")

    def test_matching_algorithm(self):
        """Test if profile matches score is calculated and sorted correctly."""
        # Calculate matches for Dr. Elena Rostova (id=1)
        matches = matcher.compute_profile_matches(1)
        self.assertGreater(len(matches), 0)
        
        # Verify match score is between 30 and 100
        for m in matches:
            self.assertTrue(30.0 <= m['match_score'] <= 100.0)
            self.assertIsNotNone(m['icebreaker'])
            
        # Verify matches are sorted in descending order
        scores = [m['match_score'] for m in matches]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_feedback_loop_mechanism(self):
        """Test if submitting feedback adjusts match score ranking."""
        active_id = 1
        other_id = 2 # Aravind Reddy
        
        # Get baseline match details
        matches_baseline = matcher.compute_profile_matches(active_id)
        baseline_score = next(m['match_score'] for m in matches_baseline if m['profile']['id'] == other_id)
        
        # Submit poor feedback rating (1 star)
        database.save_feedback(active_id, other_id, 1, "Not relevant to my current focus")
        
        # Re-compute and verify score is penalized
        matches_penalized = matcher.compute_profile_matches(active_id)
        penalized_score = next(m['match_score'] for m in matches_penalized if m['profile']['id'] == other_id)
        
        self.assertLess(penalized_score, baseline_score)
        
        # Clean up by removing feedback rating
        database.save_feedback(active_id, other_id, None, None)

    def test_simulated_icebreaker_generation(self):
        """Test simulated icebreaker logic matches profile synergy fields."""
        elena = database.get_profile(1)
        liam = database.get_profile(5)
        
        icebreaker = matcher.create_simulated_icebreaker(elena, liam)
        self.assertIn("Liam", icebreaker)
        self.assertIn("DeepMind Technologies", icebreaker)
        # They share "Agentic Workflows" / "Autonomous Agents" focus
        self.assertTrue(any(word in icebreaker.lower() for word in ["agent", "sandbox", "deepmind", "collaborate"]))

    def test_api_session_endpoints(self):
        """Test session state API endpoints."""
        # Log in first to set session cookie
        login_res = self.client.post("/api/login", json={
            "email": "elena.rostova@deepmind.example.com",
            "password": "password123"
        })
        self.assertEqual(login_res.status_code, 200)

        # Get current session
        res = self.client.get("/api/session")
        self.assertEqual(res.status_code, 200)
        self.assertIn("current_user_id", res.json())
        
        # Switch session
        res = self.client.post("/api/act-as/3")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["current_user_id"], 3)
        
        # Verify persistence of session active user in local calls
        res = self.client.get("/api/session")
        self.assertEqual(res.json()["current_user_id"], 3)
        
        # Revert session back to 1
        self.client.post("/api/act-as/1")

    def test_api_matches_endpoint(self):
        """Test matches retrieval via HTTP API."""
        res = self.client.get("/api/profiles/1/matches")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data), 0)
        self.assertIn("match_score", data[0])
        self.assertIn("icebreaker", data[0])

if __name__ == "__main__":
    unittest.main()
