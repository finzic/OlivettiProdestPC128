const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

function adapterPath(folder) {
  const cfg = vscode.workspace.getConfiguration('pc128', folder);
  const explicit = cfg.get('adapterPath');
  if (explicit) return explicit;
  const folders = folder ? [folder] : (vscode.workspace.workspaceFolders || []);
  for (const f of folders) {
    const p = path.join(f.uri.fsPath, 'tools', 'debugger', 'dap.py');
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function activate(context) {
  context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('pc128', {
    createDebugAdapterDescriptor(session) {
      const script = adapterPath(session.workspaceFolder);
      if (!script) {
        vscode.window.showErrorMessage('PC128: tools/debugger/dap.py not found; set "pc128.adapterPath".');
        return undefined;
      }
      const python = vscode.workspace.getConfiguration('pc128', session.workspaceFolder).get('python') || 'python3';
      return new vscode.DebugAdapterExecutable(python, ['-u', script], { cwd: path.dirname(path.dirname(path.dirname(script))) });
    }
  }));

  context.subscriptions.push(vscode.debug.registerDebugConfigurationProvider('pc128', {
    resolveDebugConfiguration(folder, config) {
      if (!config.type && !config.request && !config.name) {    // F5 without launch.json
        const editor = vscode.window.activeTextEditor;
        if (editor && ['asm6809', 'pc128basic', 'c'].includes(editor.document.languageId)) {
          Object.assign(config, { type: 'pc128', request: 'launch', name: 'PC128: debug current file',
                                  program: '${file}', stopOnEntry: true });
        }
      }
      return config;
    }
  }));
}

function deactivate() {}

module.exports = { activate, deactivate };
