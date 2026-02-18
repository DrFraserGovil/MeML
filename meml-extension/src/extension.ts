import * as vscode from 'vscode';
import * as path from 'path';

let myStatusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
    // --- Existing Smart Enter Command ---
    const smartEnter = vscode.commands.registerCommand('meml.smartEnter', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;
        const doc = editor.document;
        const pos = editor.selection.active;
        const line = doc.lineAt(pos.line).text;
        const exitRegex = /^\s*[*!>+#$?]\s*$/;

        if (exitRegex.test(line)) {
            await editor.edit((editBuilder) => {
                const start = new vscode.Position(pos.line, line.search(/\S/));
                const end = new vscode.Position(pos.line, line.length);
                editBuilder.delete(new vscode.Range(start, end));
            });
        } else {
            await vscode.commands.executeCommand('type', { text: '\n' });
        }
    });
    context.subscriptions.push(smartEnter);

    // 1. Initialize Status Bar
    myStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    myStatusBarItem.command = 'meml.selectMode';
    context.subscriptions.push(myStatusBarItem);

    // 2. Track Mode State
    const getMode = () => context.globalState.get<string>('activeMode') || 'minutes';
    const updateStatusBar = () => {
        const mode = getMode();
        myStatusBarItem.text = `$(settings-gear) MeML: ${mode.toUpperCase()}`;
        myStatusBarItem.show();
    };
    updateStatusBar();

    // 3. Command: Select Mode (QuickPick)
    const selectMode = vscode.commands.registerCommand('meml.selectMode', async () => {
        const result = await vscode.window.showQuickPick(['agenda', 'chair', 'minutes'], {
            placeHolder: 'Select MeML Build Mode',
        });
        if (result) {
            await context.globalState.update('activeMode', result);
            updateStatusBar();
        }
    });

    // 4. Command: Build (The single action)
    const buildDoc = vscode.commands.registerCommand('meml.build', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const mode = getMode();
        const filePath = editor.document.fileName;
        const dirName = path.dirname(filePath);
        const fileNameNoExt = path.basename(filePath, path.extname(filePath));
        
        const config = vscode.workspace.getConfiguration('meml');
        const outDirSetting = config.get<string>('outputPath') || 'compiled_pdfs';
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        const outDir = path.isAbsolute(outDirSetting) ? outDirSetting : 
                     (workspaceFolder ? path.join(workspaceFolder.uri.fsPath, outDirSetting) : path.join(dirName, outDirSetting));

        // Mapping
        const flags: any = { 'agenda': '-a', 'chair': '-c', 'minutes': '-m' };
        const suffix = mode === 'minutes' ? 'minutes' : mode;
        const pdfPath = path.join(outDir, `${fileNameNoExt}_${suffix}.pdf`);

        const cmd = `mkdir -p "${outDir}"; memlmake "${filePath}" ${flags[mode]} -o "${outDir}/" && open "${pdfPath}"`;

        let terminal = vscode.window.terminals.find(t => t.name === 'MeML Build');
        if (!terminal) terminal = vscode.window.createTerminal('MeML Build');
        terminal.show();
        terminal.sendText(cmd);
    });

    context.subscriptions.push(selectMode, buildDoc);
}

export function deactivate() {}