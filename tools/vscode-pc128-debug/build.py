#!/usr/bin/env python3
"""Pack this folder into a .vsix (no node/vsce needed) and optionally install it.

    python3 tools/vscode-pc128-debug/build.py            # build/pc128-debug-<ver>.vsix
    python3 tools/vscode-pc128-debug/build.py --install  # + install into VS Code (WSL server or local)
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FILES = ["package.json", "extension.js", "README.md", "language-configuration.json",
         "language-configuration-basic.json", "syntaxes/asm6809.tmLanguage.json", "syntaxes/pc128basic.tmLanguage.json"]


def build():
    pkg = json.loads((HERE / "package.json").read_text())
    ident = "%s.%s" % (pkg["publisher"], pkg["name"])
    manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<PackageManifest Version="2.0.0" xmlns="http://schemas.microsoft.com/developer/vsx-schema/2011">
  <Metadata>
    <Identity Language="en-US" Id="{pkg['name']}" Version="{pkg['version']}" Publisher="{pkg['publisher']}"/>
    <DisplayName>{pkg['displayName']}</DisplayName>
    <Description xml:space="preserve">{pkg['description']}</Description>
    <Categories>{",".join(pkg['categories'])}</Categories>
    <Properties>
      <Property Id="Microsoft.VisualStudio.Code.Engine" Value="{pkg['engines']['vscode']}"/>
      <Property Id="Microsoft.VisualStudio.Code.ExtensionKind" Value="workspace"/>
    </Properties>
  </Metadata>
  <Installation><InstallationTarget Id="Microsoft.VisualStudio.Code"/></Installation>
  <Dependencies/>
  <Assets>
    <Asset Type="Microsoft.VisualStudio.Code.Manifest" Path="extension/package.json" Addressable="true"/>
    <Asset Type="Microsoft.VisualStudio.Services.Content.Details" Path="extension/README.md" Addressable="true"/>
  </Assets>
</PackageManifest>
"""
    types = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension=".json" ContentType="application/json"/>
  <Default Extension=".js" ContentType="application/javascript"/>
  <Default Extension=".md" ContentType="text/markdown"/>
  <Default Extension=".vsixmanifest" ContentType="text/xml"/>
</Types>
"""
    out = ROOT / "build" / ("%s-%s.vsix" % (pkg["name"], pkg["version"]))
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("extension.vsixmanifest", manifest)
        z.writestr("[Content_Types].xml", types)
        for f in FILES:
            z.write(HERE / f, "extension/" + f)
    print("built", out, "(%s)" % ident)
    return out


def code_cli():
    """Prefer the VS Code server CLI (WSL / remote), so the extension runs where python and MAME are."""
    servers = sorted(glob.glob(os.path.expanduser("~/.vscode-server/bin/*/bin/code-server")), key=os.path.getmtime)
    if servers:
        return [servers[-1]]
    for name in ("code", "code-insiders"):
        if shutil.which(name):
            return [name]
    return None


if __name__ == "__main__":
    vsix = build()
    if "--install" in sys.argv:
        cli = code_cli()
        if not cli:
            sys.exit("VS Code CLI not found; install %s with 'Extensions: Install from VSIX...'" % vsix)
        subprocess.run(cli + ["--install-extension", str(vsix), "--force"], check=True)
        print("installed; run 'Developer: Reload Window' in VS Code")
