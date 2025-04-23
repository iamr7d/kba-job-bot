import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from handlers.ai_job_search import ai_job_search
from unittest.mock import patch, MagicMock, AsyncMock

class TestAIJobSearch(unittest.IsolatedAsyncioTestCase):
    @patch('handlers.ai_job_search.scrape_linkedin')
    @patch('handlers.ai_job_search.scrape_indeed')
    @patch('handlers.ai_job_search.gemini_client')
    async def test_ai_job_search_basic(self, mock_gemini, mock_indeed, mock_linkedin):
        # Mock Gemini generate_content
        mock_gemini.models.generate_content.return_value.text = '80 Good match.'

        # Mock job data
        job_row = {
            'title': 'AI Engineer',
            'company': 'TestCorp',
            'location': 'Remote',
            'link': 'http://job',
            'desc': 'Great job',
            'source': 'LinkedIn',
        }
        mock_linkedin.return_value = [job_row]
        mock_indeed.return_value = []

        update = MagicMock()
        update.message.reply_text = AsyncMock()
        update.effective_message = update.message
        update.effective_user.id = 123
        context = MagicMock()
        context.user_data = {}
        context.bot = MagicMock()

        await ai_job_search(update, context)
        calls = [call.args[0] for call in update.message.reply_text.call_args_list]
        assert any('New Job Match' in msg and 'AI Engineer' in msg and 'TestCorp' in msg for msg in calls)

if __name__ == "__main__":
    unittest.main()
