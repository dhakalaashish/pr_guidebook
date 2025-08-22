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

def check_issue_scope(repo_description, title, body, contribution_guidelines, issue_type, issue_number):
    """
    Check if the issue scope is manageable for a single PR.
    If too large, suggest breaking it into multiple PRs for the same issue.
    Adds reference to the issue in each PR description.
    """

    # Skip if bug
    if issue_type.strip().lower() == "bug":
        return {
            "status": "single-pr",
            "reason": "Bug fix issues are usually handled in a single PR."
        }

    # Build LLM prompt
    scope_prompt = f"""
    You are an expert open-source maintainer.

    Task:
    Analyze the following feature request and decide:
    - Can it be completed in a single PR?
    - Or should it be split into multiple PRs (for easier review and contribution)?
    
    If splitting, provide a clear PR plan: suggest 2-4 smaller PRs with titles and brief descriptions.

    Inputs:
    - Project Description: {repo_description}
    - Contribution Guidelines: {contribution_guidelines}
    - Issue Title: {title}
    - Issue Description: {body}

    Output JSON:
    If single PR:
    {{
      "status": "single-pr",
      "pr_plan": []
    }}
    If multiple PRs:
    {{
      "status": "multi-pr",
      "pr_plan": [
        {{"title": "PR Title 1", "description": "Short explanation"}},
        {{"title": "PR Title 2", "description": "Short explanation"}}
      ]
    }}
    """

    # Call LLM
    llm_response = call_llm(scope_prompt)
    if not llm_response:
        return {"error": "Failed to check issue scope."}

    # Extract JSON
    try:
        import json, re
        json_match = re.search(r"\{[\s\S]*\}", llm_response)
        if json_match:
            parsed = json.loads(json_match.group(0))

            # Append issue reference in description
            if "pr_plan" in parsed and parsed["pr_plan"]:
                for pr in parsed["pr_plan"]:
                    pr["description"] = f"{pr.get('description', '')} (Addresses Issue #{issue_number})"

            return parsed
        else:
            return {
                "status": "multi-pr",
                "pr_plan": [{
                    "title": "Manual Suggestion",
                    "description": f"{llm_response.strip()} (Addresses Issue #{issue_number})"
                }]
            }
    except Exception:
        return {
            "status": "multi-pr",
            "pr_plan": [{
                "title": "Manual Suggestion",
                "description": f"{llm_response.strip()} (Addresses Issue #{issue_number})"
            }]
        }


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

def generate_steps(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, suggestion_level=3):
    """
    Generate step-by-step guidance for a contributor to resolve a GitHub issue.
    
    Parameters:
    - owner: GitHub repo owner
    - repo: GitHub repo name
    - title: Issue title
    - issue_number: Issue number
    - suggestion_level: 1 (very high-level) to 5 (very detailed)
    - body: Issue body text
    - repo_description: Short description of the repo/project

    Returns:
    - List of steps as strings
    """
    # Map suggestion level to descriptive instructions
    suggestion_detail_map = {
        1: "High-level overview steps. Minimal technical details.",
        2: "Module-level guidance. Which modules/files to touch.",
        3: "Function-level guidance. Which functions to create or modify, with brief descriptions.",  # Default
        4: "Line-level guidance. Rough code snippets or pseudo-code for each function.",
        5: "Very detailed. Exact code recommendations or full function templates."
    }

    detail_description = suggestion_detail_map.get(suggestion_level, suggestion_detail_map[3])

    # Compose prompt for LLM
    prompt = f"""
    You are an expert open-source contributor assistant.

    The contributor wants to resolve the following GitHub issue:
    Repository: {owner}/{repo}
    Issue #{issue_number}: {title}
    Issue Body: {body}

    Repository description: {repo_description}

    Contribution guidelines (extracted from CONTRIBUTING.md or docs):
    {contribution_guidelines}

    Suggest step-by-step instructions for the contributor to solve the issue.
    Focus on technical steps including files to create, functions to implement, and their responsibilities.
    Follow these rules:
    - Use {detail_description}
    - Number the steps clearly.
    - Keep it actionable and practical for someone who wants to submit a PR.

    Output the steps as a JSON array of strings.
    """

    # Call the LLM (replace with your actual call_llm function)
    steps_text = call_llm(prompt)

    try:
        import json
        steps = json.loads(steps_text)
    except Exception:
        # fallback if LLM output isn't proper JSON
        steps = [line.strip() for line in steps_text.split("\n") if line.strip()]

    return steps

def explain_tests(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, suggestion_level=3):
    """
    Generate step-by-step guidance for writing and running tests for a given GitHub issue.

    Parameters:
    - owner: GitHub repo owner
    - repo: GitHub repo name
    - title: Issue title
    - issue_number: Issue number
    - suggestion_level: 1 (high-level) to 5 (very detailed)
    - body: Issue body text
    - repo_description: Short description of the repo/project
    - contribution_guidelines: Contribution guidelines text, to extract testing instructions

    Returns:
    - List of testing steps as strings
    """
    suggestion_detail_map = {
        1: "High-level testing instructions, minimal technical details",
        2: "Module-level guidance on which modules/files to test",
        3: "Function-level guidance, which functions/methods to test, and what scenarios to cover",  # Default
        4: "Line-level guidance or pseudo-code for writing test cases",
        5: "Very detailed instructions including exact test commands and example code snippets"
    }

    detail_description = suggestion_detail_map.get(suggestion_level, suggestion_detail_map[3])

    prompt = f"""
    You are an expert open-source contributor assistant.

    The contributor wants to resolve the following GitHub issue:
    Repository: {owner}/{repo}
    Issue #{issue_number}: {title}
    Issue Body: {body}

    Repository description: {repo_description}

    Contribution guidelines (extracted from CONTRIBUTING.md or docs):
    {contribution_guidelines}

    Before creating a pull request, the contributor must ensure proper testing.

    Suggest step-by-step instructions to conduct the necessary tests:
    - Focus on testing functions or modules affected by this issue.
    - Mention running existing tests and adding new ones.
    - Emphasize the importance of testing before creating a PR.
    - Use {detail_description}
    - Output the steps as a JSON array of strings, numbered clearly.
    """

    # Call the LLM (replace with your actual call_llm function)
    steps_text = call_llm(prompt)

    try:
        import json
        steps = json.loads(steps_text)
    except Exception:
        # fallback if LLM output isn't proper JSON
        steps = [line.strip() for line in steps_text.split("\n") if line.strip()]

    return steps


# Bulk call several prompts to generate different checklist for each guidebook heading
def call_llm(prompt):
    response  = model.generate_content(prompt)
    if response:
        return response.text
    else:
        return None