#Requires AutoHotkey v2.0
#SingleInstance Force

global sharedRoot := ResolveSharedRoot()
global imageDir := sharedRoot . "\image directory"
global leaderScreenshotPath := imageDir . "\leader_minimap.png"
global GdipToken := 0
global greenMarkers := Map()
global hwndFollowers := []
global Slot1MainPath := "C:\Program Files (x86)\Diablo II Resurrected\D2R.exe"
global Slot2FollowerPath := "C:\Program Files (x86)\Diablo 2 Resurrected\D2R.exe"
global Slot3FollowerPath := "C:\Program Files (x86)\Diablo 2x2 Resurrected\D2R.exe"
global Slot4FollowerPath := "C:\Program Files (x86)\Diablo 2x3 Resurrected\D2R.exe"
global Slot1MainName := "II"
global Slot2FollowerName := "2"
global Slot3FollowerName := "2x2"
global Slot4FollowerName := "2x3"
global SlotOrder := [Slot1MainName, Slot2FollowerName, Slot3FollowerName, Slot4FollowerName]
global leaderPath := Slot1MainPath
global MyName := Slot1MainName





; 🛠 Ensure the image directory exists before writing files
if !DirExist(imageDir)
    DirCreate(imageDir)

LoadLeaderIdentity()

; === Functions ===
Gdip_Startup() {
    global GdipToken
    if GdipToken
        return
    hGdip := DllCall("LoadLibrary", "Str", "gdiplus", "Ptr")
    si := Buffer(24, 0)
    NumPut("UInt", 1, si)
    DllCall("gdiplus\GdiplusStartup", "Ptr*", &GdipToken, "Ptr", si, "Ptr", 0)
}

Gdip_CreateBitmapFromHBITMAP(hBitmap) {
    pBitmap := 0
    DllCall("gdiplus\GdipCreateBitmapFromHBITMAP", "Ptr", hBitmap, "Ptr", 0, "Ptr*", &pBitmap)
    return pBitmap
}

Gdip_CreateBitmapFromFile(filePath) {
    pBitmap := 0
    result := DllCall("gdiplus\GdipCreateBitmapFromFile", "WStr", filePath, "Ptr*", &pBitmap)
    if (result != 0)
        return 0
    return pBitmap
}

Gdip_SaveBitmapToFile(pBitmap, filePath) {
    CLSID := Buffer(16)
    NumPut("UInt", 0x557CF406, CLSID)
    NumPut("UShort", 0x1A04, CLSID, 4)
    NumPut("UShort", 0x11D3, CLSID, 6)
    NumPut("UChar", 0x9A, CLSID, 8)
    NumPut("UChar", 0x73, CLSID, 9)
    NumPut("UChar", 0x00, CLSID, 10)
    NumPut("UChar", 0x00, CLSID, 11)
    NumPut("UChar", 0xF8, CLSID, 12)
    NumPut("UChar", 0x1E, CLSID, 13)
    NumPut("UChar", 0xF3, CLSID, 14)
    NumPut("UChar", 0x2E, CLSID, 15)
    result := DllCall("gdiplus\GdipSaveImageToFile", "Ptr", pBitmap, "WStr", filePath, "Ptr", CLSID, "Ptr", 0)
    return result == 0
}

Gdip_DisposeImage(pBitmap) {
    DllCall("gdiplus\GdipDisposeImage", "Ptr", pBitmap)
}

Gdip_GetPixel(pBitmap, x, y) {
    color := 0
    DllCall("gdiplus\GdipBitmapGetPixel", "Ptr", pBitmap, "Int", x, "Int", y, "UInt*", &color)
    return color
}

DeleteObject(hObject) {
    return DllCall("DeleteObject", "Ptr", hObject)
}

