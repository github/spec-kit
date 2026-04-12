import os
import json
import argparse
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

def setup_client():
    """
    Initializes the AI client using standard environment variables.
    Defaults to OpenAI, but can be overridden via AI_BASE_URL.
    """
    api_key = os.getenv("AI_API_KEY")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    
    if not api_key:
        raise ValueError("CRITICAL ERROR: AI_API_KEY environment variable is not set.")
        
    return OpenAI(api_key=api_key, base_url=base_url)

def load_project_context(target_dir):
    """
    Aggregates content from all markdown files in the specified directory 
    to provide the LLM with full architectural context.
    """
    context_accumulator = []
    if not os.path.exists(target_dir):
        return None
        
    for filename in os.listdir(target_dir):
        if filename.endswith(".md"):
            file_path = os.path.join(target_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    context_accumulator.append(f"--- FILE: {filename} ---\n{content}")
            except Exception as e:
                print(f"[!] Warning: Could not read {filename}: {e}")
                
    return "\n\n".join(context_accumulator)

def perform_impact_analysis(client, context, change_request, model_id):
    """
    Executes the analysis using the specified LLM and returns a structured JSON report.
    """
    system_prompt = (
        "You are a Senior Systems Architect. Analyze the impact of a proposed change "
        "on the provided technical specifications and output a structured JSON report."
    )
    
    user_prompt = f"""
    ### PROJECT CONTEXT:
    {context}

    ### PROPOSED CHANGE:
    "{change_request}"

    ### OUTPUT REQUIREMENTS:
    Return a JSON object with EXACTLY these keys:
    - complexity_score_diff: (int 1-10)
    - estimated_hours_delta: (str)
    - affected_files: (list of filenames)
    - technical_tasks: (list of strings)
    - architecture_risks: (list of strings)
    - executive_summary: (str)
    """

    try:
        completion = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": str(e)})

def render_architect_report(raw_json):
    """
    Parses and renders the architectural report in a clean, professional format.
    """
    try:
        clean_json = raw_json.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_json)
        
        if "error" in data:
            print(f"[!] Analysis Failed: {data['error']}")
            return

        score = data.get("complexity_score_diff", 0)
        status = "CRITICAL/HIGH" if score >= 7 else "MODERATE" if score >= 4 else "LOW"

        print("\n" + "="*60)
        print(" SYSTEM ARCHITECT IMPACT ANALYSIS")
        print("="*60)
        print(f" IMPACT LEVEL : {status} (Score: {score}/10)")
        print(f" EST. EFFORT  : {data.get('estimated_hours_delta')}")
        
        print(f"\n [ ] TARGETED FILES:")
        for f in data.get('affected_files', []): print(f"     * {f}")
            
        print(f"\n [ ] REQUIRED TASKS:")
        for task in data.get('technical_tasks', []): print(f"     - {task}")
        
        print(f"\n [!] ARCHITECTURAL RISKS:")
        for risk in data.get('architecture_risks', []): print(f"     ! {risk}")

        print(f"\n [*] SUMMARY: {data.get('executive_summary')}")
        print("="*60 + "\n")
        
    except Exception:
        print("[!] Error: Could not parse AI response as valid JSON.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Spec-Kit Architectural Impact Previewer")
    parser.add_argument("--change", required=True, help="Description of the change request")
    parser.add_argument("--model", default=os.getenv("AI_MODEL_ID"), help="Model ID to invoke")
    
    args = parser.parse_args()

    # Dynamic path resolution to ensure it works from root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_presets = os.path.abspath(os.path.join(script_dir, "..", "presets", "lean", "commands"))
    search_path = os.getenv("SPECKIT_PRESETS_DIR", default_presets)

    try:
        ai_client = setup_client()
        project_context = load_project_context(search_path)
        
        if not project_context:
            print(f"[!] Path Error: No specification files found at {search_path}")
        else:
            if not args.model:
                print("[!] Configuration Error: No Model ID provided via --model or AI_MODEL_ID.")
            else:
                print(f"[*] Analyzing global impact for: '{args.change[:50]}...'")
                raw_report = perform_impact_analysis(ai_client, project_context, args.change, args.model)
                render_architect_report(raw_report)
                
    except Exception as error:
        print(f"[!] Runtime Exception: {error}")