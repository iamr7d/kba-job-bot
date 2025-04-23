import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.job_alerts import job_alerts

class TestJobAlerts(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.job_alerts.scrape_jobs')
    @patch('handlers.job_alerts.score')
    async def test_job_alerts_basic(self, mock_score, mock_scrape_jobs):
        # Mock job data
        # Simulate a DataFrame with .empty, .groupby().head().iterrows(), .head().iterrows()
        job_row = {'job_url': 'http://job', 'title': 'Engineer', 'company': 'TestCorp', 'location': 'Remote', 'description': 'Great job', 'site_name': 'indeed'}
        class DFMock:
            empty = False
            def groupby(self, x):
                return self
            def head(self, n):
                return self
            def iterrows(self):
                return iter([(0, job_row)])
            def __contains__(self, item):
                return item == 'site'
            def reset_index(self, drop=True):
                return self
        mock_scrape_jobs.return_value = DFMock()

        mock_score.return_value = 80
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_message = update.message  # Patch for interactive job alerts
        update.effective_user.id = 123
        context = MagicMock()
        context.user_data = {'gemini_jobs': ['Engineer'], 'gemini_keywords': ['Python']}
        context.bot = MagicMock()
        await job_alerts(update, context)
        calls = [call.args[0] for call in update.message.reply_text.call_args_list]
        assert any('New Job Match' in msg and 'Engineer' in msg and 'TestCorp' in msg for msg in calls)

if __name__ == "__main__":
    unittest.main()
