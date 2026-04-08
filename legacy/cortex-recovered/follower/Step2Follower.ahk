; === Step2Follower.ahk ===
#Requires AutoHotkey v2.0
#SingleInstance Force

if !A_IsAdmin {
    try Run('*RunAs "' A_ScriptFullPath '"')
    ExitApp
}

; === Globals ===
global sharedRoot := ResolveSharedRoot()
global imageDir := sharedRoot . "\image directory"
global runtimeDir := sharedRoot . "\runtime"
global qtmosBindCmd := runtimeDir . "\qtmos_bind_once.cmd"
global qtmosBindRequestFile := runtimeDir . "\qtmos_bind_request.ini"
global step2ProfileFile := A_ScriptDir . "\step2_profiles.ini"
global activeProfileFile := runtimeDir . "\active_profile.json"
global GdipToken := 0
global MyName := ""
global LeaderName := ""
global hwndLeader := 0
global hwndFollowers := []
global followMode := false
global driverInFile := runtimeDir . "\driver_in.jsonl"
global driverOutFile := runtimeDir . "\driver_out.jsonl"
global driverLastCmdId := 0
global step3Enabled := false
global step3TickMs := 250
global step3HpThreshold := 0.34
global step3MpThreshold := 0.30
global step3HpKey := "1"
global step3MpKey := "2"
global step3TownEnabled := true
global step3TownThreshold := 0.03
global step3TownKey := "t"
global step3TownCooldownMs := 9000
global step3CriticalTrip := 3
global step3AltPulseEnabled := true
global step3AltPulseMs := 700
global step3LastAltAt := 0
global step3LastHpPotAt := 0
global step3LastMpPotAt := 0
global step3PotionCooldownMs := 950
global step3LastStatusAckAt := 0
global step3StatusEveryMs := 5000
global step3LastHp := -1.0
global step3LastMp := -1.0
global step3TargetCount := 0
global step3TargetMode := "followers"
global step3TargetInstance := ""
global step3SensorInvalidStreak := 0
global step3SensorInvalidTrip := 3
global step3SensorStaleMs := 2200
global step3NoTargetStreak := 0
global step3NoTargetAckMs := 15000
global step3LastNoTargetAckAt := 0
global step3HpPotAtByHwnd := Map()
global step3MpPotAtByHwnd := Map()
global step3LastTownAtByHwnd := Map()
global step3CriticalStreakByHwnd := Map()
global step3LastValidHpByHwnd := Map()
global step3LastValidMpByHwnd := Map()
global step3LastValidHpAtByHwnd := Map()
global step3LastValidMpAtByHwnd := Map()
global step3FollowersFallbackSelf := true
global step3ClassName := ""
global step3CharacterName := ""
global step3PrimaryKey := ""
global step3SecondaryKey := ""
global step3PickitProfile := ""
global step3ForceMoveKey := "LAlt"
global step3AttackEnabled := true
global step3AttackEveryMs := 550
global step3SecondaryEveryMs := 1800
global step3LastAttackAtByHwnd := Map()
global step3LastSecondaryAtByHwnd := Map()
global followerClientByHwnd := Map()
global followerProfileByHwnd := Map()
global followerMapLastSyncAt := 0
global followerMapSyncMs := 900
global mirrorRightHeld := false
global mirrorRightLastX := 0
global mirrorRightLastY := 0
global teleportJumpPx := 150
global teleportResyncMinMs := 170
global teleportLastResyncAt := 0
global teleportForceMoveBurstCount := 3
global teleportForceMoveBurstGapMs := 20
global buffEnabled := false
global buffTickMs := 95000
global buffLastAt := 0
global buffBoSpec := "khurst"
global buffBoKey := "F7"
global buffBoCasts := 2
global buffChantSpec := "ssu"
global buffChantKey := "F8"
global buffChantCasts := 1
global buffCastGapMs := 140
global forwardKeys := [
    "1","2","3","4","5","6","7","8","9","0",
    "q","w","e","r","t","y","u","i","o","p",
    "a","s","d","f","g","h","j","k","l",
    "z","x","c","v","b","n","m",
    "Tab","Space","Enter","Esc","Backspace",
    "LShift","RShift","LControl","RControl","LAlt","RAlt",
    "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12"
]

global leaderScreenshotPath := imageDir . "\leader_minimap.png"
weareFile := imageDir . "\weare.txt"
iamFile := imageDir . "\iam.txt"

if !DirExist(imageDir)
    DirCreate(imageDir)
if !DirExist(runtimeDir)
    DirCreate(runtimeDir)

if !FileExist(driverInFile)
    FileAppend("", driverInFile, "UTF-8")
if !FileExist(driverOutFile)
    FileAppend("", driverOutFile, "UTF-8")

EnsureStep2ProfileFile()
LoadIdentity()  ; ← Correct v2 syntax
SetTimer(DriverPoll, 200)
SetTimer(DriverStartupPing, -400)




; === Functions ===
ResolveSharedRoot() {
    shared := A_ScriptDir . "\..\shared"
    if !DirExist(shared)
        DirCreate(shared)
    return shared
}

LoadIdentity() {
    global MyName, LeaderName, weareFile, iamFile

    if FileExist(weareFile)
        MyName := Trim(FileRead(weareFile))

    if FileExist(iamFile)
        LeaderName := Trim(FileRead(iamFile))
}

ResolveLeaderWindow() {
    global LeaderName

    active := WinActive("ahk_exe d2r.exe")
    if active
        return active

    wins := WinGetList("ahk_exe d2r.exe")
    if (wins.Length < 1)
        return 0

    leaderInstance := GetInstanceForName(LeaderName)
    if (leaderInstance != "") {
        for _, hwnd in wins {
            if (GetWindowInstance(hwnd) = leaderInstance)
                return hwnd
        }
    }

    return wins[1]
}

