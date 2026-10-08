#!/usr/bin/env bash

hook_json_string() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//$'\n'/\\n}
    value=${value//$'\r'/\\r}
    value=${value//$'\t'/\\t}
    value=${value//$'\b'/\\b}
    value=${value//$'\f'/\\f}
    printf '"%s"' "$value"
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
    local raw=$1 inner c escaped i
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
                '"'|'\') HOOK_SCALAR+=$escaped ;;
                *) HOOK_ERROR="Unsupported YAML escape"; return ;;
            esac
        done
        return
    fi
    raw=${raw%%' #'*}
    while [[ $raw == *' ' ]]; do raw=${raw% }; done
    if [[ $raw == null || $raw == '~' ]]; then raw=""; fi
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
    if [[ $key == extension || $key == command ]] && [[ $HOOK_QUOTED == false ]]; then
        if [[ -z $HOOK_SCALAR ]] || hook_typed_scalar "$HOOK_SCALAR"; then
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
        if [[ $HOOK_QUOTED == false && $HOOK_SCALAR =~ ^(true|false|[0-9]+)$ ]]; then
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
        priority) HOOK_PRIORITY[index]=$HOOK_SCALAR ;;
        description) HOOK_DESCRIPTION[index]=$HOOK_SCALAR ;;
        prompt) HOOK_PROMPT[index]=$HOOK_SCALAR ;;
    esac
}

hook_priority() {
    local raw=$1 whole
    HOOK_RANK=10
    [[ $raw =~ ^\+?[0-9]+(\.[0-9]+)?$ ]] || return
    whole=${raw%%.*}
    whole=${whole#+}
    (( ${#whole} <= 15 )) || return
    HOOK_RANK=$((10#$whole))
    (( HOOK_RANK >= 1 )) || HOOK_RANK=10
}

resolve_hooks() {
    local phase=$1 command=$2 event config line spaces indent text key value
    local section="" target=false empty=false item_indent=-1 index=0 seen=false seen_hooks=false seen_event=false
    local i n chosen first=true
    local -a HOOK_EXT HOOK_CMD HOOK_ENABLED HOOK_OPTIONAL HOOK_CONDITION
    local -a HOOK_PRIORITY HOOK_DESCRIPTION HOOK_PROMPT HOOK_RANKS HOOK_USED
    event="${phase}_${command}"
    if [[ ! $event =~ ^(before|after)_[a-z][a-z0-9_]*$ ]]; then
        hook_error "" "Invalid hook event: $event"
        return 1
    fi
    config=.specify/extensions.yml
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
        if (( indent == 0 )); then
            if [[ $section == installed && $text == '- '* && $text != '- ' ]]; then
                hook_scalar "${text:2}"
                [[ -n $HOOK_ERROR ]] && break
                continue
            fi
            target=false
            item_indent=-1
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
            if [[ $target == true ]]; then
                index=$((index+1))
                HOOK_ENABLED[index]=true
                HOOK_OPTIONAL[index]=true
                HOOK_PRIORITY[index]=10
                hook_field "${text:2}"
            fi
        elif (( item_indent >= 0 && indent == item_indent + 2 )); then
            if [[ $target == true ]]; then hook_field "$text"; fi
        else
            HOOK_ERROR="Unsupported YAML hook layout"
        fi
        [[ -z $HOOK_ERROR ]] || break
    done < "$config"
    [[ $seen == true ]] || HOOK_ERROR="Invalid .specify/extensions.yml: expected a hooks mapping"
    if [[ -z $HOOK_ERROR ]]; then
        for ((i=1; i<=index; i++)); do
            [[ ${HOOK_ENABLED[i]} == false || -n ${HOOK_CONDITION[i]} ]] && continue
            if [[ -z ${HOOK_EXT[i]} || -z ${HOOK_CMD[i]} ]]; then
                HOOK_ERROR="hooks.$event needs extension and command"; break
            fi
            hook_priority "${HOOK_PRIORITY[i]}"
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
