import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient


def parse_hhmmss(value: str) -> int:
    hours, minutes, seconds = map(int, value.split(":"))
    return hours * 3600 + minutes * 60 + seconds


@pytest.mark.integration
class TestAnalyticsSummary:
    """Test user analytics summary endpoint."""

    def test_get_analytics_summary_success(self, client: TestClient, test_user_data, test_organization_data):
        """Test retrieving analytics summary successfully."""
        # 1. Register admin
        client.post("/api/v1/auth/register", json=test_user_data)

        # 2. Login
        login_response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user_data["email"],
                "password": test_user_data["password"],
            },
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create organization to link admin
        client.post(
            "/api/v1/organizations/create",
            json=test_organization_data,
            headers=headers,
        )

        # 4. Record some browser activities
        now = datetime.now(timezone.utc)

        # Activity 1: Development, productive, github.com, 100 seconds
        activity_1 = {
            "browser_name": "Chrome",
            "website_url": "https://github.com/Toney/FocusGuardAI",
            "website_domain": "github.com",
            "page_title": "Toney/FocusGuardAI: Enterprise productivity platform",
            "session_start_time": (now - timedelta(seconds=100)).isoformat(),
            "session_end_time": now.isoformat(),
        }
        resp = client.post("/api/v1/analytics/activity", json=activity_1, headers=headers)
        assert resp.status_code == 201

        # Activity 2: AI Tool, productive, chat.openai.com, 60 seconds
        activity_2 = {
            "browser_name": "Chrome",
            "website_url": "https://chat.openai.com/chat",
            "website_domain": "chat.openai.com",
            "page_title": "ChatGPT",
            "session_start_time": (now - timedelta(seconds=160)).isoformat(),
            "session_end_time": (now - timedelta(seconds=100)).isoformat(),
        }
        resp = client.post("/api/v1/analytics/activity", json=activity_2, headers=headers)
        assert resp.status_code == 201

        # Activity 3: Entertainment, non_productive, youtube.com, 30 seconds
        activity_3 = {
            "browser_name": "Chrome",
            "website_url": "https://www.youtube.com/watch?v=123",
            "website_domain": "youtube.com",
            "page_title": "YouTube Video",
            "session_start_time": (now - timedelta(seconds=200)).isoformat(),
            "session_end_time": (now - timedelta(seconds=170)).isoformat(),
        }
        resp = client.post("/api/v1/analytics/activity", json=activity_3, headers=headers)
        assert resp.status_code == 201

        # 5. Fetch Summary
        summary_resp = client.get("/api/v1/analytics/summary/my", headers=headers)
        assert summary_resp.status_code == 200
        summary = summary_resp.json()

        # 6. Assert user info
        assert summary["user"]["email"] == test_user_data["email"]
        assert summary["user"]["username"] == test_user_data["full_name"]

        # 7. Assert totals
        assert summary["total_websites_visited"] == 3
        assert summary["total_tab_switches"] == 3
        # Total time is 100 + 60 + 30 = 190 seconds (03 mins 10 secs -> 00:03:10)
        assert summary["total_time"] == "00:03:10"

        # 8. Assert productivity times
        # Productive: GitHub (100) + ChatGPT (60) = 160 seconds -> 00:02:40
        assert summary["productive_time"] == "00:02:40"
        # Non-productive: YouTube (30) = 30 seconds -> 00:00:30
        assert summary["non_productive_time"] == "00:00:30"
        # Neutral: 0
        assert summary["neutral_time"] == "00:00:00"

        # 9. Assert last activity timestamp (latest session_end_time)
        assert summary["last_activity_at"] is not None
        last_activity_at = datetime.fromisoformat(
            summary["last_activity_at"].replace("Z", "+00:00")
        )
        if last_activity_at.tzinfo is None:
            last_activity_at = last_activity_at.replace(tzinfo=timezone.utc)
        assert last_activity_at == now

        # 10. Assert categories (ordered array, highest time first)
        categories = summary["category_summary"]
        assert isinstance(categories, list)
        assert len(categories) == 3

        assert categories[0]["category"] == "Development"
        assert categories[0]["time_spent"] == "00:01:40"
        assert categories[0]["duration_seconds"] == 100
        assert categories[0]["percentage"] == 52.63

        assert categories[1]["category"] == "AI Tool"
        assert categories[1]["time_spent"] == "00:01:00"
        assert categories[1]["duration_seconds"] == 60
        assert categories[1]["percentage"] == 31.58

        assert categories[2]["category"] == "Entertainment"
        assert categories[2]["time_spent"] == "00:00:30"
        assert categories[2]["duration_seconds"] == 30
        assert categories[2]["percentage"] == 15.79

        category_names = {item["category"] for item in categories}
        assert "Social Media" not in category_names
        assert "Education" not in category_names
        assert "Shopping" not in category_names

        category_durations = [item["duration_seconds"] for item in categories]
        assert category_durations == sorted(category_durations, reverse=True)

        for item in categories:
            assert item["duration_seconds"] == parse_hhmmss(item["time_spent"])
            assert item["percentage"] > 0

        category_percentage_sum = sum(item["percentage"] for item in categories)
        assert category_percentage_sum == pytest.approx(100.0, abs=0.01)

        # 11. Assert website summaries (ordered array, highest time first)
        websites = summary["website_summary"]
        assert isinstance(websites, list)
        assert len(websites) == 3

        names = {site["name"] for site in websites}
        assert "GitHub" in names
        assert "ChatGPT" in names
        assert "YouTube" in names or "Youtube" in names

        github_sum = next(site for site in websites if site["name"] == "GitHub")
        assert github_sum["domain"] == "github.com"
        assert github_sum["time_spent"] == "00:01:40"
        assert github_sum["duration_seconds"] == 100
        assert github_sum["percentage"] == 52.63
        assert github_sum["visits"] == 1
        assert "github.com" in github_sum["url"]

        assert websites[0]["name"] == "GitHub"
        assert websites[0]["time_spent"] == "00:01:40"
        assert websites[0]["duration_seconds"] == 100
        assert websites[1]["name"] == "ChatGPT"
        assert websites[1]["time_spent"] == "00:01:00"
        assert websites[1]["duration_seconds"] == 60
        assert websites[2]["name"] in ("YouTube", "Youtube")
        assert websites[2]["time_spent"] == "00:00:30"
        assert websites[2]["duration_seconds"] == 30

        website_durations = [site["duration_seconds"] for site in websites]
        assert website_durations == sorted(website_durations, reverse=True)

        for site in websites:
            assert site["duration_seconds"] == parse_hhmmss(site["time_spent"])
            assert site["time_spent"] != "00:00:00"
            assert site["visits"] > 0
            assert site["domain"]
            assert site["url"]
            assert site["percentage"] > 0

        website_percentage_sum = sum(site["percentage"] for site in websites)
        assert website_percentage_sum == pytest.approx(100.0, abs=0.01)

    def test_get_analytics_summary_unauthorized(self, client: TestClient):
        """Test retrieving analytics summary without JWT."""
        response = client.get("/api/v1/analytics/summary/my")
        assert response.status_code == 401
