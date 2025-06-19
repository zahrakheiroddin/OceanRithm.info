import os
import json
import shutil
import hashlib
import subprocess
import requests
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.core.exceptions import TooManyFilesSent
from .forms import (
     GitHubConfigForm, NewRepositoryForm, 
    ExistingRepositoryForm, FileUploadForm, FolderUploadForm
)
from .models import GitHubConfig, Repository



@login_required
def dashboard_view(request):
    try:
        github_config = GitHubConfig.objects.get(user=request.user)
        has_github_config = True
    except GitHubConfig.DoesNotExist:
        has_github_config = False
        
    repositories = Repository.objects.filter(user=request.user)
    
    return render(request, 'repository/dashboard.html', {
        'has_github_config': has_github_config,
        'repositories': repositories
    })


@login_required

@login_required
def delete_repository_view(request, repo_id):
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    if request.method == "POST":
        repo_path = repository.local_path
        repository.delete()
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        messages.success(request, f"Repository '{repository.name}' deleted successfully.")
        return redirect('githubaction_dashboard')

def github_config_view(request):
    try:
        github_config = GitHubConfig.objects.get(user=request.user)
    except GitHubConfig.DoesNotExist:
        github_config = None
    
    if request.method == 'POST':
        form = GitHubConfigForm(request.POST, instance=github_config)
        if form.is_valid():
            config = form.save(commit=False)
            config.user = request.user
            config.noreply_email = f"{config.github_username}@users.noreply.github.com"
            config.save()
            messages.success(request, "GitHub configuration saved successfully!")
            return redirect('githubaction_dashboard')
    else:
        form = GitHubConfigForm(instance=github_config)
        
    return render(request, 'repository/github_config.html', {'form': form})


@login_required
def repository_choice_view(request):
    return render(request, 'repository/repository_choice.html')


@login_required
def new_repository_view(request):
    if request.method == 'POST':
        form = NewRepositoryForm(request.POST)
        if form.is_valid():
            # Get GitHub config
            try:
                github_config = GitHubConfig.objects.get(user=request.user)
            except GitHubConfig.DoesNotExist:
                messages.warning(request, "Please configure your GitHub settings first.")
                return redirect('github_config')
            
            # Create repository via GitHub API
            repo_name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            is_private = form.cleaned_data['is_private']
            
            headers = {"Authorization": f"token {github_config.github_token}"}
            data = {
                "name": repo_name,
                "description": description,
                "private": is_private,
                "auto_init": False
            }
            
            response = requests.post(
                "https://api.github.com/user/repos", 
                json=data, 
                headers=headers
            )
            
            if response.status_code != 201:
                error_msg = f"Repository creation failed: {response.status_code} {response.text}"
                error_details = {}
                
                try:
                    error_data = response.json()
                    if response.status_code == 422 and "errors" in error_data:
                        for err in error_data["errors"]:
                            if err.get("field") == "name" and "already exists" in err.get("message", ""):
                                messages.error(request, f"A repository named '{repo_name}' already exists on your GitHub account.")
                                
                                # Check if the repo exists in our database
                                existing_repos = Repository.objects.filter(
                                    user=request.user, 
                                    name=repo_name
                                )
                                
                                # Context for the template
                                return render(request, 'repository/new_repository.html', {
                                    'form': form,
                                    'repo_name': repo_name,
                                    'name_exists': True,
                                    'repo_in_db': existing_repos.exists(),
                                    'existing_repo_id': existing_repos.first().id if existing_repos.exists() else None
                                })
                except:
                    pass
                
                messages.error(request, error_msg)
                return render(request, 'repository/new_repository.html', {
                    'form': form,
                    'error': error_msg
                })
                
            # Create local repository
            repo_dir = os.path.join(settings.MEDIA_ROOT, request.user.username, repo_name)
            os.makedirs(repo_dir, exist_ok=True)
            
            # Initialize git repository
            repo_url = f"https://{github_config.github_token}@github.com/{github_config.github_username}/{repo_name}.git"
            
            subprocess.run(["git", "init"], cwd=repo_dir)
            subprocess.run(["git", "config", "user.name", github_config.github_username], cwd=repo_dir)
            subprocess.run(["git", "config", "user.email", github_config.noreply_email], cwd=repo_dir)
            subprocess.run(["git", "checkout", "-b", "main"], cwd=repo_dir)
            
            # Create GitHub Actions workflow
            workflows_dir = os.path.join(repo_dir, ".github", "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            
            with open(os.path.join(workflows_dir, "main.yml"), "w") as wf:
                wf.write("""
                        name: AutoRun on Upload

                        on:
                        push:
                        branches: [main]

                        jobs:
                        build:
                        runs-on: ubuntu-latest
                        steps:
                            - uses: actions/checkout@v3
                            - name: Show uploaded files
                            run: ls -la
                            - name: Say Hello
                            run: echo "🚀 GitHub Action triggered successfully!"
                        """.strip())
            
            # Create README.md
            with open(os.path.join(repo_dir, "README.md"), "w") as f:
                f.write(f"# {repo_name}\n{description}")
            
            # Initial commit and push
            subprocess.run(["git", "add", "."], cwd=repo_dir)
            subprocess.run(["git", "commit", "-m", "Initial commit with GitHub Actions"], cwd=repo_dir)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_dir)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_dir)
            
            # Save repository to database
            repository = form.save(commit=False)
            repository.user = request.user
            repository.url = f"https://github.com/{github_config.github_username}/{repo_name}"
            repository.local_path = repo_dir
            repository.save()
            
            messages.success(request, f"Repository '{repo_name}' created successfully!")
            return redirect('repository_detail', repo_id=repository.id)
    else:
        form = NewRepositoryForm()
        
    return render(request, 'repository/new_repository.html', {'form': form})


