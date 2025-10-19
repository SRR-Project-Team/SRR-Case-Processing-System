# Case Similarity Search Documentation

## Overview

The Case Similarity Search system provides intelligent matching of new complaints against historical cases to identify patterns, potential duplicates, and recurring issues at specific locations.

## Features

### 1. Multi-Criteria Matching

The system compares cases based on multiple criteria with weighted scoring:

| Criteria | Weight | Priority | Description |
|----------|--------|----------|-------------|
| **Location (H_location)** | 40% | Highest | Primary matching criterion |
| **Slope/Tree Number** | 30% | High | Specific subject identification |
| **Subject Matter** | 15% | Medium | Category of complaint |
| **Caller Name** | 10% | Low | Caller identification |
| **Phone Number** | 5% | Low | Contact verification |

### 2. Intelligent Matching Algorithms

#### Location Matching
- **Fuzzy matching**: Handles spelling variations and partial matches
- **Threshold**: 70% similarity required
- **Example**: "Broadwood Road Park" matches "Broadwood Rd Park"

#### Slope/Tree Number Matching
- **Exact matching**: Precise identification required
- **Flexible formatting**: Handles variations like "11SW-B/F199" vs "11SWB/F199"
- **Tree extraction**: Automatically extracts tree numbers from text

#### Subject Matter Matching
- **Keyword-based**: Uses Jaccard similarity
- **Handles variations**: Different descriptions of similar issues

#### Caller Matching
- **Name fuzzy matching**: 80% similarity threshold
- **Phone strict matching**: Exact or last 8 digits match

### 3. Duplicate Detection

Cases with **similarity ≥ 70%** are flagged as potential duplicates, indicating:
- Same location
- Same or similar subject matter
- Possibly the same complainant

### 4. Frequent Complaint Analysis

The system tracks:
- **Complaint frequency** per location
- **Complaint frequency** per slope/tree
- **Date ranges** for recurring issues
- **Subject matter patterns**

## API Endpoints

### 1. Find Similar Cases

**Endpoint**: `POST /api/find-similar-cases`

**Request Body**:
```json
{
  "H_location": "Broadwood Road Mini Park",
  "G_slope_no": "11SW-D/CR995",
  "J_subject_matter": "Slope Maintenance",
  "E_caller_name": "John Doe",
  "F_contact_no": "12345678",
  "limit": 10,
  "min_similarity": 0.3
}
```

**Response**:
```json
{
  "status": "success",
  "total_found": 5,
  "similar_cases": [
    {
      "case": {
        "id": 123,
        "C_case_number": "84878800",
        "A_date_received": "18-Mar-2025",
        "H_location": "Broadwood Road Mini Park",
        "G_slope_no": "11SW-D/CR995",
        "J_subject_matter": "Repair slope fixture/furniture",
        ...
      },
      "similarity_score": 0.875,
      "is_potential_duplicate": true,
      "match_details": {
        "location_match": 1.0,
        "slope_tree_match": 0.95,
        "subject_match": 0.75,
        "caller_name_match": 0.0,
        "caller_phone_match": 0.0,
        "component_scores": {
          "location": 0.40,
          "slope_tree": 0.285,
          "subject": 0.1125,
          "caller_name": 0.0,
          "caller_phone": 0.0
        },
        "total_score": 0.875
      }
    }
  ],
  "search_criteria": {
    "location": "Broadwood Road Mini Park",
    "slope_no": "11SW-D/CR995",
    "caller_name": "John Doe",
    "subject_matter": "Slope Maintenance"
  }
}
```

### 2. Get Case Statistics

**Endpoint**: `GET /api/case-statistics`

**Query Parameters**:
- `location` (optional): Location to filter by
- `slope_no` (optional): Slope number to filter by  
- `caller_name` (optional): Caller name to filter by

**Example Request**:
```
GET /api/case-statistics?location=Broadwood
```

**Response**:
```json
{
  "status": "success",
  "statistics": {
    "total_cases": 50,
    "date_range": {
      "earliest": "18-Mar-2025",
      "latest": "18-Mar-2025"
    },
    "subject_matter_breakdown": {
      "Repair slope fixture/furniture": 50
    },
    "case_type_breakdown": {
      "Urgent": 30,
      "General": 15,
      "Emergency": 5
    },
    "recent_cases": [
      { "case details..." }
    ],
    "is_frequent_complaint": true
  }
}
```

## Use Cases

### 1. Identifying Duplicate Complaints

**Scenario**: A new complaint is received about a slope at "Broadwood Road Mini Park"

**System Action**:
1. Searches historical cases
2. Finds 5 similar cases at the same location
3. Flags as potential duplicate (similarity > 70%)
4. Shows the history to the case handler

**Benefit**: Prevents duplicate work, provides historical context

### 2. Tracking Recurring Issues

**Scenario**: Multiple complaints about the same slope over time

