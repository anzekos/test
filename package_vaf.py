import os
import zipfile

def package_vaf():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vaf_dir = os.path.join(base_dir, "vaf_app")
    
    # Check both Release and Debug for DLLs (prefer Release)
    bin_release = os.path.join(vaf_dir, "bin", "Release", "net472")
    bin_debug = os.path.join(vaf_dir, "bin", "Debug", "net472")
    
    source_dir = bin_release if os.path.exists(bin_release) else bin_debug
    
    if not os.path.exists(source_dir):
        print(f"Error: Could not find build output. Please run 'build_vaf.py' or build in VS first.")
        return

    output_mfappx = os.path.join(base_dir, "AILegalAssistant.VAF.mfappx")
    appdef = os.path.join(vaf_dir, "appdef.xml")

    print(f"Packaging from {source_dir}...")
    
    with zipfile.ZipFile(output_mfappx, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add appdef.xml (at root)
        if os.path.exists(appdef):
            zipf.write(appdef, "appdef.xml")
            print("Added appdef.xml")
        else:
            print("Error: appdef.xml not found in vaf_app folder!")
            return

        # 2. Add DLLs
        for file in os.listdir(source_dir):
            if file.endswith(".dll"):
                file_path = os.path.join(source_dir, file)
                zipf.write(file_path, file)
                print(f"Added {file}")

    print(f"\\nSuccessfully packaged {output_mfappx}")

if __name__ == "__main__":
    package_vaf()
