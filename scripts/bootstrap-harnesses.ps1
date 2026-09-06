# Clone the math + coding harnesses labs actually wire to models.
# Vendor trees are gitignored (lm-evaluation-harness is huge).
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Math = Join-Path $Root 'vendor\math'
$Coding = Join-Path $Root 'vendor\coding'
New-Item -ItemType Directory -Force -Path $Math, $Coding | Out-Null

function Clone-IfMissing([string]$Url, [string]$Dest) {
    if (Test-Path (Join-Path $Dest '.git')) {
        Write-Host "exists  $Dest"
        return
    }
    Write-Host "clone   $Url"
    git clone --depth 1 $Url $Dest
}

Clone-IfMissing 'https://github.com/huggingface/Math-Verify.git' (Join-Path $Math 'Math-Verify')
Clone-IfMissing 'https://github.com/leanprover-community/repl.git' (Join-Path $Math 'lean-repl')
Clone-IfMissing 'https://github.com/EleutherAI/lm-evaluation-harness.git' (Join-Path $Math 'lm-evaluation-harness')
Clone-IfMissing 'https://github.com/SWE-agent/mini-swe-agent.git' (Join-Path $Coding 'mini-swe-agent')

Write-Host 'done. Lean: scoop install elan  (or elan-init) then  elan default leanprover/lean4:stable'
Write-Host 'Python packages: uv pip install -e ".[dev]"'
