#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script automatizado para desplegar CyberWatch en AWS

.PARAMETER KeyName
    Nombre del Key Pair existente en AWS

.PARAMETER StackName
    Nombre del stack de CloudFormation (default: cyberwatch-stack)

.PARAMETER InstanceType
    Tipo de instancia EC2 (default: t2.micro)
#>

param(
    [Parameter(Mandatory=$true, HelpMessage="Nombre del Key Pair existente en AWS")]
    [string]$KeyName,
    
    [Parameter(Mandatory=$false)]
    [string]$StackName = "cyberwatch-stack",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("t2.micro", "t3.micro", "t3.small")]
    [string]$InstanceType = "t2.micro"
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success { Write-ColorOutput Green $args }
function Write-Info { Write-ColorOutput Cyan $args }
function Write-Warning { Write-ColorOutput Yellow $args }
function Write-Error { Write-ColorOutput Red $args }

Write-Info "`n=== Despliegue automatizado de CyberWatch en AWS ===`n"

# 1. Validar AWS CLI
Write-Info "[1/6] Validando AWS CLI..."
try {
    $awsVersion = aws --version 2>&1
    Write-Success "OK AWS CLI instalado: $awsVersion"
} catch {
    Write-Error "ERROR AWS CLI no encontrado"
    exit 1
}

# Obtener región configurada
$Region = aws configure get region 2>&1
if ([string]::IsNullOrWhiteSpace($Region)) {
    $Region = "us-east-1"
    Write-Warning "No hay region configurada, usando: $Region"
} else {
    Write-Success "OK Region detectada: $Region"
}

# Verificar credenciales
try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    Write-Success "OK Credenciales AWS configuradas"
    Write-Info "   Account: $($identity.Account)"
} catch {
    Write-Error "ERROR Credenciales no configuradas. Ejecuta: aws configure"
    exit 1
}

# Obtener IP pública para SSH
Write-Info "Obteniendo tu IP publica..."
try {
    $MyIP = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing).Content.Trim()
    $SSHLocation = "$MyIP/32"
    Write-Success "OK Tu IP: $MyIP (SSH restringido)"
} catch {
    $SSHLocation = "0.0.0.0/0"
    Write-Warning "No se pudo obtener IP, SSH abierto a internet"
}

# 2. Verificar Key Pair
Write-Info "`n[2/6] Verificando Key Pair '$KeyName'..."
try {
    $null = aws ec2 describe-key-pairs --key-names $KeyName 2>&1 | ConvertFrom-Json
    Write-Success "OK Key Pair '$KeyName' encontrado"
} catch {
    Write-Error "ERROR Key Pair '$KeyName' no existe en $Region"
    Write-Info "Lista de Key Pairs disponibles:"
    aws ec2 describe-key-pairs --query 'KeyPairs[*].KeyName' --output table
    exit 1
}

# 3. Desplegar CloudFormation
Write-Info "`n[3/6] Desplegando stack de CloudFormation..."
$templateFile = "cloudformation-template.yml"

if (-not (Test-Path $templateFile)) {
    Write-Error "ERROR No se encuentra $templateFile"
    exit 1
}

# Verificar si el stack existe
$stackExists = $false
try {
    $null = aws cloudformation describe-stacks --stack-name $StackName 2>&1 | ConvertFrom-Json
    $stackExists = $true
    Write-Warning "Stack '$StackName' existe. Actualizando..."
    $operation = "update-stack"
} catch {
    Write-Info "Creando nuevo stack '$StackName'..."
    $operation = "create-stack"
}

Write-Info "   Stack: $StackName"
Write-Info "   Region: $Region"
Write-Info "   Instancia: $InstanceType"
Write-Info "   SSH desde: $SSHLocation"

try {
    $null = aws cloudformation $operation `
        --stack-name $StackName `
        --template-body file://$templateFile `
        --parameters `
            ParameterKey=KeyName,ParameterValue=$KeyName `
            ParameterKey=InstanceType,ParameterValue=$InstanceType `
            ParameterKey=SSHLocation,ParameterValue=$SSHLocation `
        --capabilities CAPABILITY_IAM 2>&1
    
    Write-Success "OK Stack $operation iniciado"
} catch {
    if ($_.Exception.Message -match "No updates") {
        Write-Info "No hay cambios que aplicar"
    } else {
        Write-Error "ERROR al crear/actualizar stack"
        exit 1
    }
}

