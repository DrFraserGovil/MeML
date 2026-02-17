from jinja2 import Environment, FunctionLoader, FileSystemLoader
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
import os
import meml.util
# Get the absolute path to the directory containing THIS file
_PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))

# Point to the templates folder (assuming it sits inside the 'meml' package)
_TEMPLATE_PATH = os.path.join(_PACKAGE_ROOT, 'templates')
# This environment is tuned for plain text generation
mtg_env = Environment(
    trim_blocks=True,      # Removes the newline after a block tag
    lstrip_blocks=True,    # Removes leading whitespace before a block tag
    # keep_trailing_newline=True,
    loader = FileSystemLoader(_TEMPLATE_PATH),
    block_start_string = '\\BLOCK{',
    block_end_string = '}',
    variable_start_string = '\\VAR{',
    variable_end_string = '}',
    comment_start_string = '\\#{',
    comment_end_string = '}',
    line_statement_prefix = '%%',
    line_comment_prefix = '%#',
)


def ToMeML(meeting,filepath):
    template = mtg_env.get_template("rewrite.mtg.jinja")

    render_vars = {
        "meeting": meeting,
        "attending_list": "\n\t\t".join([p.Rewrite() for p in meeting.Members.Members if p.Invited]),
        "extra_list": "\n\t".join([p.Rewrite() for p in meeting.Members.Members if not p.Invited and p.IsPresent]),
        "mention_list": "\n\t".join([p.Rewrite() for p in meeting.Members.Members if not p.Invited and not p.IsPresent]),
        "absent_list": "\n\t".join([
            f"{p.Key}" + (f"{p.gap}({p.SicknessReason})" if p.SicknessReason else "")
            for p in meeting.Members.Members if p.Sick
            ]),
        "topics": meeting.Topics
        
    }

    text = template.render(**render_vars)
    if text:
        with open(filepath,"w") as path:
            path.write(text)
    # print(template.render(**render_vars))

def ToTex(meeting,mode,filename="test",output=None):
    if mode == "agenda":
        template = mtg_env.get_template("agenda.tex.jinja")
    elif mode == "chair":
        template = mtg_env.get_template("chair.tex.jinja")
    elif mode == "notes":
        template = mtg_env.get_template("notes.tex.jinja")
    render_vars = {
        "meeting": meeting,
        "date" : meeting.Date.Format() if meeting.Date else None,
        "invite" : ", ".join([f"\\person{{{p.FullName}}}" for p in meeting.Members.Members if p.Invited]),
        "topics": meeting.Topics,
        "action_list": meeting.GetActions(),
        "decide_list": meeting.Get("decision"),
        "question_list": meeting.Get("question"),
        "summary": meeting.GetSummary(),
        "attend" : ", ".join([f"\\person{{{p.FullName}}}" for p in meeting.Members.Members if p.Invited and not p.Sick]),
        "absent" : ", ".join([f"\\person{{{p.SickName()}}}" for p in meeting.Members.Members if p.Sick]),
        "extra" : ", ".join([f"\\person{{{p.FullName}}}" for p in meeting.Members.Members if not p.Invited and p.IsPresent]),
        "mentioned" : ", ".join([f"\\person{{{p.FullName}}}" for p in meeting.Members.Members if not p.Invited and not p.IsPresent]),
    }
    pre = ""
    if mode == "agenda":
        pre = "_agenda"
    elif mode == "notes":
        pre = "_minutes"
    elif mode== "chair":
        pre = "_chair"
    code = meeting.Members.ResolveNames(template.render(**render_vars))
    path = Path(filename)
    job_name = f"{path.stem}{pre}"

    if output is None:
        final_pdf_path = path.parent / f"{job_name}.pdf"
    else:
        outpath = Path(output)
        
        # Check if the user intends this to be a directory:
        # 1. It already exists as a dir
        # 2. OR the string ends with a slash (output.endswith('/') or output.endswith('\\'))
        # 3. OR it has no file extension (e.g., 'pdf/tmp' vs 'pdf/tmp.pdf')
        is_intended_dir = outpath.is_dir() or output.endswith(('/', '\\')) or not outpath.suffix
        
        if is_intended_dir:
            # Ensure the directory structure exists (e.g., creating pdf/tmp/)
            outpath.mkdir(parents=True, exist_ok=True)
            final_pdf_path = outpath / f"{job_name}.pdf"
        else:
            # It's a specific filename. Ensure its parent directory exists.
            outpath.parent.mkdir(parents=True, exist_ok=True)
            final_pdf_path = outpath
    # Just the string name for LaTeX to use inside the temp folder
    print(f"Writing output to {final_pdf_path}")
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "main.tex")
        
        with open(tex_path, "w") as f:
            f.write(code)

        # Run pdflatex - jobname is JUST the string, no path
        process = subprocess.run(
            ['pdflatex', f'-jobname={job_name}', '-interaction=nonstopmode', 'main.tex'],
            cwd=tmpdir,
            capture_output=True,
            text=True
        )
        if process.returncode == 0:
            # Move the resulting PDF from the temp folder to your actual destination
            temp_pdf = Path(tmpdir) / f"{job_name}.pdf"
            temp_pdf.replace(final_pdf_path)
        else:
            print(f"LaTeX Error:\n{process.stdout}")
            # Optionally keep the log for debugging
            print(f"Check the logs in {tmpdir} if needed (though it will be deleted now).")
