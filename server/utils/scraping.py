import os
import re
import requests
import base64
from bs4 import BeautifulSoup
from utils.io import read_issue_files, write_issue_files
from utils.guidebook import call_llm

github_token = os.getenv('GITHUB_AUTH_TOKEN')
if not github_token:
    raise ValueError("GITHUB_AUTH_TOKEN not found in .env file")
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {github_token}"
}


# use the issue url, to fetch repo information, issue information, and other required information...
# https://github.com/jax-ml/jax/issues/30787
# https://api.github.com/repos/jax-ml/jax/issues/30787
def convert_issue_http_to_api_url(url: str) -> str:
    suffix = url.removeprefix("https://github.com/")
    return f"https://api.github.com/repos/{suffix}"

def fetch_issue(issueUrl):
    issueApiUrl = convert_issue_http_to_api_url(issueUrl)
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
    
def gather_contribution_guidelines(owner, repo, repo_description, chunk_size=4000):
    """
    Fetch and aggregate contribution guidelines for a repository.
    Handles long docs via recursive binary merging of chunks.
    """

    base_path = os.path.join("data", owner, repo)
    os.makedirs(base_path, exist_ok=True)
    file_path = os.path.join(base_path, "contribution_guidelines.txt")

    possible_paths = [
        "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md",
        "CONTRIBUTING.rst", "README.md", "CODE_OF_CONDUCT.md",
        "docs/STYLEGUIDE.md", "STYLEGUIDE.md", "DEVELOPER.md"
    ]

    fetched_texts = []

    def fetch_github_file(path):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return base64.b64decode(data.get("content", "")).decode("utf-8")
        except Exception:
            return None
        return None

    def fetch_external_url(url):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.extract()
                return soup.get_text("\n", strip=True)
        except Exception:
            return None
        return None

    for path in possible_paths:
        content = fetch_github_file(path)
        if content:
            fetched_texts.append(content)
            links = re.findall(r"https?://[^\s\)\]]+", content)
            print("The Links are:", links)
            for link in links:
                ext_text = fetch_external_url(link)
                if ext_text:
                    fetched_texts.append(ext_text)
            break  # Stop after first valid file

    if not fetched_texts:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("No contribution guidelines found.")
        return "No contribution guidelines found."

    unstructured_guidelines = ''.join(fetched_texts)

    # TODO: only keep the sentences that are important to the file
    def process_chunk(text, repo_description):
        prompt = f"""
        You are an expert open-source contributor.

        Task:
        - Extract **ALL important and slightly relevant actionable information** from the following text.
        - Reorganize into these sections for PR authors:
            ## 1. Project Goals & Vision
            ## 2. Setup Instructions
            ## 3. Technical Design Alignment
            ## 4. Code Style & Language Best Practices
            ## 5. Performance Considerations
            ## 6. Commit Quality Standards
            ## 7. Pull Request Guidelines
            ## 8. Testing (Automated & Manual)
        - Do NOT omit any useful detail, even if minor.
        - If a section is missing, leave it empty or infer best practices from the context.
        - Keep all commands, paths, branch naming conventions, PR review rules, and testing details.
        - Keep the tone directive and contributor-focused.
        - No filler or maintainers-only info.

        Repository Description:
        {repo_description}

        Text:
        {text}
        """
        return call_llm(prompt)
    
    structured_guidelines = process_chunk(unstructured_guidelines, repo_description)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(structured_guidelines)

    return structured_guidelines

# Clean the fetched information to get the important parts to it.
def clean_issue_info(issue_data):
    if not issue_data:
        # TODO: throw an error
        return None
    repo_api_url = issue_data["repository_url"]
    api_url = issue_data["url"]
    title = issue_data["title"]
    body = issue_data["body"]
    # TODO: find out if and how to get description about repo, and related files, etc.
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
    match = re.match(r"https://api\.github\.com/repos/([^/]+)/([^/]+)/issues/(\d+)", api_url)
    if match:
        repo_author_name = match.group(1)
        repo_name = match.group(2)
        issue_number = match.group(3)
        print("Repo Author:", repo_author_name)
        print("Repo Name:", repo_name)
        print("Issue Number:", issue_number)
    else:
        print("Invalid GitHub API issue URL")
    # TODO: Also extract the comments and the review comments for the repository
    contribution_guidelines = gather_contribution_guidelines(repo_author_name, repo_name, repo_description)

    write_issue_files(repo_author_name, repo_name, issue_number, title, body, repo_description, contribution_guidelines)

    return {
        "repo_author": repo_author_name,
        "repo_name": repo_name,
        "issue_number": issue_number
    }

def get_diff(owner, repo, pr_number):
    pr_api_url = "https://api.github.com/repos/" + owner + "/" + repo + "/pulls/" + pr_number
    diff_url = pr_api_url + ".diff"
    try:
        response = requests.get(diff_url, headers=headers, timeout=10)
        response.raise_for_status()
        # Handle rate limits
        remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        if remaining < 1:
            # TODO: return an error message saying wait until the reset time
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {diff_url}: {e}")
        return None


def detect_duplicates(owner, repo, issue_title):
    """
    Detect similar issues in the same repository using GitHub Search API.
    Returns a list of up to 3 similar issues with title, url, and status.
    """
    search_url = "https://api.github.com/search/issues"
    query = f"{issue_title} repo:{owner}/{repo} type:issue"
    params = {
        "q": query,
        "sort": "created",
        "order": "desc",
        "per_page": 3
    }

    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            status_label = "open"
            if item["state"] == "closed":
                # Check if closed issue is linked to a merged PR
                issue_number = item["number"]
                timeline_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/timeline"
                timeline_resp = requests.get(timeline_url, headers={**headers, "Accept": "application/vnd.github.mockingbird-preview"}, timeout=10)
                if timeline_resp.status_code == 200:
                    events = timeline_resp.json()
                    merged = any(e.get("event") == "cross-referenced" and e.get("source", {}).get("type") == "pull_request" for e in events)
                    status_label = "merged" if merged else "outdated"
                else:
                    status_label = "closed"
            else:
                status_label = "open"

            results.append({
                "title": item["title"],
                "url": item["html_url"],
                "status": status_label
            })

        return results

    except requests.exceptions.RequestException as e:
        print(f"Error searching for duplicates: {e}")
        return []
