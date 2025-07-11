from flask import current_app
import os
import zipfile
import subprocess
import shutil



def limit_object_depth(obj, max_depth, current_depth=0):
    """
    Recursively limits the depth of nested objects to prevent deep nesting attacks
    """
    if current_depth > max_depth:
        return None
    
    if isinstance(obj, list) or not isinstance(obj, dict) or obj is None:
        return obj
    
    result = {}
    for key in obj:
        val = limit_object_depth(obj[key], max_depth, current_depth + 1)
        if val is not None:
            result[key] = val
    
    if len(result) == 0:
        return None
    return result

def allowed_file(filename):
    if not filename or filename == '':
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check if file has an extension
    if '.' not in filename:
        return False
    
    # Get the extension (only the last one)
    extension = filename.rsplit('.', 1)[1].lower().strip()
    
    # Check if extension is allowed
    if extension not in current_app.config['ALLOWED_EXTENSIONS']:
        return False
    
    # Additional security: check filename length
    if len(filename) > 255:
        return False
    
    return True


def process_git_repo(zip_path, extract_base_dir):
    """
    Extracts ZIP file and runs git submodule update --init --recursive
    Expects .git directory to be in the main directory after extraction
    """
    extract_dir = None
    
    try:
        # Create unique extraction directory
        zip_name = os.path.splitext(os.path.basename(zip_path))[0]
        extract_dir = os.path.join(extract_base_dir, f"extracted_{zip_name}")
        
        # Extract ZIP file with security checks
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Security check: prevent zip bomb and path traversal
            for member in zip_ref.namelist():
                if member.startswith('/') or '..' in member:
                    return {"success": False, "error": "Malicious ZIP file detected - path traversal attempt"}
                
                # Check for zip bomb (too many files or deeply nested)
                if len(zip_ref.namelist()) > 150:  # Max 150 files
                    return {"success": False, "error": "ZIP file contains too many files"}
                
                if member.count('/') > 6:  # Max 6 levels deep
                    return {"success": False, "error": "ZIP file has excessive directory nesting"}
            
            for member in zip_ref.infolist():
                extraction_path = os.path.join(extract_dir, member.filename)
                
                normalized_path = os.path.normpath(extraction_path)
                
                if not normalized_path.startswith(os.path.normpath(extract_dir + os.sep)):
                    return {"success": False, "error": "Malicious ZIP file detected - symlink or path escape attempt"}
                
                zip_ref.extract(member, extract_dir)
                
                if os.path.islink(extraction_path):
                    os.unlink(extraction_path)
                    return {"success": False, "error": "Malicious ZIP file detected - symlink creation attempt"}
        
        # Check if .git directory exists in the extracted directory 
        git_dir = None

        # First check if .git is directly in extract_dir
        if os.path.exists(os.path.join(extract_dir, '.git')):
            git_dir = extract_dir
        else:
            # Search in subdirectories up to 2 levels deep
            for root, dirs, files in os.walk(extract_dir):
                depth = root[len(extract_dir):].count(os.sep)
                if depth <= 2 and '.git' in dirs:
                    git_dir = root
                    break

        if not git_dir:
            shutil.rmtree(extract_dir)
            return {"success": False, "error": "No Git repository found. ZIP must contain .git directory in root or main folder."}

        # Check if .git/config contains fsmonitor
        git_config_path = os.path.join(git_dir, '.git', 'config')
        if os.path.exists(git_config_path):
            with open(git_config_path, 'r') as config_file:
                config_content = config_file.read()
                if 'fsmonitor' in config_content:
                    shutil.rmtree(extract_dir)
                    return {"success": False, "error": "Malicious Git repository detected - fsmonitor found in .git/config"}

        # Run git submodule update --init --recursive
        result = run_git_submodule_update(git_dir)

        # Clean up extracted files after processing
        shutil.rmtree(extract_dir)

        return result
        
    except zipfile.BadZipFile:
        return {"success": False, "error": "Invalid or corrupted ZIP file"}
    except Exception as e:
        # Clean up on error
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        return {"success": False, "error": f"Processing failed: {str(e)}"}


def run_git_submodule_update(git_dir):
    """
    Runs git submodule update --init --recursive in the specified directory
    """
    try:
        result = subprocess.run(
            ['git', 'submodule', 'update', '--init', '--recursive'],
            cwd=git_dir,
            capture_output=True,
            text=True,
            timeout=10  
        )
        
        if result.returncode == 0:
            # Success
            output_msg = "Git submodules updated successfully!"
            if result.stdout.strip():
                output_msg += f"\nOutput: {result.stdout.strip()}"
            return {"success": True, "message": output_msg}
        else:
            error_msg = "Git submodule update failed"
            if result.stderr.strip():
                error_msg += f": {result.stderr.strip()}"
            return {"success": False, "error": error_msg}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Git command timed out (>10 seconds)"}
    except FileNotFoundError:
        return {"success": False, "error": "Git is not installed on the server"}
    except Exception as e:
        return {"success": False, "error": f"Git command execution failed: {str(e)}"}
