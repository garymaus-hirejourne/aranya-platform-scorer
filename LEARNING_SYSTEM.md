# Learning System - Making Your Search Smarter

## Overview

The learning system uses **OpenAI to analyze your hiring outcomes** and automatically improve future searches. Every time you provide feedback on candidates, the system learns what makes a good hire and adjusts accordingly.

## How It Works

```
┌─────────────────┐
│  Run Pipeline   │
│  Find 200       │
│  Candidates     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Enrich in Clay │
│  Interview Some │
│  Hire Someone   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Record Feedback│  ◄── YOU DO THIS
│  (hired/rejected)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Next Pipeline  │
│  Run Uses       │  ◄── AUTOMATIC LEARNING
│  Learnings      │
└─────────────────┘
```

## Step 1: Record Feedback on Candidates

After you interview/hire candidates, record the outcomes:

### Add Individual Feedback

```bash
python feedback_tracker.py add <username> <outcome> [notes]
```

**Outcomes:**
- `hired` - You hired this person
- `interviewed` - Made it to full interview
- `phone_screen` - Made it to phone screen
- `rejected` - Not a good fit
- `no_response` - They didn't respond

**Examples:**

```bash
# Record a hire
python feedback_tracker.py add johndoe hired "Great Kubernetes experience"

# Record an interview
python feedback_tracker.py add janedoe interviewed "Strong Go skills but not enough IaC"

# Record a rejection
python feedback_tracker.py add baddev rejected "Not enough relevant experience"
```

### Bulk Import from CSV

If you track outcomes in a spreadsheet:

```bash
python feedback_tracker.py import outcomes.csv
```

Your CSV should have columns:
- `username` - GitHub username
- `outcome` - One of: hired, interviewed, phone_screen, rejected, no_response
- `notes` - (optional) Why this outcome

**Example CSV:**

```csv
username,outcome,notes
johndoe,hired,Excellent platform engineering skills
janedoe,interviewed,Strong candidate but chose another offer
bobsmith,phone_screen,Good technical skills
alicejones,rejected,Not enough Kubernetes experience
```

### View Statistics

```bash
python feedback_tracker.py stats
```

Output:
```json
{
  "total": 15,
  "outcomes": {
    "hired": 2,
    "interviewed": 5,
    "phone_screen": 4,
    "rejected": 3,
    "no_response": 1
  },
  "success_rate": 73.33
}
```

## Step 2: Automatic Learning

Once you have **3+ successful candidates** (hired, interviewed, or phone_screen), the system automatically learns:

### What Gets Analyzed

When you run `orchestrator.py`, the learning engine:

1. **Fetches GitHub profiles** of successful candidates
2. **Analyzes their repositories** for common patterns
3. **Identifies technologies** that correlate with success
4. **Finds profile characteristics** (bio keywords, follower counts, etc.)
5. **Generates insights** using OpenAI

### What Gets Improved

The system automatically refines:

#### **Rubric Weights**
- Increases weight for dimensions that successful candidates excel in
- Decreases weight for dimensions that don't correlate with success

**Example:**
```
Original: Go_K8s = 20%, IaC = 25%
After Learning: Go_K8s = 30%, IaC = 20%
Reason: 85% of hired candidates had strong K8s repos
```

#### **Search Queries**
- Adds technologies found in successful candidates
- Adjusts follower thresholds based on what worked
- Includes new keyword combinations

**Example:**
```
Original: "language:go language:hcl followers:>5"
After Learning: "language:go kubernetes operators followers:>10"
Reason: Hired candidates averaged 15+ followers and had K8s operator repos
```

#### **Scoring Keywords**
- Updates rubric keywords to match what successful candidates actually use
- Adds new technologies discovered in their repos

## Step 3: See Learning in Action

### First Run (No Learning Data)

```bash
python orchestrator.py job_description.pdf
```

Output:
```
[LEARNING] Only 0 historical candidates tracked. Need 3+ for learning.
[LEARNING] Using base rubric without refinement
```

### After Recording Feedback

```bash
# Record some outcomes
python feedback_tracker.py add user1 hired
python feedback_tracker.py add user2 interviewed
python feedback_tracker.py add user3 phone_screen

# Run pipeline again
python orchestrator.py job_description.pdf
```

Output:
```
[LEARNING] Found 3 historical candidates with 100% success rate
[LEARNING] Refining rubric and queries based on past learnings...
[LEARNING] Applied learnings from historical data
```

## Manual Analysis

You can manually analyze patterns without running the full pipeline:

```bash
python learning_engine.py analyze
```

This outputs detailed insights:

```json
{
  "common_technologies": ["go", "kubernetes", "terraform", "helm"],
  "repository_patterns": [
    "Infrastructure automation tools",
    "Kubernetes operators",
    "Open source contributions to CNCF projects"
  ],
  "profile_characteristics": {
    "bio_keywords": ["platform engineer", "SRE", "DevOps"],
    "location_patterns": ["San Francisco", "Seattle", "Austin"],
    "follower_threshold": 15
  },
  "improved_search_queries": [
    "language:go kubernetes operators followers:>15",
    "terraform helm infrastructure followers:>10"
  ],
  "rubric_recommendations": [
    {
      "dimension": "Go_K8s_Operators",
      "current_weight": 20,
      "recommended_weight": 30,
      "reason": "This skill appeared in 85% of successful candidates"
    }
  ]
}
```

## Best Practices

### 1. Record Feedback Consistently

Track **every candidate** you reach out to, not just hires:
- ✅ Record rejections (helps identify false positives)
- ✅ Record no-responses (helps filter out inactive users)
- ✅ Add notes explaining why (helps LLM understand patterns)

### 2. Wait for Enough Data

- **Minimum:** 3 successful candidates before learning kicks in
- **Recommended:** 10+ candidates with varied outcomes for best results
- **Ideal:** 20+ candidates across multiple hiring cycles

### 3. Review Learnings Periodically

```bash
# Check what the system learned
python learning_engine.py analyze > learnings.json

# Review the insights
cat learnings.json
```

### 4. Iterate on Job Descriptions

If learnings show successful candidates have different skills than your JD emphasizes:
- Update your job description to reflect reality
- Re-run the pipeline with the updated JD
- The system will generate a better-aligned rubric

## Data Storage

All feedback is stored in:
```
data/candidate_feedback.jsonl
```

This is a **JSON Lines** file where each line is one feedback entry:

```json
{"timestamp": "2026-02-22T22:15:00", "username": "johndoe", "outcome": "hired", "notes": "Great K8s skills"}
{"timestamp": "2026-02-23T10:30:00", "username": "janedoe", "outcome": "interviewed", "notes": "Strong candidate"}
```

**Backup this file regularly** - it contains your hiring intelligence!

## Advanced: Multi-Role Learning

If you hire for different roles, you can track which JD led to which hire:

```python
from feedback_tracker import FeedbackTracker

tracker = FeedbackTracker()
tracker.add_feedback(
    username="johndoe",
    outcome="hired",
    notes="Perfect platform engineer",
    job_description_hash="platform_eng_2026_q1",
    rubric_used={"Go_K8s": 30, "IaC": 25, ...}
)
```

This allows the learning engine to:
- Learn different patterns for different roles
- Avoid mixing signals from backend vs. platform vs. SRE hires

## Troubleshooting

### "Not enough feedback data yet"

You need at least 3 successful candidates (hired, interviewed, or phone_screen).

**Solution:** Keep recording feedback until you hit the threshold.

### Learning seems wrong

The LLM might be finding spurious correlations with limited data.

**Solution:** 
- Add more feedback entries (aim for 10+)
- Review `learning_engine.py analyze` output manually
- Adjust the analysis if needed

### Feedback file corrupted

**Solution:**
```bash
# Backup first
cp data/candidate_feedback.jsonl data/candidate_feedback.backup.jsonl

# Fix any malformed JSON lines manually
# Each line must be valid JSON
```

## Example Workflow

### Week 1: First Pipeline Run
```bash
python orchestrator.py platform_engineer.pdf --top 200
# Upload to Clay, enrich, reach out to top 50
```

### Week 2: Record Outcomes
```bash
python feedback_tracker.py add user1 phone_screen "Good initial call"
python feedback_tracker.py add user2 interviewed "Strong technical skills"
python feedback_tracker.py add user3 no_response
python feedback_tracker.py add user4 rejected "Not enough K8s"
```

### Week 3: Second Pipeline Run (With Learning)
```bash
python orchestrator.py platform_engineer.pdf --top 200
# System automatically refines based on Week 2 feedback
# Better candidates found!
```

### Week 4: Hire Someone
```bash
python feedback_tracker.py add user2 hired "Excellent hire!"
# This strengthens the learning for future runs
```

### Week 5: Third Pipeline Run (Even Smarter)
```bash
python orchestrator.py platform_engineer.pdf --top 200
# System now knows what led to a hire
# Even better targeting!
```

---

## Summary

The learning system makes your search **exponentially better over time**:

1. **Run pipeline** → Find candidates
2. **Record feedback** → Track outcomes  
3. **Next run learns** → Better rubrics & queries
4. **Repeat** → Continuous improvement

After 3-4 hiring cycles, the system will be **highly tuned** to find candidates who actually get hired, not just candidates who look good on paper.
