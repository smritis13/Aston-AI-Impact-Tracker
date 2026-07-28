"""
Entity Extractor: Identifies and extracts company/person names from search queries.
Provides strict filtering to ensure results match the extracted entity.
"""

import re
from typing import Optional, Tuple, List, Dict
from django.db.models import Q
from .models import UseCase


class EntityAliasMap:
    """Maps entity aliases and variations to canonical names"""
    
    COMPANY_ALIASES = {
        # Tech companies
        'msft': 'Microsoft',
        'goog': 'Google',
        'googl': 'Google',
        'aapl': 'Apple',
        'amzn': 'Amazon',
        'tsla': 'Tesla',
        'meta': 'Meta',
        'fb': 'Facebook',
        'nvda': 'NVIDIA',
        
        # Industrial companies
        'sie': 'Siemens',
        'siemens ag': 'Siemens',
        
        # Energy companies
        'bp': 'British Petroleum',
        'shell': 'Royal Dutch Shell',
        'chevron': 'Chevron',
        'exxon': 'Exxon Mobil',
        
        # Consulting/Services
        'ibm': 'International Business Machines',
        'accenture': 'Accenture',
        'deloitte': 'Deloitte',
        'pwc': 'PwC',
        'ey': 'Ernst & Young',

        # Healthcare/medical device (Aston-PFE Medical Khamsin case)
        'pfe': 'PFE Medical',
        'pfe medical': 'PFE Medical',
        'partners for endoscopy': 'PFE Medical',
        'partnership medical': 'PFE Medical',
        'partnership medical ltd': 'PFE Medical',
        'pml': 'PFE Medical',
    }
    
    INSTITUTION_ALIASES = {
        # Top Universities (UK)
        'oxford': 'University of Oxford',
        'cambridge': 'University of Cambridge',
        'imperial': 'Imperial College London',
        'lse': 'London School of Economics',
        'ucl': 'University College London',
        'aston': 'Aston University',
        'bath': 'University of Bath',
        
        # Top Universities (US)
        'harvard': 'Harvard University',
        'mit': 'Massachusetts Institute of Technology',
        'stanford': 'Stanford University',
        'caltech': 'California Institute of Technology',
        'yale': 'Yale University',
        'princeton': 'Princeton University',
        'penn': 'University of Pennsylvania',
        
        # Top Universities (Europe)
        'eth': 'ETH Zurich',
        'zurich': 'ETH Zurich',
        'munich': 'Technische Universität München',
        'paris tech': 'ParisTech',
        
        # Research Institutions
        'bell labs': 'Bell Laboratories',
        'cern': 'European Organization for Nuclear Research',
        'max planck': 'Max Planck Institute',
        'fraunhofer': 'Fraunhofer Society',
    }
    
    @classmethod
    def resolve_alias(cls, name: str, entity_type: str = 'company') -> str:
        """
        Resolve entity name to canonical form.
        
        Args:
            name: Entity name or alias
            entity_type: 'company', 'university', 'research_institution', or 'person'
        
        Returns:
            Canonical entity name
        """
        name_lower = name.lower().strip()
        
        if entity_type in ['company', 'unknown']:
            return cls.COMPANY_ALIASES.get(name_lower, name)
        elif entity_type in ['university', 'research_institution', 'institution']:
            return cls.INSTITUTION_ALIASES.get(name_lower, name)
        
        return name
    
    @classmethod
    def detect_entity_type_from_name(cls, name: str) -> str:
        """
        Attempt to detect entity type from name patterns.
        
        Returns:
            'company', 'university', 'research_institution', 'person', or 'unknown'
        """
        name_lower = name.lower()
        
        # University patterns
        university_keywords = ['university', 'college', 'polytechnic', 'institute of technology', 'school of']
        if any(keyword in name_lower for keyword in university_keywords):
            return 'university'
        
        # Research institution patterns
        research_keywords = ['research', 'laboratory', 'lab', 'foundation', 'organization', 'max planck', 'fraunhofer', 'cern']
        if any(keyword in name_lower for keyword in research_keywords):
            return 'research_institution'
        
        # Company patterns
        company_keywords = ['inc', 'corp', 'ltd', 'llc', 'co', 'company', 'group', 'corporation', 'gmbh', 'ag', 'sa', 'plc']
        if any(keyword in name_lower for keyword in company_keywords):
            return 'company'
        
        # Check aliases
        if name_lower in cls.COMPANY_ALIASES:
            return 'company'
        if name_lower in cls.INSTITUTION_ALIASES:
            return 'university'  # Most institution aliases are universities
        
        return 'unknown'


class EntityExtractor:
    """
    Extracts organization/person names from search queries and normalizes them.
    Supports flexible matching with entity priority weighting.
    """
    
    # Common company name suffixes and keywords
    COMPANY_SUFFIXES = [
        'Inc', 'Corp', 'Ltd', 'LLC', 'Co', 'Company', 'Group', 'Corporation',
        'Incorporated', 'Limited', 'GmbH', 'AG', 'SA', 'PLC', 'plc'
    ]
    
    # University and research institution keywords
    INSTITUTION_KEYWORDS = [
        'University', 'College', 'Institute', 'School', 'Laboratory', 'Lab',
        'Academy', 'Foundation', 'Centre', 'Center', 'Organization', 'Organisation'
    ]
    
    ACADEMIC_TITLES = [
        'Prof', 'Professor', 'Dr', 'Dr.', 'Assoc', 'Associate', 'Assistant',
        'Emeritus', 'Lord', 'Chancellor', 'Provost', 'Dean', 'Director'
    ]
    
    def extract_entity(self, search_query: str) -> Optional[Tuple[str, str]]:
        """
        Extract the primary entity (company/person/institution) from a search query.
        
        Returns:
            Tuple of (entity_name, entity_type) where entity_type is 'company', 'university', 
            'research_institution', or 'person'. None if no entity can be extracted.
        """
        if not search_query or len(search_query.strip()) < 2:
            return None
        
        # Try to extract institution (university/research institution) first
        institution = self._extract_institution(search_query)
        if institution:
            canonical = EntityAliasMap.resolve_alias(institution, 'institution')
            entity_type = EntityAliasMap.detect_entity_type_from_name(canonical)
            return (canonical, entity_type)
        
        # Try to extract company name
        company = self._extract_company(search_query)
        if company:
            canonical = EntityAliasMap.resolve_alias(company, 'company')
            return (canonical, 'company')
        
        # Try to extract person name
        person = self._extract_person(search_query)
        if person:
            return (person, 'person')
        
        return None
    
    def _extract_institution(self, text: str) -> Optional[str]:
        """
        Extract university or research institution name from text.
        """
        # Pattern 1: Look for quoted institution names
        quoted_match = re.search(r'"([^"]+(?:University|College|Institute|Laboratory|School|Centre|Center|Foundation)[^"]*)\"', text, re.IGNORECASE)
        if quoted_match:
            inst_name = quoted_match.group(1).strip()
            if len(inst_name) > 2:
                return self._normalize_company_name(inst_name)
        
        # Pattern 2: Look for institution keywords
        for keyword in self.INSTITUTION_KEYWORDS:
            pattern = rf'\b([A-Z][a-zA-Z\s&-]*\s+{keyword}(?:\s+of\s+[A-Z][a-zA-Z\s&-]*)?)\b'
            match = re.search(pattern, text)
            if match:
                inst_name = match.group(1).strip()
                if len(inst_name) > 2:
                    return self._normalize_company_name(inst_name)
        
        return None
    
    def _extract_company(self, text: str) -> Optional[str]:
        """
        Extract company name from text.
        Looks for: capitalized words, company suffixes, known company patterns
        """
        # Remove common words that precede companies
        cleaned = re.sub(r'\b(by|from|at|by)\s+', '', text, flags=re.IGNORECASE)
        
        # Pattern 1: Look for quoted company names
        quoted_match = re.search(r'"([^"]+)"', cleaned)
        if quoted_match:
            company_name = quoted_match.group(1).strip()
            if len(company_name) > 2 and not self._is_generic_phrase(company_name):
                return self._normalize_company_name(company_name)
        
        # Pattern 2: Look for company suffixes (e.g., "Apple Inc", "Microsoft Corp")
        for suffix in self.COMPANY_SUFFIXES:
            pattern = rf'\b([A-Z][a-zA-Z\s&-]*\s+{suffix})\b'
            match = re.search(pattern, cleaned)
            if match:
                company_name = match.group(1).strip()
                return self._normalize_company_name(company_name)
        
        # Pattern 3: Look for all-caps words or capitalized multi-word phrases
        # that look like company names (at least 2 capital letters)
        words = cleaned.split()
        capitalized_sequence = []
        
        for word in words:
            # Skip if word is a common generic phrase
            if self._is_generic_word(word):
                if capitalized_sequence:
                    break
                continue
            
            if word and (word[0].isupper() or word[0].isdigit()):
                capitalized_sequence.append(word)
            else:
                if capitalized_sequence and len(capitalized_sequence) >= 1:
                    break
        
        if capitalized_sequence and len(capitalized_sequence) >= 1:
            company_name = ' '.join(capitalized_sequence)
            if len(company_name) > 2 and not self._is_generic_phrase(company_name):
                return self._normalize_company_name(company_name)
        
        return None
    
    def _extract_person(self, text: str) -> Optional[str]:
        """
        Extract person name from text.
        Looks for: academic titles, "FirstName LastName" patterns
        """
        # Pattern 1: Academic title followed by name (e.g., "Prof. John Smith")
        for title in self.ACADEMIC_TITLES:
            pattern = rf'{title}\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # Pattern 2: "FirstName LastName" in quotes
        quoted_match = re.search(r'"([A-Z][a-z]+\s+[A-Z][a-z]+)"', text)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        return None
    
    def _is_generic_word(self, word: str) -> bool:
        """Check if word is a common generic word that shouldn't be part of entity name"""
        generic_words = {
            'for', 'in', 'at', 'by', 'from', 'and', 'or', 'the', 'a', 'an',
            'on', 'with', 'to', 'of', 'about', 'research', 'study', 'analysis',
            'impact', 'case', 'data', 'findings', 'using', 'through', 'via',
            'demonstrates', 'shows', 'reveals', 'improves', 'reduces', 'university',
            'institute', 'college', 'school'
        }
        return word.lower() in generic_words
    
    def _is_generic_phrase(self, phrase: str) -> bool:
        """Check if phrase is too generic to be an entity name"""
        generic_phrases = {
            'research findings', 'study findings', 'research results',
            'case study', 'research impact', 'industry findings',
            'manufacturing', 'sector', 'field', 'company'
        }
        return phrase.lower() in generic_phrases
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for consistent matching"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Remove trailing punctuation
        name = name.rstrip('.,;:')
        return name
    
    def filter_by_entity(self, queryset: 'UseCase', entity_name: str, 
                        entity_type: str = 'company', strict: bool = True) -> 'UseCase':
        """
        Filter use cases to only show those involving the specified entity.
        
        Args:
            queryset: Django QuerySet of UseCase objects
            entity_name: Name of the entity to filter for
            entity_type: 'company', 'university', 'research_institution', or 'person'
            strict: If True, only exact matches. If False, also include partial matches.
        
        Returns:
            Filtered QuerySet
        """
        if not entity_name or not entity_name.strip():
            return queryset
        
        entity_name = entity_name.strip()
        
        if entity_type == 'company':
            # Filter by company field
            if strict:
                # Exact match or case-insensitive exact match
                queryset = queryset.filter(
                    Q(company__iexact=entity_name) |
                    Q(company__icontains=entity_name)  # Also catch variations like "Siemens AG"
                )
            else:
                # Partial matches allowed
                queryset = queryset.filter(company__icontains=entity_name)
        
        elif entity_type in ['university', 'research_institution']:
            # Search in use_case_description and company field for institution names
            queryset = queryset.filter(
                Q(use_case_description__icontains=entity_name) |
                Q(use_case_name__icontains=entity_name) |
                Q(company__icontains=entity_name)  # Some institution names appear in company field
            )
        
        elif entity_type == 'person':
            # Search in use_case_description and other text fields for person name
            queryset = queryset.filter(
                Q(use_case_description__icontains=entity_name) |
                Q(use_case_name__icontains=entity_name) |
                Q(company__icontains=entity_name)  # Some person names appear in company field
            )
        
        return queryset
    
    def extract_and_filter(self, queryset: 'UseCase', search_query: str, 
                          enforce_strict: bool = True) -> Tuple[Optional['UseCase'], Optional[dict]]:
        """
        Extract entity from search query and apply filtering.
        
        Returns:
            Tuple of (filtered_queryset, entity_info)
            where entity_info contains details about extracted entity
        """
        entity_info = self.extract_entity(search_query)
        
        if entity_info:
            entity_name, entity_type = entity_info
            filtered_queryset = self.filter_by_entity(
                queryset, 
                entity_name, 
                entity_type, 
                strict=enforce_strict
            )
            
            return (filtered_queryset, {
                'entity_name': entity_name,
                'entity_type': entity_type,
                'source': 'extracted'
            })
        
        return (queryset, None)
    
    def get_entity_suggestions(self, search_query: str) -> List[Dict[str, str]]:
        """
        Get list of suggested entities from the database that match the query.
        Useful for UI autocomplete.
        
        Returns:
            List of dicts with 'name' and 'type' keys
        """
        # Extract potential entity from query
        entity_info = self.extract_entity(search_query)
        
        if not entity_info:
            return []
        
        entity_name, entity_type = entity_info
        
        # Query database for similar entities
        if entity_type in ['company', 'university', 'research_institution']:
            similar_entities = UseCase.objects.filter(
                company__icontains=entity_name
            ).values_list('company', flat=True).distinct()
            
            suggestions = []
            for company in list(set(similar_entities))[:10]:  # Top 10 unique suggestions
                detected_type = EntityAliasMap.detect_entity_type_from_name(company)
                suggestions.append({
                    'name': company,
                    'type': detected_type or entity_type
                })
            return suggestions
        
        return []
    
    def get_all_company_suggestions(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        Get all companies from database for autocomplete suggestions.
        
        Returns:
            List of unique company names sorted alphabetically
        """
        companies = UseCase.objects.values_list('company', flat=True).distinct().exclude(company__isnull=True).exclude(company='')[:limit]
        return [{'name': c, 'type': 'company'} for c in sorted(set(companies))]
    
    def get_all_institution_suggestions(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        Get all institutions from database for autocomplete suggestions.
        
        Returns:
            List of unique institution names sorted alphabetically
        """
        # This would need additional logic to detect institutions in the company field
        # For now, return known institutions from alias map
        institutions = list(set(EntityAliasMap.INSTITUTION_ALIASES.values()))
        return [{'name': i, 'type': 'university'} for i in sorted(institutions)[:limit]]
    
    def _extract_company(self, text: str) -> Optional[str]:
        """
        Extract company name from text.
        Looks for: capitalized words, company suffixes, known company patterns
        """
        # Remove common words that precede companies
        cleaned = re.sub(r'\b(by|from|at|by)\s+', '', text, flags=re.IGNORECASE)
        
        # Pattern 1: Look for quoted company names
        quoted_match = re.search(r'"([^"]+)"', cleaned)
        if quoted_match:
            company_name = quoted_match.group(1).strip()
            if len(company_name) > 2 and not self._is_generic_phrase(company_name):
                return self._normalize_company_name(company_name)
        
        # Pattern 2: Look for company suffixes (e.g., "Apple Inc", "Microsoft Corp")
        for suffix in self.COMPANY_SUFFIXES:
            pattern = rf'\b([A-Z][a-zA-Z\s&-]*\s+{suffix})\b'
            match = re.search(pattern, cleaned)
            if match:
                company_name = match.group(1).strip()
                return self._normalize_company_name(company_name)
        
        # Pattern 3: Look for all-caps words or capitalized multi-word phrases
        # that look like company names (at least 2 capital letters)
        words = cleaned.split()
        capitalized_sequence = []
        
        for word in words:
            # Skip if word is a common generic phrase
            if self._is_generic_word(word):
                if capitalized_sequence:
                    break
                continue
            
            if word and (word[0].isupper() or word[0].isdigit()):
                capitalized_sequence.append(word)
            else:
                if capitalized_sequence and len(capitalized_sequence) >= 1:
                    break
        
        if capitalized_sequence and len(capitalized_sequence) >= 1:
            company_name = ' '.join(capitalized_sequence)
            if len(company_name) > 2 and not self._is_generic_phrase(company_name):
                return self._normalize_company_name(company_name)
        
        return None
    
    def _extract_person(self, text: str) -> Optional[str]:
        """
        Extract person name from text.
        Looks for: academic titles, "FirstName LastName" patterns
        """
        # Pattern 1: Academic title followed by name (e.g., "Prof. John Smith")
        for title in self.ACADEMIC_TITLES:
            pattern = rf'{title}\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # Pattern 2: "FirstName LastName" in quotes
        quoted_match = re.search(r'"([A-Z][a-z]+\s+[A-Z][a-z]+)"', text)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        return None
    
    def _is_generic_word(self, word: str) -> bool:
        """Check if word is a common generic word that shouldn't be part of entity name"""
        generic_words = {
            'for', 'in', 'at', 'by', 'from', 'and', 'or', 'the', 'a', 'an',
            'on', 'with', 'to', 'of', 'about', 'research', 'study', 'analysis',
            'impact', 'case', 'data', 'findings', 'using', 'through', 'via',
            'demonstrates', 'shows', 'reveals', 'improves', 'reduces'
        }
        return word.lower() in generic_words
    
    def _is_generic_phrase(self, phrase: str) -> bool:
        """Check if phrase is too generic to be an entity name"""
        generic_phrases = {
            'research findings', 'study findings', 'research results',
            'case study', 'research impact', 'industry findings',
            'manufacturing', 'sector', 'field', 'company'
        }
        return phrase.lower() in generic_phrases
    
    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for consistent matching"""
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Remove trailing punctuation
        name = name.rstrip('.,;:')
        return name
    
    def filter_by_entity(self, queryset: 'UseCase', entity_name: str, 
                        entity_type: str = 'company', strict: bool = True) -> 'UseCase':
        """
        Filter use cases to only show those involving the specified entity.
        
        Args:
            queryset: Django QuerySet of UseCase objects
            entity_name: Name of the entity to filter for
            entity_type: 'company' or 'person'
            strict: If True, only exact matches. If False, also include partial matches.
        
        Returns:
            Filtered QuerySet
        """
        if not entity_name or not entity_name.strip():
            return queryset
        
        entity_name = entity_name.strip()
        
        if entity_type == 'company':
            # Filter by company field
            if strict:
                # Exact match or case-insensitive exact match
                queryset = queryset.filter(
                    Q(company__iexact=entity_name) |
                    Q(company__icontains=entity_name)  # Also catch variations like "Siemens AG"
                )
            else:
                # Partial matches allowed
                queryset = queryset.filter(company__icontains=entity_name)
        
        elif entity_type == 'person':
            # Search in use_case_description and other text fields for person name
            queryset = queryset.filter(
                Q(use_case_description__icontains=entity_name) |
                Q(use_case_name__icontains=entity_name) |
                Q(company__icontains=entity_name)  # Some person names appear in company field
            )
        
        return queryset
    
    def extract_and_filter(self, queryset: 'UseCase', search_query: str, 
                          enforce_strict: bool = True) -> Tuple[Optional['UseCase'], Optional[dict]]:
        """
        Extract entity from search query and apply filtering.
        
        Returns:
            Tuple of (filtered_queryset, entity_info)
            where entity_info contains details about extracted entity
        """
        entity_info = self.extract_entity(search_query)
        
        if entity_info:
            entity_name, entity_type = entity_info
            filtered_queryset = self.filter_by_entity(
                queryset, 
                entity_name, 
                entity_type, 
                strict=enforce_strict
            )
            
            return (filtered_queryset, {
                'entity_name': entity_name,
                'entity_type': entity_type,
                'source': 'extracted'
            })
        
        return (queryset, None)
    
    def get_entity_suggestions(self, search_query: str) -> List[str]:
        """
        Get list of suggested entities from the database that match the query.
        Useful for UI autocomplete.
        """
        # Extract potential entity from query
        entity_info = self.extract_entity(search_query)
        
        if not entity_info:
            return []
        
        entity_name, entity_type = entity_info
        
        # Query database for similar entities
        if entity_type == 'company':
            similar_companies = UseCase.objects.filter(
                company__icontains=entity_name
            ).values_list('company', flat=True).distinct()
            return list(set(similar_companies))[:10]  # Return top 10 unique suggestions
        
        return []
