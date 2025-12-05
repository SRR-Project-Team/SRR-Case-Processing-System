# How to Use the SRR Case Processing System

## Quick Start Guide

### Step 1: Set OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

💡 Get your API key from: https://platform.openai.com/api-keys

### Step 2: Start the System

```bash
python start.py start
```

This will start both backend (port 8001) and frontend (port 3000).

### Step 3: Open the Interface

Open your browser and go to: http://localhost:3000

### Step 4: Upload a File

1. Click the 📁 **Upload Files** button
2. Drag and drop or select your PDF/TXT files
3. Click **Process Files**

### Step 5: View Results

The system will automatically:
1. ✅ Extract case information (A-Q columns)
2. 🤖 Generate AI summary using OpenAI
3. 🔍 Search 5,298 historical cases (Excel/CSV data only, database excluded)
4. 📊 Show location statistics and complaint frequency from historical data
5. 🔴 Flag potential duplicates (≥70% similarity)
6. 🌳 Show tree information if applicable

## What You'll See

### 1. Extracted Case Information

```
📋 Extracted Case Information:
   📅 Date Received: 18-Mar-2025
   📞 Source: TMO
   🔢 Case Number: 84878800
   📍 Location: Broadwood Road Mini Park
   🏗️ Slope Number: 11SW-D/CR995
   ...
```

### 2. AI Summary

```
🤖 AI Summary:

"Emergency case regarding slope surface cracks at Broadwood 
Road Mini Park requiring immediate inspection and repair work."
```

### 3. Similar Cases (From 5,298 Historical Records)

```
🔍 Searching for similar historical cases...

📚 Found 10 Similar Cases (from 5,298 historical records):

**1. [SRR Data 2021-2024] Case #ICC#3-6914202096** (58.8% match)
   📅 Date: 18/1/2023
   📍 Location: Broadwood Road Rest Garden
   🏗️ Slope: 11SW-D/CR995
   📝 Subject: Tree trimming/pruning
   👤 Caller: Mr. Wong
   📞 Phone: 28904087
   📄 Complaint Details: Enquiry about tree trimming progress at slope area...

**2. [Slopes Complaints 2021] Case #SC2021-1234** (70.0% match) 🔴 POTENTIAL DUPLICATE
   📅 Date: 04/10/2021
   📍 Location: Wan Chai South
   🏗️ Slope: 11SE-C/C805
   📝 Subject: Grass Cutting
   👤 Caller: Ms. Chan
   📞 Phone: 12345678
   📄 Complaint Details: Request for grass cutting service at slope location...

**3. [SRR Data 2021-2024] Case #RCC#84123456** (45.2% match)
   📅 Date: 15/3/2022
   📍 Location: Broadwood area
   🏗️ Slope: 11SW-D/CR990
   👤 Caller: Mr. Lee
   📞 Phone: 98765432
   ...

Data Sources Searched (Historical Only):
- Slopes Complaints 2021: 4,047 cases ✅
- SRR Data 2021-2024: 1,251 cases ✅
- Current Database: Excluded ❌
```

### 4. Location Statistics (From Historical Data Only)

```
📊 Location Statistics:

📍 Location: Broadwood Road Mini Park
📈 Total Historical Cases: 318 (2021-2024 data)
⚠️ Frequent Complaint: YES 🔴

Data Source Breakdown (Historical Only):
- Slopes Complaints 2021: 0 cases
- SRR Data 2021-2024: 318 cases
- Current Database: Excluded ❌

Subject Matter Breakdown:
- Tree trimming/pruning: 77 cases
- Hazardous tree: 68 cases
- Grass Cutting: 33 cases

⚠️ This location has received 318 complaints in historical 
records (2021-2024), indicating a significant recurring issue 
that requires systematic attention.
```

## Understanding the Results

### Similarity Scores

- **90-100%**: Almost identical case (likely duplicate)
- **70-89%**: Very similar case (same location + similar issue)
- **50-69%**: Similar case (same location OR similar issue)
- **30-49%**: Somewhat related case
- **< 30%**: Not shown (below threshold)

### Duplicate Indicators

🔴 **POTENTIAL DUPLICATE** appears when similarity ≥ 70%

This means:
- Same or very similar location
- Same or similar slope/tree
- Similar subject matter
- Possibly the same issue reported again

### Frequent Complaint Warning

⚠️ **Frequent Complaint: YES 🔴** appears when:
- Location has ≥ 3 historical complaints
- Indicates recurring or systemic issue
- May need permanent solution rather than temporary fix

## Matching Criteria (Priority Order)

1. **📍 Location (40%)** - Most important
   - Exact match or high similarity
   - Fuzzy matching for variations

2. **🏗️ Slope/Tree Number (30%)** - Very important
   - Exact number match
   - Handles format variations

