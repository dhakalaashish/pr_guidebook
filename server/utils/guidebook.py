import os
import json
from dotenv import load_dotenv
import google.generativeai as genai
import re

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def classify_issue(title, body):
    "Classifies if an issue is a bug or a new feature"
    # Step 1: Classify issue type
    classify_prompt = f"""
    You are an expert open-source assistant.
    Determine whether the given GitHub issue describes a FEATURE REQUEST or a BUG REPORT.

    Input:
    - Issue Title: {title}
    - Issue Description: {body}

    Respond with exactly one word:
    "feature" or "bug".
        """

    classification = call_llm(classify_prompt)
    if not classification:
        return {"error": "Failed to classify issue type."}

    return classification.strip().lower()

def verify_feature_uniqueness(owner, repo, title, body, issue_type):
    """
    Determines if the issue is a feature request or a bug.
    If feature, provides guidance on checking feature uniqueness.
    If bug, returns 'not applicable'.
    """
    if issue_type == "bug":
        return {
            "status": "not applicable",
            "reason": "This issue is a bug report, not a feature request."
        }

    uniqueness_prompt = f"""
    You are an expert open-source contributor assistant.
    The user is working on a FEATURE REQUEST issue for the repo: {owner}/{repo}.

    Issue Title: {title}
    Issue Description: {body}

    Task:
    Provide a SHORT and CLEAR guide (max 3-4 sentences) for how the contributor can verify if this feature already exists in the repository.
    Avoid generic statements like 'check the repo'; be actionable (e.g., search keywords, check specific files or directories, review docs).

    Output Format:
    A single paragraph.
        """

    guidance = call_llm(uniqueness_prompt)
    if not guidance:
        guidance = "Could not generate guidance at this time."

    return {
        "status": "feature",
        "guidance": guidance.strip()
    }


def check_issue_alignment_with_vision(repo_description, title, body, contribution_guidelines, issue_type):
    """
    Check if the issue conflicts with the project's vision using LLM.
    - If bug, return 'not applicable'.
    - If feature, analyze contribution guidelines and repo description for conflicts.
    """

    # Step 1: Skip if bug
    if issue_type.strip().lower() == "bug":
        return {
            "status": "not applicable",
            "reason": "This issue is a bug report, so alignment check is unnecessary."
        }

    # Step 2: Build prompt for LLM
    alignment_prompt = f"""
    You are an expert open-source reviewer.

    Task:
    Analyze whether the following feature request aligns with the project's vision and contribution guidelines.
    If it aligns, simply respond with: "no conflict".
    If it conflicts, explain the conflict in one short paragraph and suggest up to 2 alternative directions for the contributor.

    Inputs:
    - Project Description:
    {repo_description}

    - Contribution Guidelines:
    {contribution_guidelines}

    - Issue Title: {title}
    - Issue Description: {body}

    Output Format:
    If no conflict:
    "no conflict"
    If conflict:
    {{
    "status": "conflict",
    "conflict_reason": "...",
    "suggested_alternatives": ["alt1", "alt2"]
    }}
        """

    # Step 3: Call LLM
    llm_response = call_llm(alignment_prompt)
    if not llm_response:
        return {"error": "Failed to check alignment with vision."}

    # Step 4: Parse response
    if llm_response.strip().lower().startswith("no conflict"):
        return {"status": "no conflict"}
    else:
        # Try to extract JSON-like output from LLM
        try:
            # Ensure only JSON-like part is parsed
            json_match = re.search(r"\{[\s\S]*\}", llm_response)
            if json_match:
                return json.loads(json_match.group(0))
            else:
                return {"status": "conflict", "details": llm_response.strip()}
        except Exception:
            return {"status": "conflict", "details": llm_response.strip()}

def check_issue_scope(repo_description, title, body, contribution_guidelines, issue_type):
    """
    Check if the issue scope is manageable for a single PR.
    If too large, suggest breaking into multiple smaller issues.
    Only run for feature requests (not bugs).
    """

    # Step 1: Skip if bug
    if issue_type.strip().lower() == "bug":
        return {
            "status": "not applicable",
            "reason": "Issue is a bug report, so scope check is unnecessary."
        }

    # Step 2: Build LLM prompt
    scope_prompt = f"""
    You are an expert open-source project assistant.

    Task:
    Determine whether the following feature request is manageable as a single PR,
    or if its scope is too large and should be broken into smaller issues.
    If it is too large, suggest 2-4 smaller chunks that can each become an issue. 
    Provide actionable chunk titles suitable for new issues (like button labels).

    Inputs:
    - Project Description: {repo_description}
    - Contribution Guidelines: {contribution_guidelines}
    - Issue Title: {title}
    - Issue Description: {body}

    Output Format (JSON):
    If scope is manageable:
    {{"status": "good", "suggested_chunks": []}}
    If scope is too large:
    {{"status": "too large", "suggested_chunks": ["chunk1", "chunk2", ...]}}
        """

    # Step 3: Call LLM
    llm_response = call_llm(scope_prompt)
    if not llm_response:
        return {"error": "Failed to check issue scope."}

    # Step 4: Parse JSON-like output
    try:
        import json
        # Extract JSON part if LLM returns extra text
        import re
        json_match = re.search(r"\{[\s\S]*\}", llm_response)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            # Fallback: if no JSON, return raw text as a suggestion
            return {"status": "too large", "suggested_chunks": [llm_response.strip()]}
    except Exception:
        return {"status": "too large", "suggested_chunks": [llm_response.strip()]}

def understand_relevant_contribution_guidelines(owner, repo, title, body, contribution_guidelines):
    """
    Summarize contribution guidelines in three points:
    1. Whether signing a CLA or agreeing to guidelines is required (with URL if yes, else 'not applicable').
    2. Instructions to setup project locally.
    3. How the project expects PR creation to be done.
    """

    prompt = f"""
    You are an expert open-source assistant.

    Task:
    Based on the contribution guidelines provided, summarize the key points for a new contributor in the following structured format.

    Inputs:
    - Repository: {owner}/{repo}
    - Issue Title: {title}
    - Issue Description: {body}
    - Contribution Guidelines Text: {contribution_guidelines}

    Output Format (JSON):
    {{
    "signing_guidelines": "...",  # If contributor must sign a CLA or agree to contribution guidelines, provide the URL. Else, "not applicable".
    "local_setup_instructions": "...",  # Steps to setup the project locally (install dependencies, build, run tests, etc.)
    "PR_creation_process": "..."  # Steps or instructions on how the project expects PRs to be created
    }}
    Respond with exactly this JSON format, no extra text.
        """

    llm_response = call_llm(prompt)
    if not llm_response:
        return {"error": "Failed to fetch contribution guidelines summary."}

    # Try to parse JSON from LLM response
    try:
        import json, re
        json_match = re.search(r"\{[\s\S]*\}", llm_response)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            # Fallback if parsing fails: return as plain text in all fields
            return {
                "signing_guidelines": "not available",
                "local_setup_instructions": llm_response.strip(),
                "PR_creation_process": llm_response.strip()
            }
    except Exception:
        return {
            "signing_guidelines": "not available",
            "local_setup_instructions": llm_response.strip(),
            "PR_creation_process": llm_response.strip()
        }

# Bulk call several prompts to generate different checklist for each guidebook heading
def call_llm(prompt):
    response  = model.generate_content(prompt)
    if response:
        return response.text
    else:
        return None