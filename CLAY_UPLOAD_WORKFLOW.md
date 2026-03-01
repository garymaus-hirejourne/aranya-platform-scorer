# Clay.com LinkedIn Enrichment Workflow (Starter Plan)

**Date:** February 23, 2026

**Plan:** Clay.com Starter Plan (Limited API access)

**Time Required:** 5 minutes hands-on, 30-60 minutes Clay processing

---

## 🎯 Overview

This workflow uses Clay.com to automatically enrich candidates with LinkedIn URLs. Since the Starter plan doesn't have full API access, we use a CSV upload/download workflow that requires minimal manual work.

**Process:**
1. Export candidates needing LinkedIn → CSV (automated)
2. Upload CSV to Clay.com (2 minutes manual)
3. Clay enriches with LinkedIn URLs (30-60 minutes automatic)
4. Download enriched CSV from Clay (1 minute manual)
5. Merge results back into scored candidates (automated)

**Total hands-on time: ~5 minutes**

---

## 📋 Step-by-Step Instructions

### **Step 1: Run the Scorer (25-30 minutes, automated)**

```bash
python deep_scorer_v3.py "H:\Shared drives\HireJourne 2026\Clients\Individuals\Saunders, Michele\Clay v3\sharded_users.csv"
```

**Output:**
- `output/deep_scored_candidates_v3.csv`
- Contains all scored candidates
- LinkedIn URLs extracted from GitHub profiles (20-30%)

---

### **Step 2: Export Candidates for Clay (30 seconds, automated)**

```bash
python export_for_clay.py
```

**What it does:**
- Reads `output/deep_scored_candidates_v3.csv`
- Filters candidates without LinkedIn URLs
- Creates `output/clay_upload_candidates.csv`
- Optimized format for Clay.com upload

**Output columns:**
- GitHub Username
- Name
- Location
- Company
- Overall Score
- GitHub URL

---

### **Step 3: Upload to Clay.com (2 minutes, manual)**

**3.1 Log into Clay.com**
- Go to https://clay.com
- Log in with your account

**3.2 Create New Table**
- Click "New Table" or "+" button
- Name: "GitHub Candidates LinkedIn Enrichment"
- Or reuse existing table if you've done this before

**3.3 Import CSV**
- Click "Import" or "Add Data"
- Select "CSV Upload"
- Choose file: `output/clay_upload_candidates.csv`
- Map columns (should auto-detect)
- Click "Import"

**3.4 Add LinkedIn Enrichment Column**
- Click "Add Column" or "+"
- Search for "Find LinkedIn URL" or "Enrich Person"
- Select enrichment provider:
  - **Recommended:** Clearbit, Apollo.io, or People Data Labs
  - These have best success rates for LinkedIn URLs
- Configure enrichment:
  - Input: Use "Name" column
  - Additional inputs: "Location", "Company" (if available)
- Click "Add" or "Run"

**3.5 Run Enrichment**
- Clay will automatically start processing
- Progress bar shows enrichment status
- **Wait time: 30-60 minutes** (Clay processes in background)
- You can close the tab - Clay will continue processing

---

### **Step 4: Download Enriched Results (1 minute, manual)**

**4.1 Check Enrichment Status**
- Return to Clay.com table
- Check if enrichment is complete (progress bar at 100%)

**4.2 Export CSV**
- Click "Export" or download icon
- Select "Export as CSV"
- Download file
- **Save as:** `output/clay_enriched_results.csv`
  - Important: Use this exact filename for the merge script

**4.3 Verify Download**
- Open CSV in Excel/Sheets
- Check that LinkedIn URL column has data
- Should see LinkedIn URLs for 40-60% of candidates

---

### **Step 5: Merge Results (30 seconds, automated)**

```bash
python merge_clay_results.py
```

**What it does:**
- Reads original scored candidates
- Reads Clay enrichment results
- Merges LinkedIn URLs by GitHub Username
- Creates `output/deep_scored_candidates_v3_enriched.csv`

**Output:**
- All candidates with scores
- LinkedIn URLs from GitHub (20-30%)
- LinkedIn URLs from Clay (40-60% of remaining)
- **Total LinkedIn coverage: 55-75%**

---

## 📊 Expected Results

**For 2,629 candidates:**

| Source | LinkedIn URLs | Coverage |
|--------|--------------|----------|
| GitHub profiles | 525-790 | 20-30% |
| Clay enrichment | 735-1,260 | 28-48% |
| **Total** | **1,260-2,050** | **48-78%** |

