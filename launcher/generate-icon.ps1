<#
  Generates launcher/fs.ico (multi-resolution) and fs.png for the FeintSignal desktop app.
  Pure System.Drawing - no external assets required.
#>
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

function New-PngBytes {
  param([int]$Size)

  $bitmap = New-Object System.Drawing.Bitmap $Size, $Size
  $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAlias
  $graphics.Clear([System.Drawing.Color]::FromArgb(10, 14, 20))   # #0A0E14 dark tactical bg

  $cyan = [System.Drawing.Color]::FromArgb(79, 159, 224)          # #4F9FE0
  $green = [System.Drawing.Color]::FromArgb(63, 185, 80)          # #3FB950
  $pen = New-Object System.Drawing.Pen $cyan, ([Math]::Max(2, [int]($Size / 16)))

  # Outer frame
  $graphics.DrawRectangle($pen, [int]($Size * 0.1), [int]($Size * 0.1), [int]($Size * 0.8), [int]($Size * 0.8))

  # A radar "ping" dot, lower-right
  $dotBrush = New-Object System.Drawing.SolidBrush $green
  $d = [int]($Size * 0.12)
  $graphics.FillEllipse($dotBrush, [int]($Size * 0.66), [int]($Size * 0.66), $d, $d)

  # "FS" monogram, centered
  $font = [System.Drawing.Font]::new(
    "Consolas",
    [single]([Math]::Max(8, [int]($Size * 0.42))),
    [System.Drawing.FontStyle]::Bold,
    [System.Drawing.GraphicsUnit]::Pixel
  )
  $textBrush = New-Object System.Drawing.SolidBrush $cyan
  $format = New-Object System.Drawing.StringFormat
  $format.Alignment = [System.Drawing.StringAlignment]::Center
  $format.LineAlignment = [System.Drawing.StringAlignment]::Center
  $rect = New-Object System.Drawing.RectangleF 0, ([single](-$Size * 0.04)), ([single]$Size), ([single]$Size)
  $graphics.DrawString("FS", $font, $textBrush, $rect, $format)

  $memoryStream = New-Object System.IO.MemoryStream
  $bitmap.Save($memoryStream, [System.Drawing.Imaging.ImageFormat]::Png)
  $pngBytes = $memoryStream.ToArray()

  $graphics.Dispose(); $bitmap.Dispose(); $memoryStream.Dispose()
  $pen.Dispose(); $font.Dispose(); $textBrush.Dispose(); $dotBrush.Dispose(); $format.Dispose()
  return ,$pngBytes
}

function Write-IcoFile {
  param([byte[][]]$Images, [int[]]$Sizes, [string]$Path)

  $fileStream = [System.IO.File]::Open($Path, [System.IO.FileMode]::Create)
  $writer = New-Object System.IO.BinaryWriter $fileStream
  $writer.Write([UInt16]0); $writer.Write([UInt16]1); $writer.Write([UInt16]$Images.Count)

  $offset = 6 + (16 * $Images.Count)
  for ($index = 0; $index -lt $Images.Count; $index++) {
    $size = $Sizes[$index]; $bytes = $Images[$index]
    $writer.Write([byte]($(if ($size -ge 256) { 0 } else { $size })))
    $writer.Write([byte]($(if ($size -ge 256) { 0 } else { $size })))
    $writer.Write([byte]0); $writer.Write([byte]0)
    $writer.Write([UInt16]1); $writer.Write([UInt16]32)
    $writer.Write([UInt32]$bytes.Length); $writer.Write([UInt32]$offset)
    $offset += $bytes.Length
  }
  foreach ($bytes in $Images) { $writer.Write($bytes) }
  $writer.Flush(); $writer.Dispose(); $fileStream.Dispose()
}

$iconPath = Join-Path $PSScriptRoot "fs.ico"
$pngPath = Join-Path $PSScriptRoot "fs.png"
$sizes = @(16, 32, 48, 64, 128, 256)
$images = @()
foreach ($size in $sizes) { $images += ,(New-PngBytes -Size $size) }

[System.IO.File]::WriteAllBytes($pngPath, $images[-1])
Write-IcoFile -Images $images -Sizes $sizes -Path $iconPath
Write-Host "Generated $iconPath and $pngPath"
