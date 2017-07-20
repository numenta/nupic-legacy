# Sample script to install Python and pip under Windows
# Authors: Olivier Grisel and Kyle Kastner
# License: CC0 1.0 Universal: http://creativecommons.org/publicdomain/zero/1.0/

$BASE_URL = "https://www.python.org/ftp/python/"

$GET_PIP_URL = "http://releases.numenta.org/pip/1ebd3cb7a5a3073058d0c9552ab074bd/get-pip.py"
$GET_PIP_PATH = "C:\get-pip.py"

$GET_NUMPY_URL = "https://bitbucket.org/carlkl/mingw-w64-for-python/downloads/numpy-1.9.1+openblas-cp27-none-win_amd64.whl"
$GET_NUMPY_PATH = "C:\numpy-1.9.1+openblas-cp27-none-win_amd64.whl"


function DownloadPython ($python_version, $platform_suffix) {
    $webclient = New-Object System.Net.WebClient
    $filename = "python-" + $python_version + $platform_suffix + ".msi"
    $url = $BASE_URL + $python_version + "/" + $filename

    $basedir = $pwd.Path + "\"
    $filepath = $basedir + $filename
    if (Test-Path $filename) {
        Write-Host "Reusing" $filepath
        return $filepath
    }

    # Download and retry up to 5 times in case of network transient errors.
    Write-Host "Downloading" $filename "from" $url
    $retry_attempts = 3
    for($i=0; $i -lt $retry_attempts; $i++){
        try {
            $webclient.DownloadFile($url, $filepath)
            break
        }
        Catch [Exception]{
            Start-Sleep 1
        }
   }
   Write-Host "File saved at" $filepath
   return $filepath
}


function InstallPython ($python_version, $architecture, $python_home) {
    Write-Host "Installing Python" $python_version "for" $architecture "bit architecture to" $python_home
    if ( $(Try { Test-Path $python_home.trim() } Catch { $false }) ) {
        Write-Host $python_home "already exists, skipping."
        return $false
    }
    if ($architecture -eq "32") {
        $platform_suffix = ""
    } else {
        $platform_suffix = ".amd64"
    }
    $filepath = DownloadPython $python_version $platform_suffix
    Write-Host "Installing" $filepath "to" $python_home
    $args = "/qn /i $filepath TARGETDIR=$python_home"
    Write-Host "msiexec.exe" $args
    Start-Process -FilePath "msiexec.exe" -ArgumentList $args -Wait -Passthru
    Write-Host "Python $python_version ($architecture) installation complete"
    return $true
}


function InstallPip ($python_home) {
    $pip_path = $python_home + "\Scripts\pip.exe"
    $python_path = $python_home + "\python.exe"
    if ( $(Try { Test-Path $pip_path.trim() } Catch { $false }) ) {
        Write-Host "pip already installed at " $pip_path
        return $false
    }

    Write-Host "Installing pip..."
    $webclient = New-Object System.Net.WebClient
    $webclient.DownloadFile($GET_PIP_URL, $GET_PIP_PATH)
    Write-Host "Executing:" $python_path $GET_PIP_PATH
    Start-Process -FilePath "$python_path" -ArgumentList "$GET_PIP_PATH" -Wait -Passthru
    return $true
}

function main () {
    InstallPython $env:PYTHON_VERSION $env:PYTHON_ARCH $env:PYTHONHOME
    InstallPip $env:PYTHONHOME

    $python_path = $env:PYTHONHOME + "\python.exe"
    $pip_path = $env:PYTHONHOME + "\Scripts\pip.exe"

    Write-Host "python -m pip install --upgrade pip"
    & $python_path -m pip install --upgrade pip

    Write-Host "pip install " wheel
    & $pip_path install wheel

    Write-Host "pip install " numpy==1.9.1
    #& $pip_path install -i https://pypi.numenta.com/pypi numpy==1.9.1
    # Check AppVeyor cloud cache for NumPy wheel
    if (-Not (Test-Path $GET_NUMPY_PATH)) {
        $webclient = New-Object System.Net.WebClient
        $webclient.DownloadFile($GET_NUMPY_URL, $GET_NUMPY_PATH)
    }
    & $pip_path install $GET_NUMPY_PATH

}

main
