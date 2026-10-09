#!/usr/bin/env bash

hook_json_string() {
    local value=$1 code hex char
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    value=${value//$'\t'/\\t}
    value=${value//$'\b'/\\b}
    value=${value//$'\f'/\\f}
    for ((code=1; code<32; code++)); do
        printf -v hex '%02X' "$code"
        printf -v char '%b' "\\x$hex"
        value=${value//$char/\\u00$hex}
    done
    printf '"%s"' "$value"
}

hook_unicode() {
    local number=$1 bytes
    HOOK_UTF8=""
    if (( number == 0 || number > 0x10ffff || (number >= 0xd800 && number <= 0xdfff) )); then
        HOOK_ERROR="Unsupported YAML escape"
        return
    fi
    if (( number < 0x80 )); then
        printf -v bytes '\\x%02X' "$number"
    elif (( number < 0x800 )); then
        printf -v bytes '\\x%02X\\x%02X' "$((0xc0 | (number >> 6)))" "$((0x80 | (number & 0x3f)))"
    elif (( number < 0x10000 )); then
        printf -v bytes '\\x%02X\\x%02X\\x%02X' "$((0xe0 | (number >> 12)))" "$((0x80 | ((number >> 6) & 0x3f)))" "$((0x80 | (number & 0x3f)))"
    else
        printf -v bytes '\\x%02X\\x%02X\\x%02X\\x%02X' "$((0xf0 | (number >> 18)))" "$((0x80 | ((number >> 12) & 0x3f)))" "$((0x80 | ((number >> 6) & 0x3f)))" "$((0x80 | (number & 0x3f)))"
    fi
    printf -v HOOK_UTF8 '%b' "$bytes"
}

hook_error() {
    printf '{"event":'
    hook_json_string "$1"
    printf ',"hooks":[],"error":'
    hook_json_string "$2"
    printf '}\n'
    return 1
}

hook_scalar() {
    local raw=$1 inner c escaped i digits count
    while [[ $raw == ' '* ]]; do raw=${raw# }; done
    while [[ $raw == *' ' ]]; do raw=${raw% }; done
    HOOK_QUOTED=false
    if [[ $raw == \'* ]]; then
        HOOK_QUOTED=true
        if (( ${#raw} < 2 )) || [[ $raw != *\' ]]; then
            HOOK_ERROR="Unsupported YAML scalar"
            return
        fi
        inner=${raw:1:${#raw}-2}
        if [[ ${inner//\'\'/} == *\'* ]]; then HOOK_ERROR="Unsupported YAML scalar"; return; fi
        HOOK_SCALAR=${inner//\'\'/\'}
        return
    fi
    if [[ $raw == \"* ]]; then
        HOOK_QUOTED=true
        if (( ${#raw} < 2 )) || [[ $raw != *\" ]]; then
            HOOK_ERROR="Unsupported YAML scalar"
            return
        fi
        inner=${raw:1:${#raw}-2}
        HOOK_SCALAR=""
        for ((i=0; i<${#inner}; i++)); do
            c=${inner:i:1}
            if [[ $c != '\' ]]; then HOOK_SCALAR+=$c; continue; fi
            ((i++))
            escaped=${inner:i:1}
            case $escaped in
                n) HOOK_SCALAR+=$'\n' ;;
                t) HOOK_SCALAR+=$'\t' ;;
                r) HOOK_SCALAR+=$'\r' ;;
                b) HOOK_SCALAR+=$'\b' ;;
                f) HOOK_SCALAR+=$'\f' ;;
                a) HOOK_SCALAR+=$'\a' ;;
                v) HOOK_SCALAR+=$'\v' ;;
                e) HOOK_SCALAR+=$'\033' ;;
                N) hook_unicode 0x85; HOOK_SCALAR+=$HOOK_UTF8 ;;
                _) hook_unicode 0xa0; HOOK_SCALAR+=$HOOK_UTF8 ;;
                L) hook_unicode 0x2028; HOOK_SCALAR+=$HOOK_UTF8 ;;
                P) hook_unicode 0x2029; HOOK_SCALAR+=$HOOK_UTF8 ;;
                x|u|U)
                    count=2
                    [[ $escaped == u ]] && count=4
                    [[ $escaped == U ]] && count=8
                    digits=${inner:i+1:count}
                    if (( ${#digits} != count )) || [[ ! $digits =~ ^[[:xdigit:]]+$ ]]; then
                        HOOK_ERROR="Unsupported YAML escape"; return
                    fi
                    hook_unicode "$((16#$digits))"
                    [[ -n $HOOK_ERROR ]] && return
                    HOOK_SCALAR+=$HOOK_UTF8
                    i=$((i+count))
                    ;;
                '"'|'\'|'/') HOOK_SCALAR+=$escaped ;;
                *) HOOK_ERROR="Unsupported YAML escape"; return ;;
            esac
        done
        return
    fi
    raw=${raw%%' #'*}
    while [[ $raw == *' ' ]]; do raw=${raw% }; done
    if [[ $raw == null || $raw == Null || $raw == NULL || $raw == '~' ]]; then raw=""; fi
    case $raw in
        *'['*|*']'*|*'{'*|*'}'*|*': '*|'&'*|'*'*|'!'*|'|'*|'>'*)
            HOOK_ERROR="Unsupported YAML scalar"; return ;;
    esac
    HOOK_SCALAR=$raw
}

hook_typed_scalar() {
    case $1 in
        [Tt][Rr][Uu][Ee]|[Ff][Aa][Ll][Ss][Ee]|[Yy][Ee][Ss]|[Nn][Oo]|[Oo][Nn]|[Oo][Ff][Ff])
            return 0 ;;
    esac
    [[ $1 =~ ^[+-]?(0[xX][0-9a-fA-F_]+|0[oO][0-7_]+|0[bB][01_]+|[0-9][0-9_]*(\.[0-9_]*)?([eE][+-]?[0-9]+)?|\.[0-9_]+([eE][+-]?[0-9]+)?|\.([iI][nN][fF]|[nN][aA][nN]))$ ||
       $1 =~ ^[0-9]+(:[0-9]+)+$ ||
       $1 =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}([Tt\ ]|$) ]]
}

hook_field() {
    local field=$1 key raw
    if [[ ! $field =~ ^([a-z_]+):([[:space:]]|$) ]]; then
        HOOK_ERROR="Unsupported YAML hook field"
        return
    fi
    key=${BASH_REMATCH[1]}
    raw=${field:${#key}+1}
    hook_scalar "$raw"
    [[ -n $HOOK_ERROR ]] && return
    if [[ $key == extension || $key == command ]]; then
        if [[ -z $HOOK_SCALAR ]] ||
           { [[ $HOOK_QUOTED == false ]] && hook_typed_scalar "$HOOK_SCALAR"; }; then
            HOOK_ERROR="hooks.$event needs extension and command"
            return
        fi
    fi
    if [[ $key == condition && $HOOK_QUOTED == false && -n $HOOK_SCALAR ]] &&
       hook_typed_scalar "$HOOK_SCALAR"; then
        HOOK_ERROR="condition must be a string or null"
        return
    fi
    if [[ $key == enabled || $key == optional ]]; then
        if [[ $HOOK_QUOTED == true || ( $HOOK_SCALAR != true && $HOOK_SCALAR != false ) ]]; then
            HOOK_ERROR="$key must be a boolean"
            return
        fi
    fi
    if [[ $key == description || $key == prompt ]]; then
        if [[ $HOOK_QUOTED == false && -n $HOOK_SCALAR ]] &&
           hook_typed_scalar "$HOOK_SCALAR"; then
            HOOK_ERROR="$key must be a string"
            return
        fi
    fi
    case $key in
        extension) HOOK_EXT[index]=$HOOK_SCALAR ;;
        command) HOOK_CMD[index]=$HOOK_SCALAR ;;
        enabled) HOOK_ENABLED[index]=$HOOK_SCALAR ;;
        optional) HOOK_OPTIONAL[index]=$HOOK_SCALAR ;;
        condition) HOOK_CONDITION[index]=$HOOK_SCALAR ;;
        priority) HOOK_PRIORITY[index]=$HOOK_SCALAR; HOOK_PRIORITY_QUOTED[index]=$HOOK_QUOTED ;;
        description) HOOK_DESCRIPTION[index]=$HOOK_SCALAR ;;
        prompt) HOOK_PROMPT[index]=$HOOK_SCALAR ;;
    esac
}

hook_installed_field() {
    local field=$1 key raw
    if [[ ! $field =~ ^([a-z_]+):([[:space:]]|$) ]]; then
        HOOK_ERROR="Unsupported YAML installed entry"
        return
    fi
    key=${BASH_REMATCH[1]}
    raw=${field:${#key}+1}
    if [[ $raw =~ ^(.*[\"\'])[[:space:]]+#.*$ ]]; then raw=${BASH_REMATCH[1]}; fi
    hook_scalar "$raw"
}

hook_priority() {
    local raw=$1 quoted=$2 whole frac="" exponent=0 shift digits part octal=false
    HOOK_RANK=10
    [[ $raw == -* ]] && return
    if [[ $quoted == false && $raw =~ ^\+?0x[0-9a-fA-F_]+$ ]]; then
        digits=${raw#+}
        digits=${digits:2}
        digits=${digits//_/}
        while [[ $digits == 0* && ${#digits} -gt 1 ]]; do digits=${digits#0}; done
        (( ${#digits} <= 8 )) || return
        HOOK_RANK=$((16#$digits))
    elif [[ $quoted == false && $raw =~ ^\+?0b[01_]+$ ]]; then
        digits=${raw#+}
        digits=${digits:2}
        digits=${digits//_/}
        while [[ $digits == 0* && ${#digits} -gt 1 ]]; do digits=${digits#0}; done
        (( ${#digits} <= 31 )) || return
        HOOK_RANK=$((2#$digits))
    elif [[ $quoted == false && $raw =~ ^\+?[1-9][0-9_]*(:[0-5]?[0-9])+$ ]]; then
        digits=${raw#+}
        digits=${digits//_/}
        HOOK_RANK=0
        while [[ $digits == *:* ]]; do
            part=${digits%%:*}
            (( ${#part} <= 10 )) || { HOOK_RANK=10; return; }
            HOOK_RANK=$((HOOK_RANK * 60 + 10#$part))
            (( HOOK_RANK <= 2147483647 )) || { HOOK_RANK=10; return; }
            digits=${digits#*:}
        done
        HOOK_RANK=$((HOOK_RANK * 60 + 10#$digits))
    else
        if [[ $raw =~ ^\+?[0-9][0-9_]*$ ]]; then
            digits=${raw#+}
            [[ $quoted == false && $digits =~ ^0[0-7_]+$ ]] && octal=true
            digits=${digits//_/}
            if [[ $octal == true ]]; then
                while [[ $digits == 0* && ${#digits} -gt 1 ]]; do digits=${digits#0}; done
                (( ${#digits} <= 11 )) || return
                HOOK_RANK=$((8#$digits))
                (( HOOK_RANK >= 1 && HOOK_RANK <= 2147483647 )) || HOOK_RANK=10
                return
            fi
        elif [[ $quoted == false && $raw =~ ^[+]?[0-9][0-9_]*\.[0-9_]*([eE][+-][0-9]+)?$ ]]; then
            digits=${raw#+}
            digits=${digits//_/}
            if [[ $digits == *[eE]* ]]; then
                exponent=${digits##*[eE]}
                (( ${#exponent} <= 4 )) || return
                digits=${digits%[eE]*}
            fi
            whole=${digits%%.*}
            frac=${digits#*.}
            shift=$((exponent - ${#frac}))
            digits=$whole$frac
            if (( shift >= 0 )); then
                (( shift <= 10 )) || return
                while (( shift > 0 )); do digits+=0; shift=$((shift-1)); done
            else
                (( ${#digits} + shift > 0 )) || return
                digits=${digits:0:${#digits}+shift}
            fi
        else
            return
        fi
        while [[ $digits == 0* && ${#digits} -gt 1 ]]; do digits=${digits#0}; done
        (( ${#digits} <= 10 )) || return
        HOOK_RANK=$((10#$digits))
    fi
    (( HOOK_RANK >= 1 && HOOK_RANK <= 2147483647 )) || HOOK_RANK=10
}

hook_digest_valid() {
    local path=$1 digest=$2 expected actual
    [[ -f $path && -f $digest ]] || return 1
    IFS= read -r expected < "$digest"
    if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum -- "$path") || return 1
    elif command -v shasum >/dev/null 2>&1; then
        actual=$(shasum -a 256 -- "$path") || return 1
    else
        HOOK_ERROR="Cannot validate hook projection: sha256sum or shasum is required"
        return 1
    fi
    [[ $expected =~ ^[0-9a-f]{64}$ && ${actual%% *} == "$expected" ]]
}

hook_projection_shape_valid() {
    local response=$1 event=$2
    local string='"([^"\\[:cntrl:]]|\\(["\\/bfnrt]|u[[:xdigit:]]{4}))*"'
    local required='"([^"\\[:cntrl:]]|\\(["\\/bfnrt]|u[[:xdigit:]]{4}))+"'
    local entry='\{"extension":'"$required"',"command":'"$required"',"optional":(true|false),"description":'"$string"',"prompt":'"$string"',"priority":[1-9][0-9]*\}'
    local shape='^\{"event":"'"$event"'","hooks":\[('"$entry"'(,'"$entry"')*)?\]\}$'
    [[ $response =~ $shape ]]
}

resolve_hooks() {
    local phase=$1 command=$2 event config line spaces indent text key value
    local section="" target=false empty=false item_indent=-1 installed_indent=-1 index=0 seen=false seen_hooks=false seen_event=false
    local i n chosen first=true
    local -a HOOK_EXT HOOK_CMD HOOK_ENABLED HOOK_OPTIONAL HOOK_CONDITION
    local -a HOOK_PRIORITY HOOK_PRIORITY_QUOTED HOOK_DESCRIPTION HOOK_PROMPT HOOK_RANKS HOOK_USED HOOK_EVENTS HOOK_TARGETS
    event="${phase}_${command}"
    if [[ ! $event =~ ^(before|after)_[a-z][a-z0-9_]*$ ]]; then
        hook_error "$event" "Invalid hook event: $event"
        return 1
    fi
    config=.specify/extensions.yml
    if [[ -f $config && ! -d .specify/hook-dispatch ]]; then
        IFS= read -r line < "$config"
        if [[ $line == '# Hook projection: .specify/hook-dispatch' ]]; then
            hook_error "$event" "Hook projection is missing; reinstall the extension or refresh the project"
            return 1
        fi
    fi
    if [[ -d .specify/hook-dispatch ]]; then
        if [[ ! -f $config || ! -f .specify/hook-dispatch/source.yml ||
              ! -f .specify/hook-dispatch/events.txt ]] ||
           ! cmp -s -- "$config" .specify/hook-dispatch/source.yml; then
            hook_error "$event" "Hook projection is stale; reinstall the extension or refresh the project"
            return 1
        fi
        HOOK_ERROR=""
        if ! hook_digest_valid .specify/hook-dispatch/events.txt .specify/hook-dispatch/events.txt.sha256; then
            hook_error "$event" "${HOOK_ERROR:-Hook projection index is invalid; reinstall the extension or refresh the project}"
            return 1
        fi
        if [[ -f .specify/hook-dispatch/$event.json ]]; then
            local projection=".specify/hook-dispatch/$event.json" response
            if ! hook_digest_valid "$projection" ".specify/hook-dispatch/$event.sha256"; then
                hook_error "$event" "${HOOK_ERROR:-Hook projection is invalid; reinstall the extension or refresh the project}"
                return 1
            fi
            if ! IFS= read -r response < "$projection" ||
               ! hook_projection_shape_valid "$response" "$event"; then
                hook_error "$event" "Invalid hook projection; reinstall the extension or refresh the project"
                return 1
            fi
            cat -- "$projection"
        elif grep -Fxq -- "$event" .specify/hook-dispatch/events.txt; then
            hook_error "$event" "Hook projection is incomplete; reinstall the extension or refresh the project"
            return 1
        else
            printf '{"event":"%s","hooks":[]}\n' "$event"
        fi
        return
    fi
    if [[ ! -e $config ]]; then
        printf '{"event":"%s","hooks":[]}\n' "$event"
        return
    fi
    if [[ ! -r $config ]]; then
        hook_error "$event" "Could not read .specify/extensions.yml"
        return 1
    fi
    HOOK_ERROR=""
    while IFS= read -r line || [[ -n $line ]]; do
        line=${line%$'\r'}
        [[ $line =~ ^[[:space:]]*(#|$) ]] && continue
        seen=true
        if [[ $line == *$'\t'* ]]; then HOOK_ERROR="Tabs are not supported in canonical YAML"; break; fi
        spaces=${line%%[! ]*}
        indent=${#spaces}
        text=${line:indent}
        if [[ $section == installed && $text == '- '* && ( $indent == 0 || $indent == 2 ) ]]; then
            if [[ ${text:2} =~ ^[a-z_]+:([[:space:]]|$) ]]; then
                installed_indent=$indent
                hook_installed_field "${text:2}"
            else
                installed_indent=-1
                hook_scalar "${text:2}"
            fi
            [[ -n $HOOK_ERROR ]] && break
            continue
        fi
        if (( indent == 0 )); then
            target=false
            item_indent=-1
            installed_indent=-1
            if [[ $text == 'hooks:' || $text == 'hooks: {}' ]]; then
                if [[ $seen_hooks == true ]]; then HOOK_ERROR="Duplicate hooks mapping"; break; fi
                seen_hooks=true
                section=hooks
                empty=false
            elif [[ $text == hooks:* ]]; then
                HOOK_ERROR="Invalid .specify/extensions.yml: expected a hooks mapping"
            elif [[ $text == 'installed:' || $text == 'installed: []' ]]; then
                section=installed
            elif [[ $text == 'settings:' || $text == 'settings: {}' ]]; then
                section=settings
            else
                HOOK_ERROR="Unsupported YAML top-level layout"
            fi
            [[ -z $HOOK_ERROR ]] || break
            continue
        fi
        if [[ $section != hooks ]]; then
            if [[ $section == installed && $installed_indent -ge 0 &&
                  $indent -eq $((installed_indent+2)) ]]; then
                hook_installed_field "$text"
                [[ -n $HOOK_ERROR ]] && break
                continue
            fi
            if [[ $section != settings || $indent != 2 || ! $text =~ ^[a-z_]+:([[:space:]]|$) ]]; then
                HOOK_ERROR="Unsupported YAML top-level layout"; break
            fi
            key=${text%%:*}
            hook_scalar "${text:${#key}+1}"
            [[ -n $HOOK_ERROR ]] && break
            continue
        fi
        if (( indent == 2 )) && [[ $text =~ ^([a-z][a-z0-9_]*):([[:space:]]|$) ]]; then
            key=${BASH_REMATCH[1]}
            value=${text:${#key}+1}
            while [[ $value == ' '* ]]; do value=${value# }; done
            target=false
            if [[ $key == "$event" ]]; then
                if [[ $seen_event == true ]]; then HOOK_ERROR="Duplicate hook event"; break; fi
                seen_event=true
                target=true
            fi
            if [[ -n $value && $value != '[]' ]]; then
                HOOK_ERROR="hooks.$key must be a list"; break
            fi
            empty=false
            [[ $value == '[]' ]] && empty=true
            item_indent=-1
            continue
        fi
        if [[ $text == '- '* && ( $indent == 2 || $indent == 4 ) && $empty == false ]]; then
            item_indent=$indent
            index=$((index+1))
            HOOK_EVENTS[index]=$key
            HOOK_TARGETS[index]=$target
            HOOK_ENABLED[index]=true
            HOOK_OPTIONAL[index]=true
            HOOK_PRIORITY[index]=10
            hook_field "${text:2}"
        elif (( item_indent >= 0 && indent == item_indent + 2 )); then
            hook_field "$text"
        else
            HOOK_ERROR="Unsupported YAML hook layout"
        fi
        [[ -z $HOOK_ERROR ]] || break
    done < "$config"
    [[ $seen == true ]] || HOOK_ERROR="Invalid .specify/extensions.yml: expected a hooks mapping"
    if [[ -z $HOOK_ERROR ]]; then
        for ((i=1; i<=index; i++)); do
            if [[ -z ${HOOK_EXT[i]} || -z ${HOOK_CMD[i]} ]]; then
                HOOK_ERROR="hooks.${HOOK_EVENTS[i]} needs extension and command"; break
            fi
            [[ ${HOOK_TARGETS[i]} != true || ${HOOK_ENABLED[i]} == false || -n ${HOOK_CONDITION[i]} ]] && continue
            hook_priority "${HOOK_PRIORITY[i]}" "${HOOK_PRIORITY_QUOTED[i]}"
            HOOK_RANKS[i]=$HOOK_RANK
        done
    fi
    if [[ -n $HOOK_ERROR ]]; then
        hook_error "$event" "$HOOK_ERROR"
        return 1
    fi
    printf '{"event":"%s","hooks":[' "$event"
    for ((n=1; n<=index; n++)); do
        chosen=0
        for ((i=1; i<=index; i++)); do
            if [[ -n ${HOOK_RANKS[i]} && -z ${HOOK_USED[i]} ]] &&
                (( chosen == 0 || HOOK_RANKS[i] < HOOK_RANKS[chosen] )); then
                chosen=$i
            fi
        done
        (( chosen )) || break
        HOOK_USED[chosen]=true
        if [[ $first == false ]]; then printf ','; fi
        first=false
        printf '{"extension":'; hook_json_string "${HOOK_EXT[chosen]}"
        printf ',"command":'; hook_json_string "${HOOK_CMD[chosen]}"
        printf ',"optional":%s,"description":' "${HOOK_OPTIONAL[chosen]}"
        hook_json_string "${HOOK_DESCRIPTION[chosen]}"
        printf ',"prompt":'; hook_json_string "${HOOK_PROMPT[chosen]}"
        printf ',"priority":%s}' "${HOOK_RANKS[chosen]}"
    done
    printf ']}\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    resolve_hooks before "$1"
fi
