# Dashboard Guide - Visualizing Your Pipeline's Intelligence

## Overview

The dashboard provides **real-time visualization** of your recruiting pipeline's learning process, showing you exactly how the system thinks and improves over time.

## Launch the Dashboard

```bash
python dashboard.py
```

Then open your browser to: **http://localhost:5000**

## What You'll See

### 📊 Overall Statistics
- **Total candidates tracked** - How many people you've provided feedback on
- **Outcome breakdown** - Visual badges showing hired/interviewed/rejected counts
- **Success rate** - Percentage of candidates who reached phone screen or better

### 🎓 Learning Status
- **⏳ Collecting Data** - Shows when you need more feedback (< 3 candidates)
- **✅ Learning Active** - Indicates the system is optimizing based on your data
- **Progress indicator** - How many candidates you've tracked

### 🚀 Pipeline Status
- **Idle** - No pipeline currently running
- **Running** - Shows current step when a pipeline is executing
- **Real-time updates** - Refreshes every 5 seconds

### 📈 Rubric Weight Evolution
**Interactive line chart** showing how rubric dimension weights change over time:
- Each line represents a different technical dimension (e.g., "Go_K8s_Operators")
- X-axis: Pipeline run dates
- Y-axis: Weight percentage (0-100%)
- **Hover over points** to see exact values

**What this tells you:**
- Which skills are becoming more important based on successful hires
- How the system adapts its priorities over time
- Whether certain dimensions are consistently high/low

### 🧠 Learning Insights
**Real-time LLM analysis** of successful candidate patterns:

#### Common Technologies
Tags showing which languages/frameworks appear most in hired candidates:
- `go` `kubernetes` `terraform` `helm`

#### Repository Patterns
What types of projects successful candidates build:
- "Infrastructure automation tools"
- "Kubernetes operators"
- "Open source CNCF contributions"

#### Improved Search Queries
Optimized GitHub search strings based on learnings:
- `language:go kubernetes operators followers:>15`
- `terraform helm infrastructure followers:>10`

**Refresh button** - Click to re-analyze with latest feedback

### 📜 Feedback Timeline
**Scrollable timeline** of all candidate feedback entries:
- Date/time of feedback
- GitHub username (clickable)
- Outcome badge (color-coded)
- Your notes explaining the decision

**Color coding:**
- 🟢 Green = Hired
- 🔵 Blue = Interviewed
- 🟣 Purple = Phone Screen
- 🔴 Red = Rejected
- ⚫ Gray = No Response

### 🗂️ Pipeline Run History
**Recent pipeline executions** showing:
- Date/time of each run
- Number of rubric dimensions used
- Number of search queries executed
- Number of candidates found

**What this tells you:**
- How your pipeline configuration has evolved
- Whether recent runs are finding more/fewer candidates
- Trends in rubric complexity

## Dashboard Features

### Auto-Refresh
- **Pipeline status**: Updates every 5 seconds
- **All other data**: Updates every 30 seconds
- No need to manually refresh the page

### Responsive Design
- Works on desktop, tablet, and mobile
- Dark theme optimized for long viewing sessions
- Charts are interactive and zoomable

### Real-Time Learning Visualization
The dashboard shows **exactly how the LLM is thinking**:
1. It fetches GitHub profiles of successful candidates
2. Analyzes their repositories for patterns
3. Identifies common technologies
4. Generates improved search strategies
5. Displays all insights in real-time

## Use Cases

### During a Pipeline Run
Keep the dashboard open to monitor:
- Current execution status
- Which step is running
- Real-time progress updates

### After Recording Feedback
Immediately see:
- Updated success rate
- Whether you've hit the learning threshold (3+ candidates)
- New insights from the LLM analysis

### Before Starting a New Search
Review:
- Rubric evolution chart - See how priorities have shifted
- Learning insights - Understand what's working
- Pipeline history - Check recent run statistics

### Weekly/Monthly Reviews
Track long-term trends:
- Success rate over time
- How rubric weights have evolved
- Which technologies consistently appear in hires

## Advanced Features

