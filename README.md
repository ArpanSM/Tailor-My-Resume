# Tailor My Resume

This project uses LangGraph to create a multi-stage pipeline that automatically generates a tailored resume PDF based on a specific job description, your detailed professional information, custom rules, and a LaTeX template.

## Features

*   **LangGraph Pipeline:** Orchestrates the resume generation process through defined steps.
*   **LLM Integration:** Leverages Large Language Models (specifically via LiteLLM/Gemini in the current implementation) for:
    *   Generating a draft resume tailored to the job description.
    *   Converting the draft content into LaTeX format using a provided template.
*   **LaTeX to PDF Conversion:** Compiles the generated LaTeX code into a professional PDF document using `pdflatex`.
*   **Input Driven:** Takes the following as input:
    *   `job-Description.txt`: The target job description.
    *   `resume-Desc.txt`: Your comprehensive base resume details.
    *   `projects-Desc.txt`: Detailed descriptions of your projects.
    *   `rules.txt`: Custom rules for formatting, tone, or content inclusion.
    *   `latex_template.tex`: A LaTeX file serving as the resume template.
*   **Timestamped Output:** Saves the final PDF with an epoch timestamp in the filename (e.g., `tailored_resume_1700000000.pdf`).

## Workflow

The process is orchestrated by the `resume_graph.py` script using LangGraph:

1.  **Load Inputs:** Reads the job description, resume details, project details, rules, and LaTeX template from the `input/` directory.
2.  **Generate Draft Resume (`generate_draft` node):**
    *   Sends the job description, resume, projects, and rules to an LLM.
    *   The LLM generates a draft focusing on relevant experience and projects, adhering to the rules.
    *   (Includes a refinement step asking the LLM to review the draft against the rules).
3.  **Convert to LaTeX (`convert_latex` node):**
    *   Sends the generated draft and the LaTeX template to an LLM.
    *   The LLM populates the template with the draft content, producing valid LaTeX code.
4.  **Convert to PDF (`convert_pdf` node):**
    *   Saves the generated LaTeX code to a temporary `.tex` file.
    *   Runs `pdflatex` (requires a LaTeX distribution installed) twice to compile the `.tex` file into a PDF.
    *   Cleans up intermediate files (`.tex`, `.aux`, `.log`).
5.  **Output:** The final, timestamped PDF is saved in the `output/` directory.

## Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd Tailor-My-Resume
    ```
2.  **Python Environment:**
    *   Ensure you have Python 3.9+ installed.
    *   It's recommended to use a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
3.  **Install Dependencies:**
    *   You'll need `langgraph` and potentially `litellm` or other libraries used by `utils.call_litellm`. Create a `requirements.txt` file with:
        ```txt
        langgraph
        litellm # Or other necessary LLM client libraries
        # Add any other dependencies
        ```
    *   Install them:
        ```bash
        pip install -r requirements.txt
        ```
4.  **Install LaTeX:**
    *   You **must** have a working LaTeX distribution installed that provides the `pdflatex` command.
    *   **Windows:** [MiKTeX](https://miktex.org/download)
    *   **macOS:** [MacTeX](https://tug.org/mactex/)
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install texlive-latex-base texlive-latex-recommended texlive-fonts-recommended`
    *   Ensure `pdflatex` is added to your system's PATH.
5.  **Environment Variables:**
    *   If your LLM calls (within `utils.call_litellm`) require API keys (e.g., `GEMINI_API_KEY`), make sure they are set as environment variables.

## Usage

1.  **Prepare Input Files:**
    *   Create an `input/` directory in the project root.
    *   Place the following files inside `input/` with your content:
        *   `job-Description.txt`
        *   `resume-Desc.txt`
        *   `projects-Desc.txt`
        *   `rules.txt`
        *   `latex_template.tex` (Make sure this is a valid LaTeX document structure).
2.  **Run the Script:**
    ```bash
    python resume_graph.py
    ```
3.  **Check Output:**
    *   The script will print progress messages for each step.
    *   Upon successful completion, a timestamped PDF file will be generated in the `output/` directory.
    *   Intermediate files (`draft-Resume.txt`, `latex_output.tex`) might also be saved in `output/` depending on the current script version.

## TODO / Potential Improvements

*   Refine LLM prompts for better draft quality and LaTeX generation.
*   Implement more robust error handling for LaTeX compilation issues.
*   Add support for different LLM providers easily.
*   Parameterize model names.
*   Create a simple UI (e.g., using Streamlit or Gradio) for easier input management.
*   Add unit and integration tests.