StartFollowing(silent := false) {
    global hwndLeader, hwndFollowers

    LoadIdentity()

    winList := WinGetList("ahk_exe d2r.exe")
    if (winList.Length < 2) {
        MsgBox("❌ Not enough D2R windows found.")
        return
    }

    hwndLeader := ResolveLeaderWindow()
    if !hwndLeader {
        MsgBox("❌ Could not resolve leader window.")
        return
    }
    hwndFollowers := []
    for _, hwnd in winList {
        if (hwnd != hwndLeader)
            hwndFollowers.Push(hwnd)
    }
    BuildFollowerRuntimeMap(true)

    HotIfWinActive("ahk_id " hwndLeader)

    ; Holdable mouse buttons
    Hotkey("~LButton", ForwardMouseHold.Bind("down"), "On")
    Hotkey("~LButton up", ForwardMouseHold.Bind("up"), "On")
    Hotkey("~RButton", ForwardMouseHold.Bind("rdown"), "On")
    Hotkey("~RButton up", ForwardMouseHold.Bind("rup"), "On")
    Hotkey("~XButton1", ForwardMouseHold.Bind("x1down"), "On")
    Hotkey("~XButton1 up", ForwardMouseHold.Bind("x1up"), "On")
    Hotkey("~XButton2", ForwardMouseHold.Bind("x2down"), "On")
    Hotkey("~XButton2 up", ForwardMouseHold.Bind("x2up"), "On")
    SetKeyboardMirroring("On")
    HotIfWinActive()

    if !silent
        MsgBox(BuildMirrorEnabledText(hwndLeader, hwndFollowers), "Multibox", "Iconi")
}

StopFollowing(silent := false) {
    global hwndLeader, hwndFollowers, mirrorRightHeld, mirrorRightLastX, mirrorRightLastY

    HotIfWinActive("ahk_id " hwndLeader)

    ; Unbind all the mouse hotkeys to stop forwarding the mouse events to followers
    Hotkey("~LButton", ForwardMouseHold.Bind("down"), "Off")
    Hotkey("~LButton up", ForwardMouseHold.Bind("up"), "Off")
    Hotkey("~RButton", ForwardMouseHold.Bind("rdown"), "Off")
    Hotkey("~RButton up", ForwardMouseHold.Bind("rup"), "Off")
    Hotkey("~XButton1", ForwardMouseHold.Bind("x1down"), "Off")
    Hotkey("~XButton1 up", ForwardMouseHold.Bind("x1up"), "Off")
    Hotkey("~XButton2", ForwardMouseHold.Bind("x2down"), "Off")
    Hotkey("~XButton2 up", ForwardMouseHold.Bind("x2up"), "Off")
    SetKeyboardMirroring("Off")
    HotIfWinActive()  ; Reset filter to apply hotkeys to all windows.

    ; Manually stop forwarding any remaining mouse events to followers
    for hwnd in hwndFollowers {
        if (hwnd) {
            try PostMessage(0x202, 0, 0, , "ahk_id " hwnd) ; Release Left Button
            try PostMessage(0x205, 0, 0, , "ahk_id " hwnd) ; Release Right Button
            try PostMessage(0x20C, 0x00010000, 0, , "ahk_id " hwnd) ; Release XButton1
            try PostMessage(0x20C, 0x00020000, 0, , "ahk_id " hwnd) ; Release XButton2
        }
    }
    ReleaseMirroredKeys()

    ; Optionally, clear any mouse tracking or other behaviors to fully stop following
    mirrorRightHeld := false
    mirrorRightLastX := 0
    mirrorRightLastY := 0
    SetTimer(ForwardRightMouseMove, 0)
    hwndFollowers := []  ; Clear the follower list

    if !silent
        MsgBox("⛔ Mouse mirroring DISABLED and FOLLOWING STOPPED", "Multibox", "Iconi")
}

DriverPoll() {
    global driverInFile, driverLastCmdId

    if !FileExist(driverInFile)
        return

    raw := FileRead(driverInFile, "UTF-8")
    if (raw = "")
        return

    lines := StrSplit(raw, "`n", "`r")
    for _, line in lines {
        line := Trim(line)
        if (line = "")
            continue

        cmdId := JsonGetInt(line, "id")
        if (cmdId > 0 && cmdId <= driverLastCmdId)
            continue

        cmd := JsonGetString(line, "cmd")
        if (cmd = "")
            continue

        target := JsonGetString(line, "target")
        if !DriverTargetMatches(target)
            continue

        DriverDispatch(cmd, cmdId, line)
        if (cmdId > driverLastCmdId)
            driverLastCmdId := cmdId
    }
}

DriverStartupPing() {
    DriverAck("boot", "ok", 0, "driver_online")
}

DriverTargetMatches(target) {
    global MyName

    t := Trim(StrLower(target))
    if (t = "" || t = "all" || t = "followers" || t = "follower" || t = "step2")
        return true

    if (MyName != "" && t = StrLower(MyName))
        return true

    return false
}

DriverDispatch(cmd, cmdId, rawJson := "") {
    global MyName, LeaderName, followMode, weareFile, step3Enabled, step3TickMs
    global step3LastStatusAckAt, step3SensorInvalidStreak, step3LastHp, step3LastMp
    global step3TargetCount, step3TargetMode, step3TargetInstance
    global step3HpPotAtByHwnd, step3MpPotAtByHwnd, step3TownEnabled
    global buffEnabled, buffTickMs, buffBoSpec, buffBoKey, buffBoCasts
    global buffChantSpec, buffChantKey, buffChantCasts, buffCastGapMs

    c := StrLower(Trim(cmd))
    switch c {
        case "identify":
            if (MyName = "" && FileExist(weareFile))
                MyName := Trim(FileRead(weareFile))

            if (MyName = "")
                MyName := GetMyNameFromPath()

            if (MyName != "") {
                if FileExist(weareFile)
                    FileDelete(weareFile)
                FileAppend(MyName, weareFile)
                DriverAck(c, "ok", cmdId, "name=" . MyName)
            } else {
                DriverAck(c, "err", cmdId, "name_not_resolved")
            }

        case "follow_on":
            if (MyName = "")
                MyName := GetMyNameFromPath()

            if (MyName = LeaderName) {
                DriverAck(c, "skip", cmdId, "leader_instance")
                return
            }

            followMode := true
            StartFollowing(true)
            DriverAck(c, "ok", cmdId, "")

        case "follow_off", "panic_stop":
            followMode := false
            StopFollowing(true)
            DriverAck(c, "ok", cmdId, "")

        case "press_key":
            keyName := JsonGetString(rawJson, "key")
            if (keyName = "") {
                DriverAck(c, "err", cmdId, "missing_key")
                return
            }
            ok := DriverTapKey(keyName)
            DriverAck(c, ok ? "ok" : "err", cmdId, ok ? ("key=" . keyName) : "no_window")

        case "alt_pulse":
            ok := DriverTapKey("LAlt")
            DriverAck(c, ok ? "ok" : "err", cmdId, ok ? "" : "no_window")

        case "step3_on", "step3_off", "step3_status", "step3_target", "step3_town_on", "step3_town_off":
            Step3DisableLocal()
            DriverAck(c, "skip", cmdId, Step3StatusDetail())

        case "buff_on", "buff_off", "buff_now", "buff_status", "buff_set":
            BuffDisableLocal()
            DriverAck(c, "skip", cmdId, BuffStatusDetail())

        case "status":
            DriverAck(c, "ok", cmdId, "follow=" . (followMode ? "on" : "off") . ";" . Step3StatusDetail() . ";" . BuffStatusDetail())

        default:
            DriverAck(c, "err", cmdId, "unknown_cmd")
    }
}

