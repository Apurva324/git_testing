import subprocess
import os
import sys
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

# Initialize Groq model
model = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API")
)


def get_changed_files():
    """Get all changed, new, or deleted files in the repo"""
    try:
        result = subprocess.check_output(
            ["git", "status", "--short"],
            stderr=subprocess.STDOUT
        )
        lines = result.decode("utf-8", errors="ignore").strip().split("\n")
        files = []
        for line in lines:
            if line.strip():
                status = line[:2].strip()
                filename = line[3:].strip()
                files.append((status, filename))
        return files
    except Exception as e:
        print("Error reading git status:", e)
        return []


def get_git_diff():
    """Get staged git diff"""
    try:
        diff = subprocess.check_output(
            ["git", "diff", "--cached"],
            stderr=subprocess.STDOUT
        )
        return diff.decode("utf-8", errors="ignore").strip()
    except Exception as e:
        print("Error getting git diff:", e)
        return ""


def generate_commit_message(diff):
    """Generate commit message using Groq LLM"""
    if not diff:
        return "No changes staged."

    prompt = f"""
You are a senior software engineer generating high-quality git commit messages.

Your task:
Analyze the provided git diff and produce a precise, meaningful commit message.

Follow these STRICT rules:

1. Use Conventional Commits format:
   type(scope): short summary

2. Allowed types:
   feat, fix, docs, style, refactor, test, chore, perf, build, ci

3. Summary line:
   - Max 72 characters
   - Use imperative mood (e.g., "add", "fix", not "added", "fixed")
   - Be specific, not generic

4. Body:
   - Add bullet points ONLY if necessary
   - Explain WHAT changed and WHY (not how)
   - Focus on impact

5. Scope:
   - Infer scope from file paths or feature (e.g., auth, ui, api, db)

6. If change is small:
   - Return ONLY one-line commit

7. DO NOT:
   - Add explanations outside commit message
   - Add quotes, markdown, or extra text

8. Output must be clean and ready to paste into git

Git Diff:
{diff[:4000]}
"""
    if len(diff) > 4000:
        print("Large diff detected — only first 4000 chars sent to AI.\n")

    response = model.invoke(prompt)
    return response.content.strip()


def stage_files(exclude_files):
    """Stage all files except the excluded ones"""
    try:
        # Reset staging area first
        subprocess.run(["git", "reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Stage everything
        subprocess.run(["git", "add", "."], stderr=subprocess.DEVNULL)

        # Unstage excluded files
        for filename in exclude_files:
            subprocess.run(["git", "restore", "--staged", filename], stderr=subprocess.DEVNULL)

        # Count staged files
        result = subprocess.check_output(["git", "diff", "--cached", "--name-only"])
        staged = result.decode("utf-8").strip().split("\n")
        return len([f for f in staged if f])

    except Exception as e:
        print("Error staging files:", e)
        return 0


def git_push():
    """Push to remote"""
    try:
        result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Pushed to GitHub successfully!")
        else:
            print("Push failed:\n", result.stderr)
    except Exception as e:
        print(" Error during push:", e)


def git_commit(message):
    """Commit staged changes"""
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Committed successfully!")
            return True
        else:
            print("Commit failed:\n", result.stderr)
            return False
    except Exception as e:
        print(" Error during commit:", e)
        return False


def push_command():
    """Main push flow"""

    print("\n Scanning for changed files...\n")
    changed_files = get_changed_files()

    if not changed_files:
        print("No changes found in your repo.")
        return

    # Show changed files
    status_labels = {
        "M":  "modified",
        "A":  "added",
        "D":  "deleted",
        "??": "untracked",
        "R":  "renamed",
    }

    print("Files that will be pushed:")
    print("-" * 40)
    for i, (status, filename) in enumerate(changed_files, 1):
        label = status_labels.get(status, status)
        print(f"  {i}. [{label}] {filename}")
    print("-" * 40)

    # Ask which files to exclude
    print("\nWhich files do you want to EXCLUDE? (type filenames separated by commas, or press Enter to include all)")
    exclude_input = input("Exclude: ").strip()

    exclude_files = []
    if exclude_input:
        exclude_files = [f.strip() for f in exclude_input.split(",")]
        print(f"\n Excluding: {', '.join(exclude_files)}")

    # Stage files
    print("\n Staging files...")
    staged_count = stage_files(exclude_files)

    if staged_count == 0:
        print("No files staged after exclusions.")
        return

    print(f" {staged_count} file(s) staged.\n")

    # Generate commit message
    print(" Generating commit message with AI...\n")
    diff = get_git_diff()
    message = generate_commit_message(diff)

    print(" Suggested Commit Message:")
    print("-" * 60)
    print(message)
    print("-" * 60)

    # Ask user to confirm or edit
    print("\n[y] Commit & Push  [e] Edit message  [n] Cancel")
    choice = input("Choice: ").strip().lower()

    if choice == "e":
        message = input("Enter your commit message: ").strip()
        if not message:
            print(" Empty message. Cancelled.")
            return
        choice = "y"

    if choice == "y":
        success = git_commit(message)
        if success:
            print("\n Pushing to GitHub...")
            git_push()
    else:
        print(" Cancelled.")
        subprocess.run(["git", "reset"], stdout=subprocess.DEVNULL)


def main():
    if len(sys.argv) < 2:
        print("Usage: ai_git push")
        return

    command = sys.argv[1].lower()

    if command == "push":
        push_command()
    else:
        print(f" Unknown command: '{command}'")
        print("Available commands: push")


if __name__ == "__main__":
    main()