@login_required
def existing_repository_view(request):
    error_message = None
    repo_exists_on_github = False
    github_repo_info = None
    
    if request.method == 'POST':
        form = ExistingRepositoryForm(request.POST)
        if form.is_valid():
            # Get GitHub config
            try:
                github_config = GitHubConfig.objects.get(user=request.user)
            except GitHubConfig.DoesNotExist:
                messages.warning(request, "Please configure your GitHub settings first.")
                return redirect('github_config')
            
            repo_name = form.cleaned_data['name']
            
            # Check if repository exists in our database
            existing_repo = Repository.objects.filter(user=request.user, name=repo_name).first()
            if existing_repo:
                messages.info(request, f"Repository '{repo_name}' is already connected.")
                return redirect('repository_detail', repo_id=existing_repo.id)
            
            # Check if repository exists on GitHub
            headers = {"Authorization": f"token {github_config.github_token}"}
            response = requests.get(
                f"https://api.github.com/repos/{github_config.github_username}/{repo_name}", 
                headers=headers
            )
            
            if response.status_code != 200:
                error_message = f"Repository '{repo_name}' not found on GitHub. Please check the name and try again."
                messages.error(request, error_message)
                return render(request, 'repository/existing_repository.html', {
                    'form': form,
                    'error': error_message
                })
            
            # Repository exists on GitHub, get info
            repo_exists_on_github = True
            github_repo_info = response.json()
            
            # Create local repository directory
            repo_dir = os.path.join(settings.MEDIA_ROOT, request.user.username, repo_name)
            os.makedirs(repo_dir, exist_ok=True)
            
            # Initialize git repository and connect to remote
            repo_url = f"https://{github_config.github_token}@github.com/{github_config.github_username}/{repo_name}.git"
            
            try:
                # Initialize git and add remote
                subprocess.run(["git", "init"], cwd=repo_dir, check=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_dir, check=True)
                
                # Try to fetch and checkout
                try:
                    subprocess.run(["git", "fetch"], cwd=repo_dir, check=True)
                    
                    # Determine default branch (usually main or master)
                    default_branch = github_repo_info.get('default_branch', 'main')
                    
                    try:
                        subprocess.run(["git", "checkout", default_branch], cwd=repo_dir, check=True)
                    except subprocess.CalledProcessError:
                        # If main branch checkout fails, try to create it
                        subprocess.run(["git", "checkout", "-b", default_branch], cwd=repo_dir, check=True)
                        # For empty repositories, create a basic README
                        with open(os.path.join(repo_dir, "README.md"), "w") as f:
                            f.write(f"# {repo_name}\n{github_repo_info.get('description', '')}")
                        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
                        subprocess.run(["git", "commit", "-m", "Initial README"], cwd=repo_dir, check=True)
                        subprocess.run(["git", "push", "-u", "origin", default_branch], cwd=repo_dir, check=True)
                    
                except subprocess.CalledProcessError:
                    error_message = "Failed to fetch from repository. This may be an empty repository."
                    # Continue anyway - we'll connect to the empty repository
                    messages.warning(request, error_message)
                
                # Save repository to database regardless of git operations
                repository = Repository(
                    user=request.user,
                    name=repo_name,
                    description=github_repo_info.get('description', ''),
                    is_private=github_repo_info.get('private', False),
                    url=github_repo_info.get('html_url', f"https://github.com/{github_config.github_username}/{repo_name}"),
                    local_path=repo_dir
                )
                repository.save()
                
                messages.success(request, f"Successfully connected to repository '{repo_name}'")
                return redirect('repository_detail', repo_id=repository.id)
                
            except subprocess.CalledProcessError as e:
                error_message = f"Error connecting to repository: {str(e)}"
                messages.error(request, error_message)
                
                # Clean up failed attempt
                try:
                    shutil.rmtree(repo_dir)
                except:
                    pass
                    
                return render(request, 'repository/existing_repository.html', {
                    'form': form,
                    'error': error_message,
                    'repo_exists_on_github': repo_exists_on_github,
                    'github_repo_info': github_repo_info
                })
    else:
        form = ExistingRepositoryForm()
        
    return render(request, 'repository/existing_repository.html', {
        'form': form,
        'error': error_message
    })


