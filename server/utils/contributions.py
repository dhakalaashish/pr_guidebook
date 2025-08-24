# import os
# import re
# import base64
# import requests
# from bs4 import BeautifulSoup
# from utils.guidebook import call_llm

# github_token = os.getenv('GITHUB_AUTH_TOKEN')
# if not github_token:
#     raise ValueError("GITHUB_AUTH_TOKEN not found in .env file")
# headers = {
#     "Accept": "application/vnd.github+json",
#     "Authorization": f"Bearer {github_token}"
# }
# def gather_contribution_guidelines(owner, repo, chunk_size=4000):
#     """
#     Fetch and aggregate contribution guidelines for a repository.
#     Handles long docs via recursive binary merging of chunks.
#     """

#     base_path = os.path.join("data", owner, repo)
#     os.makedirs(base_path, exist_ok=True)
#     file_path = os.path.join(base_path, "contribution_guidelines.txt")

#     possible_paths = [
#         "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md",
#         "CONTRIBUTING.rst", "README.md", "CODE_OF_CONDUCT.md",
#         "docs/STYLEGUIDE.md", "STYLEGUIDE.md", "DEVELOPER.md"
#     ]

#     fetched_texts = []

#     def fetch_github_file(path):
#         url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
#         try:
#             r = requests.get(url, headers=headers, timeout=10)
#             if r.status_code == 200:
#                 data = r.json()
#                 return base64.b64decode(data.get("content", "")).decode("utf-8")
#         except Exception:
#             return None
#         return None

#     def fetch_external_url(url):
#         try:
#             r = requests.get(url, timeout=10)
#             if r.status_code == 200:
#                 soup = BeautifulSoup(r.text, "html.parser")
#                 for tag in soup(["script", "style", "nav", "footer", "header"]):
#                     tag.extract()
#                 return soup.get_text("\n", strip=True)
#         except Exception:
#             return None
#         return None

#     for path in possible_paths:
#         content = fetch_github_file(path)
#         if content:
#             fetched_texts.append(content)
#             links = re.findall(r"https?://\S+", content)
#             for link in links:
#                 ext_text = fetch_external_url(link)
#                 if ext_text:
#                     fetched_texts.append(ext_text)
#             break  # Stop after first valid file

#     if not fetched_texts:
#         with open(file_path, "w", encoding="utf-8") as f:
#             f.write("No contribution guidelines found.")
#         return "No contribution guidelines found."

#     def process_chunk(text, repo_description):
#         prompt = f"""
#         Rewrite and organize the contribution information for PR authors from the given text.

#         Requirements:
#         - Include ALL actionable details.
#         - Organize into these sections:
#             1. Project Goals & Vision
#             2. Setup Instructions
#             3. Technical Design Alignment
#             4. Code Style & Language Best Practices
#             5. Performance Considerations
#             6. Commit Quality Standards
#             7. Pull Request Guidelines
#             8. Testing (Automated & Manual)
#         - If the text does not cover a section, leave it or provide best practices if implied.
#         - Use Markdown headings (##).
#         - Include all relevant commands and examples.
#         - Remove filler text and maintainers-only content.
#         - Keep the tone directive, clear, and comprehensive.

#         Repository Description:
#         {repo_description}

#         Input Contribution Text:
#         {text}
#         """
#         return call_llm(prompt)



#     def merge_two(text_a, text_b):
#         prompt = f"""
#         Merge the following two structured contribution guidelines into ONE comprehensive version.
#         Preserve all details, avoid redundancy, and keep the same section structure.

#         --- Guidelines A ---
#         {text_a}

#         --- Guidelines B ---
#         {text_b}
#         """
#         return call_llm(prompt)
    
#     structured_guidelines = None
#     for path in possible_paths:
#         content = fetch_github_file(path)
#         if content:
#             print("Found one valid file")
#             # Process main file
#             structured_guidelines = process_chunk(content)

#             # Process external links sequentially
#             links = re.findall(r"https?://\S+", content)
#             for link in links:
#                 print("Found one valid link in one valid file")
#                 ext_text = fetch_external_url(link)
#                 if ext_text:
#                     # Break external text into chunks
#                     ext_processed = process_chunk(ext_text)
#                     # Merge with existing guidelines sequentially
#                     structured_guidelines = merge_two(structured_guidelines, ext_processed)

#             break  # Stop after first valid file

#     if not structured_guidelines:
#         with open(file_path, "w", encoding="utf-8") as f:
#             f.write("No contribution guidelines found.")
#         return "No contribution guidelines found."

#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(structured_guidelines)

#     return structured_guidelines
