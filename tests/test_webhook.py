import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.webhook import PushEventModel, WorkflowRunModel, DependencyFilePayload
from app.core.config import get_settings


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = MagicMock()
    settings.GITHUB_WEBHOOK_SECRET = "test_secret"
    settings.API_KEY = "test_api_key"
    return settings


@pytest.fixture
def sample_push_payload():
    """Sample GitHub push event payload"""
    return {
        "ref": "refs/heads/main",
        "repository": {
            "id": 123456789,
            "name": "example-repo",
            "full_name": "username/example-repo",
            "html_url": "https://github.com/username/example-repo"
        },
        "commits": [
            {
                "id": "abcdef123456",
                "message": "Update requirements.txt",
                "timestamp": "2023-01-01T12:00:00Z",
                "url": "https://github.com/username/example-repo/commit/abcdef123456",
                "author": {
                    "name": "User Name",
                    "email": "user@example.com"
                }
            }
        ],
        "head_commit": {
            "id": "abcdef123456",
            "message": "Update requirements.txt",
            "timestamp": "2023-01-01T12:00:00Z",
            "url": "https://github.com/username/example-repo/commit/abcdef123456",
            "author": {
                "name": "User Name",
                "email": "user@example.com"
            }
        },
        "pusher": {
            "name": "username",
            "email": "user@example.com"
        }
    }


@pytest.fixture
def sample_workflow_payload():
    """Sample GitHub workflow run event payload"""
    return {
        "workflow_run": {
            "id": 123456789,
            "name": "Dependency Scan",
            "head_branch": "main",
            "head_sha": "abcdef123456",
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/username/example-repo/actions/runs/123456789"
        },
        "repository": {
            "id": 123456789,
            "name": "example-repo",
            "full_name": "username/example-repo",
            "html_url": "https://github.com/username/example-repo"
        }
    }


@pytest.fixture
def sample_dependency_payload():
    """Sample dependency file payload"""
    return {
        "repository": "username/example-repo",
        "branch": "main",
        "commit_sha": "abcdef123456",
        "file_type": "requirements.txt",
        "file_content": "requests==2.28.1\npytest==7.1.2\nflask==2.0.1\n"
    }


def create_github_signature(payload: str, secret: str) -> str:
    """Create GitHub webhook signature"""
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"


class TestWebhookModels:
    """Test webhook data models"""
    
    def test_push_event_model_validation(self, sample_push_payload):
        """Test PushEventModel validation with valid data"""
        event = PushEventModel(**sample_push_payload)
        
        assert event.ref == "refs/heads/main"
        assert event.repository["name"] == "example-repo"
        assert len(event.commits) == 1
        assert event.head_commit.id == "abcdef123456"
        assert event.pusher["name"] == "username"
    
    def test_workflow_run_model_validation(self, sample_workflow_payload):
        """Test WorkflowRunModel validation with valid data"""
        event = WorkflowRunModel(**sample_workflow_payload)
        
        assert event.workflow_run["name"] == "Dependency Scan"
        assert event.workflow_run["head_branch"] == "main"
        assert event.repository["full_name"] == "username/example-repo"
    
    def test_dependency_file_payload_validation(self, sample_dependency_payload):
        """Test DependencyFilePayload validation with valid data"""
        payload = DependencyFilePayload(**sample_dependency_payload)
        
        assert payload.repository == "username/example-repo"
        assert payload.branch == "main"
        assert payload.file_type == "requirements.txt"
        assert "requests==2.28.1" in payload.file_content


