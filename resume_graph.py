import os
import time  # Add time import
from pathlib import Path # Add pathlib import
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END, START
import subprocess # Add subprocess import

from utils import call_litellm

# --- State Definition ---

class ResumeGenerationState(TypedDict):
    """
    Represents the state of the resume generation graph.
    """
    job_description: str
    detailed_resume: str
    detailed_projects: str
    rules: str
    latex_template: str
    draft_resume: str | None  # Generated by the first LLM call
    latex_code: str | None    # Generated by the second LLM call
    pdf_output_path: str | None # Path to the final PDF (or status message)
    error: str | None         # To capture any errors during the process

# --- Node Functions ---

def generate_draft_resume(state: ResumeGenerationState) -> Dict[str, Any]:
    """
    Generates the initial draft resume using an LLM.
    (Placeholder implementation)
    """
    print("--- Generating Draft Resume ---")
    try:
        draft_resume_prompt = f"""
        Job Description:
        {state['job_description']}

        Detailed Resume:
        {state['detailed_resume']}

        Detailed Projects:
        {state['detailed_projects']}

        Rules:
        {state['rules']}

        Task: Based on the job description, detailed resume, detailed projects, and rules provided, generate a tailored resume draft. Focus on highlighting experiences and skills relevant to the job description, adhering strictly to the specified rules for content and style.
        Output:
        - A draft resume section for "Experience" and "Projects"
        - Follow the provided "Rules" for style and formatting
        """        
        # Combine inputs for the prompt
        prompt = draft_resume_prompt.format(state=state)
        print("Prompt for draft generation (truncated):\n", prompt[:500] + "...")

        # chain of density prompt engineering
        message_state = [{"role": "user", "content": prompt}]
        _, draft = call_litellm(model="gemini/gemini-2.0-flash", messages=message_state)
        message_state.append({"role": "assistant", "content": draft})
        message_state.append({"role": "user", "content": "Based on the draft, please re-generate the draft making sure to follow the rules provided."})
        _, draft = call_litellm(model="gemini/gemini-2.0-flash", messages=message_state)
        print("Draft generated successfully.")

        # save draft to a file
        with open("output/draft-Resume.txt", "w") as f:
            f.write(str(draft))
        return {"draft_resume": draft, "error": None}
    except Exception as e:
        print(f"Error in generate_draft_resume: {e}")
        return {"error": f"Failed to generate draft resume: {str(e)}"}

def convert_to_latex(state: ResumeGenerationState) -> Dict[str, Any]:
    """
    Converts the draft resume to LaTeX format using an LLM and a template.
    (Placeholder implementation)
    """
    print("--- Converting Draft to LaTeX ---")
    if state.get("error") or not state.get("draft_resume"):
        print("Skipping LaTeX conversion due to previous error or missing draft.")
        return {} # Pass through the error state

    try:
        draft = state["draft_resume"]
        template = state["latex_template"]
        prompt = f"""
        Draft Resume Content:
        {draft}

        LaTeX Template:
        {template}

        Task: Populate the provided LaTeX template with the draft resume content. Ensure the final output is valid LaTeX code ready for compilation. Place the resume content appropriately within the template structure.
        """
        print("Prompt for LaTeX conversion (truncated):\n", prompt[:500] + "...")

        message_state = [{"role": "user", "content": prompt}]
        _, latex_output = call_litellm(model="gemini/gemini-2.0-flash", messages=message_state)
        print("LaTeX generated successfully.")
        # save latex_output to a file
        with open("output/latex_output.tex", "w") as f:
            f.write(latex_output)
        return {"latex_code": latex_output, "error": None}
    except Exception as e:
        print(f"Error in convert_to_latex: {e}")
        return {"error": f"Failed to convert to LaTeX: {str(e)}"}

