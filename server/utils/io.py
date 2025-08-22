import os
from flask import jsonify

BASE_DIR = "data"

def write_issue_files(owner, repo, issue_number, title, body, repo_description, contribution_guidelines):
    path = os.path.join(BASE_DIR, owner, repo, str(issue_number))
    os.makedirs(path, exist_ok=True)

    # Write issue info to their respective files
    with open(os.path.join(path, "title.txt"), "w") as f:
        f.write(title)

    with open(os.path.join(path, "body.txt"), "w") as f:
        f.write(body)

    with open(os.path.join(path, "repo_description.txt"), "w") as f:
        f.write(repo_description)

    # TODO: Find contributing.md for the repo, and the related files 
    with open(os.path.join(path, "contribution_guidelines.txt"), "w") as f:
        f.write(contribution_guidelines)
    
    return {
        "Done"
    }

def read_issue_files(owner, repo, issue_number):
    base_path = os.path.join(BASE_DIR, owner, repo, issue_number)
    if not os.path.exists(base_path):
        return jsonify({"error": "Issue data not found, run generate_guidebook first"}), 400

    with open(os.path.join(base_path, "title.txt")) as f:
        title = f.read()
    with open(os.path.join(base_path, "body.txt")) as f:
        body = f.read()
    with open(os.path.join(base_path, "repo_description.txt")) as f:
        repo_description = f.read()
    with open(os.path.join(base_path, "contribution_guidelines.txt")) as f:
        contribution_guidelines = f.read()
    
    return {
        "title": title,
        "body" : body,
        "repo_description": repo_description,
        "contribution_guidelines": contribution_guidelines
    }
