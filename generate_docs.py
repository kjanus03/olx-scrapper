import os
import pydoc
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

def generate_docs(source_dir, docs_dir):
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    # Walk ONLY through the source_dir ('src')
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                file_path = os.path.join(root, file)
                
                rel_path = os.path.relpath(file_path, source_dir)
                module_name = rel_path.replace(os.sep, ".").replace(".py", "")

                print(f"Generating docs for {module_name}...")

                try:
                    html_doc = pydoc.HTMLDoc().docmodule(pydoc.safeimport(module_name))
                    
                    if html_doc:
                        doc_path = os.path.join(docs_dir, f"{module_name}.html")
                        with open(doc_path, "w", encoding="utf-8") as f:
                            f.write(html_doc)
                    else:
                        print(f"  -> Warning: Could not import {module_name}")
                except Exception as e:
                    print(f"  -> Failed to generate docs for {module_name}: {e}")

if __name__ == "__main__":
    source_directory = "src"
    docs_directory = "docs"
    generate_docs(source_directory, docs_directory)