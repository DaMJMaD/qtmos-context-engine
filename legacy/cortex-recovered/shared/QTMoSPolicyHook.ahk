#Requires AutoHotkey v2.0
#Include "QTMoSSharedSync.ahk"

global QTMOS_LastPolicyHookId := ""

if QTMOS_HasCliArg("--once") {
    WatchQTMoSPolicy()
    ExitApp()
}

SetTimer(WatchQTMoSPolicy, 1000)
WatchQTMoSPolicy()

WatchQTMoSPolicy() {
    global QTMOS_LastPolicyHookId

    latestPath := QTMOS_GetChannelDir("ahk-policy") "\latest.json"
    if !FileExist(latestPath)
        return

    Try jsonText := FileRead(latestPath, "UTF-8")
    Catch
        return

    hookId := QTMOS_JsonValue(jsonText, "hook_id")
    if (hookId = "" || hookId = QTMOS_LastPolicyHookId)
        return

    action := QTMOS_JsonValue(jsonText, "action", "warn")
    reason := QTMOS_JsonValue(jsonText, "reason", "No reason provided")
    policyRule := QTMOS_JsonValue(jsonText, "policy_rule", "default_fallback")
    summary := QTMOS_JsonValue(jsonText, "summary", "")
    surfaceTitle := QTMOS_JsonValue(jsonText, "surface_title", "unknown surface")
    surfaceId := QTMOS_JsonValue(jsonText, "surface_id", "unknown surface")
    webOrigin := QTMOS_JsonValue(jsonText, "web_origin", "unknown origin")
    contextCondition := QTMOS_JsonValue(jsonText, "context_condition", QTMOS_JsonValue(jsonText, "mindseye_condition", "UNKNOWN"))
    severity := QTMOS_JsonValue(jsonText, "severity", "")
    uiHint := QTMOS_JsonValue(jsonText, "ui_hint", action)

    QTMOS_ShowPolicyAction(
        hookId,
        action,
        reason,
        policyRule,
        summary,
        surfaceTitle,
        surfaceId,
        webOrigin,
        contextCondition,
        severity,
        uiHint
    )
    QTMOS_LastPolicyHookId := hookId
}

QTMOS_ShowPolicyAction(hookId, action, reason, policyRule, summary, surfaceTitle, surfaceId, webOrigin, contextCondition, severity := "", uiHint := "") {
    action := StrLower(action)
    header := "QTMoS " StrUpper(action) " [" policyRule "]"
    detail := reason
    if (summary != "")
        detail .= "`n" summary
    detail .= "`nSurface: " surfaceTitle
    detail .= "`nSurface ID: " surfaceId
    detail .= "`nWeb: " webOrigin
    detail .= "`nContext: " contextCondition
    if (severity != "")
        detail .= "`nSeverity: " severity
    if (uiHint != "")
        detail .= "`nUI Hint: " uiHint

    quietAllow := (action = "allow")
    subtleHeader := "QTMoS " StrUpper(action)

    switch action {
        case "allow":
            ToolTip("✅ " subtleHeader "`n" reason)
            SetTimer(() => ToolTip(), -1500)
        case "warn":
            SoundBeep(700, 150)
            ToolTip("⚠️ " header "`n" reason)
            SetTimer(() => ToolTip(), -4000)
        case "review":
            SoundBeep(900, 300)
            result := MsgBox(detail "`n`nContinue anyway?", header, "YN Icon? T12")
            QTMOS_LogPolicyFeedback(
                hookId,
                action,
                policyRule,
                result = "Yes" ? "continue" : result = "No" ? "decline" : "timeout",
                surfaceId,
                surfaceTitle,
                webOrigin,
                reason,
                contextCondition,
                summary
            )
            if (result = "No") {
                ToolTip("QTMoS: Review declined - logged")
                SetTimer(() => ToolTip(), -2200)
            } else if (result != "Yes") {
                ToolTip("QTMoS: Review timed out - logged")
                SetTimer(() => ToolTip(), -2200)
            }
        case "quarantine":
            SoundBeep(600, 500)
            SoundBeep(800, 300)
            ToolTip("🛡️ " header "`n" reason)
            SetTimer(() => ToolTip(), -8000)
        case "deny":
            SoundBeep(1200, 800)
            MsgBox(detail, header, "Iconx T12")
        default:
            ToolTip(header "`n" reason)
            SetTimer(() => ToolTip(), -2000)
    }
}

QTMOS_LogPolicyFeedback(hookId, action, policyRule, userResponse, surfaceId, surfaceTitle, webOrigin, reason, contextCondition, summary) {
    payload := Map(
        "observer", "QTMoSPolicyHook",
        "original_hook_id", hookId,
        "original_action", action,
        "original_rule", policyRule,
        "user_response", userResponse,
        "surface_id", surfaceId,
        "surface_title", surfaceTitle,
        "web_origin", webOrigin,
        "reason", reason,
        "context_condition", contextCondition,
        "summary", summary
    )
    QTMOS_PublishState("ahk-feedback", "QTMoSPolicyHook", "review_response", payload)
}

QTMOS_JsonValue(jsonText, key, fallback := "") {
    pattern := '"' key '":\s*"((?:\\.|[^"])*)"'
    if RegExMatch(jsonText, pattern, &match)
        return QTMOS_JsonUnescape(match[1])

    boolPattern := '"' key '":\s*(true|false)'
    if RegExMatch(jsonText, boolPattern, &boolMatch)
        return boolMatch[1]

    numberPattern := '"' key '":\s*(-?\d+(?:\.\d+)?)'
    if RegExMatch(jsonText, numberPattern, &numberMatch)
        return numberMatch[1]

    return fallback
}

QTMOS_JsonUnescape(text) {
    text := StrReplace(text, '\"', '"')
    text := StrReplace(text, "\\", "\")
    text := StrReplace(text, "\r", "`r")
    text := StrReplace(text, "\n", "`n")
    text := StrReplace(text, "\t", "`t")
    return text
}

QTMOS_HasCliArg(target) {
    for arg in A_Args {
        if (arg = target)
            return true
    }
    return false
}