DriverAck(cmd, status, cmdId, detail := "") {
    global driverOutFile

    safeCmd := EscapeJsonText(cmd)
    safeStatus := EscapeJsonText(status)
    safeDetail := EscapeJsonText(detail)
    ts := EscapeJsonText(A_Now)
    q := Chr(34)
    payload := "{"
        . q . "ts" . q . ":" . q . ts . q . ","
        . q . "source" . q . ":" . q . "step2" . q . ","
        . q . "cmd" . q . ":" . q . safeCmd . q . ","
        . q . "status" . q . ":" . q . safeStatus . q . ","
        . q . "id" . q . ":" . cmdId . ","
        . q . "detail" . q . ":" . q . safeDetail . q
        . "}"
    FileAppend(payload . "`n", driverOutFile, "UTF-8")
}

AiDisabledDetail(feature := "ai") {
    return feature . "=removed"
}

BuffEnableLocal() {
    global buffEnabled, buffLastAt
    buffEnabled := false
    buffLastAt := 0
    SetTimer(BuffTick, 0)
}

BuffDisableLocal() {
    global buffEnabled
    buffEnabled := false
    SetTimer(BuffTick, 0)
}

BuffTick() {
    return
}

BuffStatusDetail() {
    return AiDisabledDetail("buff")
}

BuffRunCycle(reason := "manual") {
    DriverAck("buff_tick", "skip", 0, BuffStatusDetail() . ";reason=" . reason)
    return false
}

BuffCastRole(spec, keyName, casts := 1, gapMs := 120) {
    return -1
}

ResolveWindowBySpec(spec) {
    global LeaderName
    s := StrLower(Trim(spec))
    wins := WinGetList("ahk_exe d2r.exe")
    if (wins.Length < 1)
        return 0

    if (s = "" || s = "self" || s = "me")
        return ResolveDriverWindow()

    if (s = "leader") {
        for _, hwnd in wins {
            if (GetWindowInstance(hwnd) = GetInstanceForName(LeaderName))
                return hwnd
        }
        return wins[1]
    }

    inst := ""
    if RegExMatch(s, "i)^(?:slot|instance)?\s*([1-4])$", &m)
        inst := m[1]

    if (inst = "")
        inst := GetInstanceForName(s)
    if (inst = "")
        return 0

    for _, hwnd in wins {
        if (GetWindowInstance(hwnd) = inst)
            return hwnd
    }
    return 0
}

Step3EnableLocal() {
    global step3Enabled, step3TargetCount
    step3Enabled := false
    step3TargetCount := 0
    SetTimer(Step3Tick, 0)
}

Step3DisableLocal() {
    global step3Enabled, step3TargetCount
    step3Enabled := false
    step3TargetCount := 0
    SetTimer(Step3Tick, 0)
}

SetStep3TargetBySpec(spec) {
    global step3TargetMode, step3TargetInstance
    step3TargetMode := "disabled"
    step3TargetInstance := ""
    return false
}

Step3Tick() {
    return
}

Step3StatusDetail() {
    return AiDisabledDetail("step3")
}

ListJoin(items, sep := "|") {
    out := ""
    for idx, val in items {
        if (idx > 1)
            out .= sep
        out .= val
    }
    return out
}

ResolveStep3Targets() {
    return []
}

ShowAiRemovedToolTip(msg := "AI removed from this build") {
    ToolTip(msg), Sleep(800), ToolTip()
}

Step3HotkeyRemoved(*) {
    Step3DisableLocal()
    ShowAiRemovedToolTip("Step3 removed")
}

BuffHotkeyRemoved(*) {
    BuffDisableLocal()
    ShowAiRemovedToolTip("Buff AI removed")
}

ResolveDriverWindow() {
    global MyName

    wins := WinGetList("ahk_exe d2r.exe")
    if (wins.Length < 1)
        return 0

    myInstance := GetInstanceForName(MyName)
    if (myInstance != "") {
        for _, hwnd in wins {
            pid := WinGetPID("ahk_id " hwnd)
            cmdLine := GetProcessCommandLine(pid)
            if (cmdLine != "" && RegExMatch(cmdLine, "i)-instance\s*" . myInstance . "(\D|$)"))
                return hwnd
        }
    }

    active := WinActive("ahk_exe d2r.exe")
    if active
        return active

    return wins[1]
}

GetInstanceForName(name) {
    n := StrLower(Trim(name))
    if (n = "")
        return ""

    ; Normalize noisy labels such as "SSU - Account Active."
    if InStr(n, "satansmiled") || InStr(n, "ssu")
        return "4"
    if InStr(n, "khurst")
        return "3"
    if InStr(n, "damjmad") || InStr(n, "damj")
        return "1"

    ; Keep plain "mad" mapping, but avoid matching inside "damjmad".
    if (n = "mad")
        return "2"
    if RegExMatch(n, "i)(^|[^a-z])mad([^a-z]|$)")
        return "2"

    return ""
}

GetNameForInstance(inst) {
    switch inst {
        case "1":
            return "DaMJMaD"
        case "2":
            return "MaD"
        case "3":
            return "Khurst"
        case "4":
            return "SSU"
        default:
            return "Unknown"
    }
}

