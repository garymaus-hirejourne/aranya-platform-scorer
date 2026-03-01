# Running the Hybrid LinkedIn Discovery Scorer

**Date:** February 23, 2026

**Status:** Ready to run once Google API is activated

---

## 🎯 What This Does

Runs the V3 scorer with hybrid LinkedIn discovery:

1. **Scores all 2,629 candidates** with the improved V3 rubric
2. **Extracts LinkedIn URLs** using hybrid approach:
   - Stage 1: GitHub profile (bio, blog, social accounts)
   - Stage 2: Google Custom Search fallback
3. **Outputs CSV** with scores and LinkedIn URLs

---

## 🚀 Command to Run

```bash
python deep_scorer_v3.py "H:\Shared drives\HireJourne 2026\Clients\Individuals\Saunders, Michele\Clay v3\sharded_users.csv"
```

**Note:** Use the full path to the sharded_users.csv file

---

## ⏱️ Expected Time & Cost

**Time:** 25-30 minutes
- 0.5 seconds per candidate for scoring
- 0.1 seconds per Google API call (for candidates without GitHub LinkedIn)

**Cost:** ~$10-13
- Google Custom Search API: $5 per 1,000 queries
- Estimated 2,000-2,200 Google searches needed
- Total: ~$10-11

**API Usage:**
- 100 free queries per day from Google
- After that: $5 per 1,000 queries
- You'll use ~2,000-2,200 queries total

---

## 📊 Expected Results

**LinkedIn URL Coverage:**

| Source | Candidates | Percentage |
|--------|-----------|------------|
| GitHub profile | 525-790 | 20-30% |
| Google Search | 735-1,050 | 28-40% |
| **Total found** | **1,260-1,840** | **48-70%** |
| Not found | 790-1,370 | 30-52% |

**Top candidates (80+ scores):**
- Expected: 20-30 candidates scoring 80+
- LinkedIn coverage: 70-90% (most will have LinkedIn)

---

## 📁 Output Files

**Primary output:**
- `output/deep_scored_candidates_v3.csv`

**Columns:**
- GitHub Username
- Overall Score
- Analyzed Repos
- Source
- Location
- Go_K8s_Operators (score)
- IaC_Terraform_Helm (score)
- Tooling_Automation (score)
- GitOps (score)
- Storage (score)
- OSS_Familiarity (score)
- Rationale
- Risks
- **LinkedIn URL** ← NEW!

---

## 🔍 What to Check After Running

### **1. Check LinkedIn URL coverage:**
```bash
python -c "import pandas as pd; df = pd.read_csv('output/deep_scored_candidates_v3.csv'); print(f'LinkedIn URLs found: {df[\"LinkedIn URL\"].notna().sum()}/{len(df)} ({df[\"LinkedIn URL\"].notna().sum()/len(df)*100:.1f}%)')"
```

### **2. Check top 20 candidates:**
```bash
python -c "import pandas as pd; df = pd.read_csv('output/deep_scored_candidates_v3.csv'); print(df[['GitHub Username', 'Overall Score', 'Location', 'LinkedIn URL']].head(20))"
```

### **3. Check 80+ scorers with LinkedIn:**
```bash
python -c "import pandas as pd; df = pd.read_csv('output/deep_scored_candidates_v3.csv'); high_scorers = df[df['Overall Score'] >= 80]; print(f'80+ scorers: {len(high_scorers)}'); print(f'With LinkedIn: {high_scorers[\"LinkedIn URL\"].notna().sum()}')"
```

---

## 🎯 Next Steps After Scoring

### **1. Generate Manual Verification Sheet**
```bash
python create_manual_verification_sheet.py
```

This creates `output/manual_verification_top_50.xlsx` for manual LinkedIn verification.

### **2. Manually Verify Top Candidates**
- Open the Excel file
- For each candidate (focus on 80+ scorers):
  - Click GitHub URL to review repos
  - Search LinkedIn for name + location
  - Verify match and enter correct LinkedIn URL
  - Rate match quality

### **3. Use Verified Data for Enrichment**
- Use manually verified LinkedIn URLs for SignalHire
- High confidence these are correct people
- No more wrong matches like before

---

## ⚠️ Troubleshooting

### **Google API Rate Limit**
If you hit rate limits:
- Script will automatically pause for 60 seconds
- Then retry
- This is normal and expected

### **Google API Quota Exceeded**
If you exceed 100 free queries:
- You'll need to enable billing in Google Cloud Console
- Cost: $5 per 1,000 queries
- For 2,629 candidates: ~$10-13 total

### **Low LinkedIn Coverage**
If coverage is lower than expected:
- Check Google API is working (test with `python google_linkedin_finder.py`)
- Check CSE ID is correct in `.env`
- Verify Custom Search Engine is searching `linkedin.com/in/*`

---

## 📞 Support

If you encounter issues:
1. Check the error message carefully
2. Verify Google API credentials in `.env`
3. Test Google API with `python google_linkedin_finder.py`
4. Check Google Cloud Console for API usage/errors

---

**Ready to run once Google API is activated (5 minute wait after enabling).**
