import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('meml.smartEnter', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const doc = editor.document;
    const pos = editor.selection.active;
    const line = doc.lineAt(pos.line).text;

    const exitRegex = /^\s*[*!>+#$?]\s*$/;

    if (exitRegex.test(line)) {
      await editor.edit((editBuilder: vscode.TextEditorEdit) => {
        const start = new vscode.Position(pos.line, line.search(/\S/));
        const end = new vscode.Position(pos.line, line.length);
        editBuilder.delete(new vscode.Range(start, end));
      });
    } else {
      await vscode.commands.executeCommand('type', { text: '\n' });
    }
  });

  context.subscriptions.push(disposable);
}

export function deactivate() {}