GetRealmForHwnd(hwnd) {
    pid := WinGetPID("ahk_id " hwnd)
    if !pid
        return ""

    cmdLine := GetProcessCommandLine(pid)
    if (cmdLine = "")
        return ""

    if RegExMatch(cmdLine, "i)-address\s+([^\s`"]+)", &m)
        return m[1]

    return ""
}

BuildMirrorEnabledText(leaderHwnd, followers) {
    global MyName

    leaderInst := GetWindowInstance(leaderHwnd)
    leaderName := GetNameForInstance(leaderInst)
    if (leaderName = "Unknown" && MyName != "")
        leaderName := MyName

    msg := "✅ Mouse + combat key mirroring ENABLED`n"
        . "Leader: " . leaderName . "`n"
        . "Followers: " . followers.Length . "`n`n"

    for _, hwnd in followers {
        if !hwnd
            continue

        inst := GetWindowInstance(hwnd)
        name := GetNameForInstance(inst)
        realm := GetRealmForHwnd(hwnd)

        line := "- "
        if (inst != "")
            line .= inst . " - "
        line .= name
        if (realm != "")
            line .= " (" . realm . ")"
        line .= " - Diablo II: Resurrected"

        msg .= line . "`n"
    }

    return RTrim(msg, "`n")
}

GetWindowInstance(hwnd) {
    if (!hwnd || !WinExist("ahk_id " hwnd))
        return ""

    try pid := WinGetPID("ahk_id " hwnd)
    catch
        return ""
    if !pid
        return ""

    cmdLine := GetProcessCommandLine(pid)
    if (cmdLine = "")
        return ""

    if RegExMatch(cmdLine, "i)-instance\s*([1-4])", &m)
        return m[1]

    return ""
}

DriverTapKey(keyName, hwnd := 0, holdMs := 35) {
    if !hwnd
        hwnd := ResolveDriverWindow()
    if !hwnd
        return false
    if !WinExist("ahk_id " hwnd)
        return false

    vk := GetKeyVK(keyName)
    if !vk
        return false

    msgDown := 0x0100
    msgUp := 0x0101
    if (keyName = "LAlt" || keyName = "RAlt") {
        msgDown := 0x0104
        msgUp := 0x0105
    }

    lDown := BuildKeyLParam(keyName, true)
    lUp := BuildKeyLParam(keyName, false)
    winSpec := "ahk_id " hwnd

    try PostMessage(msgDown, vk, lDown, , winSpec)
    catch
        return false

    if (holdMs > 0)
        Sleep(holdMs)

    ; Window can disappear during transitions; don't crash the whole script.
    if !WinExist(winSpec)
        return true

    try PostMessage(msgUp, vk, lUp, , winSpec)
    catch
        return false
    return true
}

EstimateResourcePct(hwnd, which) {
    pos := GetWindowRect(hwnd)
    w := pos.right - pos.left
    h := pos.bottom - pos.top
    if (w < 400 || h < 300)
        return -1.0

    if (which = "hp") {
        xStart := pos.left + Floor(w * 0.020)
        xEnd := pos.left + Floor(w * 0.280)
    } else if (which = "mp") {
        xStart := pos.left + Floor(w * 0.720)
        xEnd := pos.left + Floor(w * 0.980)
    } else {
        return -1.0
    }

    if (xEnd <= xStart)
        return -1.0

    best := -1.0
    for _, yFrac in [0.84, 0.87, 0.90, 0.93, 0.96] {
        y := pos.top + Floor(h * yFrac)
        ratio := EstimateResourceLine(xStart, xEnd, y, which)
        if (ratio > best)
            best := ratio
    }

    orbRatio := EstimateResourceOrb(pos, w, h, which)
    if (orbRatio > best)
        best := orbRatio

    return best
}

EstimateResourceLine(xStart, xEnd, y, which) {
    step := Floor((xEnd - xStart) / 66)
    if (step < 2)
        step := 2

    hits := 0
    total := 0
    x := xStart
    while (x <= xEnd) {
        try {
            c := PixelGetColor(x, y, "RGB")
            r := (c >> 16) & 0xFF
            g := (c >> 8) & 0xFF
            b := c & 0xFF
            if (which = "hp") {
                if (r >= 45 && r > g + 5 && r > b + 5)
                    hits++
            } else {
                if (b >= 45 && b > r + 5 && b > g + 5)
                    hits++
            }
            total++
        } catch {
        }
        x += step
    }

    if (total < 4)
        return -1.0

    return hits / total
}

EstimateResourceOrb(pos, w, h, which) {
    if (which = "hp") {
        cx := pos.left + Floor(w * 0.128)
        cy := pos.top + Floor(h * 0.900)
    } else if (which = "mp") {
        cx := pos.left + Floor(w * 0.872)
        cy := pos.top + Floor(h * 0.900)
    } else {
        return -1.0
    }

    rx := Floor(w * 0.090)
    ry := Floor(h * 0.100)
    if (rx < 24 || ry < 18)
        return -1.0

    hits := 0
    total := 0
    y := cy - ry
    while (y <= cy + ry) {
        ny := (y - cy) / ry
        x := cx - rx
        while (x <= cx + rx) {
            nx := (x - cx) / rx
            if ((nx * nx + ny * ny) <= 1.0) {
                try {
                    c := PixelGetColor(x, y, "RGB")
                    r := (c >> 16) & 0xFF
                    g := (c >> 8) & 0xFF
                    b := c & 0xFF
                    if (which = "hp") {
                        if (r >= 40 && r > g + 4 && r > b + 4)
                            hits++
                    } else {
                        if (b >= 40 && b > r + 4 && b > g + 4)
                            hits++
                    }
                    total++
                } catch {
                }
            }
            x += 4
        }
        y += 4
    }

    if (total < 60)
        return -1.0

    return hits / total
}

