import * as vscode from 'vscode';
import * as path from 'path';
import { exec } from 'child_process';

const outputChannel = vscode.window.createOutputChannel("MeML Build");
let myStatusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext) {
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

        outputChannel.clear();
        outputChannel.appendLine(`[${new Date().toLocaleTimeString()}] Starting MeML build in ${mode} mode...`);
        // outputChannel.show(true); // Show the panel but don't steal focus

        const fullCmd = `mkdir -p "${outDir}"; memlmake "${filePath}" ${flags[mode]} -o "${outDir}/"`;

// Use /bin/bash explicitly to avoid shell-specific quirks
const shellCmd = `bash -c '${fullCmd}'`;

const process = exec(shellCmd);

process.stdout?.on('data', (data) => {
    outputChannel.append(data.toString());
});

process.stderr?.on('data', (data) => {
    // Some compilers send warnings to stderr; we'll log them as-is
    outputChannel.append(data.toString());
});

process.on('close', async (code) => {
    if (code === 0) {
        outputChannel.appendLine(`\n[SUCCESS] Build finished.`);
        vscode.window.setStatusBarMessage(`MeML: Build Successful`, 4000);

        const pdfUri = vscode.Uri.file(pdfPath);
        await vscode.commands.executeCommand('vscode.open', pdfUri, {
            viewColumn: vscode.ViewColumn.Beside,
            preserveFocus: true
        });
    } else {
        outputChannel.appendLine(`\n[FAILED] Build exited with code ${code}.`);
        vscode.window.showErrorMessage("MeML build failed. Check Output tab.");
        outputChannel.show(); // Bring to front so you can see the error
    }
});
    });

    context.subscriptions.push(selectMode, buildDoc);

    context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
        if (document.languageId === 'meml') {
            const config = vscode.workspace.getConfiguration('meml');
            const buildOnSave = config.get<boolean>('buildOnSave');

            if (buildOnSave) {
                vscode.commands.executeCommand('meml.build');
            }
        }
    })
);
}

export function deactivate() {}