#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Historical Case Matcher Service

Provides intelligent matching of new complaints against historical cases from multiple data sources.
Implements weighted similarity scoring to identify patterns, duplicates, and recurring issues.

Data Sources:
- Slopes Complaints 2021 Excel (4,047 cases)
- SRR Data 2021-2024 CSV (1,251 cases)  
- Tree Inventory Excel (32,405 trees)
- Current Database (excluded from similarity search to avoid self-matching)

Author: Project3 Team
Version: 2.0
"""

import pandas as pd
import sqlite3
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
from datetime import datetime
import chardet


class HistoricalCaseMatcher:
    """
    Historical case matching service with multi-criteria similarity scoring
    
    Features:
    - Weighted similarity calculation (Location 40%, Slope 30%, Subject 15%, Caller 10%, Phone 5%)
    - Fuzzy text matching for locations and names
    - Exact matching for slope/tree numbers
    - Jaccard similarity for subject matter
    - Tree information extraction from remarks
    - Location-slope mapping learning
    """
    
    def __init__(self, data_dir: str, db_path: str):
        """
        Initialize historical case matcher
        
        Args:
            data_dir: Directory containing Excel/CSV data files
            db_path: Path to SQLite database (excluded from searches)
        """
        self.data_dir = data_dir
        self.db_path = db_path
        
        # Data containers
        self.slopes_complaints = pd.DataFrame()
        self.srr_data = pd.DataFrame()
        self.tree_inventory = pd.DataFrame()
        self.db_case_count = 0
        
        # Similarity weights (must sum to 1.0)
        self.WEIGHT_LOCATION = 0.40       # 40% - Primary matching criterion
        self.WEIGHT_SLOPE_TREE = 0.30      # 30% - Subject matter
        self.WEIGHT_SUBJECT = 0.15         # 15% - Subject category
        self.WEIGHT_CALLER_NAME = 0.10     # 10% - Caller info
        self.WEIGHT_CALLER_PHONE = 0.05    # 5% - Phone verification
        
        # Load all historical data
        self._load_historical_data()
        
        # Build location-slope mapping from historical data
        self.location_slope_mapping = self._build_location_slope_mapping()
        
        total_historical = len(self.slopes_complaints) + len(self.srr_data)
        
        print(f"✅ Historical Case Matcher initialized:")
        print(f"   📊 Slopes Complaints 2021: {len(self.slopes_complaints):,} cases")
        print(f"   📊 SRR Data 2021-2024: {len(self.srr_data):,} cases")
        print(f"   🌳 Tree Inventory: {len(self.tree_inventory):,} trees")
        print(f"   🗺️  Location-Slope Mappings: {len(self.location_slope_mapping):,} learned")
        print(f"   ⚠️  Database cases: {self.db_case_count} (excluded from similarity search)")
        print(f"   📈 Total searchable historical cases: {total_historical:,}")
        print(f"   ✅ Search scope: Historical Excel/CSV data only (database excluded)")
    
    def _load_historical_data(self):
        """Load all historical data sources"""
        try:
            # Load Slopes Complaints 2021
            slopes_file = os.path.join(self.data_dir, 'Slopes Complaints & Enquires Under             TC K928   4-10-2021.xlsx')
            if os.path.exists(slopes_file):
                # Read Excel and clean data
                df = pd.read_excel(slopes_file)
                
                # Remove completely empty rows
                df = df.dropna(how='all')
                
                # Remove rows where key columns are all null
                key_cols = ['Received \nDate', 'Case No. ', 'Venue', 'District']
                existing_key_cols = [col for col in key_cols if col in df.columns]
                if existing_key_cols:
                    df = df.dropna(subset=existing_key_cols, how='all')
                
                # Drop unnecessary 'Unnamed' columns to reduce memory
                df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
                
                self.slopes_complaints = df
                print(f"📂 Loaded Slopes Complaints: {len(self.slopes_complaints)} records (cleaned)")
            
            # Load SRR Data 2021-2024
            srr_file = os.path.join(self.data_dir, 'SRR data 2021-2024.csv')
            if os.path.exists(srr_file):
                # Detect encoding
                with open(srr_file, 'rb') as f:
                    result = chardet.detect(f.read())
                    encoding = result['encoding']
                
                # Read CSV and clean data
                df = pd.read_csv(srr_file, encoding=encoding)
                
                # Remove completely empty rows
                df = df.dropna(how='all')
                
                # Remove rows where key columns are all null
                key_cols = ['Received \nDate', 'Source', 'District']
                existing_key_cols = [col for col in key_cols if col in df.columns]
                if existing_key_cols:
                    df = df.dropna(subset=existing_key_cols, how='all')
                
                self.srr_data = df
                print(f"📂 Loaded SRR Data: {len(self.srr_data)} records (cleaned)")
            
            # Load Tree Inventory
            tree_file = os.path.join(self.data_dir, 'Tree inventory.xlsx')
            if os.path.exists(tree_file):
                # Read Excel and clean data
                df = pd.read_excel(tree_file)
                
                # Remove completely empty rows
                df = df.dropna(how='all')
                
                # Drop unnecessary 'Unnamed' columns
                df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
                
                self.tree_inventory = df
                print(f"📂 Loaded Tree Inventory: {len(self.tree_inventory)} trees (cleaned)")
            
            # Count database cases (but don't load for searching)
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM srr_cases")
                self.db_case_count = cursor.fetchone()[0]
                conn.close()
                print(f"📂 Current Database: {self.db_case_count} cases")
                
        except Exception as e:
            print(f"⚠️ Error loading historical data: {e}")
    
    def find_similar_cases(
        self,
        current_case: Dict[str, Any],
        limit: int = 10,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical cases using weighted similarity scoring
        
        Args:
            current_case: Dictionary containing case information to match
            limit: Maximum number of results to return
            min_similarity: Minimum similarity score (0.0-1.0) to include
            
        Returns:
            List of similar cases with similarity scores and match details
        """
        all_similar = []
        
        # Search in Slopes Complaints 2021 (4,047 cases)
        slopes_similar = self._search_slopes_complaints(current_case, min_similarity)
        all_similar.extend(slopes_similar)
        
        # Search in SRR Data 2021-2024 (1,251 cases)
        srr_similar = self._search_srr_data(current_case, min_similarity)
        all_similar.extend(srr_similar)
        
        # NOTE: Database search intentionally excluded to avoid self-matching
        # newly added cases against themselves
        
        # Sort by similarity score
        all_similar.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return all_similar[:limit]
    
    def _search_slopes_complaints(
        self,
        current_case: Dict[str, Any],
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Search in Slopes Complaints 2021 Excel data"""
        results = []
        
        if self.slopes_complaints.empty:
            return results
        
        for idx, row in self.slopes_complaints.iterrows():
            # Extract tree information from Remarks
            tree_info = self._extract_tree_info_from_remarks(self._safe_get(row, 'Remarks'))
            
            # Use Verified Slope No. if available, otherwise original Slope no
            slope_no = self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope no')
            
            # Use Venue if available, otherwise District
            location = self._safe_get(row, 'Venue') or self._safe_get(row, 'District')
            
            # Combine Nature of complaint and Remarks for full complaint details
            nature = self._safe_get(row, 'Nature of complaint')
            remarks = self._safe_get(row, 'Remarks')
            complaint_details = self._combine_complaint_details(nature, remarks)
            
            # Map Excel columns to standard format
            historical_case = {
                'A_date_received': self._safe_get(row, 'Received \nDate'),
                'C_case_number': self._safe_get(row, 'Case No. '),
                'B_source': self._safe_get(row, 'Source'),
                'D_type': self._safe_get(row, 'Type\nEmergency, Urgent, General'),
                'G_slope_no': slope_no,  # Use verified slope number
                'H_location': location,  # Prefer Venue over District
                'E_caller_name': self._extract_name(self._safe_get(row, 'Name of Complaint & Contact No.')),
                'F_contact_no': self._extract_phone(self._safe_get(row, 'Name of Complaint & Contact No.')),
                'I_nature_of_request': complaint_details,  # Full complaint details
                'J_subject_matter': self._safe_get(row, 'AIMS Complaint Type'),
                'tree_id': tree_info['tree_id'],  # Tree ID if available
                'tree_count': tree_info['tree_count'],  # Number of trees
                'inspector_remarks': tree_info['inspector_remarks']  # Inspector comments
            }
            
            # Calculate similarity
            score, details = self._calculate_similarity(current_case, historical_case)
            
            if score >= min_similarity:
                results.append({
                    'case': historical_case,
                    'similarity_score': score,
                    'is_potential_duplicate': score >= 0.70,
                    'match_details': details,
                    'data_source': 'Slopes Complaints 2021'
                })
        
        return results
    
    def _search_srr_data(
        self,
        current_case: Dict[str, Any],
        min_similarity: float
    ) -> List[Dict[str, Any]]:
        """Search in SRR Data 2021-2024 CSV"""
        results = []
        
        if self.srr_data.empty:
            return results
        
        for idx, row in self.srr_data.iterrows():
            # Use Verified Slope No. if available
            slope_no = self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope No.\n')
            
            # Use Venue if available, otherwise District
            location = self._safe_get(row, 'Venue') or self._safe_get(row, 'District')
            
            historical_case = {
                'A_date_received': self._safe_get(row, 'Received Date'),
                'C_case_number': self._safe_get(row, 'Case No.'),
                'B_source': self._safe_get(row, 'Source'),
                'D_type': self._safe_get(row, 'Type'),
                'G_slope_no': slope_no,
                'H_location': location,
                'E_caller_name': self._safe_get(row, 'Name'),
                'F_contact_no': self._safe_get(row, 'Contact No.'),
                'I_nature_of_request': self._safe_get(row, 'Inquiry'),
                'J_subject_matter': self._safe_get(row, 'Subject Matter'),
            }
            
            score, details = self._calculate_similarity(current_case, historical_case)
            
            if score >= min_similarity:
                results.append({
                    'case': historical_case,
                    'similarity_score': score,
                    'is_potential_duplicate': score >= 0.70,
                    'match_details': details,
                    'data_source': 'SRR Data 2021-2024'
                })
        
        return results
    
    def _calculate_similarity(
        self,
        current: Dict[str, Any],
        historical: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate weighted similarity score between two cases
        
        Returns:
            (total_score, match_details)
        """
        # Calculate individual component scores
        location_score = self._match_location(
            current.get('H_location'),
            historical.get('H_location')
        )
        
        slope_score = self._match_slope_tree(
            current.get('G_slope_no'),
            historical.get('G_slope_no')
        )
        
        subject_score = self._match_subject(
            current.get('J_subject_matter'),
            historical.get('J_subject_matter')
        )
        
        caller_name_score = self._match_caller_name(
            current.get('E_caller_name'),
            historical.get('E_caller_name')
        )
        
        caller_phone_score = self._match_phone(
            current.get('F_contact_no'),
            historical.get('F_contact_no')
        )
        
        # Calculate weighted total score
        total_score = (
            location_score * self.WEIGHT_LOCATION +
            slope_score * self.WEIGHT_SLOPE_TREE +
            subject_score * self.WEIGHT_SUBJECT +
            caller_name_score * self.WEIGHT_CALLER_NAME +
            caller_phone_score * self.WEIGHT_CALLER_PHONE
        )
        
        # Build match details
        match_details = {
            'location_match': location_score,
            'slope_tree_match': slope_score,
            'subject_match': subject_score,
            'caller_name_match': caller_name_score,
            'caller_phone_match': caller_phone_score,
            'component_scores': {
                'location': location_score * self.WEIGHT_LOCATION,
                'slope_tree': slope_score * self.WEIGHT_SLOPE_TREE,
                'subject': subject_score * self.WEIGHT_SUBJECT,
                'caller_name': caller_name_score * self.WEIGHT_CALLER_NAME,
                'caller_phone': caller_phone_score * self.WEIGHT_CALLER_PHONE
            },
            'total_score': total_score
        }
        
        return total_score, match_details
    
    def _match_location(self, loc1: str, loc2: str) -> float:
        """Fuzzy match locations (returns actual similarity ratio)"""
        if not loc1 or not loc2:
            return 0.0
        
        # Normalize
        l1 = self._normalize_text(loc1)
        l2 = self._normalize_text(loc2)
        
        # Use SequenceMatcher for fuzzy matching
        similarity = SequenceMatcher(None, l1, l2).ratio()
        
        # Return actual similarity (no threshold here, threshold applied to total_score)
        return similarity
    
    def _match_slope_tree(self, slope1: str, slope2: str) -> float:
        """Exact or normalized match for slope/tree numbers"""
        if not slope1 or not slope2:
            return 0.0
        
        # Normalize (remove spaces, hyphens, etc.)
        s1 = self._normalize_slope_number(slope1)
        s2 = self._normalize_slope_number(slope2)
        
        # Exact match after normalization
        return 1.0 if s1 == s2 else 0.0
    
    def _match_subject(self, subj1: str, subj2: str) -> float:
        """Jaccard similarity for subject matter"""
        if not subj1 or not subj2:
            return 0.0
        
        # Convert to word sets
        words1 = set(self._normalize_text(subj1).split())
        words2 = set(self._normalize_text(subj2).split())
        
        # Jaccard = intersection / union
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _match_caller_name(self, name1: str, name2: str) -> float:
        """Fuzzy match caller names (returns actual similarity ratio)"""
        if not name1 or not name2:
            return 0.0
        
        n1 = self._normalize_text(name1)
        n2 = self._normalize_text(name2)
        
        similarity = SequenceMatcher(None, n1, n2).ratio()
        
        # Return actual similarity (threshold applied to total_score)
        return similarity
    
    def _match_phone(self, phone1: str, phone2: str) -> float:
        """Exact or last 8 digits match for phone numbers"""
        if not phone1 or not phone2:
            return 0.0
        
        # Extract digits only
        p1 = re.sub(r'\D', '', str(phone1))
        p2 = re.sub(r'\D', '', str(phone2))
        
        # Exact match
        if p1 == p2:
            return 1.0
        
        # Last 8 digits match (HK phone numbers)
        if len(p1) >= 8 and len(p2) >= 8:
            if p1[-8:] == p2[-8:]:
                return 1.0
        
        return 0.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text or pd.isna(text):
            return ''
        return str(text).lower().strip()
    
    def _normalize_slope_number(self, slope: str) -> str:
        """Normalize slope number for comparison"""
        if not slope or pd.isna(slope):
            return ''
        # Remove spaces, hyphens, slashes
        normalized = re.sub(r'[\s\-/]', '', str(slope).upper())
        return normalized
    
    def _extract_name(self, text: str) -> str:
        """Extract name from combined name/contact field"""
        if not text or pd.isna(text):
            return ''
        
        text = str(text)
        # Try to find name before phone number
        match = re.search(r'^([^0-9]+)', text)
        if match:
            return match.group(1).strip()
        return text.strip()
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text"""
        if not text or pd.isna(text):
            return ''
        
        text = str(text)
        # Find 8-digit phone number
        match = re.search(r'\d{8}', text)
        return match.group(0) if match else ''
    
    def _extract_tree_number(self, text: str) -> Optional[str]:
        """Extract tree number from text"""
        if not text or pd.isna(text):
            return None
        
        text = str(text)
        patterns = [
            r'(?i)tree\s*(?:no\.?|number)?\s*[:#]?\s*([A-Z0-9]+)',
            r'(?i)tree\s*ID[:#]?\s*([A-Z0-9]+)',
            r'(?i)t[:#]?\s*([0-9]+)',
            r'TS\d+'  # Tree ID pattern like TS036
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                if match.groups():
                    return match.group(1).upper()
                else:
                    return match.group(0).upper()
        
        return None
    
    def _extract_tree_info_from_remarks(self, remarks: str) -> Dict[str, Any]:
        """
        Extract tree information from Remarks column
        
        Args:
            remarks: Content from Remarks column (AZ)
            
        Returns:
            Dictionary with tree_id, tree_count, inspector_remarks
        """
        tree_info = {
            'tree_id': None,
            'tree_count': None,
            'inspector_remarks': None
        }
        
        if not remarks or pd.isna(remarks):
            return tree_info
        
        remarks_str = str(remarks)
        
        # Extract tree ID (e.g., "Tree ID: TS036")
        tree_id_match = re.search(r'Tree\s*ID[:#]?\s*([A-Z0-9]+)', remarks_str, re.IGNORECASE)
        if tree_id_match:
            tree_info['tree_id'] = tree_id_match.group(1).upper()
        
        # Extract number of trees (e.g., "No. of tree: 1")
        tree_count_match = re.search(r'No\.\s*of\s*tree[s]?[:#]?\s*(\d+)', remarks_str, re.IGNORECASE)
        if tree_count_match:
            tree_info['tree_count'] = int(tree_count_match.group(1))
        
        # Extract inspector remarks (text after "Remark:" or "Remark:")
        remark_match = re.search(r'Remark[s]?[:#]\s*(.+?)(?:\[|$)', remarks_str, re.IGNORECASE | re.DOTALL)
        if remark_match:
            inspector_text = remark_match.group(1).strip()
            # Limit to 200 characters
            tree_info['inspector_remarks'] = inspector_text[:200] + ('...' if len(inspector_text) > 200 else '')
        
        return tree_info
    
    def _combine_complaint_details(self, nature: str, remarks: str) -> str:
        """
        Combine Nature of complaint and Remarks for full complaint details
        
        Args:
            nature: Content from "Nature of complaint" column
            remarks: Content from "Remarks" column (AZ)
            
        Returns:
            Combined complaint details text
        """
        details_parts = []
        
        # Add nature of complaint
        if nature and not pd.isna(nature):
            nature_str = str(nature).strip()
            if nature_str:
                details_parts.append(nature_str)
        
        # Add relevant parts from remarks
        if remarks and not pd.isna(remarks):
            remarks_str = str(remarks).strip()
            if remarks_str:
                # Extract the complaint description (before "Remark:")
                complaint_part = re.split(r'Remark[s]?[:#]', remarks_str, flags=re.IGNORECASE)[0].strip()
                if complaint_part and (complaint_part not in nature_str if nature else True):
                    details_parts.append(complaint_part)
        
        # Combine and limit to 300 characters
        combined = ' | '.join(details_parts)
        if len(combined) > 300:
            combined = combined[:300] + '...'
        
        return combined if combined else 'N/A'
    
    def _safe_get(self, row, column: str) -> str:
        """Safely get value from DataFrame row"""
        try:
            val = row.get(column)
            if pd.isna(val):
                return ''
            return str(val).strip()
        except:
            return ''
    
    def _build_location_slope_mapping(self) -> Dict[str, List[str]]:
        """
        Build location-to-slope mapping from historical data
        Learn different address names used for the same slope numbers
        
        Returns:
            Dictionary mapping normalized locations to list of slope numbers
        """
        mapping = {}
        
        # Learn from Slopes Complaints 2021
        if not self.slopes_complaints.empty:
            for idx, row in self.slopes_complaints.iterrows():
                slope_no = self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope no')
                venue = self._safe_get(row, 'Venue')
                district = self._safe_get(row, 'District')
                
                if slope_no:
                    slope_norm = self._normalize_slope_number(slope_no)
                    
                    # Map venue to slope
                    if venue:
                        venue_norm = self._normalize_text(venue)
                        if venue_norm:
                            if venue_norm not in mapping:
                                mapping[venue_norm] = set()
                            mapping[venue_norm].add(slope_norm)
                    
                    # Map district to slope
                    if district:
                        district_norm = self._normalize_text(district)
                        if district_norm:
                            if district_norm not in mapping:
                                mapping[district_norm] = set()
                            mapping[district_norm].add(slope_norm)
        
        # Learn from SRR Data 2021-2024
        if not self.srr_data.empty:
            for idx, row in self.srr_data.iterrows():
                slope_no = self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope No.\n')
                venue = self._safe_get(row, 'Venue')
                district = self._safe_get(row, 'District')
                
                if slope_no:
                    slope_norm = self._normalize_slope_number(slope_no)
                    
                    if venue:
                        venue_norm = self._normalize_text(venue)
                        if venue_norm:
                            if venue_norm not in mapping:
                                mapping[venue_norm] = set()
                            mapping[venue_norm].add(slope_norm)
                    
                    if district:
                        district_norm = self._normalize_text(district)
                        if district_norm:
                            if district_norm not in mapping:
                                mapping[district_norm] = set()
                            mapping[district_norm].add(slope_norm)
        
        # Convert sets to lists
        mapping = {k: list(v) for k, v in mapping.items()}
        
        return mapping
    
    def get_slopes_for_location(self, location: str) -> List[str]:
        """
        Get slope numbers associated with a location based on historical learning
        
        Args:
            location: Location name or partial match
            
        Returns:
            List of slope numbers found at this location in historical data
        """
        if not location:
            return []
        
        location_norm = self._normalize_text(location)
        slopes = set()
        
        # Direct match
        if location_norm in self.location_slope_mapping:
            slopes.update(self.location_slope_mapping[location_norm])
        
        # Partial match
        for known_location, slope_list in self.location_slope_mapping.items():
            if location_norm in known_location or known_location in location_norm:
                slopes.update(slope_list)
        
        return list(slopes)
    
    def get_tree_info(self, slope_no: str) -> List[Dict[str, Any]]:
        """
        Get tree information for a specific slope
        
        Args:
            slope_no: Slope number to search for
            
        Returns:
            List of trees on the slope with details
        """
        if self.tree_inventory.empty or not slope_no:
            return []
        
        slope_norm = self._normalize_slope_number(slope_no)
        trees = []
        
        for idx, row in self.tree_inventory.iterrows():
            tree_slope = self._safe_get(row, 'Slope No.')
            if self._normalize_slope_number(tree_slope) == slope_norm:
                trees.append({
                    'tree_id': self._safe_get(row, 'Tree ID'),
                    'species': self._safe_get(row, 'Species'),
                    'dbh': self._safe_get(row, 'DBH'),
                    'height': self._safe_get(row, 'Height'),
                    'condition': self._safe_get(row, 'Condition'),
                    'slope_no': tree_slope
                })
        
        return trees
    
    def get_case_statistics(
        self,
        location: str = None,
        slope_no: str = None,
        venue: str = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics from historical data
        
        Args:
            location: Optional location filter
            slope_no: Optional slope number filter
            venue: Optional venue filter
            
        Returns:
            Dictionary with statistical analysis
        """
        # Collect all cases matching filters
        matching_cases = []
        
        # Search Slopes Complaints
        if not self.slopes_complaints.empty:
            for idx, row in self.slopes_complaints.iterrows():
                if self._matches_filters(row, location, slope_no, venue, source='slopes'):
                    matching_cases.append({
                        'date': self._safe_get(row, 'Received \nDate'),
                        'location': self._safe_get(row, 'Venue') or self._safe_get(row, 'District'),
                        'slope_no': self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope no'),
                        'subject': self._safe_get(row, 'AIMS Complaint Type'),
                        'type': self._safe_get(row, 'Type\nEmergency, Urgent, General'),
                        'source': 'Slopes Complaints 2021'
                    })
        
        # Search SRR Data
        if not self.srr_data.empty:
            for idx, row in self.srr_data.iterrows():
                if self._matches_filters(row, location, slope_no, venue, source='srr'):
                    matching_cases.append({
                        'date': self._safe_get(row, 'Received Date'),
                        'location': self._safe_get(row, 'Venue') or self._safe_get(row, 'District'),
                        'slope_no': self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope No.\n'),
                        'subject': self._safe_get(row, 'Subject Matter'),
                        'type': self._safe_get(row, 'Type'),
                        'source': 'SRR Data 2021-2024'
                    })
        
        # Build statistics
        stats = {
            'total_cases': len(matching_cases),
            'date_range': self._get_date_range(matching_cases),
            'subject_matter_breakdown': self._group_by(matching_cases, 'subject'),
            'case_type_breakdown': self._group_by(matching_cases, 'type'),
            'location_breakdown': self._group_by(matching_cases, 'location'),
            'slope_breakdown': self._group_by(matching_cases, 'slope_no'),
            'data_source_breakdown': self._group_by(matching_cases, 'source'),
            'is_frequent_location': len(matching_cases) >= 5,
            'is_frequent_slope': len(matching_cases) >= 3
        }
        
        return stats
    
    def _matches_filters(self, row, location, slope_no, venue, source) -> bool:
        """Check if row matches the provided filters"""
        if location:
            if source == 'slopes':
                loc_val = self._safe_get(row, 'Venue') or self._safe_get(row, 'District')
            else:
                loc_val = self._safe_get(row, 'Venue') or self._safe_get(row, 'District')
            if not loc_val or location.lower() not in loc_val.lower():
                return False
        
        if slope_no:
            if source == 'slopes':
                slope_val = self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope no')
            else:
                slope_val = self._safe_get(row, 'Verified Slope No.') or self._safe_get(row, 'Slope No.\n')
            if not slope_val or slope_no.lower() not in slope_val.lower():
                return False
        
        if venue:
            venue_val = self._safe_get(row, 'Venue')
            if not venue_val or venue.lower() not in venue_val.lower():
                return False
        
        return True
    
    def _get_date_range(self, cases: List[Dict]) -> Dict[str, str]:
        """Get earliest and latest dates from cases"""
        dates = [c.get('date') for c in cases if c.get('date')]
        if not dates:
            return {'earliest': 'N/A', 'latest': 'N/A'}
        
        return {
            'earliest': min(dates),
            'latest': max(dates)
        }
    
    def _group_by(self, cases: List[Dict], field: str) -> Dict[str, int]:
        """Group cases by field and count"""
        groups = {}
        for case in cases:
            val = case.get(field, 'Unknown')
            if val:
                groups[val] = groups.get(val, 0) + 1
        return groups


# Global singleton instance
_matcher_instance = None


def init_historical_matcher(data_dir: str, db_path: str):
    """Initialize the global historical case matcher instance"""
    global _matcher_instance
    _matcher_instance = HistoricalCaseMatcher(data_dir, db_path)


def get_historical_matcher() -> HistoricalCaseMatcher:
    """Get the global historical case matcher instance"""
    if _matcher_instance is None:
        raise RuntimeError("Historical matcher not initialized. Call init_historical_matcher() first.")
    return _matcher_instance

