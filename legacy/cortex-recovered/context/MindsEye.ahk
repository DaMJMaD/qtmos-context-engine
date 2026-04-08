; Mind's Eye :: Full Reflection Loop
#Requires AutoHotkey v2.0
#Include "..\shared\QTMoSSharedSync.ahk"

EnvSet("QTMOS_SHARE_DIR", A_ScriptDir "\..\shared\qtmos-share")

; ========== CONFIG ==========
imageDir := ResolveImageDir()
thybodyPath := imageDir "\thybody.txt"
syncChannel := "mindseye"
syncSource := "MindsEye"
lastResult := ""

; ========== STARTUP ==========
InitPulse()
SetTimer(WatchVitals, 1000)

; ========== FUNCTIONS ==========

InitPulse() {
    global thybodyPath
    QTMOS_EnsureParentDir(thybodyPath)
    Try FileDelete(thybodyPath)
    SafeWrite(thybodyPath, "Initializing vitals...")
    PublishMindsEyeSync("Initializing vitals...", "init")
    PulseVitalsOnce()
}

PulseVitalsOnce() {
    CaptureLeaderRegion()
    ParseVitalsFromImage()
}

WatchVitals() {
    global imageDir, lastResult, thybodyPath
    Try {
        newResult := Trim(FileRead(thybodyPath, "UTF-8"))
        if (newResult != "" && newResult != lastResult) {
            ToolTip("❤️ " newResult)
            PublishMindsEyeSync(newResult, "pulse")
            lastResult := newResult
        }
    } Catch {
        ToolTip("❌ Cannot read vitals")
    }
}

SafeWrite(filePath, textToWrite) {
    timestamp := FormatTime("yyyyMMdd-HHmmss")
    backupPath := StrReplace(filePath, ".txt", "_backup_" timestamp ".txt")
    tmpPath := filePath ".tmp"

    QTMOS_EnsureParentDir(filePath)
    Try FileMove(filePath, backupPath, true)
    Try FileDelete(tmpPath)
    FileAppend(textToWrite, tmpPath, "UTF-8-RAW")
    FileMove(tmpPath, filePath, true)

    FileAppend(FormatTime("[yyyy-MM-dd HH:mm:ss] ") "SafeWrite to " filePath " complete.`n", A_ScriptDir "\write_log.txt")
}

ResolveImageDir() {
    candidates := [
        A_ScriptDir "\..\shared\image directory",
        A_ScriptDir "\image directory"
    ]

    for path in candidates {
        if DirExist(path)
            return path
    }

    DirCreate(candidates[1])
    return candidates[1]
}

PublishMindsEyeSync(rawText, stage := "pulse") {
    global imageDir, thybodyPath, syncChannel, syncSource

    payload := BuildVitalsPayload(rawText)
    payload["stage"] := stage
    payload["image_dir"] := imageDir
    payload["thybody_path"] := thybodyPath
    payload["observer"] := "Mind's Eye"

    QTMOS_PublishState(syncChannel, syncSource, "vitals", payload)
}

BuildVitalsPayload(rawText) {
    payload := Map(
        "raw_text", rawText,
        "hp", "",
        "mp", "",
        "condition", ""
    )

    if RegExMatch(rawText, "i)HP:\s*([0-9]+)", &hpMatch)
        payload["hp"] := hpMatch[1] + 0

    if RegExMatch(rawText, "i)MP:\s*([0-9]+)", &mpMatch)
        payload["mp"] := mpMatch[1] + 0

    if RegExMatch(rawText, "i)Condition:\s*([A-Z_ ]+)", &conditionMatch)
        payload["condition"] := Trim(conditionMatch[1])

    return payload
}

; ========== PLACEHOLDER STUBS ==========
CaptureLeaderRegion() {
    ; Stub function – replace with your image capture logic
    MsgBox "[Stub] CaptureLeaderRegion() called"
}

ParseVitalsFromImage() {
    ; Stub function – simulate parsing and write to thybody
    global thybodyPath
    dummyVitals := "HP: 95 | MP: 66 | Condition: STABLE"
    SafeWrite(thybodyPath, dummyVitals)
}
