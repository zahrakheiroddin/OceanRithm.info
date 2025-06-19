from django.shortcuts import render
import platform
import os
import distro
import subprocess
import time
import sys
import shutil
import urllib.request
from django.contrib import messages
from django.http import JsonResponse
import json

# Create your views here.

def get_os_details():
    """Get detailed OS information"""
    os_info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }
    
    # Get more detailed Linux distribution information
    if os_info['system'] == 'Linux':
        try:
            os_info['distribution'] = distro.name(pretty=True)
            os_info['distribution_version'] = distro.version()
            os_info['codename'] = distro.codename()
            
            # Get kernel version
            kernel_version = subprocess.check_output(['uname', '-r']).decode().strip()
            os_info['kernel_version'] = kernel_version
        except:
            os_info['distribution'] = 'Unknown Linux distribution'
    
    # Get Windows specific information
    elif os_info['system'] == 'Windows':
        os_info['edition'] = platform.win32_edition() if hasattr(platform, 'win32_edition') else 'Unknown'
    
    # Get macOS specific information
    elif os_info['system'] == 'Darwin':
        os_info['system'] = 'macOS'
        try:
            mac_version = subprocess.check_output(['sw_vers', '-productVersion']).decode().strip()
            os_info['mac_version'] = mac_version
        except:
            os_info['mac_version'] = 'Unknown'
    
    return os_info

def run_command(command, cwd=None):
    """Execute shell command safely"""
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd, 
                              capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, str(e)

def check_command_exists(cmd):
    """Check if a command exists in the system"""
    return shutil.which(cmd) is not None

def jenkins_dashboard(request):
    os_info = get_os_details()
    return render(request, 'jenkins/jenkins_dashboard.html', {'os_info': os_info})

def jenkins_config_windows(request):
    """Jenkins configuration page for Windows"""
    if request.method == 'POST':
        installation_type = request.POST.get('installation_type')
        
        if installation_type == 'msi':
            return install_jenkins_windows_msi(request)
        elif installation_type == 'chocolatey':
            return install_jenkins_windows_chocolatey(request)
        elif installation_type == 'docker':
            return install_jenkins_windows_docker(request)
        elif installation_type == 'check_status':
            return check_jenkins_status_windows(request)
    
    # Check current status
    java_installed = check_command_exists('java')
    docker_installed = check_command_exists('docker')
    jenkins_installed = check_jenkins_windows_installed()
    choco_installed = check_command_exists('choco')
    
    os_info = get_os_details()
    
    context = {
        'os_info': os_info,
        'java_installed': java_installed,
        'docker_installed': docker_installed,
        'jenkins_installed': jenkins_installed,
        'choco_installed': choco_installed,
    }
    
    return render(request, 'jenkins/jenkins_config_windows.html', context)

def jenkins_config_linux(request):
    """Jenkins configuration page for Linux"""
    if request.method == 'POST':
        installation_type = request.POST.get('installation_type')
        
        if installation_type == 'package':
            return install_jenkins_ubuntu_package(request)
        elif installation_type == 'docker':
            return install_jenkins_ubuntu_docker(request)
        elif installation_type == 'check_status':
            return check_jenkins_status_linux(request)
    
    # Check current status
    java_installed = check_command_exists('java')
    docker_installed = check_command_exists('docker')
    jenkins_installed = check_command_exists('jenkins')
    
    os_info = get_os_details()
    
    context = {
        'os_info': os_info,
        'java_installed': java_installed,
        'docker_installed': docker_installed,
        'jenkins_installed': jenkins_installed,
    }
    
    return render(request, 'jenkins/jenkins_config_linux.html', context)

def jenkins_config_mac(request):
    if request.method == 'POST':
        installation_type = request.POST.get('installation_type')
        
        if installation_type == 'homebrew':
            return install_jenkins_homebrew(request)
        elif installation_type == 'docker':
            return install_jenkins_docker(request)
        elif installation_type == 'check_status':
            return check_jenkins_status(request)
    
    # Check current status
    homebrew_installed = check_command_exists('brew')
    docker_installed = check_command_exists('docker')
    jenkins_installed = check_command_exists('jenkins')
    
    context = {
        'homebrew_installed': homebrew_installed,
        'docker_installed': docker_installed,
        'jenkins_installed': jenkins_installed,
        'architecture': platform.machine(),
    }
    
    return render(request, 'jenkins/jenkins_config_mac.html', context)