# 4. Esperar a que el stack este listo
Write-Info "`n[4/6] Esperando a que el stack este listo (3-5 min)..."
$maxWaitTime = 600
$waited = 0
$statusToWait = if ($stackExists) { "UPDATE_COMPLETE" } else { "CREATE_COMPLETE" }

while ($waited -lt $maxWaitTime) {
    Start-Sleep -Seconds 10
    $waited += 10
    
    try {
        $stack = aws cloudformation describe-stacks --stack-name $StackName 2>&1 | ConvertFrom-Json
        $status = $stack.Stacks[0].StackStatus
        
        Write-Host "." -NoNewline
        
        if ($status -eq $statusToWait) {
            Write-Host ""
            Write-Success "`nOK Stack completado"
            break
        }
        
        if ($status -match "FAILED" -or $status -match "ROLLBACK") {
            Write-Host ""
            Write-Error "`nERROR El stack fallo: $status"
            exit 1
        }
    } catch {
        Write-Error "`nERROR al verificar estado del stack"
        exit 1
    }
}

if ($waited -ge $maxWaitTime) {
    Write-Error "`nERROR Timeout esperando el stack"
    exit 1
}

# 5. Obtener IP pública
Write-Info "`n[5/6] Obteniendo informacion del servidor..."
try {
    $outputs = aws cloudformation describe-stacks --stack-name $StackName 2>&1 | ConvertFrom-Json
    $publicIP = ($outputs.Stacks[0].Outputs | Where-Object { $_.OutputKey -eq "PublicIP" }).OutputValue
    $websiteURL = ($outputs.Stacks[0].Outputs | Where-Object { $_.OutputKey -eq "WebsiteURL" }).OutputValue
    
    Write-Success "OK Servidor creado"
    Write-Info "   IP Publica: $publicIP"
    Write-Info "   URL: $websiteURL"
} catch {
    Write-Error "ERROR al obtener outputs del stack"
    exit 1
}

Write-Info "`nEsperando 60 seg a que el servidor termine configuracion..."
Start-Sleep -Seconds 60

# 6. Subir codigo
Write-Info "`n[6/6] Subiendo codigo de CyberWatch..."

$keyPath = "$HOME\.ssh\$KeyName.pem"
if (-not (Test-Path $keyPath)) {
    Write-Warning "No se encuentra la clave en $keyPath"
    $keyPath = Read-Host "Ingresa la ruta completa al archivo .pem"
}

icacls $keyPath /inheritance:r | Out-Null
icacls $keyPath /grant:r "${env:USERNAME}:(R)" | Out-Null

Write-Info "Subiendo archivos (1-2 min)..."
try {
    scp -i $keyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r * "ubuntu@${publicIP}:/opt/cyberwatch/" 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        throw "Error en SCP"
    }
    
    Write-Success "OK Codigo subido"
} catch {
    Write-Error "ERROR al subir codigo"
    Write-Info "Subelo manualmente:"
    Write-Info "scp -i $keyPath -r * ubuntu@${publicIP}:/opt/cyberwatch/"
    exit 1
}

Write-Info "`nIniciando servicio de CyberWatch..."
try {
    ssh -i $keyPath -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "ubuntu@$publicIP" "sudo /opt/deploy-cyberwatch.sh" 2>&1 | Out-Null
    Write-Success "OK Servicio iniciado"
} catch {
    Write-Warning "No se pudo iniciar automaticamente"
    Write-Info "Conectate por SSH y ejecuta: sudo /opt/deploy-cyberwatch.sh"
}

Write-Success "`n=== Despliegue completado exitosamente ===`n"
Write-Info "Informacion del servidor:"
Write-Info "  URL:      $websiteURL"
Write-Info "  IP:       $publicIP"
Write-Info "  Region:   $Region"
Write-Info "  Type:     $InstanceType"
Write-Info "`nComandos utiles:"
Write-Info "  SSH:      ssh -i $keyPath ubuntu@$publicIP"
Write-Info "  Logs:     ssh -i $keyPath ubuntu@$publicIP 'sudo journalctl -u cyberwatch -f'"
Write-Info "  Restart:  ssh -i $keyPath ubuntu@$publicIP 'sudo systemctl restart cyberwatch'"
Write-Info "`nEliminar:"
Write-Info "  aws cloudformation delete-stack --stack-name $StackName"
Write-Success "`nAbre tu navegador en: $websiteURL"
Write-Info "(Espera 1-2 minutos si no carga inmediatamente)`n"
