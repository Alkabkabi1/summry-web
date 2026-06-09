# Publish Summry Web to GitHub (same pattern as portfolio repo)
# Prerequisite: gh auth login

Set-Location $PSScriptRoot

$repo = "summry-web"
$owner = "Alkabkabi1"

Write-Host "Checking GitHub auth..."
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: gh auth login"
    exit 1
}

Write-Host "Creating repo https://github.com/$owner/$repo ..."
gh repo create $repo `
    --public `
    --source=. `
    --remote=origin `
    --push `
    --description "Upload PDFs and generate exam-prep study packs with summaries, flashcards, and practice tests."

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Done! Open: https://github.com/$owner/$repo"
}
