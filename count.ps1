# --- Configuration ---
param (
    [Parameter(Mandatory=$true)]
    [string]$AuthorName
)

$DateStamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputFile = "blame_results_$DateStamp.txt"
$BinaryExtensions = @('.jpg', '.png', '.gif', '.zip', '.tar', '.gz', '.exe', '.bin', '.dll', '.pdb', '.o', '.so', '.a', '.lockb')

Write-Host "--- Starting Blame Analysis ---" -ForegroundColor Cyan
Write-Host "Target Author: `"$AuthorName`""
Write-Host "Output File: $OutputFile"
Write-Host "-------------------------------"

# Initialize counters
$totalLinesRepo = 0
$totalMatchedLines = 0

# Ensure the output file is empty/created
$null = New-Item -Path $OutputFile -ItemType File -Force

# Get all tracked files
$files = git ls-files

foreach ($file in $files) {
    # Skip binary files based on extension
    $extension = [System.IO.Path]::GetExtension($file)
    if ($BinaryExtensions -contains $extension) { continue }

    # Run git blame with porcelain output (easier to parse than standard blame)
    $blameData = git blame -w --porcelain $file 2>$null
    if (-not $blameData) { continue }

    $fileTotalLines = 0
    $fileMatchedLines = 0
    $currentFileContent = New-Object System.Text.StringBuilder

    # Parsing the Porcelain output:
    # Lines starting with 'author ' contain the name
    # Lines starting with a Tab (\t) contain the actual code
    $currentAuthor = ""
    foreach ($line in $blameData) {
        if ($line -match '^author\s+(.*)') {
            $currentAuthor = $matches[1].Trim()
        }
        elseif ($line -match "^\t(.*)") {
            $codeLine = $matches[1]
            $fileTotalLines++
            
            if ($currentAuthor -eq $AuthorName) {
                $fileMatchedLines++
                [void]$currentFileContent.AppendLine($codeLine)
            }
        }
    }

    # Update global counters
    $totalLinesRepo += $fileTotalLines
    $totalMatchedLines += $fileMatchedLines

    # Write to file and host if matches found
    if ($fileMatchedLines -gt 0) {
        Write-Host "Found $fileMatchedLines lines in: $file"
        
        $header = @"
==========================================
File: $file ($fileMatchedLines lines blamed to $AuthorName)
==========================================
"@
        Add-Content -Path $OutputFile -Value $header
        Add-Content -Path $OutputFile -Value $currentFileContent.ToString()
    }
}

# --- Final Summary Calculation ---
Write-Host "`n--- Analysis Complete ---" -ForegroundColor Cyan

if ($totalLinesRepo -gt 0) {
    $percentage = ($totalMatchedLines / $totalLinesRepo) * 100
    $summary = @"
Total Code Lines Blamed (Across Repo): $totalLinesRepo
Lines Attributed to '$AuthorName': $totalMatchedLines
Percentage Attributed: $("$("{0:N2}" -f $percentage)%")
"@
} else {
    $summary = @"
Total Code Lines Blamed (Across Repo): 0
Lines Attributed to '$AuthorName': 0
Percentage Attributed: N/A
"@
}

Write-Host $summary
$summary | Add-Content -Path $OutputFile
Write-Host "Detailed output saved to: $OutputFile"
Write-Host "-------------------------"