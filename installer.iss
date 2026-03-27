; Inno Setup Script for FFmpeg Studio
; Builds a standard Windows installer

#define MyAppName "FFmpeg Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Alfonso Cifuentes Alonso"
#define MyAppExeName "FFmpegStudio.exe"
#define MyAppURL "https://github.com/AlfonsoCifuentes/FFmpegStudio"

[Setup]
AppId={{B3E7F4A2-8C1D-4E6F-A5B9-2D3C7E8F1A4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=C:\Users\Fonnzer\FFmpegStudio\output
OutputBaseFilename=FFmpegStudio_Setup
SetupIconFile=C:\Users\Fonnzer\FFmpegStudio\assets\icon.ico
WizardImageFile=C:\Users\Fonnzer\FFmpegStudio\assets\installer_wizard.bmp
WizardSmallImageFile=C:\Users\Fonnzer\FFmpegStudio\assets\installer_small.bmp
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoCopyright=Copyright (C) 2025-2026 Alfonso Cifuentes Alonso
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\Fonnzer\FFmpegStudio\dist\FFmpegStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