**For top 50 candidates (80+ scores):**
- Expected LinkedIn coverage: 70-90%
- High-value candidates more likely to have LinkedIn

---

## 💰 Cost

**Clay.com Credits:**
- Starter plan includes credits
- Typical usage: 1-5 credits per enrichment
- For ~2,000 candidates: 2,000-10,000 credits
- Check your Clay dashboard for credit balance

**If you run out of credits:**
- Purchase additional credits in Clay
- Or upgrade to Explorer plan for more credits
- Or run enrichment in batches (top candidates first)

---

## 🔄 Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Run Scorer (25-30 min, automated)                        │
│    python deep_scorer_v3.py "path/to/candidates.csv"        │
│    → output/deep_scored_candidates_v3.csv                   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Export for Clay (30 sec, automated)                      │
│    python export_for_clay.py                                │
│    → output/clay_upload_candidates.csv                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Upload to Clay.com (2 min, manual)                       │
│    - Log into Clay.com                                      │
│    - Create/open table                                      │
│    - Import CSV                                             │
│    - Add "Find LinkedIn URL" enrichment                     │
│    - Run enrichment                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Wait for Clay Processing (30-60 min, automatic)          │
│    - Clay enriches in background                            │
│    - Can close browser                                      │
│    - Check back later                                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Download from Clay (1 min, manual)                       │
│    - Export enriched CSV                                    │
│    - Save as: output/clay_enriched_results.csv              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Merge Results (30 sec, automated)                        │
│    python merge_clay_results.py                             │
│    → output/deep_scored_candidates_v3_enriched.csv          │
└─────────────────────────────────────────────────────────────┘
```

**Total time:** ~1 hour (5 minutes hands-on, 55 minutes automated)

---

## 🎯 Tips for Best Results

**1. Prioritize High Scorers**
- If you have limited Clay credits
- Export only candidates with 70+ scores first
- Enrich top candidates before lower-scoring ones

**2. Batch Processing**
- Upload 500-1,000 candidates at a time
- Easier to manage and monitor
- Can prioritize by score

**3. Choose Right Enrichment Provider**
- **Clearbit:** Best for US candidates
- **Apollo.io:** Good for tech professionals
- **People Data Labs:** Broadest coverage
- Try different providers if one has low success rate

**4. Reuse Clay Table**
- Keep the same table for future batches
- Just delete old rows and import new CSV
- Enrichment settings are saved

**5. Monitor Credit Usage**
- Check Clay dashboard for credit balance
- Each enrichment uses 1-5 credits
- Plan accordingly for large batches

---

## 🚀 Automation Upgrade Path

**Current (Starter Plan):**
- 5 minutes manual work per batch
- 55 minutes automated processing
- CSV upload/download workflow

**Future (Explorer Plan - $349/month):**
- 0 minutes manual work
- 100% automated via API
- Webhook-based real-time enrichment
- Worth it if running weekly/daily

**ROI for Explorer:**
- Saves 5 minutes per batch
- If running daily: 150 minutes/month = 2.5 hours
- If running weekly: 20 minutes/month
- Upgrade makes sense if running multiple times per week

---

## ❓ Troubleshooting

**Problem: Clay enrichment has low success rate**
- Try different enrichment provider (Clearbit vs Apollo vs PDL)
- Check if Name and Location columns are populated
- Some candidates may not have public LinkedIn profiles

**Problem: CSV won't upload to Clay**
- Check file format (must be CSV, not Excel)
- Verify column headers are present
- File size limit: Check Clay's documentation

**Problem: Merge script can't find files**
- Verify file paths are correct
- Check that files are in `output/` directory
- Ensure Clay export is saved as `clay_enriched_results.csv`

**Problem: Running out of Clay credits**
- Purchase additional credits in Clay
- Or process in smaller batches
- Or upgrade to Explorer plan for more credits

---

## 📞 Support

**Clay.com Support:**
- Help Center: https://university.clay.com
- Community: https://community.clay.com
- Email: support@clay.com

**Script Issues:**
- Check error messages
- Verify file paths
- Ensure all dependencies installed: `pip install -r requirements.txt`

---

## ✅ Success Metrics

**After enrichment, you should have:**
- 48-78% of candidates with LinkedIn URLs
- 70-90% of top candidates (80+ scores) with LinkedIn
- Ready for contact enrichment (email/phone lookup)
- High-quality leads for outreach

**Next steps after LinkedIn enrichment:**
- Use SignalHire or Hunter.io for email/phone
- Export to CRM or outreach tool
- Begin personalized outreach campaigns
