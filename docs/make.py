import subprocess
import pathlib
import shutil
import json

def get_git_tags_sorted():
    """
    Retrieves and sorts Git tags from newest to oldest based on their creation date.

    Returns:
        A list of Git tag strings, sorted from newest to oldest, or None if an error occurs.
    """
    try:
        process = subprocess.Popen(
            ["git", "for-each-ref", "--sort=-creatordate", "--format=%(refname:short)", "refs/tags"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()

        if process.returncode == 0:
            tags = stdout.strip().split("\n")
            return [tag for tag in tags if tag]
        else:
            print(f"Error retrieving Git tags: {stderr}")
            return None

    except FileNotFoundError:
        print("Git command not found. Make sure Git is installed and in your PATH.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def checkout_tag(tag):
    """Checks out a given Git tag."""
    try:
        subprocess.run(["git", "checkout", tag, "zakat"], check=True)
        print(f"Checked out tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking out tag {tag}: {e}")

def get_current_branch():
    """Gets the currently checked-out branch."""
    try:
        process = subprocess.Popen(["git", "branch", "--show-current"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            return stdout.strip()
        else:
            print(f"Error getting current branch: {stderr}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def checkout_branch(branch):
    """Checks out a given branch."""
    try:
        subprocess.run(["git", "checkout", branch], check=True)
        print(f"Checked out branch: {branch}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking out branch {branch}: {e}")

def generate_docs(tag, output_dir):
    """Generates documentation for the given tag using pdoc."""
    try:
        git_describe_process = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit code
        )
        git_describe = git_describe_process.stdout.strip() or "unknown"

        # Construct the footer text
        footer_text = f"v{git_describe}"

        output_path = pathlib.Path(output_dir) / tag
        subprocess.run([
            'pdoc',
            '--footer-text',
            footer_text,
            '--logo',
            'https://raw.githubusercontent.com/vzool/zakat/main/images/logo.jpg',
            '-t',
            './docs/template',
            '-o',
            f'./{output_path}',
            "./zakat",
        ], check=True)
        print(f"Documentation generated for tag {tag} in {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating documentation for tag {tag}: {e}")

def save_tags_to_json(tags, filename="docs/tags.json"):
    """Saves the list of tags to a JSON file, creating the directory if needed."""
    try:
        file_path = pathlib.Path(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if they don't exist
        with open(file_path, "w") as f:
            json.dump(tags, f, indent=4)
        print(f"Tags saved to {filename}")
    except Exception as e:
        print(f"Error saving tags to JSON: {e}")

if __name__ == "__main__":
    tags = get_git_tags_sorted()
    tags = ['main'] + tags
    if tags:
        original_branch = get_current_branch()
        output_directory = "docs/api" # Directory where documentation will be generated
        # Delete existing docs directory if it exists
        if pathlib.Path(output_directory).exists():
            try:
                shutil.rmtree(output_directory)
                print(f"Deleted existing {output_directory} directory.")
            except Exception as e:
                print(f"Error deleting existing {output_directory} directory: {e}")
        pathlib.Path(output_directory).mkdir(parents=True, exist_ok=True) #create docs directory if it does not exist.

        save_tags_to_json(tags) #save tags to json file.
        for tag in tags:
            checkout_tag(tag)
            generate_docs(tag, output_directory)

        if original_branch:
            checkout_tag(original_branch)
        else:
            print("Could not return to original branch, as the original branch could not be determined.")
    else:
        print("No tags found.")
               