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

def generate_steps(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, pr_title=None, pr_description=None, suggestion_level=3):
    detail_map = {1: "High-level overview steps", 2: "Module-level guidance", 3: "Function-level guidance",
                  4: "Line-level guidance", 5: "Very detailed with pseudo-code"}
    detail_description = detail_map.get(suggestion_level, detail_map[3])

    # Only include PR info if pr_title is provided
    pr_info = ""
    if pr_title and pr_description:
        pr_info = f"""
        The contributor has chosen this PR plan:
        Title: {pr_title}
        Description: {pr_description}
        """

    prompt = f"""
    You are an expert open-source contributor assistant.

    Repository: {owner}/{repo}
    Issue #{issue_number}: {title}
    Issue Body: {body}

    Repository description: {repo_description}

    Contribution guidelines:
    {contribution_guidelines}

    {pr_info}

    Suggest step-by-step instructions for implementing this PR.
    Focus on:
    - Files to create or modify
    - Functions to implement, and their responsibilities
    - Use {detail_description}

    ### Output format
    Return **only valid JSON**, no Markdown, no commentary. 
    Example:
    [
      "Update README with setup instructions",
      "Modify src/utils.py to add parse_data()",
      "Write unit tests in tests/test_utils.py"
    ]
    """

    steps_text = call_llm(prompt).strip()

    try:
        import json
        parsed = json.loads(steps_text)
        # Always normalize to list of strings
        return [str(s).strip() for s in parsed if str(s).strip()]
    except:
        # fallback: split lines
        return [line.strip("-* ") for line in steps_text.split("\n") if line.strip()]

def explain_tests(owner, repo, title, issue_number, body, repo_description,
                  contribution_guidelines, pr_title=None, pr_description=None,
                  suggestion_level=3):

    detail_map = {
        1: "High-level testing instructions",
        2: "Module-level guidance",
        3: "Function-level guidance",
        4: "Line-level pseudo-code",
        5: "Very detailed with commands and examples"
    }
    detail_description = detail_map.get(suggestion_level, detail_map[3])

    pr_info = ""
    if pr_title and pr_description:
        pr_info = f"""
        The contributor is implementing this PR:
        Title: {pr_title}
        Description: {pr_description}
        """

    prompt = f"""
    You are an expert open-source contributor assistant.

    Repository: {owner}/{repo}
    Issue #{issue_number}: {title}
    Issue Body: {body}

    Repository description: {repo_description}

    Contribution guidelines:
    {contribution_guidelines}

    {pr_info}

    Provide detailed instructions for:
    - Running existing tests
    - Writing new tests for added functionality
    - Use {detail_description}
    - Emphasize testing before creating a PR

    ### Output format
    Return **only valid JSON**, no Markdown, no commentary. 
    Example:
    [
      "Run pytest to execute all tests",
      "Add unit tests in tests/test_utils.py for parse_data()",
      "Verify coverage with pytest --cov"
    ]
    """

    steps_text = call_llm(prompt).strip()

    try:
        import json
        parsed = json.loads(steps_text)
        return [str(s).strip() for s in parsed if str(s).strip()]
    except:
        return [line.strip("-*• ") for line in steps_text.split("\n") if line.strip()]

def validate_pr_resolution(owner, repo, issue_number, repo_description, diff):
    """
    Validates if the selected PR is fully implemented according to the user's choice.
    Returns a markdown list of items still missing if any.
    """
    pr_choice_file = os.path.join("data", owner, repo, str(issue_number), "pr_choice.txt")
    if not os.path.exists(pr_choice_file):
        return "PR choice not found. User must select a PR plan first."

    # Read the PR choice (plain text)
    with open(pr_choice_file, "r", encoding="utf-8") as f:
        pr_choice_text = f.read().strip()

    # Compose prompt for LLM
    prompt = f"""
    You are reviewing a pull request.

    PR plan chosen by the user:
    {pr_choice_text}

    Repository description:
    {repo_description}

    Diff of the PR:
    {diff}

    Task: Check if the PR fully implements the chosen PR plan.
    If some parts of the PR plan are not implemented, create a markdown list of what is still missing.
    Focus only on the PR plan itself. Do not consider the original issue description.
    """

    # Call your LLM function here
    result = call_llm(prompt)
    return result

