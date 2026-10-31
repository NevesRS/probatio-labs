if [ -d /flag ] && [ -t 1 ] && [ -z "${FLAG_WATCH_ACTIVE:-}" ]; then
    export FLAG_WATCH_ACTIVE=1
    (
        _last=""
        while true; do
            if [ -r /flag/flag.txt ]; then
                _cur=$(md5sum /flag/flag.txt 2>/dev/null)
                if [ -n "$_cur" ] && [ "$_cur" != "$_last" ]; then
                    _flag=$(tr -d '\n' < /flag/flag.txt)
                    printf '\r\n\r\n\e[2K==============================================================\r\n\e[2K  OBJETIVO CONCLUIDO — FLAG GERADA\r\n\e[2K  %s\r\n\e[2K  Valide no frontend: http://localhost:8080\r\n\e[2K==============================================================\r\n\r\n' "$_flag" >/dev/tty
                    _last="$_cur"
                fi
            fi
            sleep 1
        done
    ) >/dev/tty 2>&1 &
    disown 2>/dev/null || true
fi
