param([string]$JavaHome = 'C:\Program Files\Android\Android Studio\jbr')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$classes = Join-Path $root 'apps\android\app\build\tmp\kotlin-classes\debug'
if (!(Test-Path -LiteralPath $classes)) { throw 'Compile Android first (assembleDebug).' }
$stdlibRoot = Join-Path $root '.cache\gradle\caches\modules-2\files-2.1\org.jetbrains.kotlin\kotlin-stdlib\2.0.21'
$stdlib = Get-ChildItem -LiteralPath $stdlibRoot -Recurse -File -Filter 'kotlin-stdlib-2.0.21.jar' | Select-Object -First 1
if (!$stdlib) { throw 'Kotlin 2.0.21 runtime is missing from the build cache.' }
$output = Join-Path $root '.cache\tests\android-packet'
New-Item -ItemType Directory -Path $output -Force | Out-Null
$classpath = $classes + ';' + $stdlib.FullName
& "$JavaHome\bin\javac.exe" -encoding UTF-8 -classpath $classpath -d $output (Join-Path $root 'tests\WakePacketTest.java')
if ($LASTEXITCODE -ne 0) { throw 'WoL test compilation failed.' }
& "$JavaHome\bin\java.exe" --class-path ($output + ';' + $classpath) WakePacketTest
if ($LASTEXITCODE -ne 0) { throw 'WoL production-code tests failed.' }
