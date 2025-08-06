# PowerShell script to run RockSmith Guitar Mute example on Windows

Write-Host "RockSmith Guitar Mute - Example Run (Windows)" -ForegroundColor Green
Write-Host "=" * 45

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Check if sample file exists
$sampleFile = "sample\2minutes_p.psarc"
if (-not (Test-Path $sampleFile)) {
    Write-Host "✗ Sample file not found: $sampleFile" -ForegroundColor Red
    Write-Host "Please ensure the sample file is in the correct location." -ForegroundColor Yellow
    exit 1
}

# Create output directory
$outputDir = "output"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Run the main script
$cmd = @("python", "rocksmith_guitar_mute.py", $sampleFile, $outputDir, "--verbose")
Write-Host "Running command: $($cmd -join ' ')" -ForegroundColor Cyan
Write-Host ""

try {
    & python rocksmith_guitar_mute.py $sampleFile $outputDir --verbose
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=" * 45
        Write-Host "✓ Example run completed successfully!" -ForegroundColor Green
        Write-Host "Check the '$outputDir' directory for the processed file." -ForegroundColor Cyan
    } else {
        Write-Host "✗ Example run failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
} catch {
    Write-Host "✗ Example run failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")