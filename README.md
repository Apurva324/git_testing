# AutoGit: AI-Powered Git Automation
Automate your Git workflow with AutoGit, a CLI tool that simplifies Git pushes with AI-generated commit messages.

## Features
* Stage files and generate AI commit messages
* Push changes to GitHub
* Generate `.gitignore` files based on project scans
* Create `README.md` files by reading project files

## Tech Stack
* `subprocess` for Git command execution
* `os` and `sys` for system operations
* `dotenv` for environment variable management
* `langchain_groq` for AI-powered commit message generation

## Installation
To install AutoGit, clone this repository and install the required dependencies.

## Usage
### Push Changes with AI-Generated Commit Messages
```bash
ai_git push
```
Stages files, generates an AI commit message, and pushes changes to GitHub.

### Generate .gitignore Files
```bash
ai_git ignore
```
Scans the project and generates a `.gitignore` file.

### Create README.md Files
```bash
ai_git readme
```
Reads project files and generates a `README.md` file.

## License
AutoGit is licensed under the MIT License.