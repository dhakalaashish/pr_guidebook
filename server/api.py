import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.guidebook import fetch_issue, clean_issue_info, generate_prompt, call_llm, clean_llm_result

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
    print("Done with useful issue info")
    if not useful_issue_info:
        return jsonify({"error": "Failed to extract useful issue info"}), 400
    # Create a prompt, with the guidelines, "several different prompts"
    prompts = generate_prompt(useful_issue_info)
    print("Done with generating prompt")
    # Bulk call several prompts to generate different checklist for each guidebook heading
    llm_result = call_llm(prompts)
    print("Done with calling LLM")
    print(llm_result)
    # return each of them as a dictionary, such that it is easily readable in the frontend
    json_checklist = clean_llm_result(llm_result)
    print("Done with generating checklist")
    print(json_checklist)
    return json_checklist