@login_required
def repository_detail_view(request, repo_id):
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    
    # Forward to the browse view with empty path (root directory)
    return repository_browse_view(request, repo_id, '')


@login_required
def repository_browse_view(request, repo_id, path=''):
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    file_form = FileUploadForm()
    folder_form = FolderUploadForm()
    
    # Normalize the path for security
    current_path = os.path.normpath(path).lstrip('/')
    full_path = os.path.join(repository.local_path, current_path)
    
    # Process file uploads
    if request.method == 'POST':
        try:
            # Add debug info about the POST request
            post_data_keys = list(request.POST.keys())
            files_data_keys = list(request.FILES.keys())
            has_folder_data = 'folder' in request.FILES
            has_multiple_upload = 'multiple_upload' in request.POST
            
            # Log this information as messages for debugging
            messages.info(request, f"POST keys: {post_data_keys}")
            messages.info(request, f"FILES keys: {files_data_keys}")
            messages.info(request, f"Has folder data: {has_folder_data}")
            messages.info(request, f"Has multiple_upload: {has_multiple_upload}")
            
            if 'file' in request.FILES:
                file_form = FileUploadForm(request.POST, request.FILES)
                if file_form.is_valid():
                    uploaded_file = request.FILES['file']
                    
                    # Determine the target path
                    if current_path:
                        file_path = os.path.join(repository.local_path, current_path, uploaded_file.name)
                        target_redirect = f"repository_browse"
                        redirect_args = {"repo_id": repository.id, "path": current_path}
 
                    else:
                        file_path = os.path.join(repository.local_path, uploaded_file.name)
                        target_redirect = f"repository_detail"
                        redirect_args = {"repo_id": repository.id}

                    
                    # Save the file
                    with open(file_path, 'wb+') as destination:
                        for chunk in uploaded_file.chunks():
                            destination.write(chunk)
                            
                    # Git operations
                    subprocess.run(["git", "add", "."], cwd=repository.local_path)
                    subprocess.run(["git", "commit", "-m", f"Upload: {uploaded_file.name}"], cwd=repository.local_path)
                    subprocess.run(["git", "push", "origin", "main"], cwd=repository.local_path)
                    
                    messages.success(request, f"Successfully uploaded file '{uploaded_file.name}'")
                    
                    # Stay in the current directory after upload
                    if current_path:
                       
                        return redirect('repository_browse', repo_id=repository.id, path=current_path)
                    else:
                    
                        return redirect('repository_browse_root', repo_id=repository.id)
                
            elif 'folder' in request.FILES or 'multiple_upload' in request.POST:
                # Debug info for folder uploads
                folder_form = FolderUploadForm(request.POST, request.FILES)
                
                # If multiple_upload button was clicked but no folder field in request.FILES
                if 'multiple_upload' in request.POST and not request.FILES:
                    messages.error(request, "No files were selected for upload. Please select a folder.")
                    return redirect('repository_browse', repo_id=repository.id, path=current_path) if current_path else redirect('repository_browse_root', repo_id=repository.id)
                
                # Get all files from the request
                files = []
                for key in request.FILES:
                    if key == 'folder' or key.startswith('folder['):
                        files.extend(request.FILES.getlist(key))
                
                if not files:
                    messages.error(request, "No files were found in the selected folder.")
                    return redirect('repository_browse', repo_id=repository.id, path=current_path) if current_path else redirect('repository_browse_root', repo_id=repository.id)
                    
                uploaded_files = []
                
                for f in files:
                    if f and f.name:
                        # Determine the target path, preserving folder structure
                        file_path = os.path.join(repository.local_path, current_path, f.name) if current_path else os.path.join(repository.local_path, f.name)
                        
                        # Ensure directories exist
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        
                        with open(file_path, 'wb+') as destination:
                            for chunk in f.chunks():
                                destination.write(chunk)
                                
                        uploaded_files.append(f.name)
                
                # Git operations if files were uploaded
                if uploaded_files:
                    subprocess.run(["git", "add", "."], cwd=repository.local_path)
                    commit_msg = "Upload: " + ", ".join(uploaded_files[:5])
                    if len(uploaded_files) > 5:
                        commit_msg += f" and {len(uploaded_files) - 5} more files"
                    subprocess.run(["git", "commit", "-m", commit_msg], cwd=repository.local_path)
                    subprocess.run(["git", "push", "origin", "main"], cwd=repository.local_path)
                
                messages.success(request, f"Successfully uploaded {len(uploaded_files)} files.")
                
                # Stay in the current directory after upload
                if current_path:
                  
                    return redirect('repository_browse', repo_id=repository.id, path=current_path)
                else:
              
                    return redirect('repository_browse_root', repo_id=repository.id)
        except TooManyFilesSent as e:
            messages.error(request, f"Too many files sent: {str(e)}")
            return redirect('repository_browse', repo_id=repository.id, path=current_path) if current_path else redirect('repository_browse_root', repo_id=repository.id)
    
    # List files and directories
    files = []
    directories = []
    breadcrumbs = []
    error = None
    
    # Generate breadcrumbs
    if current_path:
        parts = current_path.split('/')
        breadcrumbs = [{'name': 'Root', 'path': ''}]
        for i, part in enumerate(parts):
            breadcrumbs.append({
                'name': part,
                'path': '/'.join(parts[:i+1])
            })
    
    # List the contents of the directory
    try:
        for item in os.listdir(full_path):
            if item == '.git':
                continue
                
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                directories.append({
                    'name': item,
                    'path': os.path.join(current_path, item) if current_path else item
                })
            else:
                files.append({
                    'name': item,
                    'path': os.path.join(current_path, item) if current_path else item,
                    'size': os.path.getsize(item_path),
                    'type': os.path.splitext(item)[1][1:].lower() or 'unknown'
                })
    except Exception as e:
        error = str(e)
        messages.error(request, f"Error accessing directory: {error}")
    
    return render(request, 'repository/repository_detail.html', {
        'repository': repository,
        'file_form': file_form,
        'folder_form': folder_form,
        'files': files,
        'directories': directories,
        'current_path': current_path,
        'breadcrumbs': breadcrumbs,
        'error': error
    }) 