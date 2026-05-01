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


# ─────────────────────────────────────────────
# GIT HELPERS
# ─────────────────────────────────────────────

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


def stage_files(exclude_files):
    """Stage all files except excluded ones"""
    try:
        subprocess.run(["git", "reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "add", "."], stderr=subprocess.DEVNULL)

        for filename in exclude_files:
            subprocess.run(["git", "restore", "--staged", filename], stderr=subprocess.DEVNULL)

        result = subprocess.check_output(["git", "diff", "--cached", "--name-only"])
        staged = result.decode("utf-8").strip().split("\n")
        return len([f for f in staged if f])
    except Exception as e:
        print("Error staging files:", e)
        return 0


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
        print("Error during commit:", e)
        return False


def git_push():
    """Push to remote"""
    try:
        result = subprocess.run(
            ["git", "push", "--set-upstream", "origin", "main"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("Pushed to GitHub successfully!")
        else:
            print("Push failed:\n", result.stderr)
    except Exception as e:
        print("Error during push:", e)


# ─────────────────────────────────────────────
# AI HELPERS
# ─────────────────────────────────────────────

def generate_commit_message(diff):
    """Generate commit message using Groq LLM"""
    if not diff:
        return "No changes staged."

    if len(diff) > 4000:
        print("Large diff detected — only first 4000 chars sent to AI.\n")

    prompt = f"""
You are a senior software engineer generating high-quality git commit messages.

Follow these STRICT rules:
1. Use Conventional Commits format: type(scope): short summary
2. Allowed types: feat, fix, docs, style, refactor, test, chore, perf, build, ci
3. Summary line: Max 72 characters, imperative mood, specific
4. Add bullet points in body ONLY if necessary
5. If change is small: return ONLY one-line commit
6. DO NOT add any explanation, quotes, markdown, or extra text outside the commit message
7. Output must be clean and ready to paste into git

Git Diff:
{diff[:4000]}
"""
    response = model.invoke(prompt)
    return response.content.strip()


def generate_gitignore():
    """Scan project and generate .gitignore using AI"""
    try:
        result = subprocess.check_output(
            ["find", ".", "-not", "-path", "./.git/*", "-type", "f"],
            stderr=subprocess.DEVNULL
        )
        all_files = result.decode("utf-8").strip()
    except:
        all_files = ""

    prompt = f"""
You are an expert developer. Based on the following list of files in a project, generate a comprehensive and clean .gitignore file.

Rules:
- Include common patterns for the detected languages/frameworks
- Always include: .env, .DS_Store, __pycache__, *.pyc, node_modules, .venv, venv
- Group entries with comments like # Python, # Node, # OS files etc.
- Output ONLY the .gitignore content, nothing else, no markdown, no explanation

Project files:
{all_files[:3000]}
"""
    response = model.invoke(prompt)
    return response.content.strip()


def generate_readme(description):
    """Smart file selection + generate README.md using AI"""

    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', '.env',
                   'dist', 'build', '.idea', '.vscode', 'coverage', '.pytest_cache'}
    ignore_exts = {'.pyc', '.pyo', '.png', '.jpg', '.jpeg', '.gif', '.ico',
                   '.svg', '.lock', '.log', '.zip', '.tar', '.gz', '.exe', '.bin'}
    ignore_files = {'.env', '.DS_Store', 'package-lock.json', 'yarn.lock'}

    # Entry point files — read fully
    entry_points = {'main.py', 'app.py', 'index.py', 'server.py', 'index.js',
                    'app.js', 'server.js', 'manage.py', 'run.py',
                    'requirements.txt', 'package.json', 'pyproject.toml', 'setup.py'}

    # Step 1: Get folder structure (names only, no content)
    folder_structure = []
    all_files = []

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        level = root.replace(".", "").count(os.sep)
        indent = "  " * level
        folder_structure.append(f"{indent}{os.path.basename(root)}/")
        for file in files:
            if file not in ignore_files:
                folder_structure.append(f"{indent}  {file}")
                all_files.append(os.path.join(root, file))

    structure_str = "\n".join(folder_structure)

    # Step 2: Read files smartly
    context = ""
    for filepath in all_files:
        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1]

        if ext in ignore_exts or filename in ignore_files:
            continue

        # Read entry points fully, others partially
        read_limit = 3000 if filename in entry_points else 300

        try:
            with open(filepath, "r", errors="ignore") as f:
                content = f.read(read_limit)
            if content.strip():
                context += f"\n\n### {filepath}\n{content}"
        except:
            continue

    # Use smarter model for README
    readme_model = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API")
    )

    prompt = f"""
You are a senior developer writing a professional GitHub README.md.

About this project (provided by the developer):
{description}

Use this description as context to understand the project goal, but write 
the README in your own words. Expand on it using the code files below. 
Do NOT copy the description word for word.

STRICT RULES:
- ONLY use information from the files provided below
- Do NOT invent features, code, or endpoints not present in the files
- Do NOT hallucinate. If unsure, skip it
- Output ONLY the README.md markdown content, nothing else

Based ONLY on these files, write a README.md with:
- Project title and short catchy description
- Features (only what you see in the code)
- Tech stack (only libraries actually imported)
- Installation steps
- Usage section must show these exact commands with explanations:
  * `ai_git push` → stages files, generates AI commit message, pushes to GitHub
  * `ai_git ignore` → scans project and generates .gitignore
  * `ai_git readme` → reads project files and generates README.md
  Do NOT show raw git commands like `git add` or `git commit`.
- License (MIT)

Project folder structure:
{structure_str}

Project file contents:
{context[:6000]}
"""
    response = readme_model.invoke(prompt)
    return response.content.strip()


# ─────────────────────────────────────────────
# COMMANDS
# ─────────────────────────────────────────────

def push_command():
    """Main push flow"""

    # Auto-check for .gitignore
    if not os.path.exists(".gitignore"):
        print("No .gitignore found!")
        choice = input("Generate one automatically? (y/n): ").strip().lower()
        if choice == "y":
            ignore_command()

    print("\n Scanning for changed files...\n")
    changed_files = get_changed_files()

    if not changed_files:
        print("No changes found in your repo.")
        return

    status_labels = {
        "M": "modified", "A": "added", "D": "deleted",
        "??": "untracked", "R": "renamed"
    }

    print("Files that will be pushed:")
    print("-" * 40)
    for i, (status, filename) in enumerate(changed_files, 1):
        label = status_labels.get(status, status)
        print(f"  {i}. [{label}] {filename}")
    print("-" * 40)

    print("\nWhich files do you want to EXCLUDE? (comma separated, or press Enter to include all)")
    exclude_input = input("Exclude: ").strip()

    exclude_files = []
    if exclude_input:
        exclude_files = [f.strip() for f in exclude_input.split(",")]
        print(f"\n Excluding: {', '.join(exclude_files)}")

    print("\n Staging files...")
    staged_count = stage_files(exclude_files)

    if staged_count == 0:
        print("No files staged after exclusions.")
        return

    print(f"{staged_count} file(s) staged.\n")

    print("Generating commit message with AI...\n")
    diff = get_git_diff()
    message = generate_commit_message(diff)

    print("Suggested Commit Message:")
    print("-" * 60)
    print(message)
    print("-" * 60)

    print("\n[y] Commit & Push  [e] Edit message  [r] Regenerate  [n] Cancel")
    choice = input("Choice: ").strip().lower()

    if choice == "r":
        print("\n Regenerating...\n")
        message = generate_commit_message(diff)
        print("New Commit Message:")
        print("-" * 60)
        print(message)
        print("-" * 60)
        choice = input("\n[y] Commit & Push  [e] Edit message  [n] Cancel\nChoice: ").strip().lower()

    if choice == "e":
        message = input("Enter your commit message: ").strip()
        if not message:
            print("Empty message. Cancelled.")
            return
        choice = "y"

    if choice == "y":
        success = git_commit(message)
        if success:
            print("\n Pushing to GitHub...")
            git_push()
    else:
        print("Cancelled.")
        subprocess.run(["git", "reset"], stdout=subprocess.DEVNULL)


def ignore_command():
    """Generate .gitignore for the project"""
    print("\n Scanning project files...")
    print("Generating .gitignore with AI...\n")

    content = generate_gitignore()

    print("Generated .gitignore:")
    print("-" * 60)
    print(content)
    print("-" * 60)

    confirm = input("\nSave as .gitignore? (y/n): ").strip().lower()
    if confirm == "y":
        with open(".gitignore", "w") as f:
            f.write(content)
        print(".gitignore saved!")
    else:
        print("Cancelled.")


def readme_command():
    """Generate README.md for the project"""
    print("\n Let's generate your README.md!\n")
    description = input("Describe your project in one line: ").strip()

    if not description:
        print("Description cannot be empty.")
        return

    print("\n Reading project files...")
    print("Generating README.md with AI...\n")

    content = generate_readme(description)

    print("Generated README.md preview:")
    print("-" * 60)
    print(content[:1000] + "\n... (truncated for preview)")
    print("-" * 60)

    confirm = input("\nSave as README.md? (y/n): ").strip().lower()
    if confirm == "y":
        with open("README.md", "w") as f:
            f.write(content)
        print("README.md saved!")
    else:
        print("Cancelled.")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("\n ai_git — AI-powered Git CLI")
        print("-" * 40)
        print("  ai_git push    → stage, commit & push with AI commit message")
        print("  ai_git ignore  → generate .gitignore for your project")
        print("  ai_git readme  → generate README.md for your project")
        print("-" * 40)
        return

    command = sys.argv[1].lower()

    if command == "push":
        push_command()
    elif command == "ignore":
        ignore_command()
    elif command == "readme":
        readme_command()
    else:
        print(f"Unknown command: '{command}'")
        print("Available commands: push, ignore, readme")


if __name__ == "__main__":
    main()