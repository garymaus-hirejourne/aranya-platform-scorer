$ErrorActionPreference = 'Stop'

$commitMessage = "Update Aranya scorer to rubric v2; preserve v1; write candidates CSVs to output; add rubric sample v2.0"

Write-Host "Preparing clean commit (excluding generated outputs, shard_search.py, and tasks/)" -ForegroundColor Cyan

# If candidates_new.csv is currently tracked, untrack it (keep file on disk)
$trackedCandidates = git ls-files --error-unmatch candidates_new.csv 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Host "Untracking candidates_new.csv (generated output)" -ForegroundColor Yellow
  git rm --cached candidates_new.csv | Out-Host
}

# Stage only the intended files
$paths = @(
  '.gitignore',
  'src/aranya_scorer.py',
  'src/aranya_scorer_v1.py',
  'src/aranya_scorer_lite.py',
  'rubric_samples/Aranya - Rubric v2.0.csv'
)

git add -- $paths | Out-Host

# Show what will be committed
Write-Host "Staged changes:" -ForegroundColor Cyan
git diff --cached --name-status | Out-Host

# Commit if there is anything staged
$staged = git diff --cached --name-only
if (-not $staged) {
  Write-Host "No staged changes to commit. Exiting." -ForegroundColor Yellow
  exit 0
}

git commit -m $commitMessage | Out-Host

git push origin main | Out-Host

Write-Host "Done." -ForegroundColor Green
