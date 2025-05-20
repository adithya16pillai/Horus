from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.models.dependency import PackageDependency, DependencyFileContent, DependencyFileType, PackageEcosystem


class DependencyParser(ABC):
    """Base class for all dependency file parsers"""
    
    def __init__(self, file_content: str):
        """
        Initialize the parser with file content.
        
        Args:
            file_content: The raw contents of the dependency file
        """
        self.file_content = file_content
    
    @abstractmethod
    def parse(self) -> DependencyFileContent:
        """
        Parse the dependency file content.
        
        Returns:
            DependencyFileContent: The parsed dependency information
        """
        pass
    
    @property
    @abstractmethod
    def file_type(self) -> DependencyFileType:
        """
        Get the file type that this parser handles.
        
        Returns:
            DependencyFileType: The type of dependency file
        """
        pass
    
    @property
    @abstractmethod
    def ecosystem(self) -> PackageEcosystem:
        """
        Get the package ecosystem for this parser.
        
        Returns:
            PackageEcosystem: The package ecosystem
        """
        pass


class ParserFactory:
    """Factory for creating appropriate parser based on file type"""
    
    @staticmethod
    def create_parser(file_type: str, file_content: str) -> DependencyParser:
        """
        Create a parser for the given file type.
        
        Args:
            file_type: The type of dependency file
            file_content: The raw contents of the dependency file
            
        Returns:
            DependencyParser: An appropriate parser instance
            
        Raises:
            ValueError: If the file type is not supported
        """
        from app.services.parser.pip import RequirementsTxtParser
        from app.services.parser.poetry import PoetryLockParser
        
        # Map file types to parser classes
        parser_map = {
            DependencyFileType.REQUIREMENTS_TXT: RequirementsTxtParser,
            DependencyFileType.POETRY_LOCK: PoetryLockParser,
            # Add other parsers as they are implemented
        }
        
        # Convert string to enum
        try:
            file_type_enum = DependencyFileType(file_type)
        except ValueError:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Get parser class or raise error
        parser_class = parser_map.get(file_type_enum)
        if not parser_class:
            raise ValueError(f"No parser available for file type: {file_type}")
        
        return parser_class(file_content)