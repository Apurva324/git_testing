# AutoGit: AI-Powered Git Automation
Automate your Git workflow with AutoGit, a CLI tool that leverages AI to generate commit messages, create `.gitignore` files, and produce READMEs.

## Features
* Generate AI-powered commit messages
* Automatically create `.gitignore` files
* Produce high-quality READMEs
* Summarize recent commits in plain English

## Tech Stack
* `langchain-groq` for AI-powered text generation
* `python-dotenv` for environment variable management

## Installation
To install AutoGit, run the following command:
```bash
pip install ai-git-cli-apurva
```
This will install the `ai_git` command globally on your system.

## Usage
### Commit and Push
Use `ai_git push` to stage all files, generate an AI-powered commit message, and push to GitHub.
```bash
ai_git push
```
This command will automatically stage all files, generate a commit message using AI, and push the changes to your remote repository.

### Generate .gitignore
Use `ai_git ignore` to scan your project and generate a `.gitignore` file.
```bash
ai_git ignore
```
This command will analyze your project directory and create a `.gitignore` file based on the files and directories it finds.

### Generate README
Use `ai_git readme` to read your project files and generate a high-quality README.
```bash
ai_git readme
```
This command will parse your project files and produce a well-structured README that summarizes your project.

## License
AutoGit is licensed under the MIT License.