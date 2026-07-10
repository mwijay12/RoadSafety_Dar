# Switch to PostgreSQL for Vercel/Supabase
$schema = "C:\Users\MWIJAY TECH\Desktop\RoadSafety_Dar\landing\prisma\schema.prisma"
$content = Get-Content $schema -Raw
$content = $content -replace 'provider = "sqlite"', 'provider = "postgresql"'
Set-Content -Path $schema -Value $content

$env = "C:\Users\MWIJAY TECH\Desktop\RoadSafety_Dar\landing\.env"
$envContent = Get-Content $env -Raw
$envContent = $envContent -replace '^DATABASE_URL="file:\./dev\.db"', '# DATABASE_URL="file:./dev.db"'
$envContent = $envContent -replace '# DATABASE_URL="postgresql://.*"', 'DATABASE_URL="postgresql://postgres:UB5a3bCPnpty*8A@db.aoibkktdmqntfqvuryuc.supabase.co:5432/postgres"'
Set-Content -Path $env -Value $envContent

Write-Host "✅ Switched to PostgreSQL. Run: npx prisma generate"
