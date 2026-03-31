import os
import zipfile
import shutil

# KONFIGURACIJA
MFAPPX = "AILegalAssistant.VAF.mfappx"
VAF_DIR = os.path.join("vaf_app", "bin")

CORRECT_APPDEF = '''<?xml version="1.0" encoding="utf-8" ?>
<application
    type="server-application"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:noNamespaceSchemaLocation="http://www.m-files.com/schemas/appdef-server-v2.xsd">
    <guid>0B3E8C11-9A22-4D93-9F9B-B12345678912</guid>
    <name>AI Legal Assistant Server-Side</name>
    <description>M-Files VAF Configuration for AI Colleagues</description>
    <publisher>Antigravity</publisher>
    <version>1.3.0.0</version>
    <copyright>Antigravity 2026</copyright>
    <required-m-files-version>21.0.0.0</required-m-files-version>
    <extension-objects>
        <extension-object>
            <name>AILegalAssistant.VaultApplication</name>
            <assembly>AILegalAssistant.VAF.dll</assembly>
            <class>AILegalAssistant.VaultApplication</class>
        </extension-object>
    </extension-objects>
    <!-- ✅ Dodamo eksplicitno definicijo razširitvenih metod -->
    <extension-methods>
        <extension-method>
            <name>GetAISodelavci</name>
            <extension-object>AILegalAssistant.VaultApplication</extension-object>
        </extension-method>
        <!-- Če uporabljate tudi CreateAISodelavec, ga dodajte -->
        <extension-method>
            <name>CreateAISodelavec</name>
            <extension-object>AILegalAssistant.VaultApplication</extension-object>
        </extension-method>
    </extension-methods>
</application>'''

def rebuild_mfappx():
    base_dir = os.getcwd()
    vaf_dir = os.path.join(base_dir, "vaf_app")
    
    # 1. Poiščemo DLL-je (prioriteta Release)
    source_dir = ""
    for config in ["Release", "Debug"]:
        path = os.path.join(vaf_dir, "bin", config, "net472")
        if os.path.exists(path) and any(f.endswith(".dll") for f in os.listdir(path)):
            source_dir = path
            break
            
    if not source_dir:
        print("[!] Build direktorij ni najden! Najprej zgradi projekt v VS.")
        return

    print(f"=== Gradim nov {MFAPPX} iz {source_dir} ===")
    
    # Backup
    if os.path.exists(MFAPPX):
        shutil.copy2(MFAPPX, MFAPPX + ".bak")

    with zipfile.ZipFile(MFAPPX, 'w', zipfile.ZIP_DEFLATED) as z:
        # Appdef
        z.writestr("appdef.xml", CORRECT_APPDEF.encode("utf-8"))
        print("  + appdef.xml (type=server-application, GUID ...912)")
        
        # DLLs
        for f in os.listdir(source_dir):
            if f.endswith(".dll"):
                z.write(os.path.join(source_dir, f), f)
                print(f"  + {f}")
            elif os.path.isdir(os.path.join(source_dir, f)):
                # Resource subfolders (fi, fr...)
                sub = os.path.join(source_dir, f)
                for sf in os.listdir(sub):
                    if sf.endswith(".dll"):
                        z.write(os.path.join(sub, sf), os.path.join(f, sf))
                        print(f"  + {f}/{sf}")

    print(f"\n[OK] {MFAPPX} je pripravljen.")

if __name__ == "__main__":
    rebuild_mfappx()