### Manual Insight Refresh
Click the **🔄 Refresh Insights** button to:
- Re-run LLM analysis with latest feedback
- Get updated recommendations
- See new patterns that emerged

**When to use:**
- After adding multiple feedback entries
- When you want fresh analysis
- Before starting a new pipeline run

### Rubric Evolution Analysis
The line chart shows **decision-making evolution**:

**Example interpretation:**
```
Run 1: Go_K8s = 20%, IaC = 30%
Run 2: Go_K8s = 25%, IaC = 28%
Run 3: Go_K8s = 30%, IaC = 25%
```

**What this means:**
- The system learned that Kubernetes skills correlate more with successful hires
- IaC is still important but slightly less predictive
- Future searches will prioritize K8s candidates more heavily

### Timeline Patterns
Look for patterns in the feedback timeline:
- **Clustering of outcomes** - Are you rejecting similar candidates?
- **Time gaps** - How long between feedback entries?
- **Notes consistency** - Are rejection reasons similar?

## Troubleshooting

### Dashboard won't start
```bash
# Install Flask if missing
pip install Flask==3.0.0

# Run dashboard
python dashboard.py
```

### "No data" messages
- **Stats/Timeline**: Record some feedback first
- **Insights**: Need 3+ successful candidates
- **History**: Run the pipeline at least once
- **Rubric Evolution**: Need 2+ pipeline runs

### Charts not showing
- Ensure you have multiple pipeline runs
- Check browser console for JavaScript errors
- Try refreshing the page

### Insights show "insufficient_data"
You need at least 3 candidates with outcomes of:
- `hired`
- `interviewed`
- `phone_screen`

Record more feedback to enable learning.

## Dashboard API Endpoints

The dashboard exposes REST APIs you can query directly:

```bash
# Get statistics
curl http://localhost:5000/api/stats

# Get feedback timeline
curl http://localhost:5000/api/timeline

# Get learning insights
curl http://localhost:5000/api/insights

# Get pipeline history
curl http://localhost:5000/api/pipeline_history

# Get rubric evolution
curl http://localhost:5000/api/rubric_evolution

# Get current pipeline progress
curl http://localhost:5000/api/progress
```

**Use case:** Integrate with other tools or build custom visualizations

## Tips for Maximum Insight

### 1. Record Detailed Notes
```bash
python feedback_tracker.py add johndoe hired "Strong K8s operator experience, contributed to Istio, excellent communication"
```

Better notes = Better LLM analysis

### 2. Track All Outcomes
Don't just track hires - track rejections too:
- Helps identify false positives
- Improves pattern recognition
- Refines future searches

### 3. Review Insights Regularly
- Check dashboard before each new pipeline run
- Look for emerging patterns
- Adjust job descriptions based on insights

### 4. Monitor Rubric Evolution
- Watch for dimensions that consistently increase
- Consider manually emphasizing those in job descriptions
- Use insights to guide interview questions

### 5. Use Timeline for Retrospectives
- Review what led to successful hires
- Identify common rejection reasons
- Spot trends in candidate quality over time

## Example Dashboard Session

### Scenario: You've just hired someone

1. **Record the hire:**
   ```bash
   python feedback_tracker.py add johndoe hired "Perfect platform engineer"
   ```

2. **Open dashboard:**
   ```bash
   python dashboard.py
   # Visit http://localhost:5000
   ```

3. **Check Statistics:**
   - Success rate increased to 75%
   - Now have 4 successful candidates

4. **Refresh Insights:**
   - Click "🔄 Refresh Insights"
   - See new technologies: `istio`, `envoy` added
   - New search query suggested: `language:go istio service-mesh followers:>10`

5. **Review Rubric Evolution:**
   - "Service_Mesh" dimension weight increased from 15% → 25%
   - System learned this skill matters more

6. **Next Pipeline Run:**
   - Will automatically use these learnings
   - Better targeting of candidates with service mesh experience

---

## Summary

The dashboard transforms your recruiting pipeline from a **black box into a glass box** - you can see exactly:
- What the system is learning
- How it's adapting
- Why it makes certain decisions
- How to improve future searches

It's your **window into the AI's decision-making process**.