3. **📝 Subject Matter (15%)** - Important
   - Category of complaint
   - Keyword matching

4. **👤 Caller Information (15%)** - Additional context
   - Name matching (10%)
   - Phone matching (5%)

## Use Cases

### Case 1: Checking for Duplicates

**When to check**: New complaint received

**What system does**:
- Automatically searches when file is processed
- Shows cases with similarity ≥ 30%
- Flags potential duplicates (≥ 70%)

**What you should do**:
- Review flagged duplicates
- Check if follow-up to existing case
- Avoid duplicate investigations

### Case 2: Identifying Hotspots

**When to check**: Location shows "Frequent Complaint: YES"

**What system shows**:
- Total number of complaints
- Date range of complaints
- Subject matter breakdown
- Case type distribution

**What you should do**:
- Consider if location needs systematic inspection
- Escalate to management if ≥ 5 complaints
- Plan preventive maintenance

### Case 3: Tracking Caller History

**When to check**: Same caller appears multiple times

**What system shows**:
- All previous cases from this caller
- Different locations or same location
- Pattern of complaints

**What you should do**:
- Provide better customer service
- Reference previous interactions
- Track resolution quality

## Advanced Features

### Manual Similar Case Search

You can also ask the chatbot:

```
"Find similar cases to this one"
"Show me other complaints at this location"
"Has this caller filed complaints before?"
```

### Query Examples

- "What is the basic information of this case?"
- "Show similar cases"
- "Is this location a frequent complaint area?"
- "How many complaints has this location received?"
- "Contact information"
- "Important dates"

## Troubleshooting

### No Similar Cases Found

**Possible Reasons**:
- Unique location
- First complaint at this location
- No historical data available

**Note**: This is normal for new locations

### Too Many Similar Cases

**Possible Reasons**:
- Common location name (e.g., "Main Road")
- Generic subject matter

**Solution**: Review the similarity scores, focus on high matches (>70%)

### Statistics Show 0 Cases

**Possible Reasons**:
- Location name doesn't match exactly
- Database has limited historical data

**Solution**: Try searching with partial location name

## Technical Details

### Proxy Configuration

The system automatically uses Clash proxy for OpenAI API:
- **Proxy URL**: http://127.0.0.1:7890
- **Enabled by default**: Yes
- **No manual configuration needed**: Just set API key

### API Endpoints

- `POST /api/process-srr-file` - Process single file
- `POST /api/process-multiple-files` - Process multiple files
- `POST /api/find-similar-cases` - Find similar cases
- `GET /api/case-statistics` - Get statistics
- `GET /health` - Health check

### Response Time

- File processing: 1-5 seconds (TXT), 30-120 seconds (PDF)
- AI summary: 1-3 seconds
- Similar case search: < 1 second
- Total: 2-125 seconds depending on file type

## Best Practices

### For Efficient Processing

1. **Batch Upload**: Upload related files together
2. **File Naming**: Use clear, descriptive filenames
3. **File Pairing**: TXT files with corresponding email files

### For Similarity Search

1. **Review High Matches**: Focus on cases with >70% similarity
2. **Check Dates**: Recent cases are more relevant
3. **Verify Location**: Confirm location names match
4. **Cross-reference**: Check case numbers in existing system

### For Duplicate Management

1. **Check Flagged Cases**: Review all 🔴 marked cases
2. **Verify Details**: Compare case details manually
3. **Contact Caller**: Confirm if follow-up or new issue
4. **Link Cases**: Reference original case if duplicate

## Support

### Common Questions

**Q: Why didn't my AI summary generate?**  
A: Check that OPENAI_API_KEY is set and Clash is running

**Q: Why are there so many similar cases?**  
A: Common locations may have many complaints. Focus on high similarity scores.

**Q: How accurate is the duplicate detection?**  
A: Cases with ≥70% similarity are flagged. Manual verification recommended.

**Q: Can I adjust the similarity threshold?**  
A: Yes, modify `min_similarity` parameter in the code (default: 0.3)

### Getting Help

1. Check documentation in `docs/` folder
2. Review `FEATURES_IMPLEMENTATION_SUMMARY.md`
3. Check application logs for errors
4. Verify Clash proxy is running: `lsof -i :7890`

## Summary

✅ **OpenAI API**: Configured with Clash proxy  
✅ **Similarity Search**: Automatic on file processing  
✅ **Duplicate Detection**: Flags cases ≥70% similarity  
✅ **Location Statistics**: Shows complaint frequency  
✅ **User Interface**: Integrated chat with automatic display  

**Ready to use!** Just set your OPENAI_API_KEY and start the system.

---

**Last Updated**: 2025-10-19  
**System Version**: 2.0  
**Status**: Production Ready
