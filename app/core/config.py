from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List, Optional
import os
from enum import Enum
from functools import lru_cache


class NotificationMethod(str, Enum):
    EMAIL = "email"
    SLACK = "slack" 
    DISCORD = "discord"
    ALL = "all"


class Settings(BaseSettings):
    # API Configuration
    API_KEY: str
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "Dependency Scanner"
    VERSION: str = "0.1.0"
    
    # GitHub API Configuration
    GITHUB_TOKEN: str
    GITHUB_WEBHOOK_SECRET: str
    
    # Vulnerability Scanner APIs
    OSV_API_URL: str = "https://api.osv.dev/v1"
    GITHUB_GRAPHQL_URL: str = "https://api.github.com/graphql"
    
    # Notification Configuration
    NOTIFICATION_METHOD: NotificationMethod = NotificationMethod.EMAIL
    
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_TO: Optional[str] = None
    
    DATABASE_URL: str = "sqlite:///./horus.db"
    
    @validator('EMAIL_TO', pre=True)
    def split_email_string(cls, v):
        if isinstance(v, str) and ',' in v:
            return v.split(',')
        return v
    
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    DISCORD_WEBHOOK_URL: Optional[str] = None
    
    @validator('NOTIFICATION_METHOD')
    def check_notification_config(cls, v, values):
        if v in [NotificationMethod.EMAIL, NotificationMethod.ALL]:
            required_fields = ['SMTP_SERVER', 'SMTP_PORT', 'SMTP_USERNAME', 
                               'SMTP_PASSWORD', 'EMAIL_FROM', 'EMAIL_TO']
            missing = [f for f in required_fields if not values.get(f)]
            if missing:
                raise ValueError(f"Email notification selected but missing: {', '.join(missing)}")
                
        if v in [NotificationMethod.SLACK, NotificationMethod.ALL]:
            if not values.get('SLACK_WEBHOOK_URL'):
                raise ValueError("Slack notification selected but SLACK_WEBHOOK_URL is missing")
                
        if v in [NotificationMethod.DISCORD, NotificationMethod.ALL]:
            if not values.get('DISCORD_WEBHOOK_URL'):
                raise ValueError("Discord notification selected but DISCORD_WEBHOOK_URL is missing")
        
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Create cached instance of settings"""
    return Settings()