EscapeJsonText(text) {
    q := Chr(34)
    s := text . ""
    s := StrReplace(s, "\", "\\")
    s := StrReplace(s, q, "\" . q)
    s := StrReplace(s, "`r", "\r")
    s := StrReplace(s, "`n", "\n")
    return s
}

JsonGetString(jsonLine, key) {
    q := Chr(34)
    pattern := q . key . q . "\s*:\s*" . q . "([^" . q . "]*)" . q
    if RegExMatch(jsonLine, pattern, &m)
        return m[1]
    return ""
}

JsonGetInt(jsonLine, key) {
    q := Chr(34)
    pattern := q . key . q . "\s*:\s*(-?\d+)"
    if RegExMatch(jsonLine, pattern, &m)
        return m[1] + 0
    return 0
}


ForwardMouseHold(state, *) {
    global hwndLeader, hwndFollowers, mirrorRightHeld, mirrorRightLastX, mirrorRightLastY

    MouseGetPos(&x, &y)

    ; Limit passthrough to only when mouse is inside the leader window
    leaderWin := hwndLeader
    if (!leaderWin || !WinExist("ahk_id " leaderWin))
        leaderWin := ResolveLeaderWindow()
    if !leaderWin
        return

    pos := GetWindowRect(leaderWin)

    ; If mouse is outside the leader window, abort passthrough
    if (x < pos.left || x > pos.right || y < pos.top || y > pos.bottom)
        return

    ; Continue sending input to followers
    pushForceMove := (state = "down" || state = "rdown")
    for hwnd in hwndFollowers {
        if !hwnd
            continue

        pt := ScreenToClient(hwnd, x, y)
        lParam := (pt.y << 16) | (pt.x & 0xFFFF)

        msg := 0
        wParam := 0
        switch state {
            case "down":
                msg := 0x201, wParam := 0x0001
            case "up":
                msg := 0x202, wParam := 0
            case "rdown":
                msg := 0x204, wParam := 0x0002
                mirrorRightHeld := true
                mirrorRightLastX := x
                mirrorRightLastY := y
                SetTimer(ForwardRightMouseMove, 25)
            case "rup":
                msg := 0x205, wParam := 0
                mirrorRightHeld := false
                mirrorRightLastX := 0
                mirrorRightLastY := 0
                SetTimer(ForwardRightMouseMove, 0)
            case "x1down":
                msg := 0x20B, wParam := 0x00010000
            case "x1up":
                msg := 0x20C, wParam := 0x00010000
            case "x2down":
                msg := 0x20B, wParam := 0x00020000
            case "x2up":
                msg := 0x20C, wParam := 0x00020000
        }

        if msg
            try PostMessage(msg, wParam, lParam, , "ahk_id " hwnd)
        if pushForceMove
            ForceMoveBurstForHwnd(hwnd, 1)
    }
}
GetWindowRect(hwnd) {
    if (!hwnd || !WinExist("ahk_id " hwnd))
        return { left: 0, top: 0, right: 0, bottom: 0 }

    buf := Buffer(16)
    try {
        ok := DllCall("GetWindowRect", "Ptr", hwnd, "Ptr", buf)
        if !ok
            return { left: 0, top: 0, right: 0, bottom: 0 }
    } catch {
        return { left: 0, top: 0, right: 0, bottom: 0 }
    }

    return {
        left: NumGet(buf, 0, "Int"),
        top: NumGet(buf, 4, "Int"),
        right: NumGet(buf, 8, "Int"),
        bottom: NumGet(buf, 12, "Int")
    }
}

ForwardMouseRelease() {
    ForwardMouseHold("up")
}

SetKeyboardMirroring(state) {
    global forwardKeys

    for _, keyName in forwardKeys {
        hkDown := "*~" . keyName
        hkUp := "*~" . keyName . " up"

        if (state = "On") {
            Hotkey(hkDown, ForwardKeyState.Bind(keyName, true), "On")
            Hotkey(hkUp, ForwardKeyState.Bind(keyName, false), "On")
        } else {
            try Hotkey(hkDown, "Off")
            try Hotkey(hkUp, "Off")
        }
    }
}

ForwardRightMouseMove() {
    global hwndLeader, hwndFollowers, mirrorRightHeld, mirrorRightLastX, mirrorRightLastY
    global teleportJumpPx, teleportResyncMinMs, teleportLastResyncAt

    if !mirrorRightHeld
        return

    MouseGetPos(&x, &y)
    leaderWin := hwndLeader
    if (!leaderWin || !WinExist("ahk_id " leaderWin))
        leaderWin := ResolveLeaderWindow()
    if !leaderWin
        return

    pos := GetWindowRect(leaderWin)
    if (x < pos.left || x > pos.right || y < pos.top || y > pos.bottom)
        return

    dx := Abs(x - mirrorRightLastX)
    dy := Abs(y - mirrorRightLastY)
    jumped := (mirrorRightLastX != 0 || mirrorRightLastY != 0) && (dx + dy >= teleportJumpPx)
    now := A_TickCount
    resync := jumped && ((now - teleportLastResyncAt) >= teleportResyncMinMs)

    for hwnd in hwndFollowers {
        if !hwnd
            continue
        pt := ScreenToClient(hwnd, x, y)
        lParam := (pt.y << 16) | (pt.x & 0xFFFF)
        try PostMessage(0x200, 0x0002, lParam, , "ahk_id " hwnd) ; WM_MOUSEMOVE + MK_RBUTTON
        if resync {
            try PostMessage(0x204, 0x0002, lParam, , "ahk_id " hwnd) ; retrigger RMB down after big jump
            ForceMoveBurstForHwnd(hwnd)
        }
    }

    if resync
        teleportLastResyncAt := now
    mirrorRightLastX := x
    mirrorRightLastY := y
}

ForwardKeyState(keyName, isDown, *) {
    global hwndFollowers

    vk := GetKeyVK(keyName)
    if !vk
        return

    msg := isDown ? 0x0100 : 0x0101
    if (keyName = "LAlt" || keyName = "RAlt")
        msg := isDown ? 0x0104 : 0x0105

    lParam := BuildKeyLParam(keyName, isDown)

    for hwnd in hwndFollowers {
        if !hwnd
            continue
        try PostMessage(msg, vk, lParam, , "ahk_id " hwnd)
    }

    ; No hardcoded leader key triggers here.
    ; Movement nudges should come from mirrored mouse/step3 pulse/profile mapping only.
}

ForceMoveBurstFollowers() {
    global hwndFollowers
    for hwnd in hwndFollowers {
        if !hwnd
            continue
        ForceMoveBurstForHwnd(hwnd)
    }
}

ForceMoveBurstForHwnd(hwnd, countOverride := 0) {
    global teleportForceMoveBurstCount, teleportForceMoveBurstGapMs, step3ForceMoveKey
    profile := GetFollowerProfileByHwnd(hwnd)
    forceMoveKey := profile.Has("force_move_key") ? profile["force_move_key"] : step3ForceMoveKey
    if (forceMoveKey = "")
        forceMoveKey := "LAlt"

    loops := countOverride > 0 ? countOverride : teleportForceMoveBurstCount
    Loop loops {
        DriverTapKey(forceMoveKey, hwnd, 20)
        if (A_Index < loops)
            Sleep(teleportForceMoveBurstGapMs)
    }
}

ReleaseMirroredKeys() {
    global hwndFollowers, forwardKeys

    for hwnd in hwndFollowers {
        if !hwnd
            continue

        for _, keyName in forwardKeys {
            vk := GetKeyVK(keyName)
            if !vk
                continue

            msg := (keyName = "LAlt" || keyName = "RAlt") ? 0x0105 : 0x0101
            lParam := BuildKeyLParam(keyName, false)
            try PostMessage(msg, vk, lParam, , "ahk_id " hwnd)
        }
    }
}

BuildKeyLParam(keyName, isDown) {
    sc := GetKeySC(keyName)
    if !sc
        sc := 0

    lParam := 1 | (sc << 16)

    if IsExtendedKey(keyName)
        lParam := lParam | (1 << 24)

    if !isDown
        lParam := lParam | (1 << 30) | (1 << 31)

    return lParam
}

IsExtendedKey(keyName) {
    switch keyName {
        case "RControl", "RAlt", "Insert", "Delete", "Home", "End", "PgUp", "PgDn", "Up", "Down", "Left", "Right", "NumpadDiv", "NumpadEnter":
            return true
        default:
            return false
    }
}

ScreenToClient(hwnd, x, y) {
    pt := Buffer(8)
    NumPut("Int", x, pt)
    NumPut("Int", y, pt, 4)
    DllCall("ScreenToClient", "Ptr", hwnd, "Ptr", pt)
    return { x: NumGet(pt, 0, "Int"), y: NumGet(pt, 4, "Int") }
}

; === Hotkeys ===
Numpad0:: {
    Step3HotkeyRemoved()
}
NumpadIns:: {
    Step3HotkeyRemoved()
}

Numpad1:: {
    Step3HotkeyRemoved()
}
NumpadEnd:: {
    Step3HotkeyRemoved()
}

Numpad4:: {
    BuffHotkeyRemoved()
}
NumpadLeft:: {
    BuffHotkeyRemoved()
}

Numpad6:: {
    BuffHotkeyRemoved()
}
NumpadRight:: {
    BuffHotkeyRemoved()
}

Numpad2:: {
    global followMode
    if (MyName = "") {
        MsgBox("⚠️ You must identify first (Numpad5)")
        return
    }
    if (MyName = LeaderName) {
        MsgBox("👑 Leader cannot follow itself")
        return
    }
    followMode := true
    StartFollowing()
    ToolTip("🟢 Following Leader"), Sleep(800), ToolTip()
}
NumpadDown:: {
    global followMode
    if (MyName = "") {
        MsgBox("⚠️ You must identify first (Numpad5)")
        return
    }
    if (MyName = LeaderName) {
        MsgBox("👑 Leader cannot follow itself")
        return
    }
    followMode := true
    StartFollowing()
    ToolTip("🟢 Following Leader"), Sleep(800), ToolTip()
}

Numpad3:: {
    global followMode
    followMode := false
    StopFollowing()
}
NumpadPgDn:: {
    global followMode
    followMode := false
    StopFollowing()
}

Numpad9::ExitApp()
NumpadPgUp::ExitApp()

; === Manual ID Setup ===
Numpad5:: {
    MyName := GetMyNameFromPath()
    if FileExist(weareFile)
        FileDelete(weareFile)
    FileAppend(MyName, weareFile)
    LoadClientProfile(MyName)
    TriggerQtmosBind()
    tip := "You are: " MyName
    if (step3ClassName = "" && step3CharacterName = "")
        tip .= " | PROFILE BLANK"
    if (step3ClassName != "")
        tip .= " | " step3ClassName
    if (step3CharacterName != "")
        tip .= " | " step3CharacterName
    ToolTip(tip), Sleep(1300), ToolTip()
}
NumpadClear:: {
    MyName := GetMyNameFromPath()
    if FileExist(weareFile)
        FileDelete(weareFile)
    FileAppend(MyName, weareFile)
    LoadClientProfile(MyName)
    TriggerQtmosBind()
    tip := "You are: " MyName
    if (step3ClassName = "" && step3CharacterName = "")
        tip .= " | PROFILE BLANK"
    if (step3ClassName != "")
        tip .= " | " step3ClassName
    if (step3CharacterName != "")
        tip .= " | " step3CharacterName
    ToolTip(tip), Sleep(1300), ToolTip()
}

TriggerQtmosBind() {
    global qtmosBindCmd

    if !FileExist(qtmosBindCmd)
        return

    try Run('"' qtmosBindCmd '"', , "Hide")
}

EnsureStep2ProfileFile() {
    global step2ProfileFile

    if FileExist(step2ProfileFile)
        return

    template :=
(
"; Edit this file once. Numpad5 loads the matching account section." "`n"
"; Valid class_name values: druid, paladin, amazon, necromancer, assassin, barbarian, sorceress, warlock" "`n`n"
"[DaMJMaD]" "`n"
"character_name=" "`n"
"class_name=" "`n"
"hp_threshold=0.34" "`n"
"mp_threshold=0.30" "`n"
"town_threshold=0.28" "`n"
"primary_key=" "`n"
"secondary_key=" "`n"
"force_move_key=" "`n"
"force_move_every_ms=700" "`n"
"attack_enabled=1" "`n"
"attack_every_ms=550" "`n"
"secondary_every_ms=1800" "`n"
"pickit_profile=" "`n`n"
"[MaD]" "`n"
"character_name=" "`n"
"class_name=" "`n"
"hp_threshold=0.34" "`n"
"mp_threshold=0.30" "`n"
"town_threshold=0.28" "`n"
"primary_key=" "`n"
"secondary_key=" "`n"
"force_move_key=" "`n"
"force_move_every_ms=700" "`n"
"attack_enabled=1" "`n"
"attack_every_ms=550" "`n"
"secondary_every_ms=1800" "`n"
"pickit_profile=" "`n`n"
"[Khurst]" "`n"
"character_name=" "`n"
"class_name=" "`n"
"hp_threshold=0.34" "`n"
"mp_threshold=0.30" "`n"
"town_threshold=0.28" "`n"
"primary_key=" "`n"
"secondary_key=" "`n"
"force_move_key=" "`n"
"force_move_every_ms=700" "`n"
"attack_enabled=1" "`n"
"attack_every_ms=550" "`n"
"secondary_every_ms=1800" "`n"
"pickit_profile=" "`n`n"
"[SSU]" "`n"
"character_name=" "`n"
"class_name=" "`n"
"hp_threshold=0.34" "`n"
"mp_threshold=0.30" "`n"
"town_threshold=0.28" "`n"
"primary_key=" "`n"
"secondary_key=" "`n"
"force_move_key=" "`n"
"force_move_every_ms=700" "`n"
"attack_enabled=1" "`n"
"attack_every_ms=550" "`n"
"secondary_every_ms=1800" "`n"
"pickit_profile=" "`n"
)

    FileAppend(template, step2ProfileFile, "UTF-8")
}

LoadClientProfile(clientId) {
    global step2ProfileFile, qtmosBindRequestFile, activeProfileFile
    global step3ClassName, step3CharacterName, step3PrimaryKey, step3SecondaryKey, step3PickitProfile, step3ForceMoveKey
    global step3HpThreshold, step3MpThreshold, step3TownThreshold
    global step3AttackEnabled, step3AttackEveryMs, step3SecondaryEveryMs, step3AltPulseMs

    EnsureStep2ProfileFile()

    section := Trim(clientId)
    step3CharacterName := Trim(IniRead(step2ProfileFile, section, "character_name", ""))
    step3ClassName := StrLower(Trim(IniRead(step2ProfileFile, section, "class_name", "")))
    step3PrimaryKey := Trim(IniRead(step2ProfileFile, section, "primary_key", ""))
    step3SecondaryKey := Trim(IniRead(step2ProfileFile, section, "secondary_key", ""))
    step3ForceMoveKey := Trim(IniRead(step2ProfileFile, section, "force_move_key", "LAlt"))
    step3PickitProfile := Trim(IniRead(step2ProfileFile, section, "pickit_profile", ""))

    hpRaw := Trim(IniRead(step2ProfileFile, section, "hp_threshold", ""))
    mpRaw := Trim(IniRead(step2ProfileFile, section, "mp_threshold", ""))
    townRaw := Trim(IniRead(step2ProfileFile, section, "town_threshold", ""))
    attackEnabledRaw := Trim(IniRead(step2ProfileFile, section, "attack_enabled", "1"))
    attackEveryRaw := Trim(IniRead(step2ProfileFile, section, "attack_every_ms", GetDefaultAttackEveryMs(step3ClassName)))
    secondaryEveryRaw := Trim(IniRead(step2ProfileFile, section, "secondary_every_ms", GetDefaultSecondaryEveryMs(step3ClassName)))
    forceMoveEveryRaw := Trim(IniRead(step2ProfileFile, section, "force_move_every_ms", "700"))

    if (hpRaw != "")
        step3HpThreshold := hpRaw + 0
    if (mpRaw != "")
        step3MpThreshold := mpRaw + 0
    if (townRaw != "")
        step3TownThreshold := townRaw + 0
    step3AttackEnabled := !(attackEnabledRaw = "0" || StrLower(attackEnabledRaw) = "false" || StrLower(attackEnabledRaw) = "off")
    if (attackEveryRaw != "")
        step3AttackEveryMs := attackEveryRaw + 0
    if (secondaryEveryRaw != "")
        step3SecondaryEveryMs := secondaryEveryRaw + 0
    if (forceMoveEveryRaw != "")
        step3AltPulseMs := forceMoveEveryRaw + 0

    WriteQtmosBindRequest(clientId, step3ClassName, step3CharacterName)
    WriteActiveProfileSnapshot(clientId)
}

GetDefaultAttackEveryMs(className) {
    switch StrLower(Trim(className)) {
        case "paladin":
            return "350"
        case "amazon":
            return "450"
        case "necromancer":
            return "600"
        case "druid":
            return "500"
        default:
            return "550"
    }
}

GetDefaultSecondaryEveryMs(className) {
    switch StrLower(Trim(className)) {
        case "paladin":
            return "1800"
        case "amazon":
            return "2200"
        case "necromancer":
            return "2600"
        case "druid":
            return "2400"
        default:
            return "1800"
    }
}

GetClientForceMoveKey(clientId) {
    global step2ProfileFile, step3ForceMoveKey

    section := Trim(clientId)
    if (section = "" || !FileExist(step2ProfileFile))
        return step3ForceMoveKey

    keyName := Trim(IniRead(step2ProfileFile, section, "force_move_key", step3ForceMoveKey))
    return (keyName != "") ? keyName : step3ForceMoveKey
}

LoadClientRuntimeProfile(clientId) {
    global step2ProfileFile
    global step3ClassName, step3PrimaryKey, step3SecondaryKey, step3ForceMoveKey
    global step3HpThreshold, step3MpThreshold, step3TownThreshold
    global step3AttackEnabled, step3AttackEveryMs, step3SecondaryEveryMs

    profile := Map()
    section := Trim(clientId)
    if (section = "")
        section := "unknown"
    profile["client_id"] := section
    profile["class_name"] := StrLower(Trim(IniRead(step2ProfileFile, section, "class_name", step3ClassName)))
    profile["force_move_key"] := Trim(IniRead(step2ProfileFile, section, "force_move_key", step3ForceMoveKey))
    profile["primary_key"] := Trim(IniRead(step2ProfileFile, section, "primary_key", step3PrimaryKey))
    profile["secondary_key"] := Trim(IniRead(step2ProfileFile, section, "secondary_key", step3SecondaryKey))
    profile["hp_threshold"] := Trim(IniRead(step2ProfileFile, section, "hp_threshold", step3HpThreshold)) + 0
    profile["mp_threshold"] := Trim(IniRead(step2ProfileFile, section, "mp_threshold", step3MpThreshold)) + 0
    profile["town_threshold"] := Trim(IniRead(step2ProfileFile, section, "town_threshold", step3TownThreshold)) + 0
    profile["attack_every_ms"] := Trim(IniRead(step2ProfileFile, section, "attack_every_ms", step3AttackEveryMs)) + 0
    profile["secondary_every_ms"] := Trim(IniRead(step2ProfileFile, section, "secondary_every_ms", step3SecondaryEveryMs)) + 0
    attackRaw := StrLower(Trim(IniRead(step2ProfileFile, section, "attack_enabled", step3AttackEnabled ? "1" : "0")))
    profile["attack_enabled"] := !(attackRaw = "0" || attackRaw = "false" || attackRaw = "off")
    return profile
}

BuildFollowerRuntimeMap(force := false) {
    global hwndFollowers, followerClientByHwnd, followerProfileByHwnd, followerMapLastSyncAt, followerMapSyncMs

    now := A_TickCount
    if (!force && (now - followerMapLastSyncAt) < followerMapSyncMs)
        return

    followerClientByHwnd := Map()
    followerProfileByHwnd := Map()
    for _, hwnd in hwndFollowers {
        if (!hwnd || !WinExist("ahk_id " hwnd))
            continue
        inst := GetWindowInstance(hwnd)
        clientId := GetNameForInstance(inst)
        if (clientId = "" || clientId = "Unknown")
            continue
        followerClientByHwnd[hwnd] := clientId
        followerProfileByHwnd[hwnd] := LoadClientRuntimeProfile(clientId)
    }
    followerMapLastSyncAt := now
}

GetFollowerProfileByHwnd(hwnd) {
    global followerProfileByHwnd, step3ForceMoveKey

    if (followerProfileByHwnd.Has(hwnd))
        return followerProfileByHwnd[hwnd]

    inst := GetWindowInstance(hwnd)
    clientId := GetNameForInstance(inst)
    if (clientId = "" || clientId = "Unknown") {
        fallback := Map()
        fallback["force_move_key"] := step3ForceMoveKey
        fallback["attack_enabled"] := false
        return fallback
    }
    return LoadClientRuntimeProfile(clientId)
}

WriteQtmosBindRequest(clientId, className, characterName) {
    global qtmosBindRequestFile

    SplitPath(qtmosBindRequestFile, , &dir)
    if !DirExist(dir)
        DirCreate(dir)

    if FileExist(qtmosBindRequestFile)
        FileDelete(qtmosBindRequestFile)

    body := "[bind]`n"
        . "client_id=" clientId "`n"
        . "class_name=" className "`n"
        . "character_name=" characterName "`n"
    FileAppend(body, qtmosBindRequestFile, "UTF-8")
}

WriteActiveProfileSnapshot(clientId) {
    global activeProfileFile
    global step3ClassName, step3CharacterName, step3PrimaryKey, step3SecondaryKey, step3PickitProfile, step3ForceMoveKey
    global step3HpThreshold, step3MpThreshold, step3TownThreshold
    global step3AttackEnabled, step3AttackEveryMs, step3SecondaryEveryMs, step3AltPulseMs

    body := "{"
        . '"client_id":"' . EscapeJsonText(clientId) . '"'
        . ',"character_name":"' . EscapeJsonText(step3CharacterName) . '"'
        . ',"class_name":"' . EscapeJsonText(step3ClassName) . '"'
        . ',"hp_threshold":' . Format("{:.2f}", step3HpThreshold)
        . ',"mp_threshold":' . Format("{:.2f}", step3MpThreshold)
        . ',"town_threshold":' . Format("{:.2f}", step3TownThreshold)
        . ',"primary_key":"' . EscapeJsonText(step3PrimaryKey) . '"'
        . ',"secondary_key":"' . EscapeJsonText(step3SecondaryKey) . '"'
        . ',"force_move_key":"' . EscapeJsonText(step3ForceMoveKey) . '"'
        . ',"force_move_every_ms":' . step3AltPulseMs
        . ',"attack_enabled":' . (step3AttackEnabled ? "true" : "false")
        . ',"attack_every_ms":' . step3AttackEveryMs
        . ',"secondary_every_ms":' . step3SecondaryEveryMs
        . ',"pickit_profile":"' . EscapeJsonText(step3PickitProfile) . '"'
        . ',"updated_at":"' . EscapeJsonText(A_Now) . '"}'

    if FileExist(activeProfileFile)
        FileDelete(activeProfileFile)
    FileAppend(body, activeProfileFile, "UTF-8")
}

GetMyNameFromPath() {
    path := WinGetProcessPath("A")

    ; Loader now launches from a single path with -instance1..4
    if (path = "C:\Program Files (x86)\Diablo II Resurrected\D2R.exe") {
        instance := GetActiveD2RInstance()
        switch instance {
            case "1":
                return "DaMJMaD"
            case "2":
                return "MaD"
            case "3":
                return "Khurst"
            case "4":
                return "SSU"
        }
    }

    switch path {
        case "C:\Program Files (x86)\Diablo II Resurrected\D2R.exe":
            return "DaMJMaD"
        case "C:\Program Files (x86)\Diablo 2 Resurrected\D2R.exe":
            return "MaD"
        case "C:\Program Files (x86)\Diablo 2x2 Resurrected\D2R.exe":
            return "Khurst"
        case "C:\Program Files (x86)\Diablo 2x3 Resurrected\D2R.exe":
            return "SSU"
        default:
            MsgBox("❌ Path not matched, returning blank name")
            return ""
    }
}

GetActiveD2RInstance() {
    pid := WinGetPID("A")
    if !pid
        return ""

    cmdLine := GetProcessCommandLine(pid)
    if (cmdLine = "")
        return ""

    if RegExMatch(cmdLine, "i)-instance\s*([1-4])", &m)
        return m[1]

    return ""
}

GetProcessCommandLine(pid) {
    try {
        wmi := ComObject("WbemScripting.SWbemLocator").ConnectServer(".", "root\cimv2")
        query := "SELECT CommandLine FROM Win32_Process WHERE ProcessId=" . pid
        for proc in wmi.ExecQuery(query)
            return String(proc.CommandLine)
    } catch as err {
    }

    return ""
}
