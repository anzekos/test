import os
import subprocess
import zipfile
import shutil

def build_vaf():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    vaf_dir = os.path.join(base_dir, "vaf_app")
    proj_path = os.path.join(vaf_dir, "AILegalAssistant.VAF.csproj")
    output_mfappx = os.path.join(base_dir, "AILegalAssistant.VAF.mfappx")
    bin_dir = os.path.join(vaf_dir, "bin", "Release")

    print("Checking for MSBuild...")
    msbuild_exe = None
    
    # 1. Try vswhere.exe (official tool)
    vswhere = r"C:\\Program Files (x86)\\Microsoft Visual Studio\\Installer\\vswhere.exe"
    if os.path.exists(vswhere):
        try:
            result = subprocess.run([vswhere, "-latest", "-requires", "Microsoft.Component.MSBuild", "-find", "MSBuild\\**\\Bin\\MSBuild.exe"], capture_output=True, text=True)
            if result.stdout.strip():
                msb = result.stdout.strip().split('\n')[0]
                if os.path.exists(msb):
                    msbuild_exe = msb
        except Exception as e:
            print(f"vswhere failed: {e}")

    # 2. Hardcoded fallback paths
    if not msbuild_exe:
        msbuild_paths = [
            r"C:\\Program Files\\Microsoft Visual Studio\\2026\\Professional\\MSBuild\\Current\\Bin\\MSBuild.exe",
            r"C:\\Program Files\\Microsoft Visual Studio\\2026\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe",
            r"C:\\Program Files\\Microsoft Visual Studio\\2026\\Enterprise\\MSBuild\\Current\\Bin\\MSBuild.exe",
            r"C:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\MSBuild\\Current\\Bin\\MSBuild.exe",
            r"C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe",
            r"C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Professional\\MSBuild\\Current\\Bin\\MSBuild.exe",
            r"C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe",
            "msbuild"
        ]
        for path in msbuild_paths:
            try:
                subprocess.run([path, "-version"], capture_output=True)
                msbuild_exe = path
                break
            except:
                continue

    if not msbuild_exe:
        print("Error: MSBuild.exe not found. Please install Visual Studio or MS Build Tools.")
        return

    print(f"Building project using {msbuild_exe}...")
    try:
        subprocess.run([msbuild_exe, proj_path, "/p:Configuration=Release", "/t:Rebuild"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return

    print("Packaging .mfappx...")
    if not os.path.exists(bin_dir):
        print(f"Error: Build output directory {bin_dir} not found.")
        return

    with zipfile.ZipFile(output_mfappx, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add appdef.xml (MUST be at the root)
        appdef = os.path.join(vaf_dir, "appdef.xml")
        if os.path.exists(appdef):
            zipf.write(appdef, "appdef.xml")
        
        # 2. Add DLLs from bin/Release
        for file in os.listdir(bin_dir):
            if file.endswith(".dll"):
                zipf.write(os.path.join(bin_dir, file), file)
                print(f"Added {file}")

    print(f"\\nSuccessfully built {output_mfappx}")

if __name__ == "__main__":
    build_vaf()
