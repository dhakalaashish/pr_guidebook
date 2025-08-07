import os
from dotenv import load_dotenv
import requests
import google.generativeai as genai
import re


# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# use the issue url, to fetch repo information, issue information, and other required information...
# https://github.com/jax-ml/jax/issues/30787
# https://api.github.com/repos/jax-ml/jax/issues/30787
def convert_issue_http_to_api_url(url: str) -> str:
    suffix = url.removeprefix("https://github.com/")
    return f"https://api.github.com/repos/{suffix}"

def fetch_issue(issueUrl):
    issueApiUrl = convert_issue_http_to_api_url(issueUrl)
    github_token = os.getenv('GITHUB_AUTH_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_AUTH_TOKEN not found in .env file")
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}"
    }
    try:
        response = requests.get(issueApiUrl, headers=headers, timeout=10)
        response.raise_for_status()
        # Handle rate limits
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining < 1:
            # TODO: return an error message saying wait until the reset time
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {issueApiUrl}: {e}")
        return None
    
# Clean the fetched information to get the important parts to it.

def clean_issue_info(issue_data):
    if not issue_data:
        # TODO: throw an error
        return None
    repo_api_url = issue_data["repository_url"]
    title = issue_data["title"]
    body = issue_data["body"]
    # TODO: find out if and how to get description about repo, and related files, etc.
    github_token = os.getenv('GITHUB_AUTH_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_AUTH_TOKEN not found in .env file")
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}"
    }
    try:
        response = requests.get(repo_api_url, headers=headers, timeout=10)
        response.raise_for_status()
        # Handle rate limits
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining < 1:
            # TODO: return an error message saying wait until the reset time
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        repo_data =  response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {repo_api_url}: {e}")
        return None
    if not repo_data:
        # TODO: throw an error
        return None
    repo_description = repo_data["description"]
    return {
        "title": title,
        "body": body,
        "repo_description": repo_description
    }

# Create a prompt, with the guidelines, "several different prompts"
def generate_prompt(useful_issue_info):
    title = useful_issue_info.get("title", "")
    body = useful_issue_info.get("body", "")
    repo_description = useful_issue_info.get("repo_description", "")

    prompt = f"""
                You are an expert open-source contributor assistant. Given the **GitHub Issue Title**, **Issue Description**, and **Repository Description**, your task is to create a detailed **Pull Request Checklist** under predefined sections. This checklist helps a programmer solve the issue from scratch and write a high-quality PR.

                Use the following predefined major headings. Each heading must have sub-steps tailored to the specific issue. Your response should be formatted using these exact headings in bold. Avoid generic advice. Be specific, actionable, and step-by-step wherever possible.

                ---

                **Input:**

                - **Issue Title:** {title}
                - **Issue Description:** {body}
                - **Repository Description:** {repo_description}

                ---

                **Output Format (strictly use these exact headings and follow order):**

                ---

                **A. Git Skills**  
                Steps to fork the repo, set up a local branch, sync with upstream, and push changes. Include dealing with merge conflicts if relevant.

                **B. Ensure not superseded or outdated or redundant or low-priority**  
                Checklist to:
                1. Search for existing PRs that may already solve this issue.
                2. Check if the functionality/fix is already in the codebase.
                3. Determine if the issue is still relevant.
                4. Estimate the importance of this fix/feature in the project context.

                **C. Understand the basics of the project**  
                Provide:
                1. A summary of the project (or a direct quote from repo description).
                2. A link to or summary of contribution guidelines (use common filenames like `CONTRIBUTING.md` or `.github/CONTRIBUTING.md`).

                **D. Writing code for the PR**  
                Steps to ensure the code fully solves the issue and avoids unnecessary or unrelated changes.

                **E. PR Conformance to Project Standards**  
                Checklist with guidance on:
                1. Project ideology alignment.
                2. Technical and architectural fit.
                3. Code style and idioms.
                4. Commit practices (one commit per subsystem, clean history, meaningful messages).
                5. PR description clarity and structure.
                6. Performance or code size implications.

                **F. Testing**  
                Checklist for:
                1. Running existing CI tests (mention what frameworks or tools might be used).
                2. Writing and running manual or automated tests specific to the change.

                ---

                Make the checklist personalized and contextual based on the input issue. Do not omit any major heading. Output only the checklist, no extra text.
                """
    return prompt.strip()

# Bulk call several prompts to generate different checklist for each guidebook heading
def call_llm(prompt):
    response  = model.generate_content(prompt)
    if response:
        return response.text
    else:
        return None
    
# return each of them as a dictionary, such that it is easily readable in the frontend
def clean_llm_result(llm_result):
    if not llm_result or not isinstance(llm_result, str):
        return {"error": "No valid LLM response received."}

    headings = [
        "A. Git Skills",
        "B. Ensure not superseded or outdated or redundant or low-priority",
        "C. Understand the basics of the project",
        "D. Writing code for the PR",
        "E. PR Conformance to Project Standards",
        "F. Testing"
    ]

    # Use regex to split the LLM result at each major heading
    pattern = r"\*\*(A\. Git Skills|B\. Ensure not superseded or outdated or redundant or low-priority|C\. Understand the basics of the project|D\. Writing code for the PR|E\. PR Conformance to Project Standards|F\. Testing)\*\*"
    sections = re.split(pattern, llm_result)

    if len(sections) < 2:
        return {"error": "Unexpected LLM output format."}

    # The format will be like: ['', 'A. Git Skills', content1, 'B. ...', content2, ...]
    cleaned_result = {}
    for i in range(1, len(sections), 2):
        heading = sections[i].strip()
        content = sections[i + 1].strip() if (i + 1) < len(sections) else ""
        cleaned_result[heading] = content

    return cleaned_result