GetWindowRect(hwnd) {
    buf := Buffer(16)
    DllCall("GetWindowRect", "Ptr", hwnd, "Ptr", buf)
    return {
        left: NumGet(buf, 0, "Int"),
        top: NumGet(buf, 4, "Int"),
        right: NumGet(buf, 8, "Int"),
        bottom: NumGet(buf, 12, "Int")
    }
}

ResolveSharedRoot() {
    shared := A_ScriptDir . "\..\shared"
    if !DirExist(shared)
        DirCreate(shared)
    return shared
}

NormalizePath(path) {
    p := StrLower(StrReplace(Trim(path), "/", "\"))
    p := StrReplace(p, "\\?\", "")
    while InStr(p, "\\")
        p := StrReplace(p, "\\", "\")
    return p
}

GetSlotPathMap() {
    global Slot1MainName, Slot2FollowerName, Slot3FollowerName, Slot4FollowerName
    global Slot1MainPath, Slot2FollowerPath, Slot3FollowerPath, Slot4FollowerPath
    return Map(
        Slot1MainName, Slot1MainPath,
        Slot2FollowerName, Slot2FollowerPath,
        Slot3FollowerName, Slot3FollowerPath,
        Slot4FollowerName, Slot4FollowerPath
    )
}

NormalizeIdentityToSlot(name) {
    global Slot1MainName, Slot2FollowerName, Slot3FollowerName, Slot4FollowerName
    n := Trim(name)
    if (n = "DaMJMaD")
        return Slot1MainName
    if (n = "MaD")
        return Slot2FollowerName
    if (n = Slot1MainName || n = Slot2FollowerName || n = Slot3FollowerName || n = Slot4FollowerName)
        return n
    return ""
}

NameFromPath(path) {
    slotMap := GetSlotPathMap()
    normPath := NormalizePath(path)
    for name, slotPath in slotMap {
        if (normPath = NormalizePath(slotPath))
            return name
    }
    return ""
}

PathFromName(name) {
    slotMap := GetSlotPathMap()
    if slotMap.Has(name)
        return slotMap[name]
    return ""
}

GetFollowerNames() {
    global SlotOrder, MyName
    names := []
    for _, slotName in SlotOrder {
        if (slotName != MyName)
            names.Push(slotName)
    }
    return names
}

GetNextLeaderPath() {
    global SlotOrder, leaderPath
    currName := NameFromPath(leaderPath)
    if (currName = "")
        return PathFromName(SlotOrder[1])

    for idx, slotName in SlotOrder {
        if (slotName = currName) {
            nextIdx := (idx = SlotOrder.Length) ? 1 : (idx + 1)
            return PathFromName(SlotOrder[nextIdx])
        }
    }
    return PathFromName(SlotOrder[1])
}

SetRolesByLeaderPath(newLeaderPath) {
    global leaderPath, MyName
    leaderName := NameFromPath(newLeaderPath)
    if (leaderName = "")
        return false
    leaderPath := PathFromName(leaderName)
    MyName := leaderName
    return true
}

SaveLeaderIdentity() {
    global imageDir, MyName
    FileDelete(imageDir . "\iam.txt")
    FileAppend(MyName, imageDir . "\iam.txt")
}

LoadLeaderIdentity() {
    global imageDir, Slot1MainPath
    iamFile := imageDir . "\iam.txt"
    leaderName := ""
    if FileExist(iamFile)
        leaderName := NormalizeIdentityToSlot(Trim(FileRead(iamFile)))

    leaderPathFromFile := PathFromName(leaderName)
    if (leaderPathFromFile != "")
        SetRolesByLeaderPath(leaderPathFromFile)
    else
        SetRolesByLeaderPath(Slot1MainPath)

    SaveLeaderIdentity()
}

GetActiveSlotPath() {
    try path := WinGetProcessPath("A")
    catch
        return ""
    activeName := NameFromPath(path)
    if (activeName = "")
        return ""
    return PathFromName(activeName)
}

GetHwndByProcessPath(targetPath) {
    wanted := NormalizePath(targetPath)
    for hwnd in WinGetList("ahk_exe d2r.exe") {
        try processPath := WinGetProcessPath("ahk_id " hwnd)
        catch
            continue
        if (NormalizePath(processPath) = wanted)
            return hwnd
    }
    return 0
}

ResolveLeaderFollowerWindows(&hwndLeader, &followerWindows) {
    global leaderPath

    hwndLeader := GetHwndByProcessPath(leaderPath)
    followerWindows := []

    for _, followerName in GetFollowerNames() {
        followerPath := PathFromName(followerName)
        hwnd := GetHwndByProcessPath(followerPath)
        if (hwnd && hwnd != hwndLeader)
            followerWindows.Push(hwnd)
    }

    winList := WinGetList("ahk_exe d2r.exe")
    if (winList.Length < 2)
        return false

    if !hwndLeader {
        active := WinActive("A")
        activeIsD2R := false
        if active {
            try pname := StrLower(WinGetProcessName("ahk_id " active))
            catch
                pname := ""
            activeIsD2R := (pname = "d2r.exe")
        }

        if activeIsD2R
            hwndLeader := active
        else
            hwndLeader := winList[1]
    }

    if (followerWindows.Length = 0) {
        for _, hwnd in winList {
            if (hwnd != hwndLeader)
                followerWindows.Push(hwnd)
        }
    } else {
        seen := Map()
        for _, hwnd in followerWindows
            seen[hwnd] := true
        for _, hwnd in winList {
            if (hwnd = hwndLeader)
                continue
            if !seen.Has(hwnd) {
                followerWindows.Push(hwnd)
                seen[hwnd] := true
            }
        }
    }

    return (hwndLeader && followerWindows.Length > 0)
}

StackWindows() {
    global MyName

    hwndLeader := 0
    followerWindows := []
    if !ResolveLeaderFollowerWindows(&hwndLeader, &followerWindows) {
        MsgBox("❌ Could not find 2 D2R windows to stack.")
        return
    }

    pos := GetWindowRect(hwndLeader)
    w := pos.right - pos.left
    h := pos.bottom - pos.top

    for _, hwndFollower in followerWindows {
        try WinRestore("ahk_id " hwndFollower)
        try WinMove(pos.left, pos.top, w, h, "ahk_id " hwndFollower)
    }
    try WinActivate("ahk_id " hwndLeader)

    MsgBox("✅ Stacked " followerWindows.Length " follower window(s) under leader: " MyName)
}

CaptureLeaderRegion(silent := false) {
    global leaderScreenshotPath, GdipToken, leaderPath, MyName, imageDir

    hwndLeader := 0
    followerWindows := []
    if !ResolveLeaderFollowerWindows(&hwndLeader, &followerWindows) {
        MsgBox("❌ Leader/follower windows not found for capture.")
        return
    }
    hwnd := hwndLeader
    if !silent {
        WinActivate("ahk_id " hwnd)
        Sleep(300)
    }

    pos := GetWindowRect(hwnd)
    x := pos.left, y := pos.top, w := 1285, h := 840

    hDC := DllCall("GetDC", "Ptr", 0, "Ptr")
    hMemDC := DllCall("CreateCompatibleDC", "Ptr", hDC, "Ptr")
    hBitmap := DllCall("CreateCompatibleBitmap", "Ptr", hDC, "Int", w, "Int", h, "Ptr")
    hOld := DllCall("SelectObject", "Ptr", hMemDC, "Ptr", hBitmap)
    DllCall("BitBlt", "Ptr", hMemDC, "Int", 0, "Int", 0, "Int", w, "Int", h,
                     "Ptr", hDC, "Int", x, "Int", y, "UInt", 0x00CC0020)
    DllCall("SelectObject", "Ptr", hMemDC, "Ptr", hOld)
    DllCall("DeleteDC", "Ptr", hMemDC)
    DllCall("ReleaseDC", "Ptr", 0, "Ptr", hDC)

    if !GdipToken
        Gdip_Startup()

    pBitmap := Gdip_CreateBitmapFromHBITMAP(hBitmap)
    DeleteObject(hBitmap)

    if !pBitmap {
        MsgBox("❌ Failed to create bitmap.")
        return
    }

    if !DirExist(imageDir)
        DirCreate(imageDir)

    saved := false
    Loop 3 {
        Try FileDelete(leaderScreenshotPath)
        if Gdip_SaveBitmapToFile(pBitmap, leaderScreenshotPath) {
            saved := true
            break
        }
        Sleep(40)
    }

    if !saved {
        MsgBox("❌ Failed to save screenshot.`nPath: " leaderScreenshotPath)
    } else if !silent {
        ToolTip("✅ Screenshot saved"), Sleep(800), ToolTip()
    }

    Gdip_DisposeImage(pBitmap)
}

ApplyLeaderHandoff(newLeaderPath) {
    global MyName

    if !SetRolesByLeaderPath(newLeaderPath) {
        MsgBox("❌ Could not set leader handoff role.")
        return
    }

    SaveLeaderIdentity()
    ToolTip("👑 Leader set to: " MyName), Sleep(1000), ToolTip()
}
SaveGreenMarkers() {
    global greenMarkers, imageDir, MyName

    prevMarkers := greenMarkers
    greenMarkers := Map()
    followerNames := GetFollowerNames()
    hasPrev := IsObject(prevMarkers) && prevMarkers.Has(MyName)
    for _, followerName in followerNames {
        if !(IsObject(prevMarkers) && prevMarkers.Has(followerName))
            hasPrev := false
    }
    roleMarkers := DetectRoleMarkersFromScreenshot()

    if IsObject(roleMarkers) {
        greenMarkers[MyName] := roleMarkers.self
        for _, followerName in followerNames
            greenMarkers[followerName] := roleMarkers.other
    } else if hasPrev {
        ; Keep last known live values if this frame parse fails.
        greenMarkers[MyName] := prevMarkers[MyName]
        for _, followerName in followerNames
            greenMarkers[followerName] := prevMarkers[followerName]
    } else {
        ; First-frame fallback around map center.
        greenMarkers[MyName] := {x: 651, y: 428}
        fallback := [{x: 771, y: 428}, {x: 771, y: 458}, {x: 771, y: 398}]
        for idx, followerName in followerNames {
            pos := (idx <= fallback.Length) ? fallback[idx] : {x: 771, y: 428}
            greenMarkers[followerName] := pos
        }
    }

    greenMarkerFile := imageDir . "\greenMarkers.txt"
    if FileExist(greenMarkerFile)
        FileDelete(greenMarkerFile)

    for name, pos in greenMarkers {
        if IsObject(pos) && IsNumber(pos.x) && IsNumber(pos.y)
            FileAppend(name ":" pos.x "," pos.y "`n", greenMarkerFile)
    }

    ; ✅ THIS must come last:
    global greenMarkerPositions := greenMarkers
}

DetectRoleMarkersFromScreenshot() {
    global leaderScreenshotPath
    pBitmap := Gdip_CreateBitmapFromFile(leaderScreenshotPath)
    if !pBitmap
        return 0

    ; Wide search region for full-screen map + corner map variants.
    x1 := 200, y1 := 80, x2 := 1085, y2 := 780
    centerX := 651, centerY := 428
    radius := 12
    samples := []

    y := y1
    while (y <= y2) {
        x := x1
        while (x <= x2) {
            c := Gdip_GetPixel(pBitmap, x, y)
            r := (c >> 16) & 0xFF
            g := (c >> 8) & 0xFF
            b := c & 0xFF
            if IsMarkerPixel(r, g, b)
                samples.Push({x: x, y: y})
            x += 2
        }
        y += 2
    }

    Gdip_DisposeImage(pBitmap)

    if (samples.Length < 2)
        return 0

    selfSeed := GetNearestPoint(samples, centerX, centerY)
    if !IsObject(selfSeed)
        return 0

    selfPos := GetClusterCentroid(samples, selfSeed, radius)
    if !IsObject(selfPos)
        return 0

    otherSeed := GetNearestPointExcludingRadius(samples, centerX, centerY, selfPos, radius + 6)
    if !IsObject(otherSeed)
        return 0

    otherPos := GetClusterCentroid(samples, otherSeed, radius)
    if !IsObject(otherPos)
        return 0

    return { self: selfPos, other: otherPos }
}

IsMarkerPixel(r, g, b) {
    greenLike := (g > 100 && g - r > 20 && g - b > 15)
    blueLike := (b > 100 && b - r > 20 && b - g > 15)
    return (greenLike || blueLike)
}

GetNearestPoint(points, cx, cy) {
    best := 0
    bestDist := 1.0e20
    for _, p in points {
        d := (p.x - cx) ** 2 + (p.y - cy) ** 2
        if (d < bestDist) {
            bestDist := d
            best := p
        }
    }
    return best
}

GetNearestPointExcludingRadius(points, cx, cy, excludedCenter, minRadius) {
    best := 0
    bestDist := 1.0e20
    minRadiusSq := minRadius * minRadius
    for _, p in points {
        dEx := (p.x - excludedCenter.x) ** 2 + (p.y - excludedCenter.y) ** 2
        if (dEx <= minRadiusSq)
            continue
        d := (p.x - cx) ** 2 + (p.y - cy) ** 2
        if (d < bestDist) {
            bestDist := d
            best := p
        }
    }
    return best
}

GetClusterCentroid(points, seed, radius) {
    radiusSq := radius * radius
    sumX := 0
    sumY := 0
    count := 0

    for _, p in points {
        d := (p.x - seed.x) ** 2 + (p.y - seed.y) ** 2
        if (d <= radiusSq) {
            sumX += p.x
            sumY += p.y
            count += 1
        }
    }

    if (count = 0)
        return 0

    return { x: Round(sumX / count), y: Round(sumY / count) }
}

UpdateLiveMarkers() {
    global imageDir, greenMarkerPositions
    path := imageDir "\liveMarkers.txt"

    try {
        ; Refresh marker positions each tick for live leash tracking.
        CaptureLeaderRegion(true)
        SaveGreenMarkers()

        file := FileOpen(path, "w")  ; Overwrite the file cleanly
        file.Write("timestamp=" A_Now "`n")

        for name, coords in greenMarkerPositions {
            if IsObject(coords) && IsNumber(coords.x) && IsNumber(coords.y)
                file.Write(name "=" coords.x "," coords.y "`n")
        }

        file.Close()
    } catch as err {
        ToolTip("❌ Error writing liveMarkers.txt")
        SetTimer(() => ToolTip(), -1000)
    }
}



; === Hotkeys ===
Numpad0::StackWindows()

Numpad1:: {
    SaveLeaderIdentity()
    CaptureLeaderRegion()
    SaveGreenMarkers()
    UpdateLiveMarkers()                      ; 💥 run once immediately
    SetTimer(UpdateLiveMarkers, 250)         ; faster live marker refresh for leash chase
    ToolTip("📸 Leader SS + greenMarkers saved"), Sleep(1000), ToolTip()
}

Numpad5:: {
    path := GetActiveSlotPath()
    if (path = "") {
        MsgBox("❌ Active window is not a configured D2R slot (II, 2, 2x2, 2x3).")
        return
    }
    ApplyLeaderHandoff(path)
}

Numpad6:: {
    ApplyLeaderHandoff(GetNextLeaderPath())
}

Numpad9::ExitApp()
 #HotIf WinActive("ahk_class AutoHotkeyGUI") || true
;Numpad7::ToggleMindsEye()

;ToggleMindsEye() {
;    ToolTip("👁 MindsEye capturing..."), Sleep(600), ToolTip()
;    MindsEye()
;}