def install_jenkins_homebrew(request):
    """Install Jenkins using Homebrew"""
    messages.info(request, "Starting Jenkins installation via Homebrew...")
    
    try:
        # Check if Homebrew is installed
        if not check_command_exists('brew'):
            messages.info(request, "Installing Homebrew...")
            success, output = run_command('/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"')
            if not success:
                messages.error(request, f"Failed to install Homebrew: {output}")
                return JsonResponse({'success': False, 'message': 'Homebrew installation failed'})
        
        # Update Homebrew
        messages.info(request, "Updating Homebrew...")
        success, output = run_command("brew update")
        if not success:
            messages.warning(request, f"Homebrew update warning: {output}")
        
        # Install Jenkins LTS
        messages.info(request, "Installing Jenkins LTS...")
        success, output = run_command("brew install jenkins-lts")
        if not success:
            messages.error(request, f"Failed to install Jenkins: {output}")
            return JsonResponse({'success': False, 'message': 'Jenkins installation failed'})
        
        # Start Jenkins service
        messages.info(request, "Starting Jenkins service...")
        success, output = run_command("brew services start jenkins-lts")
        if not success:
            messages.warning(request, f"Failed to start Jenkins service: {output}")
        
        # Check status
        success, output = run_command("brew services list | grep jenkins-lts")
        
        messages.success(request, "Jenkins installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        
        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via Homebrew'})
        
    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def install_jenkins_docker(request):
    """Install Jenkins using Docker"""
    messages.info(request, "Starting Jenkins installation via Docker...")
    
    try:
        # Check if Docker is installed
        if not check_command_exists('docker'):
            messages.error(request, "Docker is not installed. Please install Docker Desktop first.")
            return JsonResponse({'success': False, 'message': 'Docker not found'})
        
        # Create Jenkins Docker setup
        jenkins_dir = os.path.expanduser("~/jenkins-docker")
        os.makedirs(jenkins_dir, exist_ok=True)
        
        # Create Dockerfile
        dockerfile_content = """FROM jenkins/jenkins:lts

USER root

RUN apt-get update && \\
    apt-get install -y python3 python3-pip && \\
    apt-get clean

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY casc.yaml /usr/share/jenkins/ref/casc.yaml

ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
"""
        
        with open(os.path.join(jenkins_dir, 'Dockerfile'), 'w') as f:
            f.write(dockerfile_content)
        
        # Create plugins.txt
        plugins_content = """configuration-as-code
git
workflow-aggregator
"""
        
        with open(os.path.join(jenkins_dir, 'plugins.txt'), 'w') as f:
            f.write(plugins_content)
        
        # Create casc.yaml
        casc_content = """jenkins:
  systemMessage: "Jenkins configured automatically by JCasC"
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: admin
          password: admin
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false
"""
        
        with open(os.path.join(jenkins_dir, 'casc.yaml'), 'w') as f:
            f.write(casc_content)
        
        # Create docker-compose.yml
        compose_content = """version: '3.8'

services:
  jenkins:
    build: .
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
      - CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml

volumes:
  jenkins_home:
"""
        
        with open(os.path.join(jenkins_dir, 'docker-compose.yml'), 'w') as f:
            f.write(compose_content)
        
        # Build and run Jenkins
        messages.info(request, "Building Jenkins Docker image...")
        success, output = run_command("docker compose build", cwd=jenkins_dir)
        if not success:
            messages.error(request, f"Failed to build Docker image: {output}")
            return JsonResponse({'success': False, 'message': 'Docker build failed'})
        
        messages.info(request, "Starting Jenkins container...")
        success, output = run_command("docker compose up -d", cwd=jenkins_dir)
        if not success:
            messages.error(request, f"Failed to start container: {output}")
            return JsonResponse({'success': False, 'message': 'Container startup failed'})
        
        messages.success(request, "Jenkins Docker installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        messages.info(request, "Login credentials: admin / admin")
        
        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via Docker'})
        
    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def check_jenkins_status(request):
    """Check Jenkins installation status"""
    status = {
        'homebrew_installed': check_command_exists('brew'),
        'docker_installed': check_command_exists('docker'),
        'jenkins_installed': check_command_exists('jenkins'),
        'jenkins_running': False
    }
    
    # Check if Jenkins is running on port 8080
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:8080', timeout=5)
        status['jenkins_running'] = True
    except:
        status['jenkins_running'] = False
    
    return JsonResponse(status)

def check_jenkins_windows_installed():
    """Check if Jenkins is installed on Windows"""
    try:
        # Check if Jenkins service exists
        result = subprocess.run(['sc', 'query', 'jenkins'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def install_jenkins_windows_msi(request):
    """Install Jenkins using MSI installer on Windows"""
    messages.info(request, "Starting Jenkins installation via MSI installer...")
    
    try:
        # Step 1: Check Java installation
        messages.info(request, "[1/6] Checking Java installation...")
        java_installed = check_java_windows()
        
        if not java_installed:
            messages.info(request, "[2/6] Installing OpenJDK 17...")
            success = install_java_windows()
            if not success:
                return JsonResponse({'success': False, 'message': 'Java installation failed'})
        else:
            messages.info(request, "Java already installed, skipping installation.")
        
        # Step 3: Download Jenkins installer
        messages.info(request, "[3/6] Downloading Jenkins installer...")
        jenkins_url = "https://get.jenkins.io/windows-stable/jenkins.msi"
        jenkins_installer = "jenkins.msi"
        
        success = download_file_windows(jenkins_url, jenkins_installer)
        if not success:
            return JsonResponse({'success': False, 'message': 'Failed to download Jenkins installer'})
        
        # Step 4: Install Jenkins
        messages.info(request, "[4/6] Installing Jenkins silently...")
        success, output = run_command(f'msiexec /i {jenkins_installer} /qn /norestart')
        if not success:
            messages.error(request, f"Failed to install Jenkins: {output}")
            return JsonResponse({'success': False, 'message': 'Jenkins installation failed'})
        
        # Clean up installer
        try:
            os.remove(jenkins_installer)
        except:
            pass
        
        # Step 5: Configure Jenkins service
        messages.info(request, "[5/6] Setting Jenkins service to start automatically...")
        run_command('sc config jenkins start= auto')
        
        # Step 6: Start Jenkins service
        messages.info(request, "[6/6] Starting Jenkins service...")
        success, output = run_command('sc start jenkins')
        if not success:
            messages.warning(request, f"Failed to start Jenkins service: {output}")
        
        # Verify installation
        messages.info(request, "Verifying Jenkins service status...")
        success, output = run_command('sc query jenkins')
        if success and "RUNNING" in output:
            messages.success(request, "Jenkins service is running successfully!")
        else:
            messages.warning(request, "Jenkins service is not running. Please check manually.")
        
        messages.success(request, "Jenkins MSI installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        messages.info(request, "Get initial admin password from Jenkins installation directory.")
        
        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via MSI installer'})
        
    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def install_jenkins_windows_chocolatey(request):
    """Install Jenkins using Chocolatey on Windows"""
    messages.info(request, "Starting Jenkins installation via Chocolatey...")
    
    try:
        # Check if Chocolatey is installed
        if not check_command_exists('choco'):
            messages.info(request, "[1/3] Installing Chocolatey...")
            success = install_chocolatey_windows()
            if not success:
                return JsonResponse({'success': False, 'message': 'Chocolatey installation failed'})
        
        # Install Java via Chocolatey if needed
        if not check_command_exists('java'):
            messages.info(request, "[2/3] Installing OpenJDK via Chocolatey...")
            success, output = run_command('choco install openjdk17 -y')
            if not success:
                messages.error(request, f"Failed to install Java: {output}")
                return JsonResponse({'success': False, 'message': 'Java installation failed'})
        
        # Install Jenkins via Chocolatey
        messages.info(request, "[3/3] Installing Jenkins via Chocolatey...")
        success, output = run_command('choco install jenkins -y')
        if not success:
            messages.error(request, f"Failed to install Jenkins: {output}")
            return JsonResponse({'success': False, 'message': 'Jenkins installation failed'})
        
        # Start Jenkins service
        messages.info(request, "Starting Jenkins service...")
        success, output = run_command('sc start jenkins')
        if not success:
            messages.warning(request, f"Failed to start Jenkins service: {output}")
        
        messages.success(request, "Jenkins Chocolatey installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        
        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via Chocolatey'})
        
    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def install_jenkins_windows_docker(request):
    """Install Jenkins using Docker on Windows"""
    messages.info(request, "Starting Jenkins installation via Docker on Windows...")
    
    try:
        # Install Docker if not present
        if not check_command_exists('docker'):
            messages.info(request, "[1/2] Installing Docker Desktop...")
            success = install_docker_windows()
            if not success:
                return JsonResponse({'success': False, 'message': 'Docker installation failed'})
        
        # Create Jenkins Docker setup
        jenkins_dir = os.path.expanduser("~/jenkins-docker")
        os.makedirs(jenkins_dir, exist_ok=True)
        
        messages.info(request, "[1/5] Creating Jenkins Docker environment...")
        
        # Create Dockerfile
        dockerfile_content = """FROM jenkins/jenkins:lts

USER root

RUN apt-get update && \\
    apt-get install -y python3 python3-pip && \\
    apt-get clean

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY casc.yaml /usr/share/jenkins/ref/casc.yaml

ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
"""
        
        with open(os.path.join(jenkins_dir, 'Dockerfile'), 'w') as f:
            f.write(dockerfile_content)
        
        messages.info(request, "[2/5] Writing Dockerfile...")
        
        # Create plugins.txt
        plugins_content = """configuration-as-code
git
workflow-aggregator
"""
        
        with open(os.path.join(jenkins_dir, 'plugins.txt'), 'w') as f:
            f.write(plugins_content)
        
        messages.info(request, "[3/5] Writing plugins.txt...")
        
        # Create casc.yaml
        casc_content = """jenkins:
  systemMessage: "Jenkins configured automatically by JCasC"
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: admin
          password: admin
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false
"""
        
        with open(os.path.join(jenkins_dir, 'casc.yaml'), 'w') as f:
            f.write(casc_content)
        
        messages.info(request, "[4/5] Writing casc.yaml...")
        
        # Create docker-compose.yml
        compose_content = """version: '3.8'

services:
  jenkins:
    build: .
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
      - CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml

volumes:
  jenkins_home:
"""
        
        with open(os.path.join(jenkins_dir, 'docker-compose.yml'), 'w') as f:
            f.write(compose_content)
        
        messages.info(request, "[5/5] Writing docker-compose.yml...")
        
        # Build and run Jenkins
        messages.info(request, "[1/2] Building Jenkins Docker image...")
        success, output = run_command("docker compose build", cwd=jenkins_dir)
        if not success:
            messages.error(request, f"Failed to build Docker image: {output}")
            return JsonResponse({'success': False, 'message': 'Docker build failed'})
        
        messages.info(request, "[2/2] Running Jenkins container...")
        success, output = run_command("docker compose up -d", cwd=jenkins_dir)
        if not success:
            messages.error(request, f"Failed to start container: {output}")
            return JsonResponse({'success': False, 'message': 'Container startup failed'})
        
        messages.success(request, "Jenkins Docker installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        messages.info(request, "Login credentials: admin / admin")
        
        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via Docker'})
        
    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def check_java_windows():
    """Check if Java is installed on Windows"""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        return "version" in result.stderr
    except FileNotFoundError:
        return False

def install_java_windows():
    """Install Java on Windows"""
    try:
        jdk_url = "https://github.com/adoptium/temurin17-binaries/releases/latest/download/OpenJDK17U-jdk_x64_windows_hotspot_17.0.8_7.msi"
        jdk_installer = "OpenJDK17.msi"
        
        if download_file_windows(jdk_url, jdk_installer):
            success, output = run_command(f'msiexec /i {jdk_installer} /qn /norestart')
            try:
                os.remove(jdk_installer)
            except:
                pass
            return success
        return False
    except:
        return False

def install_chocolatey_windows():
    """Install Chocolatey on Windows"""
    try:
        choco_install_cmd = 'powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(\'https://community.chocolatey.org/install.ps1\'))"'
        success, output = run_command(choco_install_cmd)
        return success
    except:
        return False

def install_docker_windows():
    """Install Docker Desktop on Windows"""
    try:
        # Try to install via winget
        success, output = run_command("winget install --id Docker.DockerDesktop -e --source winget")
        if success:
            # Launch Docker Desktop
            run_command(r'start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"')
            
            # Wait for Docker to initialize
            import time
            for _ in range(30):  # Wait up to 60 seconds
                if check_command_exists("docker"):
                    try:
                        subprocess.run("docker info", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return True
                    except subprocess.CalledProcessError:
                        pass
                time.sleep(2)
        return False
    except:
        return False

def download_file_windows(url, dest):
    """Download file on Windows"""
    try:
        urllib.request.urlretrieve(url, dest)
        return True
    except:
        return False

def check_jenkins_status_windows(request):
    """Check Jenkins installation status on Windows"""
    status = {
        'java_installed': check_java_windows(),
        'docker_installed': check_command_exists('docker'),
        'jenkins_installed': check_jenkins_windows_installed(),
        'choco_installed': check_command_exists('choco'),
        'jenkins_running': False,
        'jenkins_service_status': 'unknown'
    }
    
    # Check if Jenkins service is running
    try:
        success, output = run_command("sc query jenkins")
        if success and 'RUNNING' in output:
            status['jenkins_service_status'] = 'running'
            status['jenkins_running'] = True
        elif success:
            status['jenkins_service_status'] = 'stopped'
        else:
            status['jenkins_service_status'] = 'not_installed'
    except:
        status['jenkins_service_status'] = 'unknown'
    
    # Check if Jenkins is accessible on port 8080
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:8080', timeout=5)
        status['jenkins_running'] = True
    except:
        pass
    
    return JsonResponse(status)

def install_jenkins_ubuntu_package(request):
    """Install Jenkins using Ubuntu package manager"""
    messages.info(request, "Starting Jenkins installation via Ubuntu package manager...")
    
    try:
        # Step 0: Removing all old Jenkins keys and repo files
        messages.info(request, "[0/11] Removing all old Jenkins keys and repo files...")
        run_command("sudo apt-key del 5BA31D57EF5975CA || true")
        run_command("sudo rm -f /etc/apt/trusted.gpg.d/jenkins.gpg /etc/apt/trusted.gpg.d/jenkins-keyring.gpg || true")
        run_command("sudo gpg --no-default-keyring --keyring /etc/apt/trusted.gpg --delete-key 5BA31D57EF5975CA || true")
        run_command("sudo rm -f /etc/apt/sources.list.d/jenkins.list || true")

        # Step 1: Cleaning apt cache
        messages.info(request, "[1/11] Cleaning apt cache...")
        run_command("sudo apt clean")
        run_command("sudo rm -rf /var/lib/apt/lists/* /var/cache/apt/*")

        # Step 2: Updating system packages
        messages.info(request, "[2/11] Updating system packages...")
        success, output = run_command("sudo apt update -y")
        if not success:
            messages.warning(request, f"Update warning: {output}")
        
        success, output = run_command("sudo apt upgrade -y")
        if not success:
            messages.warning(request, f"Upgrade warning: {output}")

        # Step 3: Installing prerequisites
        messages.info(request, "[3/11] Installing prerequisites...")
        success, output = run_command("sudo apt install -y curl gnupg2 openjdk-17-jdk apt-transport-https ca-certificates software-properties-common")
        if not success:
            messages.error(request, f"Failed to install prerequisites: {output}")
            return JsonResponse({'success': False, 'message': 'Prerequisites installation failed'})

        # Step 4: Downloading and installing the latest Jenkins GPG key
        messages.info(request, "[4/11] Downloading and installing the latest Jenkins GPG key...")
        success, output = run_command("curl -fsSL https://pkg.jenkins.io/debian/jenkins.io-2023.key -o /tmp/jenkins-keyring.asc")
        if not success:
            messages.error(request, f"Failed to download Jenkins key: {output}")
            return JsonResponse({'success': False, 'message': 'Jenkins key download failed'})
        
        run_command("sudo gpg --dearmor -o /usr/share/keyrings/jenkins-keyring.gpg /tmp/jenkins-keyring.asc")
        run_command("sudo rm /tmp/jenkins-keyring.asc")

        # Step 5: Verifying Jenkins key fingerprint
        messages.info(request, "[5/11] Verifying Jenkins key fingerprint...")
        run_command("gpg --show-keys --with-fingerprint /usr/share/keyrings/jenkins-keyring.gpg")

        # Step 6: Creating new Jenkins repo file
        messages.info(request, "[6/11] Creating new Jenkins repo file...")
        success, output = run_command("echo 'deb [signed-by=/usr/share/keyrings/jenkins-keyring.gpg] https://pkg.jenkins.io/debian binary/' | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null")
        if not success:
            messages.error(request, f"Failed to create repo file: {output}")
            return JsonResponse({'success': False, 'message': 'Repository configuration failed'})

        # Step 7: Cleaning apt cache after repo addition
        messages.info(request, "[7/11] Cleaning apt cache after repo addition...")
        run_command("sudo rm -rf /var/lib/apt/lists/* /var/cache/apt/*")

        # Step 8: Updating package lists
        messages.info(request, "[8/11] Updating package lists after repo addition...")
        success, output = run_command("sudo apt update -y")
        if not success:
            messages.warning(request, f"Package list update warning: {output}")

        # Step 9: Installing Jenkins
        messages.info(request, "[9/11] Installing Jenkins...")
        success, output = run_command("sudo apt install -y jenkins")
        if not success:
            messages.error(request, f"Failed to install Jenkins: {output}")
            return JsonResponse({'success': False, 'message': 'Jenkins installation failed'})

        # Step 10: Starting Jenkins service
        messages.info(request, "[10/11] Starting Jenkins service...")
        success, output = run_command("sudo systemctl start jenkins")
        if not success:
            messages.warning(request, f"Failed to start Jenkins service: {output}")
        
        success, output = run_command("sudo systemctl enable jenkins")
        if not success:
            messages.warning(request, f"Failed to enable Jenkins service: {output}")

        # Step 11: Installation completed
        messages.success(request, "[11/11] Jenkins installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        messages.info(request, "Get initial admin password with: sudo cat /var/lib/jenkins/secrets/initialAdminPassword")

        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via Ubuntu package manager'})

    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def install_jenkins_ubuntu_docker(request):
    """Install Jenkins using Docker on Ubuntu"""
    messages.info(request, "Starting Jenkins installation via Docker on Ubuntu...")
    
    try:
        # Step 1: Check if Docker is installed
        messages.info(request, "[1/6] Checking Docker installation...")
        docker_installed = check_command_exists('docker')
        
        if not docker_installed:
            messages.info(request, "[2/6] Installing Docker Engine...")
            
            # Remove old Docker packages
            run_command("sudo apt-get remove -y docker docker-engine docker.io containerd runc")
            
            # Update package index
            success, output = run_command("sudo apt-get update")
            if not success:
                messages.warning(request, f"Update warning: {output}")
            
            # Install prerequisites
            success, output = run_command("sudo apt-get install -y ca-certificates curl gnupg lsb-release")
            if not success:
                messages.error(request, f"Failed to install prerequisites: {output}")
                return JsonResponse({'success': False, 'message': 'Prerequisites installation failed'})
            
            # Add Docker's official GPG key
            run_command("sudo mkdir -p /etc/apt/keyrings")
            success, output = run_command("curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg")
            if not success:
                messages.error(request, f"Failed to add Docker GPG key: {output}")
                return JsonResponse({'success': False, 'message': 'Docker GPG key installation failed'})
            
            # Set up Docker repository
            success, output = run_command('echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null')
            if not success:
                messages.error(request, f"Failed to set up Docker repository: {output}")
                return JsonResponse({'success': False, 'message': 'Docker repository setup failed'})
            
            # Update package index again
            success, output = run_command("sudo apt-get update")
            if not success:
                messages.warning(request, f"Package update warning: {output}")
            
            # Install Docker Engine
            success, output = run_command("sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")
            if not success:
                messages.error(request, f"Failed to install Docker: {output}")
                return JsonResponse({'success': False, 'message': 'Docker installation failed'})
            
            # Add current user to docker group
            run_command("sudo usermod -aG docker $USER")
            
            # Start and enable Docker service
            run_command("sudo systemctl start docker")
            run_command("sudo systemctl enable docker")
            
            messages.info(request, "Docker Engine installed successfully!")
        else:
            messages.info(request, "Docker already installed, skipping installation.")
        
        # Step 3: Create Jenkins Docker setup
        messages.info(request, "[3/6] Creating Jenkins Docker environment...")
        jenkins_dir = os.path.expanduser("~/jenkins-docker")
        os.makedirs(jenkins_dir, exist_ok=True)
        
        # Create Dockerfile
        dockerfile_content = """FROM jenkins/jenkins:lts

USER root

RUN apt-get update && \\
    apt-get install -y python3 python3-pip && \\
    apt-get clean

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

COPY casc.yaml /usr/share/jenkins/ref/casc.yaml

ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

USER jenkins
"""
        
        with open(os.path.join(jenkins_dir, 'Dockerfile'), 'w') as f:
            f.write(dockerfile_content)
        
        # Create plugins.txt
        plugins_content = """configuration-as-code:1757.v71c1572b_65b_b
git:5.2.1
workflow-aggregator:596.v8c21c963d92d
blueocean:1.27.11
docker-workflow:580.vc0c340686b_54
"""
        
        with open(os.path.join(jenkins_dir, 'plugins.txt'), 'w') as f:
            f.write(plugins_content)
        
        # Create casc.yaml
        casc_content = """jenkins:
  systemMessage: "Jenkins configured automatically by JCasC for Ubuntu Docker"
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: admin
          password: admin
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false

unclassified:
  location:
    url: http://localhost:8080/
"""
        
        with open(os.path.join(jenkins_dir, 'casc.yaml'), 'w') as f:
            f.write(casc_content)
        
        # Create docker-compose.yml
        compose_content = """version: '3.8'

services:
  jenkins:
    build: .
    container_name: jenkins
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "50000:50000"
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false
      - CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc.yaml
    user: root

volumes:
  jenkins_home:
    driver: local
"""
        
        with open(os.path.join(jenkins_dir, 'docker-compose.yml'), 'w') as f:
            f.write(compose_content)
        
        # Step 4: Build and run Jenkins
        messages.info(request, "[4/6] Building Jenkins Docker image...")
        success, output = run_command("sudo docker compose build", cwd=jenkins_dir)
        if not success:
            messages.error(request, f"Failed to build Docker image: {output}")
            return JsonResponse({'success': False, 'message': 'Docker build failed'})
        
        messages.info(request, "[5/6] Starting Jenkins container...")
        success, output = run_command("sudo docker compose up -d", cwd=jenkins_dir)
        if not success:
            messages.error(request, f"Failed to start container: {output}")
            return JsonResponse({'success': False, 'message': 'Container startup failed'})
        
        # Step 5: Wait for Jenkins to be ready
        messages.info(request, "[6/6] Waiting for Jenkins to be ready...")
        
        # Wait for Jenkins to start
        import time
        for i in range(30):  # Wait up to 60 seconds
            try:
                import urllib.request
                urllib.request.urlopen('http://localhost:8080', timeout=5)
                break
            except:
                time.sleep(2)
        
        messages.success(request, "Jenkins Docker installation completed successfully!")
        messages.info(request, "Jenkins is accessible at http://localhost:8080")
        messages.info(request, "Login credentials: admin / admin")
        messages.info(request, f"Docker setup created in: {jenkins_dir}")
        
        return JsonResponse({'success': True, 'message': 'Jenkins installed successfully via Docker on Ubuntu'})
        
    except Exception as e:
        messages.error(request, f"Installation error: {str(e)}")
        return JsonResponse({'success': False, 'message': str(e)})

def check_jenkins_status_linux(request):
    """Check Jenkins installation status on Linux"""
    status = {
        'java_installed': check_command_exists('java'),
        'docker_installed': check_command_exists('docker'),
        'jenkins_installed': check_command_exists('jenkins'),
        'jenkins_running': False,
        'jenkins_service_status': 'unknown'
    }
    
    # Check if Jenkins service is running
    try:
        success, output = run_command("systemctl is-active jenkins")
        if success and 'active' in output:
            status['jenkins_service_status'] = 'active'
        else:
            status['jenkins_service_status'] = 'inactive'
    except:
        status['jenkins_service_status'] = 'unknown'
    
    # Check if Jenkins is running on port 8080
    try:
        import urllib.request
        urllib.request.urlopen('http://localhost:8080', timeout=5)
        status['jenkins_running'] = True
    except:
        status['jenkins_running'] = False
    
    return JsonResponse(status)
