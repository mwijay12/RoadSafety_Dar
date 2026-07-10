# Switch to SQLite for local development
$schema = "C:\Users\MWIJAY TECH\Desktop\RoadSafety_Dar\landing\prisma\schema.prisma"
$content = Get-Content $schema -Raw
$content = $content -replace 'provider = "postgresql"', 'provider = "sqlite"'
Set-Content -Path $schema -Value $content

$env = "C:\Users\MWIJAY TECH\Desktop\RoadSafety_Dar\landing\.env"
$envContent = Get-Content $env -Raw
$envContent = $envContent -replace '^DATABASE_URL="postgresql://.*"', '# DATABASE_URL="postgresql://..."'
$envContent = $envContent -replace '# DATABASE_URL="file:./dev.db"', 'DATABASE_URL="file:./dev.db"'
Set-Content -Path $env -Value $envContent

Write-Host "✅ Switched to SQLite. Run: npx prisma generate && npx prisma db push"