def convert_to_pdf(state: ResumeGenerationState) -> Dict[str, Any]:
    """
    Compiles the LaTeX code into a PDF using pdflatex.
    """
    print("--- Converting LaTeX to PDF ---")
    if state.get("error") or not state.get("latex_code"):
        print("Skipping PDF conversion due to previous error or missing LaTeX code.")
        return {} # Pass through the error state

    latex_code = state["latex_code"]
    timestamp = int(time.time())
    base_filename = f"tailored_resume_{timestamp}"
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    tex_filename = f"{base_filename}.tex"
    pdf_filename = f"{base_filename}.pdf"
    aux_filename = f"{base_filename}.aux"
    log_filename = f"{base_filename}.log"

    tex_file_path = output_dir / tex_filename
    pdf_file_path = output_dir / pdf_filename

    try:
        # 1. Save the LaTeX code to a .tex file
        print(f"Saving LaTeX code to {tex_file_path}")
        with open(tex_file_path, "w", encoding='utf-8') as f:
            f.write(latex_code)

        # 2. Run pdflatex command
        cmd = [
            'pdflatex',
            '-interaction=nonstopmode', # Don't stop on errors
            '-output-directory', str(output_dir),
            str(tex_file_path) # Pass the full path to the tex file
        ]

        print(f"Running pdflatex... (command: {' '.join(cmd)})")
        # First run
        result1 = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=output_dir)
        if result1.returncode != 0:
            print(f"Warning: pdflatex first run reported errors/warnings (log: {log_filename})")
            # print(result1.stdout) # Can be very verbose
            # print(result1.stderr)

        # Second run (often needed for references, TOC, etc.)
        print("Running pdflatex a second time...")
        result2 = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=output_dir)
        if result2.returncode != 0 and not pdf_file_path.exists(): # Only fail if PDF doesn't exist after second run
             print(f"Error: pdflatex second run failed and PDF not generated.")
             print("stdout:", result2.stdout)
             print("stderr:", result2.stderr)
             # Attempt to read log file for more detailed errors
             try:
                 log_path = output_dir / log_filename
                 if log_path.exists():
                     print(f"\n--- pdflatex Log ({log_path}) --- \n{log_path.read_text()[:1000]}...\n-----------------------------")
             except Exception as log_e:
                 print(f"Could not read log file: {log_e}")
             raise RuntimeError(f"pdflatex execution failed. Check logs in {output_dir}")

        # 3. Check if PDF was created
        if pdf_file_path.is_file():
            print(f"Successfully created PDF: {pdf_file_path}")
            return {"pdf_output_path": str(pdf_file_path), "error": None}
        else:
            print(f"Error: PDF file {pdf_file_path} not found after running pdflatex.")
            # Attempt to read log file for more detailed errors
            try:
                log_path = output_dir / log_filename
                if log_path.exists():
                    print(f"\n--- pdflatex Log ({log_path}) ---\n{log_path.read_text()[:1000]}...\n-----------------------------")
            except Exception as log_e:
                 print(f"Could not read log file: {log_e}")
            return {"error": f"PDF generation failed. Check logs in {output_dir}. stdout: {result2.stdout}"}

    except FileNotFoundError:
         print("Error: 'pdflatex' command not found.")
         print("Please ensure a LaTeX distribution (like MiKTeX or TeX Live) is installed and in your system's PATH.")
         return {"error": "pdflatex not found. Install LaTeX distribution."}
    except Exception as e:
        print(f"An unexpected error occurred during PDF conversion: {e}")
        return {"error": f"Failed to generate PDF: {str(e)}"}
    finally:
        # 4. Clean up temporary files
        print("Cleaning up auxiliary files...")
        for filename in [tex_filename, aux_filename, log_filename]:
            try:
                file_to_delete = output_dir / filename
                if file_to_delete.exists():
                    file_to_delete.unlink()
            except OSError as e:
                print(f"Warning: Could not delete temporary file {filename}: {e}")

# --- Graph Definition ---

workflow = StateGraph(ResumeGenerationState)

# Add nodes
workflow.add_node("generate_draft", generate_draft_resume)
workflow.add_node("convert_latex", convert_to_latex)
workflow.add_node("convert_pdf", convert_to_pdf)

# Define edges
workflow.add_edge(START, "generate_draft")
workflow.add_edge("generate_draft", "convert_latex")
workflow.add_edge("convert_latex", "convert_pdf")
workflow.add_edge("convert_pdf", END)

# Compile the graph
app = workflow.compile()

# --- Execution Example ---

if __name__ == "__main__":
    # --- Input Loading ---
    input_dir = Path(__file__).parent / "input" # Assumes 'input' is in the same dir as the script
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    required_files = {
        "job_description": "job-Description.txt",
        "detailed_resume": "resume-Desc.txt",
        "detailed_projects": "projects-Desc.txt",
        "rules": "rules.txt",
        "latex_template": "latex_template.tex",
    }
    input_data = {}
    errors = []

    print(f"--- Loading Input Files from: {input_dir} ---")
    for key, filename in required_files.items():
        file_path = input_dir / filename
        try:
            input_data[key] = file_path.read_text(encoding='utf-8')
            print(f"Successfully loaded: {filename}")
        except FileNotFoundError:
            errors.append(f"Error: Input file not found: {file_path}")
            print(f"Error: Input file not found: {file_path}")
        except Exception as e:
            errors.append(f"Error reading file {file_path}: {e}")
            print(f"Error reading file {file_path}: {e}")

    if errors:
        print("\nErrors encountered loading input files. Exiting.")
        exit(1)

    # --- Graph Execution ---
    initial_state = ResumeGenerationState(
        job_description=input_data["job_description"],
        detailed_resume=input_data["detailed_resume"],
        detailed_projects=input_data["detailed_projects"],
        rules=input_data["rules"],
        latex_template=input_data["latex_template"],
        draft_resume=None,
        latex_code=None,
        pdf_output_path=None,
        error=None,
    )

    print("--- Starting Resume Generation Graph ---")
    final_state = app.invoke(initial_state)

    print("\n--- Final State ---")
    if final_state.get("error"):
        print("Graph finished with an error:")
        print(final_state["error"])
    else:
        print("Graph finished successfully.")
        # print("Draft Resume:", final_state.get("draft_resume")) # Can be long
        # print("LaTeX Code:", final_state.get("latex_code"))     # Can be long
        print("PDF Output Status:", final_state.get("pdf_output_path")) 