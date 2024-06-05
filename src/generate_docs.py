import os
import pydoc


def generate_docs(source_dir, docs_dir):
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                module_name = file_path.replace(os.sep, ".").replace(".py", "")

                # Exclude the base directory from the module name

                while module_name.startswith("."):
                    module_name = module_name[1:]

                print(f"Generating docs for {module_name}")

                try:
                    html_doc = pydoc.HTMLDoc().docmodule(pydoc.safeimport(module_name))
                    doc_path = os.path.join(docs_dir, f"{module_name}.html")
                    with open(doc_path, "w", encoding="utf-8") as f:
                        f.write(html_doc)
                except Exception as e:
                    print(f"Failed to generate docs for {module_name}: {e}")


if __name__ == "__main__":
    source_directory = "."
    docs_directory = "./docs"
    generate_docs(source_directory, docs_directory)
