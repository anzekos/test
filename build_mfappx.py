import os
import zipfile

def build_mfappx():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(base_dir, "frontend")
    output_zip = os.path.join(base_dir, "MFilesAILegalAssistant.mfappx")
    
    if not os.path.exists(frontend_dir):
        print(f"Error: Directory {frontend_dir} does not exist.")
        return

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(frontend_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Compute relative path to store in zip
                arcname = os.path.relpath(file_path, frontend_dir)
                zipf.write(file_path, arcname)
                print(f"Added {arcname}")
                
    print(f"\\nSuccessfully built {output_zip}")

if __name__ == "__main__":
    build_mfappx()
