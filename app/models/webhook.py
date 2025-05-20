from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class GitHubEventType(str, Enum):
    """GitHub webhook event types we're interested in"""
    PUSH = "push"  # When commits are pushed to a branch
    WORKFLOW_RUN = "workflow_run"  # When a GitHub Action workflow completes


class CommitModel(BaseModel):
    """GitHub commit information"""
    id: str
    message: str
    timestamp: datetime
    url: str
    author: Dict[str, Any]


class PushEventModel(BaseModel):
    """Model for GitHub push events"""
    ref: str  # Branch that was pushed to
    repository: Dict[str, Any]
    commits: List[CommitModel]
    head_commit: Optional[CommitModel]
    pusher: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
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
                        "message": "Update dependencies",
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
                    "message": "Update dependencies",
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
        }


class WorkflowRunModel(BaseModel):
    """Model for GitHub workflow run events"""
    workflow_run: Dict[str, Any]
    repository: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
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
        }


class DependencyFilePayload(BaseModel):
    """Payload sent from GitHub Actions with dependency files"""
    repository: str = Field(..., description="Repository name (owner/repo)")
    branch: str = Field(..., description="Branch name")
    commit_sha: str = Field(..., description="Commit SHA")
    file_type: str = Field(..., description="Type of dependency file (e.g., 'requirements.txt', 'poetry.lock')")
    file_content: str = Field(..., description="Content of the dependency file")
    
    class Config:
        schema_extra = {
            "example": {
                "repository": "username/example-repo",
                "branch": "main",
                "commit_sha": "abcdef123456",
                "file_type": "requirements.txt",
                "file_content": "requests==2.28.1\npytest==7.1.2\nFlask==2.0.1\n"
            }
        }