**System Action**:
1. Identifies all cases related to slope "11SW-D/CR995"
2. Shows complaint frequency (e.g., 5 times in 3 months)
3. Displays subject matter patterns
4. Flags as "frequent complaint"

**Benefit**: Identifies systemic issues requiring permanent solutions

### 3. Caller History

**Scenario**: Same caller contacts multiple times

**System Action**:
1. Matches caller name and/or phone number
2. Shows all previous complaints from this caller
3. Identifies if caller is reporting different locations or same location

**Benefit**: Better customer service, pattern recognition

### 4. Location Hotspot Analysis

**Scenario**: Checking if a location frequently receives complaints

**System Action**:
1. Queries statistics for the location
2. Shows total number of cases
3. Breaks down by subject matter and urgency
4. Indicates if location is a "hotspot"

**Benefit**: Resource allocation, preventive maintenance planning

## Python Usage Example

```python
from src.services.case_similarity_service import CaseSimilarityService

# Initialize service
service = CaseSimilarityService('data/srr_cases.db')

# Find similar cases
new_case = {
    'H_location': 'Broadwood Road Mini Park',
    'G_slope_no': '11SW-D/CR995',
    'J_subject_matter': 'Slope Maintenance'
}

similar_cases = service.find_similar_cases(
    current_case=new_case,
    limit=10,
    min_similarity=0.3
)

# Check for duplicates
for result in similar_cases:
    if result['is_potential_duplicate']:
        print(f"⚠️ Potential duplicate found!")
        print(f"   Case: {result['case']['C_case_number']}")
        print(f"   Similarity: {result['similarity_score']:.2%}")

# Get statistics for a location
stats = service.get_case_statistics(location="Broadwood")
if stats['is_frequent_complaint']:
    print(f"🔴 This is a frequent complaint location!")
    print(f"   Total cases: {stats['total_cases']}")
```

## Configuration

### Similarity Thresholds

Defined in `CaseSimilarityService.__init__`:

```python
LOCATION_THRESHOLD = 0.7   # 70% for location matching
NAME_THRESHOLD = 0.8       # 80% for name matching
PHONE_THRESHOLD = 0.9      # 90% for phone matching
```

### Scoring Weights

```python
WEIGHT_LOCATION = 0.40        # 40% - Highest priority
WEIGHT_SLOPE_TREE = 0.30      # 30% - Subject matter
WEIGHT_SUBJECT = 0.15         # 15% - Subject category
WEIGHT_CALLER_NAME = 0.10     # 10% - Caller info
WEIGHT_CALLER_PHONE = 0.05    # 5% - Phone verification
```

### Frequent Complaint Threshold

A location/slope is considered a "frequent complaint" if it has **≥ 3 historical cases**.

## Technical Details

### Fuzzy Matching Algorithm

Uses Python's `difflib.SequenceMatcher` for string similarity:

```python
similarity = SequenceMatcher(None, string1, string2).ratio()
```

- Returns value between 0.0 (no match) and 1.0 (exact match)
- Threshold applied to filter weak matches

### Tree Number Extraction

Supports multiple patterns:
- `Tree no: T12345`
- `Tree Number: 12345`
- `T:12345`
- `樹木編號: T12345`

### Slope Number Normalization

Handles format variations:
- `11SW-B/F199` 
- `11SWB/F199`
- `11 SW-B / F199`

All normalized for comparison.

## Testing

Run the test script to verify functionality:

```bash
python3 test_similarity_search.py
```

This will test:
1. Location-based similarity search
2. Slope number matching
3. Statistics generation
4. Caller information matching
5. Duplicate detection

## Performance

- **Database**: SQLite with indexed queries
- **Response Time**: < 1 second for typical queries
- **Scalability**: Tested with 100+ historical cases
- **Memory**: Minimal footprint, cases loaded on-demand

## Future Enhancements

1. **Machine Learning**: Train models on historical match accuracy
2. **Temporal Patterns**: Identify seasonal trends
3. **Geographic Clustering**: Map-based hotspot visualization
4. **Priority Scoring**: Adjust urgency based on complaint frequency
5. **Automated Notifications**: Alert when duplicates detected

## Troubleshooting

### No Similar Cases Found

**Possible Reasons**:
- Minimum similarity threshold too high
- Limited historical data
- Unique case with no precedent

**Solution**: Lower `min_similarity` parameter or check data availability

### Too Many False Positives

**Possible Reasons**:
- Similarity threshold too low
- Generic location names

**Solution**: Increase `min_similarity` or adjust weights

### Performance Issues

**Possible Reasons**:
- Large dataset
- Complex queries

**Solution**: Add database indexes, limit result set

## Support

For issues or questions:
1. Check test script: `python3 test_similarity_search.py`
2. Review API logs for errors
3. Verify database connectivity
4. Check data quality (null values, formatting)

---

**Version**: 1.0  
**Last Updated**: 2025-10-19  
**Author**: Project3 Team


