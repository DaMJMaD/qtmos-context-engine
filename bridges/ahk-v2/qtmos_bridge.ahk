#Requires AutoHotkey v2.0
#SingleInstance Force

global BRIDGE_ROOT := A_ScriptDir
global DATA_DIR := BRIDGE_ROOT "\data"
global DEFAULTS_FILE := DATA_DIR "\default_knowledge.txt"
global LEARN_LOG := DATA_DIR "\learn.jsonl"
global RECORD_LOG := DATA_DIR "\record.jsonl"

EnsureDir(DATA_DIR)

args := A_Args
if (args.Length = 0) {
    ShowStatus()
    ExitApp()
}

command := StrLower(args[1])

switch command {
    case "status":
        ShowStatus()
    case "defaults":
        ShowDefaults()
    case "learn":
        if (args.Length < 2)
            FailUsage("learn <text>")
        Learn(args[2])
    case "record":
        if (args.Length < 3)
            FailUsage("record <kind> <subject> [value]")
        value := args.Length >= 4 ? args[4] : ""
        Record(args[2], args[3], value)
    default:
        FailUsage("status | defaults | learn <text> | record <kind> <subject> [value]")
}

ExitApp()

ShowStatus() {
    defaults := LoadDefaults()
    learnCount := CountJsonl(LEARN_LOG)
    recordCount := CountJsonl(RECORD_LOG)

    output := []
    output.Push("QTMoS AHK Bridge")
    output.Push("bridge_root=" BRIDGE_ROOT)
    output.Push("defaults=" defaults.Length)
    output.Push("learn_entries=" learnCount)
    output.Push("record_entries=" recordCount)
    output.Push("data_dir=" DATA_DIR)
    WriteLinesToStdout(output)
}

ShowDefaults() {
    defaults := LoadDefaults()
    output := []
    output.Push("QTMoS AHK Defaults")
    for index, line in defaults
        output.Push(index ". " line)
    WriteLinesToStdout(output)
}

Learn(text) {
    entry := Map(
        "ts", NowIso(),
        "kind", "learn",
        "text", text
    )
    AppendJsonLine(LEARN_LOG, entry)
    WriteLinesToStdout(["learned=" text])
}

Record(kind, subject, value := "") {
    entry := Map(
        "ts", NowIso(),
        "kind", kind,
        "subject", subject,
        "value", value
    )
    AppendJsonLine(RECORD_LOG, entry)
    WriteLinesToStdout(["recorded=" kind " subject=" subject])
}

LoadDefaults() {
    items := []
    if !FileExist(DEFAULTS_FILE)
        return items

    text := FileRead(DEFAULTS_FILE, "UTF-8")
    for line in StrSplit(text, "`n", "`r") {
        clean := Trim(line)
        if (clean != "")
            items.Push(clean)
    }
    return items
}

CountJsonl(path) {
    if !FileExist(path)
        return 0

    count := 0
    for line in StrSplit(FileRead(path, "UTF-8"), "`n", "`r") {
        if (Trim(line) != "")
            count += 1
    }
    return count
}

AppendJsonLine(path, obj) {
    json := DumpJson(obj)
    FileAppend(json "`n", path, "UTF-8-RAW")
}

DumpJson(value) {
    kind := Type(value)

    if (kind = "String")
        return '"' EscapeJson(value) '"'

    if (kind = "Integer" || kind = "Float")
        return value

    if (kind = "Array") {
        parts := []
        for item in value
            parts.Push(DumpJson(item))
        return "[" Join(parts, ",") "]"
    }

    if (kind = "Map") {
        parts := []
        for key, item in value
            parts.Push('"' EscapeJson(key) '":' DumpJson(item))
        return "{" Join(parts, ",") "}"
    }

    if (value = true)
        return "true"
    if (value = false)
        return "false"

    return '"' EscapeJson(String(value)) '"'
}

EscapeJson(text) {
    text := StrReplace(text, "\", "\\")
    text := StrReplace(text, '"', '\"')
    text := StrReplace(text, "`r", "\r")
    text := StrReplace(text, "`n", "\n")
    text := StrReplace(text, "`t", "\t")
    return text
}

Join(items, delim) {
    out := ""
    for index, item in items {
        if (index > 1)
            out .= delim
        out .= item
    }
    return out
}

WriteLinesToStdout(lines) {
    for _, line in lines
        FileAppend(line "`n", "*", "UTF-8-RAW")
}

NowIso() {
    timestamp := FormatTime(, "yyyy-MM-dd'T'HH:mm:ss")
    return timestamp
}

EnsureDir(path) {
    if !DirExist(path)
        DirCreate(path)
}

FailUsage(message) {
    WriteLinesToStdout([
        "usage_error=" message,
        "commands=status | defaults | learn <text> | record <kind> <subject> [value]"
    ])
    ExitApp(2)
}
