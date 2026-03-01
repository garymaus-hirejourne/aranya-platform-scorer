# Quick Start: Clay.com LinkedIn Enrichment

**Total time: ~1 hour (5 minutes hands-on)**

---

## 🚀 Run This Now

### **Step 1: Score All Candidates (25-30 minutes)**

```bash
python deep_scorer_v3.py "H:\Shared drives\HireJourne 2026\Clients\Individuals\Saunders, Michele\Clay v3\sharded_users.csv"
```

**Output:** `output/deep_scored_candidates_v3.csv`

---

### **Step 2: Export for Clay (30 seconds)**

```bash
python export_for_clay.py
```

**Output:** `output/clay_upload_candidates.csv`

---

### **Step 3: Upload to Clay.com (2 minutes)**

1. Go to https://clay.com
2. Create table: "GitHub Candidates LinkedIn Enrichment"
3. Import `output/clay_upload_candidates.csv`
4. Add column: "Find LinkedIn URL" (use Clearbit or Apollo)
5. Run enrichment
6. Wait 30-60 minutes (Clay processes automatically)

---

### **Step 4: Download from Clay (1 minute)**

1. Export enriched CSV from Clay
2. Save as: `output/clay_enriched_results.csv`

---

### **Step 5: Merge Results (30 seconds)**

```bash
python merge_clay_results.py
```

**Output:** `output/deep_scored_candidates_v3_enriched.csv`

---

## ✅ Expected Results

**LinkedIn URL Coverage:**
- GitHub extraction: 20-30%
- Clay enrichment: 28-48% more
- **Total: 48-78% coverage**

**For top 50 candidates:** 70-90% will have LinkedIn URLs

---

## 📖 Full Documentation

See `CLAY_UPLOAD_WORKFLOW.md` for detailed instructions and troubleshooting.

---

## 🎯 What You Get

**Final CSV includes:**
- All 2,629 scored candidates
- Overall scores (0-100)
- LinkedIn URLs (48-78% coverage)
- GitHub profiles
- Location, company info
- Ready for email/phone enrichment

---

## 💡 Next Steps After This

1. **Contact enrichment:** Use SignalHire or Hunter.io for emails/phones
2. **CRM import:** Import top candidates to your CRM
3. **Outreach:** Begin personalized campaigns
4. **Repeat:** Run weekly/monthly for new candidates
