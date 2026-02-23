<#
PowerShell helper to remove tracked `venv` and `data/processed/faiss.index` from index
and optionally rewrite repository history using git-filter-repo (preferred) or BFG.

Usage (from repo root):
  .\scripts\clean_repo.ps1          # does safe untrack + commit
  .\scripts\clean_repo.ps1 -RewriteHistory  # rewrites history (force-push required)

Be sure to have `git` installed and available in PATH. Rewriting history will
require force-pushing and all collaborators must re-clone afterwards.
#>

param(
    [switch]$RewriteHistory
)

function Check-Command($name) {
    $proc = Get-Command $name -ErrorAction SilentlyContinue
    return $null -ne $proc
}

if (-not (Check-Command git)) {
    Write-Error "Git is not available in PATH. Install Git for Windows and re-run this script."
    exit 1
}

$repoRoot = (Get-Location).Path
Write-Output "Repository root: $repoRoot"

# Stage removal from index (keeps files on disk)
Write-Output "Removing tracked `venv` and `data/processed/faiss.index` from index (cached)..."
git rm -r --cached -q venv 2>$null
git rm --cached -q "data/processed/faiss.index" 2>$null

# Ensure .gitignore contains recommended entries
if (-not (Select-String -Path .gitignore -Pattern "^venv/" -SimpleMatch -Quiet)) {
    Add-Content .gitignore "venv/"
}
if (-not (Select-String -Path .gitignore -Pattern "^data/processed/" -SimpleMatch -Quiet)) {
    Add-Content .gitignore "data/processed/"
}

git add .gitignore

try {
    git commit -m "Remove venv and processed data from index; update .gitignore" -q
    Write-Output "Committed removal from index. This does NOT rewrite history."
} catch {
    Write-Output "Nothing to commit or commit failed: $_"
}

if ($RewriteHistory) {
    $origin = git remote get-url origin 2>$null
    if (-not $origin) {
        Write-Error "No 'origin' remote detected. Aborting history rewrite."
        exit 1
    }

    $tmp = Join-Path $env:TEMP ("repo-mirror-{0}" -f ([guid]::NewGuid().ToString()))
    Write-Output "Cloning mirror to: $tmp"
    git clone --mirror $origin $tmp

    Push-Location $tmp
    try {
        if (-not (Check-Command git-filter-repo)) {
            Write-Output "git-filter-repo not found. Attempting to install via pip..."
            python -m pip install --user git-filter-repo
        }

        Write-Output "Running git-filter-repo to remove paths from history..."
        git filter-repo --path venv --path data/processed/faiss.index --invert-paths

        Write-Output "Cleaning up local repo mirror and forcing push..."
        git reflog expire --expire=now --all
        git gc --prune=now --aggressive
        git push --force --all
        git push --force --tags
    } finally {
        Pop-Location
        Remove-Item -Recurse -Force $tmp
    }

    Write-Output "History rewrite complete. All branches and tags force-pushed."
    Write-Output "NOTE: All collaborators must re-clone the repository after this."
}

Write-Output "Done. If you still cannot push due to size limits, inspect large objects with:\n  git verify-pack -v .git/objects/pack/pack-*.idx | sort -k3 -n | tail -n 20\nand map SHAs to paths via:\n  git rev-list --objects --all | grep <SHA>"
