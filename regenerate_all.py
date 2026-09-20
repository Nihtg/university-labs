import os
import subprocess
import glob
import shutil

repo_dir = r"c:\Users\Слава\Documents\university-labs"
desktop_dir = r"C:\Users\Слава\Desktop\Все_Конспекты_Универ"

# find all markdown files recursively, ignore exam-prep, venv, node_modules, README
md_files = []
for root, dirs, files in os.walk(repo_dir):
    if any(ignore in root for ignore in ['exam-prep', 'venv', 'node_modules', '.git']):
        continue
    for file in files:
        if file.endswith(".md") and not file.lower() == "readme.md":
            md_files.append(os.path.join(root, file))

for md_path in md_files:
    pdf_path = md_path[:-3] + ".pdf"
    print(f"Converting {md_path} -> {pdf_path}")
    
    # Run the PDF conversion
    subprocess.run(["python", os.path.join(repo_dir, "md_to_pdf.py"), md_path, pdf_path])
    
    # Copy to desktop
    subject_dir = os.path.basename(os.path.dirname(os.path.dirname(md_path)))
    filename = os.path.basename(pdf_path)
    new_filename = f"{subject_dir}_{filename}"
    dest_path = os.path.join(desktop_dir, new_filename)
    
    shutil.copy2(pdf_path, dest_path)
    print(f"Copied to {dest_path}")

print("All done!")
