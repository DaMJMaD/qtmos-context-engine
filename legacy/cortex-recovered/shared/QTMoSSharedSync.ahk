#Requires AutoHotkey v2.0

QTMOS_GetSharedRoot(defaultFolder := "qtmos-share") {
    envRoot := EnvGet("QTMOS_SHARE_DIR")
    if (envRoot != "") {
        QTMOS_EnsureDir(envRoot)
        return envRoot
    }

    fallback := A_ScriptDir "\" defaultFolder
    QTMOS_EnsureDir(fallback)
    return fallback
}

QTMOS_GetChannelDir(channel, defaultFolder := "qtmos-share") {
    channelDir := QTMOS_GetSharedRoot(defaultFolder) "\" channel
    QTMOS_EnsureDir(channelDir)
    return channelDir
}

QTMOS_PublishState(channel, source, subject, payload, defaultFolder := "qtmos-share") {
    channelDir := QTMOS_GetChannelDir(channel, defaultFolder)
    latestPath := channelDir "\latest.json"
    eventsPath := channelDir "\events.jsonl"
    tmpPath := latestPath ".tmp"

    envelope := Map(
        "ts", QTMOS_NowIso(),
        "channel", channel,
        "source", source,
        "subject", subject,
        "payload", payload
    )

    Try FileDelete(tmpPath)
    FileAppend(QTMOS_DumpJson(envelope), tmpPath, "UTF-8-RAW")
    FileMove(tmpPath, latestPath, true)
    FileAppend(QTMOS_DumpJson(envelope) "`n", eventsPath, "UTF-8-RAW")

    return envelope
}

QTMOS_EnsureDir(path) {
    if !DirExist(path)
        DirCreate(path)
}

QTMOS_EnsureParentDir(filePath) {
    SplitPath(filePath, , &parentDir)
    if (parentDir != "")
        QTMOS_EnsureDir(parentDir)
}

QTMOS_NowIso() {
    return FormatTime(, "yyyy-MM-dd'T'HH:mm:ss")
}

QTMOS_DumpJson(value) {
    kind := Type(value)

    if (kind = "String")
        return '"' QTMOS_EscapeJson(value) '"'

    if (kind = "Integer" || kind = "Float")
        return value

    if (kind = "Array") {
        parts := []
        for item in value
            parts.Push(QTMOS_DumpJson(item))
        return "[" QTMOS_Join(parts, ",") "]"
    }

    if (kind = "Map") {
        parts := []
        for key, item in value
            parts.Push('"' QTMOS_EscapeJson(String(key)) '":' QTMOS_DumpJson(item))
        return "{" QTMOS_Join(parts, ",") "}"
    }

    if (value = true)
        return "true"
    if (value = false)
        return "false"

    return '"' QTMOS_EscapeJson(String(value)) '"'
}

QTMOS_EscapeJson(text) {
    text := StrReplace(text, "\", "\\")
    text := StrReplace(text, '"', '\"')
    text := StrReplace(text, "`r", "\r")
    text := StrReplace(text, "`n", "\n")
    text := StrReplace(text, "`t", "\t")
    return text
}

QTMOS_Join(items, delim) {
    output := ""
    for index, item in items {
        if (index > 1)
            output .= delim
        output .= item
    }
    return output
}
