from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class PackageEcosystem(str, Enum):
    """Supported package ecosystems"""
    PYPI = "PyPI"       # Python packages
    NPM = "npm"         # Node.js packages
    COMPOSER = "Composer"  # PHP packages
    MAVEN = "Maven"     # Java packages
    NUGET = "NuGet"     # .NET packages
    RUBYGEMS = "RubyGems"  # Ruby packages
    CARGO = "Cargo"     # Rust packages
    GO = "Go"           # Go modules
    OTHER = "Other"     # Other ecosystems


class DependencyFileType(str, Enum):
    """Supported dependency file types"""
    REQUIREMENTS_TXT = "requirements.txt"
    POETRY_LOCK = "poetry.lock"
    PIPFILE_LOCK = "Pipfile.lock"
    PACKAGE_JSON = "package.json"
    PACKAGE_LOCK_JSON = "package-lock.json"
    YARN_LOCK = "yarn.lock"
    COMPOSER_JSON = "composer.json"
    COMPOSER_LOCK = "composer.lock"
    GEMFILE = "Gemfile"
    GEMFILE_LOCK = "Gemfile.lock"
    CARGO_LOCK = "Cargo.lock"
    GO_MOD = "go.mod"
    GO_SUM = "go.sum"
    

class PackageDependency(BaseModel):
    """Information about a package dependency"""
    name: str = Field(..., description="Package name")
    version: str = Field(..., description="Package version")
    ecosystem: PackageEcosystem = Field(PackageEcosystem.PYPI, description="Package ecosystem")
    is_dev_dependency: bool = Field(False, description="Whether this is a development dependency")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "requests",
                "version": "2.28.1",
                "ecosystem": "PyPI",
                "is_dev_dependency": False
            }
        }


class DependencyFileContent(BaseModel):
    """Contents of a parsed dependency file"""
    file_type: DependencyFileType
    dependencies: List[PackageDependency] = Field(..., description="List of dependencies")
    
    class Config:
        schema_extra = {
            "example": {
                "file_type": "requirements.txt",
                "dependencies": [
                    {
                        "name": "requests",
                        "version": "2.28.1",
                        "ecosystem": "PyPI",
                        "is_dev_dependency": False
                    },
                    {
                        "name": "pytest",
                        "version": "7.1.2",
                        "ecosystem": "PyPI",
                        "is_dev_dependency": True
                    }
                ]
            }
        }