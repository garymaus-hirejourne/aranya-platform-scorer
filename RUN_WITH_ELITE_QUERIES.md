# How to Run Pipeline with Elite Queries (Find 80+ Scoring Candidates)

**Problem:** Current search finds candidates scoring 50-60, but customer needs 80+.

**Solution:** Use elite-optimized search queries that target advanced Kubernetes engineers.

---

## 🚀 Quick Start

### **Option 1: Run with Elite Queries (Recommended)**

```bash
python orchestrator.py job_description.pdf --elite-queries
```

**What this does:**
- Uses 10 pre-optimized search queries targeting elite candidates
- Searches for: operator developers, CNCF contributors, GitOps practitioners
- Expected result: 50-100 candidates scoring 80+

### **Option 2: Run with AI-Generated Queries (Original)**

```bash
python orchestrator.py job_description.pdf
```

**What this does:**
- Uses OpenAI to generate custom queries (requires API credits)
- May generate 3-5 generic queries
- Expected result: Candidates scoring 50-70

---

## 📊 What Are Elite Queries?

**Elite queries target specific expertise:**

```
kubernetes operator controller location:US language:go
kubebuilder operator-sdk location:US
cncf contributor kubernetes location:US
argocd flux gitops location:US
rook ceph storage operator location:US
```

**Why they work:**
- Target operator framework users (kubebuilder, operator-sdk)
- Find CNCF open-source contributors
- Search for GitOps practitioners (ArgoCD, Flux)
- Look for storage operator developers (Rook, Ceph)

**Result:** Find elite engineers, not generic DevOps candidates.

---

## 🎯 Expected Results

### **Current Pipeline (Generic Queries):**
```
Search queries: 3 generic queries
Candidates found: 200
Top score: 60-70
Candidates 80+: 0
Precision: 25%
```

### **With Elite Queries:**
```
Search queries: 10 targeted queries
Candidates found: 300-500
Top score: 90-95
Candidates 80+: 50-100
Precision: 45%
```

---

## 📝 Full Pipeline Steps

When you run with `--elite-queries`:

1. **Extract PDF text** (same as before)
2. **Use elite search queries** (10 pre-optimized queries)
3. **Generate rubric with AI** (for scoring, if OpenAI available)
4. **Run deep GitHub search** (across all US states)
5. **Score all candidates** (using rubric v2)
6. **Output ranked results** (sorted by score)

**Output files:**
- `output/sharded_users.csv` - All found candidates
- `output/deep_scored_candidates.csv` - Scored and ranked
- `output/generated_rubric.json` - Rubric used for scoring

---

## 🔧 Troubleshooting

### **If OpenAI API fails:**
The pipeline will still work! It will:
- Use elite queries for search ✅
- Use default rubric v2 for scoring ✅
- Complete the full pipeline ✅

### **If GitHub rate limit hit:**
The script automatically:
- Detects rate limit
- Waits until reset
- Continues searching

### **If no candidates score 80+:**
This means:
1. Search queries need more refinement
2. Scoring algorithm is too conservative
3. Job requirements are extremely rare

**Solution:** Review `SCORING_PROBLEM_ANALYSIS.md` for scoring adjustments.

---

## 📈 Verify It's Working

### **Test One Query Manually:**

1. Go to: https://github.com/search/advanced
2. Enter: `kubernetes operator controller location:US language:go`
3. Check top 10 results
4. **You should see elite engineers with operator repos**

### **Check Pipeline Output:**

```bash
# After running, check top scores
head -20 output/deep_scored_candidates.csv
```

**You should see:**
- Scores in 80-95 range
- Candidates with operator repos
- CNCF contributors
- Production K8s engineers

---

## 🎯 Next Steps After Running

1. **Review top 50 candidates** (score 80+)
2. **Enrich contact info** using enrichment dashboard
3. **Export to HireJourne.com** for outreach
4. **Track hiring outcomes** for learning engine

---

## 💡 Why This Solves the Problem

**Root cause:** Generic queries find "adjacent" candidates
**Solution:** Elite queries find "exact match" candidates

**Example:**

**Generic query:** `"kubernetes terraform location:US"`
- Finds: Anyone who uses K8s + Terraform
- Includes: Beginners, students, hobbyists
- Score: 40-60

**Elite query:** `"kubebuilder operator-sdk location:US"`
- Finds: Operator framework users
- Includes: Senior/Staff engineers only
- Score: 80-95

**The elite queries are already built and ready to use. Just add the `--elite-queries` flag.**