def enforce_contribution_guidelines(owner, repo, issue_number, contribution_guidelines, diff):
    """
    Evaluates if the PR follows the repository's contribution guidelines:
    - technical_design_alignment
    - match_project_code_style
    - language_specific_best_practices
    - possible_performance_issues
    - high_source_code_quality
    - commit_quality_standards

    Returns a structured JSON object with suggestions.
    """
    import os, json, re

    # Read PR choice
    pr_choice_file = os.path.join("data", owner, repo, str(issue_number), "pr_choice.txt")
    if not os.path.exists(pr_choice_file):
        return {"error": "PR choice not found. User must select a PR plan first."}

    with open(pr_choice_file, "r", encoding="utf-8") as f:
        pr_choice_text = f.read().strip()

    # Compose prompt for LLM
    prompt = f"""
    You are an expert open-source assistant.

    Task:
    Evaluate a pull request against the repository's contribution guidelines. Assess all of the following aspects in one review:
    1. Technical design alignment with the project's expectations.
    2. Match to the project's code style.
    3. Adherence to language-specific best practices.
    4. Possible performance issues in the code.
    5. Overall source code quality.
    6. Commit quality standards (if any).

    Inputs:
    - Repository: {owner}/{repo}
    - Contribution Guidelines: {contribution_guidelines}
    - PR plan chosen by the user:
    {pr_choice_text}
    - Diff of the PR:
    {diff}

    Output Format (JSON):
    {{
        "technical_design_alignment": "...",  # Suggestions or observations
        "match_project_code_style": "...",  # Issues or confirmation
        "language_specific_best_practices": "...",
        "possible_performance_issues": "...",
        "high_source_code_quality": "...",
        "commit_quality_standards": "..."
    }}
    Respond **only** with JSON, no extra text.
    """

    # Call your LLM function
    llm_response = call_llm(prompt)
    if not llm_response:
        return {"error": "Failed to fetch contribution guidelines enforcement."}

    # Parse JSON from LLM response
    try:
        json_match = re.search(r"\{[\s\S]*\}", llm_response)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            # fallback: return all fields with raw text
            return {
                "technical_design_alignment": llm_response.strip(),
                "match_project_code_style": llm_response.strip(),
                "language_specific_best_practices": llm_response.strip(),
                "possible_performance_issues": llm_response.strip(),
                "high_source_code_quality": llm_response.strip(),
                "commit_quality_standards": llm_response.strip()
            }
    except Exception:
        return {
            "technical_design_alignment": llm_response.strip(),
            "match_project_code_style": llm_response.strip(),
            "language_specific_best_practices": llm_response.strip(),
            "possible_performance_issues": llm_response.strip(),
            "high_source_code_quality": llm_response.strip(),
            "commit_quality_standards": llm_response.strip()
        }

def clear_pr_description(owner, repo, issue_number, contribution_guidelines, diff):
    """
    Checks the PR description and generates a markdown with suggestions
    for making it clear, concise, linked to the issue, and consistent
    with contribution guidelines.
    
    Returns a markdown string.
    """
    import os

    # Read PR choice
    pr_choice_file = os.path.join("data", owner, repo, str(issue_number), "pr_choice.txt")
    if not os.path.exists(pr_choice_file):
        return "PR choice not found. User must select a PR plan first."

    with open(pr_choice_file, "r", encoding="utf-8") as f:
        pr_choice_text = f.read().strip()

    # Extract the PR description from the text
    pr_description = ""
    lines = pr_choice_text.split("\n")
    for line in lines:
        if line.lower().startswith("pr description:"):
            pr_description = line[len("pr description:"):].strip()

    prompt = f"""
    You are an expert open-source assistant.

    Task:
    Review the following PR description and the associated code diff.
    Provide feedback in markdown format on how to make it clear, concise, informative,
    and aligned with the repository's contribution guidelines regarding PR descriptions.

    Your response should include:
    1. Current PR description.
    2. Suggestions to improve clarity, brevity, and informativeness.
    3. Recommendations from the contribution guidelines (if they mention PR description format).
    4. An example improved PR description that the user can copy-paste.
    5. Ensure the PR links to the issue it fixes (use a placeholder #ISSUE_NUMBER if needed).

    Inputs:
    - Repository: {owner}/{repo}
    - Contribution Guidelines: {contribution_guidelines}
    - Current PR Description: {pr_description}
    - Diff of the PR:
    {diff}

    Respond ONLY in markdown format. Do not include JSON or any extra text.
    """

    # Call LLM
    llm_response = call_llm(prompt)

    return llm_response

def tests_presence(owner, repo, issue_number, contribution_guidelines, diff):
    """
    Checks whether tests are present in the PR, if the contribution guidelines
    recommend tests, and if the PR itself suggests testing is required.
    Generates a markdown with:
      - Status of automated tests
      - Recommendations for additional tests
      - Instructions for manual testing if needed
    """
    import os

    # Read PR choice
    pr_choice_file = os.path.join("data", owner, repo, str(issue_number), "pr_choice.txt")
    if not os.path.exists(pr_choice_file):
        return "PR choice not found. User must select a PR plan first."

    with open(pr_choice_file, "r", encoding="utf-8") as f:
        pr_choice_text = f.read().strip()

    # Extract the PR title and description from the text
    pr_title = ""
    pr_description = ""
    lines = pr_choice_text.split("\n")
    for line in lines:
        if line.lower().startswith("pr title:"):
            pr_title = line[len("pr title:"):].strip()
        elif line.lower().startswith("pr description:"):
            pr_description = line[len("pr description:"):].strip()

    prompt = f"""
    You are an expert open-source assistant.

    Task:
    Review the following pull request diff, the PR title, and PR description.
    Check whether:
    1. The PR includes automated tests.
    2. Contribution guidelines mention testing requirements.
    3. The PR title or description implies that testing is required.

    Then:
    - Suggest any additional automated tests that should be added.
    - Provide instructions for manual testing if necessary.
    - Provide your response in markdown format.

    Inputs:
    - Repository: {owner}/{repo}
    - Contribution Guidelines: {contribution_guidelines}
    - PR Title: {pr_title}
    - PR Description: {pr_description}
    - Diff of the PR:
    {diff}

    Output format:
    - Status of automated tests: ...
    - Required tests from contribution guidelines: ...
    - Additional automated tests: ...
    - Manual testing instructions: ...

    Respond ONLY in markdown format.
    """

    # Call the LLM
    llm_response = call_llm(prompt)
    return llm_response


# Bulk call several prompts to generate different checklist for each guidebook heading
def call_llm(prompt):
    response  = model.generate_content(prompt)
    if response:
        return response.text
    else:
        return None