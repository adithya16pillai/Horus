import re
from typing import List, Dict, Any, Optional

from app.models.dependency import (
    PackageDependency, 
    DependencyFileContent, 
    DependencyFileType, 
    PackageEcosystem
)
from app.services.parser.base import DependencyParser


class RequirementsTxtParser(DependencyParser):
    """Parser for requirements.txt files"""
    
    @property
    def file_type(self) -> DependencyFileType:
        return DependencyFileType.REQUIREMENTS_TXT
    
    @property
    def ecosystem(self) -> PackageEcosystem:
        return PackageEcosystem.PYPI
    
    def parse(self) -> DependencyFileContent:
        """
        Parse requirements.txt file content.
        
        Returns:
            DependencyFileContent: The parsed dependency information
        """
        dependencies = []
        
        # Split the file content by lines and process each line
        for line in self.file_content.splitlines():
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Handle line continuations
            if line.endswith('\\'):
                line = line[:-1].strip()
                
            # Skip -r, -f, -i options
            if line.startswith(('-r', '-f', '-i', '--requirement', '--find-links', '--index-url')):
                continue
                
            # Handle editable installs (-e)
            if line.startswith('-e'):
                line = line[2:].strip()
                
            # Parse the package name and version
            package = self._parse_package(line)
            if package:
                dependencies.append(package)
                
        return DependencyFileContent(
            file_type=self.file_type,
            dependencies=dependencies
        )
    
    def _parse_package(self, line: str) -> Optional[PackageDependency]:
        """
        Parse a single package line into a PackageDependency.
        
        Args:
            line: A single line from requirements.txt
            
        Returns:
            PackageDependency: The parsed package dependency, or None if invalid
        """
        # Handle git/url installs
        if any(prefix in line for prefix in ['git+', 'http://', 'https://']):
            # Extract package name from git/url if possible
            match = re.search(r'#egg=([a-zA-Z0-9_.-]+)', line)
            if match:
                name = match.group(1)
                return PackageDependency(
                    name=name,
                    version="unknown",
                    ecosystem=self.ecosystem,
                    is_dev_dependency=False
                )
            return None
            
        # Handle normal package specifications
        # Regex to extract package name and version constraints
        pattern = r'^([a-zA-Z0-9_.-]+)(?:\[[a-zA-Z0-9_.-]+\])?(.*)$'
        match = re.match(pattern, line)
        
        if not match:
            return None
            
        name = match.group(1)
        version_constraints = match.group(2).strip()
        
        # Parse version constraints
        version = "latest"
        if version_constraints:
            # Handle exact version (==)
            exact_match = re.search(r'==\s*([a-zA-Z0-9_.-]+)', version_constraints)
            if exact_match:
                version = exact_match.group(1)
            # For simplicity, take the first version constraint if multiple are specified
            elif '>=' in version_constraints:
                match = re.search(r'>=\s*([a-zA-Z0-9_.-]+)', version_constraints)
                if match:
                    version = f">={match.group(1)}"
            elif '>' in version_constraints:
                match = re.search(r'>\s*([a-zA-Z0-9_.-]+)', version_constraints)
                if match:
                    version = f">{match.group(1)}"
            elif '<=' in version_constraints:
                match = re.search(r'<=\s*([a-zA-Z0-9_.-]+)', version_constraints)
                if match:
                    version = f"<={match.group(1)}"
            elif '<' in version_constraints:
                match = re.search(r'<\s*([a-zA-Z0-9_.-]+)', version_constraints)
                if match:
                    version = f"<{match.group(1)}"
            elif '~=' in version_constraints:
                match = re.search(r'~=\s*([a-zA-Z0-9_.-]+)', version_constraints)
                if match:
                    version = f"~={match.group(1)}"
            
        return PackageDependency(
            name=name,
            version=version,
            ecosystem=self.ecosystem,
            is_dev_dependency=False  # requirements.txt doesn't distinguish dev dependencies
        )