class TestWebhookSecurity:
    """Test webhook security and signature verification"""
    
    @patch('app.core.security.get_settings')
    def test_valid_github_signature(self, mock_get_settings, client, sample_push_payload):
        """Test webhook with valid GitHub signature"""
        mock_get_settings.return_value.GITHUB_WEBHOOK_SECRET = "test_secret"
        
        payload_str = json.dumps(sample_push_payload)
        signature = create_github_signature(payload_str, "test_secret")
        
        with patch('app.api.routes.webhook.process_github_event') as mock_process:
            mock_process.return_value = {"status": "processed"}
            
            response = client.post(
                "/api/webhook/github",
                content=payload_str,
                headers={
                    "X-Hub-Signature-256": signature,
                    "X-GitHub-Event": "push",
                    "Content-Type": "application/json"
                }
            )
            
            assert response.status_code == 200
            mock_process.assert_called_once()
    
    @patch('app.core.security.get_settings')
    def test_invalid_github_signature(self, mock_get_settings, client, sample_push_payload):
        """Test webhook with invalid GitHub signature"""
        mock_get_settings.return_value.GITHUB_WEBHOOK_SECRET = "test_secret"
        
        payload_str = json.dumps(sample_push_payload)
        invalid_signature = "sha256=invalid_signature"
        
        response = client.post(
            "/api/webhook/github",
            content=payload_str,
            headers={
                "X-Hub-Signature-256": invalid_signature,
                "X-GitHub-Event": "push",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 403
        assert "Invalid signature" in response.json()["detail"]
    
    def test_missing_signature_header(self, client, sample_push_payload):
        """Test webhook without signature header"""
        payload_str = json.dumps(sample_push_payload)
        
        response = client.post(
            "/api/webhook/github",
            content=payload_str,
            headers={
                "X-GitHub-Event": "push",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 401
        assert "X-Hub-Signature-256 header is missing" in response.json()["detail"]


class TestWebhookEndpoints:
    """Test webhook API endpoints"""
    
    @patch('app.core.security.get_settings')
    @patch('app.api.routes.webhook.process_github_event')
    def test_github_webhook_push_event(self, mock_process, mock_get_settings, client, sample_push_payload):
        """Test GitHub webhook with push event"""
        mock_get_settings.return_value.GITHUB_WEBHOOK_SECRET = "test_secret"
        mock_process.return_value = {"status": "processed", "scanned_files": 1}
        
        payload_str = json.dumps(sample_push_payload)
        signature = create_github_signature(payload_str, "test_secret")
        
        response = client.post(
            "/api/webhook/github",
            content=payload_str,
            headers={
                "X-Hub-Signature-256": signature,
                "X-GitHub-Event": "push",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        mock_process.assert_called_once_with("push", sample_push_payload)
    
    @patch('app.core.security.get_settings')
    @patch('app.api.routes.webhook.process_github_event')
    def test_github_webhook_workflow_event(self, mock_process, mock_get_settings, client, sample_workflow_payload):
        """Test GitHub webhook with workflow run event"""
        mock_get_settings.return_value.GITHUB_WEBHOOK_SECRET = "test_secret"
        mock_process.return_value = {"status": "processed"}
        
        payload_str = json.dumps(sample_workflow_payload)
        signature = create_github_signature(payload_str, "test_secret")
        
        response = client.post(
            "/api/webhook/github",
            content=payload_str,
            headers={
                "X-Hub-Signature-256": signature,
                "X-GitHub-Event": "workflow_run",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "processed"
        mock_process.assert_called_once_with("workflow_run", sample_workflow_payload)
    
    @patch('app.core.security.get_settings')
    def test_github_webhook_unsupported_event(self, mock_get_settings, client):
        """Test GitHub webhook with unsupported event type"""
        mock_get_settings.return_value.GITHUB_WEBHOOK_SECRET = "test_secret"
        
        payload = {"action": "opened"}
        payload_str = json.dumps(payload)
        signature = create_github_signature(payload_str, "test_secret")
        
        response = client.post(
            "/api/webhook/github",
            content=payload_str,
            headers={
                "X-Hub-Signature-256": signature,
                "X-GitHub-Event": "pull_request",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        assert "ignored" in response.json()["status"]
    
    @patch('app.core.security.get_api_key')
    @patch('app.services.scanner.osv.scan_dependencies')
    def test_dependency_scan_webhook(self, mock_scan, mock_api_key, client, sample_dependency_payload):
        """Test dependency scan webhook endpoint"""
        mock_api_key.return_value = "test_api_key"
        
        # Mock scan result
        mock_scan_result = MagicMock()
        mock_scan_result.repository = "username/example-repo"
        mock_scan_result.has_vulnerabilities = False
        mock_scan_result.vulnerabilities = []
        mock_scan_result.dependencies_count = 3
        mock_scan.return_value = mock_scan_result
        
        response = client.post(
            "/api/webhook/scan",
            json=sample_dependency_payload,
            headers={"X-API-Key": "test_api_key"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["repository"] == "username/example-repo"
        assert result["status"] == "completed"
        mock_scan.assert_called_once()
    
    def test_dependency_scan_webhook_unauthorized(self, client, sample_dependency_payload):
        """Test dependency scan webhook without API key"""
        response = client.post(
            "/api/webhook/scan",
            json=sample_dependency_payload
        )
        
        assert response.status_code == 401


class TestWebhookProcessing:
    """Test webhook event processing logic"""
    
    @patch('app.services.github.get_dependency_files')
    @patch('app.services.scanner.osv.scan_dependencies')
    async def test_process_push_event_with_dependency_files(self, mock_scan, mock_get_files):
        """Test processing push event that includes dependency files"""
        from app.api.routes.webhook import process_github_event
        
        # Mock dependency files found
        mock_get_files.return_value = [
            {
                "path": "requirements.txt",
                "content": "requests==2.28.1\nflask==2.0.1",
                "type": "requirements.txt"
            }
        ]
        
        # Mock scan result
        mock_scan_result = MagicMock()
        mock_scan_result.has_vulnerabilities = False
        mock_scan.return_value = mock_scan_result
        
        result = await process_github_event("push", {
            "repository": {"full_name": "username/repo"},
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123"}
        })
        
        assert result["status"] == "processed"
        assert result["scanned_files"] == 1
        mock_get_files.assert_called_once()
        mock_scan.assert_called_once()
    
    @patch('app.services.github.get_dependency_files')
    async def test_process_push_event_no_dependency_files(self, mock_get_files):
        """Test processing push event with no dependency files"""
        from app.api.routes.webhook import process_github_event
        
        # Mock no dependency files found
        mock_get_files.return_value = []
        
        result = await process_github_event("push", {
            "repository": {"full_name": "username/repo"},
            "ref": "refs/heads/main",
            "head_commit": {"id": "abc123"}
        })
        
        assert result["status"] == "no_dependency_files"
        mock_get_files.assert_called_once()
    
    async def test_process_unsupported_event(self):
        """Test processing unsupported event type"""
        from app.api.routes.webhook import process_github_event
        
        result = await process_github_event("pull_request", {})
        
        assert result["status"] == "ignored"
        assert "unsupported" in result["message"]


class TestWebhookIntegration:
    """Integration tests for webhook functionality"""
    
    @patch('app.core.security.get_settings')
    @patch('app.services.github.get_dependency_files')
    @patch('app.services.scanner.osv.scan_dependencies')
    @patch('app.services.notification.email.send_vulnerability_notification')
    def test_end_to_end_webhook_with_vulnerabilities(
        self, mock_notify, mock_scan, mock_get_files, mock_get_settings, 
        client, sample_push_payload
    ):
        """Test complete webhook flow when vulnerabilities are found"""
        mock_get_settings.return_value.GITHUB_WEBHOOK_SECRET = "test_secret"
        
        # Mock dependency files
        mock_get_files.return_value = [
            {
                "path": "requirements.txt",
                "content": "requests==2.28.1",
                "type": "requirements.txt"
            }
        ]
        
        # Mock scan result with vulnerabilities
        mock_scan_result = MagicMock()
        mock_scan_result.has_vulnerabilities = True
        mock_scan_result.vulnerabilities = [MagicMock()]
        mock_scan_result.dependencies_count = 1
        mock_scan.return_value = mock_scan_result
        
        payload_str = json.dumps(sample_push_payload)
        signature = create_github_signature(payload_str, "test_secret")
        
        response = client.post(
            "/api/webhook/github",
            content=payload_str,
            headers={
                "X-Hub-Signature-256": signature,
                "X-GitHub-Event": "push",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "processed"
        assert result["scanned_files"] == 1
        
        # Verify notification was triggered
        mock_notify.assert_called_once()
        mock_scan.assert_called_once()