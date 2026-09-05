"""Helper validators for CV parsing."""

import re
from datetime import datetime
from typing import Optional, Tuple


class EmailValidator:
    """Email validation helper."""

    # Simple but effective regex for email
    PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
"""Helper validators for CV parsing."""

import re
from datetime import datetime
from typing import Optional, Tuple


class EmailValidator:
    """Email validation helper."""

    # Simple but effective regex for email
    PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email format is valid."""
        return bool(cls.PATTERN.match(email.strip()))

    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """Extract first valid email from text."""
        # More permissive pattern for extraction
        pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None


class PhoneValidator:
    """Phone number validation helper."""

    # Pattern for common international formats
    PATTERN = re.compile(
        r'(?:\+\d{1,3})?[-.\s]?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
    )

    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """Extract first valid phone from text."""
        match = cls.PATTERN.search(text)
        return match.group(0).strip() if match else None


class DateParser:
    """Date parsing helper for work experience."""

    # Common date formats
    FORMATS = [
        "%Y-%m",           # 2020-01
        "%Y/%m",           # 2020/01
        "%B %Y",           # January 2020
        "%b %Y",           # Jan 2020
        "%Y",              # 2020 (year only)
        "%m/%Y",           # 01/2020
    ]

    MONTH_MAPPING = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }

    @classmethod
    def parse(cls, date_str: str) -> Optional[str]:
        """
        Parse various date formats to YYYY-MM or YYYY.
        Returns: "YYYY-MM" or "YYYY" or None if unparseable.
        """
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip().lower()

        # Try each format
        for fmt in cls.FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Return in YYYY-MM format, unless only year was provided
                if fmt == "%Y":
                    return str(parsed.year)
                return f"{parsed.year}-{parsed.month:02d}"
            except ValueError:
                continue

        return None

    @classmethod
    def calculate_duration(
        cls, start: str, end: Optional[str] = None
    ) -> float:
        """
        Calculate duration in years between two dates.
        If end is None, assume current date.
        Returns: float (years).
        """
        try:
            start_date = cls._parse_to_datetime(start)
            if not start_date:
                return 0.0

            end_date = (
                cls._parse_to_datetime(end)
                if end
                else datetime.now()
            )
            if not end_date:
                return 0.0

            delta = end_date - start_date
            return round(delta.days / 365.25, 2)
        except Exception:
            return 0.0

    @classmethod
    def _parse_to_datetime(cls, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        date_str = date_str.strip().lower()
        for fmt in cls.FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None


class SkillExtractor:
    """Extract and normalize skills from text."""

    # Common skill keywords
    COMMON_SKILLS = {
        # Languages
        'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'go', 'rust',
        'php', 'swift', 'kotlin', 'scala', 'typescript',

        # Frameworks
        'fastapi', 'django', 'flask', 'react', 'vue', 'angular', 'spring',
        'rails', 'express', 'nest.js',

        # Databases
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'dynamodb',

        # DevOps/Cloud
        'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform',
        'jenkins', 'github actions', 'gitlab ci',

        # Tools
        'git', 'sql', 'rest api', 'graphql', 'linux', 'unix',

        # Soft Skills
        'leadership', 'communication', 'teamwork', 'problem solving',
        'agile', 'scrum', 'kanban',
    }

    @classmethod
    def extract(cls, text: str) -> list[str]:
        """
        Extract known skills from text.
        Returns: list of skill names found.
        """
        text_lower = text.lower()
        found_skills = set()

        for skill in cls.COMMON_SKILLS:
            if skill in text_lower:
                found_skills.add(skill.title())

        return sorted(list(found_skills))

    @classmethod
    def extract_custom(cls, text: str, known_skills: list[str]) -> list[str]:
        """
        Extract skills from a provided list (more accurate).
        Searches case-insensitive.
        """
        text_lower = text.lower()
        found_skills = []

        for skill in known_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        return found_skills


class LocationExtractor:
    """Extract location information from text."""

    # Common location indicators
    LOCATION_KEYWORDS = [
        'based in', 'located in', 'location:', 'city:', 'address:',
        'remote', 'work from home'
    ]

    @classmethod
    def extract(cls, text: str, limit: int = 100) -> Optional[str]:
        """
        Extract location from text (usually first occurrence).
        Returns: location string or None.
        """
        text_lower = text.lower()

        for keyword in cls.LOCATION_KEYWORDS:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract text after keyword (next 100 chars)
                start = idx + len(keyword)
                snippet = text[start:start+limit].strip()
                # Take first line
                location = snippet.split('\n')[0].strip()
                if location and len(location) > 2:
                    return location

        return None
    @classmethod
    def is_valid(cls, email: str) -> bool:
        """Check if email format is valid."""
        return bool(cls.PATTERN.match(email.strip()))

    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """Extract first valid email from text."""
        # More permissive pattern for extraction
        pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None


class PhoneValidator:
    """Phone number validation helper."""

    # Pattern for common international formats
    PATTERN = re.compile(
        r'(?:\+\d{1,3})?[-.\s]?\(?[0-9]{1,4}\)?[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
    )

    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """Extract first valid phone from text."""
        match = cls.PATTERN.search(text)
        return match.group(0).strip() if match else None


class DateParser:
    """Date parsing helper for work experience."""

    # Common date formats
    FORMATS = [
        "%Y-%m",           # 2020-01
        "%Y/%m",           # 2020/01
        "%B %Y",           # January 2020
        "%b %Y",           # Jan 2020
        "%Y",              # 2020 (year only)
        "%m/%Y",           # 01/2020
    ]

    MONTH_MAPPING = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }

    @classmethod
    def parse(cls, date_str: str) -> Optional[str]:
        """
        Parse various date formats to YYYY-MM or YYYY.
        Returns: "YYYY-MM" or "YYYY" or None if unparseable.
        """
        if not date_str or not isinstance(date_str, str):
            return None

        date_str = date_str.strip().lower()

        # Try each format
        for fmt in cls.FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # Return in YYYY-MM format, unless only year was provided
                if fmt == "%Y":
                    return str(parsed.year)
                return f"{parsed.year}-{parsed.month:02d}"
            except ValueError:
                continue

        return None

    @classmethod
    def calculate_duration(
        cls, start: str, end: Optional[str] = None
    ) -> float:
        """
        Calculate duration in years between two dates.
        If end is None, assume current date.
        Returns: float (years).
        """
        try:
            start_date = cls._parse_to_datetime(start)
            if not start_date:
                return 0.0

            end_date = (
                cls._parse_to_datetime(end)
                if end
                else datetime.now()
            )
            if not end_date:
                return 0.0

            delta = end_date - start_date
            return round(delta.days / 365.25, 2)
        except Exception:
            return 0.0

    @classmethod
    def _parse_to_datetime(cls, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        date_str = date_str.strip().lower()
        for fmt in cls.FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None


class SkillExtractor:
    """Extract and normalize skills from text."""

    # Common skill keywords
    COMMON_SKILLS = {
        # Languages
        'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'go', 'rust',
        'php', 'swift', 'kotlin', 'scala', 'typescript',

        # Frameworks
        'fastapi', 'django', 'flask', 'react', 'vue', 'angular', 'spring',
        'rails', 'express', 'nest.js',

        # Databases
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'dynamodb',

        # DevOps/Cloud
        'docker', 'kubernetes', 'aws', 'gcp', 'azure', 'terraform',
        'jenkins', 'github actions', 'gitlab ci',

        # Tools
        'git', 'sql', 'rest api', 'graphql', 'linux', 'unix',

        # Soft Skills
        'leadership', 'communication', 'teamwork', 'problem solving',
        'agile', 'scrum', 'kanban',
    }

    @classmethod
    def extract(cls, text: str) -> list[str]:
        """
        Extract known skills from text.
        Returns: list of skill names found.
        """
        text_lower = text.lower()
        found_skills = set()

        for skill in cls.COMMON_SKILLS:
            if skill in text_lower:
                found_skills.add(skill.title())

        return sorted(list(found_skills))

    @classmethod
    def extract_custom(cls, text: str, known_skills: list[str]) -> list[str]:
        """
        Extract skills from a provided list (more accurate).
        Searches case-insensitive.
        """
        text_lower = text.lower()
        found_skills = []

        for skill in known_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)

        return found_skills


class LocationExtractor:
    """Extract location information from text."""

    # Common location indicators
    LOCATION_KEYWORDS = [
        'based in', 'located in', 'location:', 'city:', 'address:',
        'remote', 'work from home'
    ]

    @classmethod
    def extract(cls, text: str, limit: int = 100) -> Optional[str]:
        """
        Extract location from text (usually first occurrence).
        Returns: location string or None.
        """
        text_lower = text.lower()

        for keyword in cls.LOCATION_KEYWORDS:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract text after keyword (next 100 chars)
                start = idx + len(keyword)
                snippet = text[start:start+limit].strip()
                # Take first line
                location = snippet.split('\n')[0].strip()
                if location and len(location) > 2:
                    return location

        return None