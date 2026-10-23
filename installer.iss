; installer.iss — скрипт установщика для Дэна
; Компилируется через Inno Setup Compiler

#define MyAppName "Дэн"
#define MyAppVersion "2.0"
#define MyAppPublisher "Lazy Fox Games"
#define MyAppExeName "Den.exe"

[Setup]
AppId={{D3N-4S51-ST4N-T2025-DEN00000001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Den
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=DenSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"

[Files]
; Копируем всю папку dist\Den целиком
Source: "dist\Den\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Ярлык в меню Пуск
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"
; Ярлык на рабочем столе (если выбрано)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; После установки — предложить запустить
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent