import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.guidebook import classify_issue, verify_feature_uniqueness, check_issue_alignment_with_vision, check_issue_scope, understand_relevant_contribution_guidelines, generate_steps, explain_tests
from utils.scraping import fetch_issue, clean_issue_info, get_diff, detect_duplicates
from utils.io import read_issue_files

app = Flask(__name__)
CORS(app)

@app.route('/api/time')
def get_current_time():
    return {'time': time.time()}

@app.route('/api/generate_guidebook', methods=['POST'])
def generate_guidebook():
    issueUrl = request.get_json()
    # use the issue url, to fetch repo information, issue information, and other required information...
    # https://github.com/jax-ml/jax/issues/30787
    fetched_issue_information = fetch_issue(issueUrl["issueUrl"])
    print("Fetched the issue")
    if not fetched_issue_information:
        return jsonify({"error": "Failed to fetch issue information"}), 400
    # Clean the fetched information to get the important parts to it.
    useful_issue_info = clean_issue_info(fetched_issue_information)
    return useful_issue_info

@app.route('/api/getting_started_guide', methods=['POST'])
def getting_started():
    issue_info = request.get_json()
    owner = issue_info['repo_author']
    repo = issue_info['repo_name']
    issue_number = issue_info['issue_number']
    issue_files = read_issue_files(owner, repo, issue_number)

    title = issue_files["title"]
    body = issue_files["body"]
    repo_description = issue_files["repo_description"]
    contribution_guidelines = issue_files["contribution_guidelines"]

    # === Subtasks =====
    results = {}
    issue_duplicates = detect_duplicates(owner, repo, title)
    results["issue_duplicates"] = issue_duplicates
    issue_type = classify_issue(title, body)
    feature_uniqueness = verify_feature_uniqueness(owner, repo, title, body, issue_type)
    results["feature_uniqueness"] = feature_uniqueness
    align_with_project_vision = check_issue_alignment_with_vision(repo_description, title, body, contribution_guidelines, issue_type)
    results["align_with_project_vision"] = align_with_project_vision
    tune_contribution_guidelines = understand_relevant_contribution_guidelines(owner, repo, title, body, contribution_guidelines)
    results["tune_contribution_guidelines"] = tune_contribution_guidelines
    issue_scope = check_issue_scope(repo_description, title, body, contribution_guidelines, issue_type, issue_number)
    results["issue_scope"] = issue_scope
    print(results)
    return jsonify(results)

@app.route('/api/implementation_guide', methods=['POST'])
def implementation():
    issue_info = request.get_json()
    owner = issue_info['repo_author']
    repo = issue_info['repo_name']
    issue_number = issue_info['issue_number']
    suggestion_level = issue_info.get('suggestion_level', 3)
    pr_title = issue_info.get('prTitle', '')
    pr_description = issue_info.get('prDescription', '')

    # Save PR choice to pr_choice.txt
    pr_choice_path = f"data/{owner}/{repo}/{issue_number}/pr_choice.txt"
    os.makedirs(os.path.dirname(pr_choice_path), exist_ok=True)
    with open(pr_choice_path, 'w', encoding='utf-8') as f:
        f.write(f"PR Title: {pr_title}\nPR Description: {pr_description}")

    issue_files = read_issue_files(owner, repo, issue_number)
    title = issue_files["title"]
    body = issue_files["body"]
    repo_description = issue_files["repo_description"]
    contribution_guidelines = issue_files["contribution_guidelines"]

    # === Subtasks ===
    results = {}
    results["steps"] = generate_steps(
        owner, repo, title, issue_number, body, repo_description, contribution_guidelines,
        pr_title, pr_description, suggestion_level
    )
    results["tests"] = explain_tests(
        owner, repo, title, issue_number, body, repo_description, contribution_guidelines,
        pr_title, pr_description, suggestion_level
    )

    return jsonify(results)

@app.route('/api/automate_PR_review', methods=['POST'])
def automate_PR_review():
    issue_info = request.get_json()
    owner = issue_info['repo_author']
    repo = issue_info['repo_name']
    issue_number = issue_info['issue_number']
    pr_url = issue_info['pr_url']

    issue_files = read_issue_files(owner, repo, issue_number)

    title = issue_files["title"]
    body = issue_files["body"]
    repo_description = issue_files["repo_description"]
    contribution_guidelines = issue_files["contribution_guidelines"]

    # TODO: fetch PR data - especially PR patch and then evaluate technical design alignment
    # https://github.com/jax-ml/jax/pull/31251
    # https://api.github.com/repos/jax-ml/jax/pulls/31251
    pr_number = pr_url.rstrip('/').split('/')[-1]
    dir_path = os.path.join("data", owner, repo, issue_number)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, "pr_number.txt")
    with open(file_path, "w") as f:
        f.write(str(pr_number))

    print(f"PR number {pr_number} written to {file_path}")

    # Firstly extract the patch body, then pass it 
    diff = get_diff(owner, repo, pr_number)

    # === Subtasks ===
    results = {}
    results["validate_issue_resolution"] = validate_issue_resolution(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, diff)
    results["enforce_contribution_guidelines"] = enforce_contribution_guidelines(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, diff)
    # All of the following enforcement of contribution guidelines must happen in a single conversation state
        # technical_design_alignment
        # match_project_code_style
        # language_specific_best_practices
        # possible_performance_issues
        # high_source_code_quality
        # commit_quality_standards
    results["clear_pr_description"] = clear_pr_description(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, diff)
    results["tests_presence"] = tests_presence(owner, repo, title, issue_number, body, repo_description, contribution_guidelines, diff)

    return jsonify(results)



# This changes things a little. It is because, now what I want to do is this. Instead of asking the LLM to suggest how to solve the issue in the generate_steps step. I want to ask the user to choose which issue they want to solve in the check_issue_scope. Their choice should then be prepended to the /api/implementation_guide. 
