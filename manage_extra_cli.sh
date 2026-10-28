# Sourced by manage.sh — web shop + dedicated sub CLI (upstream features, fork helpers).
# Do not run this file directly.

DSUB_PORT=8004

dsub_cli() {
    ( cd "$INSTALL_DIR" && source venv/bin/activate && python -m dedicated_sub "$1"; deactivate ) 2>/dev/null
}

setup_dedicated_sub() {
    if [ ! -d "$INSTALL_DIR/sub_server" ]; then
        echo -e "${RED}$(t dsub_dir_missing)${RESET}"
        return
    fi
    read -rp "$(t prompt_domain_dsub)" DOMAIN
    if [ -z "$DOMAIN" ]; then
        echo -e "${RED}$(t domain_empty)${RESET}"
        return
    fi
    echo -e "${CYAN}$(t checking_dns)${RESET}"
    SERVER_IP=$(curl -fsSL ifconfig.me || echo "")
    DOMAIN_IP=$(getent ahosts "$DOMAIN" 2>/dev/null | awk '{print $1}' | head -1)
    if [ -n "$SERVER_IP" ] && [ -n "$DOMAIN_IP" ] && [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
        echo -e "${YELLOW}$(t dns_mismatch_warn "$SERVER_IP" "$DOMAIN_IP")${RESET}"
        read -rp "$(t continue_prompt)" CONT
        [ "$CONT" != "yes" ] && return
    fi
    echo -e "${CYAN}$(t installing_nginx)${RESET}"
    sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 apt-get update -qq
    timeout 120 sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 \
        apt-get install -y -qq nginx certbot python3-certbot-nginx > /dev/null
    tune_nginx_for_scale
    echo -e "${CYAN}$(t installing_miniapp_pkgs)${RESET}"
    cd "$INSTALL_DIR"
    source venv/bin/activate
    $PIP_CPU_TORCH || true
    $PIP_REQS
    deactivate
    echo -e "${CYAN}$(t creating_dsub_service)${RESET}"
    DSUB_SERVICE="${SERVICE_NAME}-sub"
    EXEC_START="$(service_exec_start "$INSTALL_DIR/venv/bin/uvicorn" "sub_server.server:app" "--host" "127.0.0.1" "--port" "$DSUB_PORT" "--workers" "1" "--no-proxy-headers")"
    sudo bash -c "cat > /etc/systemd/system/${DSUB_SERVICE}.service" <<EOF
[Unit]
Description=ShopVPN Dedicated Subscription Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$EXEC_START
Restart=always
RestartSec=5
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable "$DSUB_SERVICE" > /dev/null 2>&1
    repair_unit_execstart "/etc/systemd/system/${DSUB_SERVICE}.service" \
        "$(unit_default_execstart "$DSUB_SERVICE")" > /dev/null
    restart_service_and_wait "$DSUB_SERVICE" || true
    echo -e "${CYAN}$(t configuring_nginx "$DOMAIN")${RESET}"
    sudo bash -c "cat > /etc/nginx/sites-available/${DOMAIN}.conf" <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 100m;
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;

    location / {
        proxy_pass http://127.0.0.1:$DSUB_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$remote_addr;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    sudo ln -sf "/etc/nginx/sites-available/${DOMAIN}.conf" "/etc/nginx/sites-enabled/${DOMAIN}.conf"
    if ! sudo nginx -t > /dev/null 2>&1; then
        echo -e "${RED}$(t nginx_error "$(sudo nginx -t 2>&1)")${RESET}"
        return
    fi
    sudo systemctl reload nginx
    echo -e "${CYAN}$(t getting_ssl)${RESET}"
    sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos \
        --register-unsafely-without-email --redirect
    if [ $? -ne 0 ]; then
        echo -e "${RED}$(t ssl_failed)${RESET}"
        return
    fi
    set_env_key DEDICATED_SUB_URL "https://$DOMAIN"
    set_env_key DEDICATED_SUB_PORT "$DSUB_PORT"
    echo -e "${GREEN}$(t dsub_env_saved)${RESET}"
    restart_service_and_wait "$DSUB_SERVICE" || true
    sudo systemctl restart "$SERVICE_NAME" 2>/dev/null || true
    sleep 2
    if curl -fsS -m 10 "https://$DOMAIN/healthz" > /dev/null 2>&1; then
        echo -e "${GREEN}$(t dsub_health_ok)${RESET}"
    else
        echo -e "${YELLOW}$(t dsub_health_fail "$DSUB_SERVICE")${RESET}"
    fi
    echo -e "${GREEN}${BOLD}$(t dsub_ready "https://$DOMAIN")${RESET}"
    read -rp "$(t dsub_enable_ask)" ANS
    if [[ ! "$ANS" =~ ^[nN]$ ]]; then
        dsub_cli enable
    fi
    echo -e "${GREEN}$(t dsub_hint)${RESET}"
}

toggle_dedicated_sub() {
    DSUB_SERVICE="${SERVICE_NAME}-sub"
    if [ ! -f "/etc/systemd/system/${DSUB_SERVICE}.service" ]; then
        echo -e "${RED}$(t dsub_not_installed)${RESET}"
        return
    fi
    local cur
    cur=$(dsub_cli status | head -1)
    echo -e "${CYAN}$(t dsub_state "${cur:-?}")${RESET}"
    echo -e "${DIM}$(t dsub_toggle_off_note)${RESET}"
    read -rp "$(t dsub_toggle_prompt)" CH
    case "$CH" in
        1) dsub_cli enable | head -1 ;;
        2) dsub_cli disable | head -1 ;;
        *) echo -e "${YELLOW}$(t cancelled)${RESET}" ;;
    esac
}

update_dedicated_sub() {
    DSUB_SERVICE="${SERVICE_NAME}-sub"
    if ! systemctl list-units --full -all | grep -q "${DSUB_SERVICE}.service"; then
        echo -e "${RED}$(t dsub_not_installed)${RESET}"
        return
    fi
    if [ ! -f "$INSTALL_DIR/main.py" ]; then
        echo -e "${RED}$(t bot_not_installed)${RESET}"
        return
    fi
    cd "$INSTALL_DIR"
    local failed=0
    section_header "$(t update_dsub_header)"
    run_step 1 3 "$(t fetching_latest)" fetch_project_code "$INSTALL_DIR" || failed=1
    run_step 2 3 "$(t updating_packages)" bash -c "source '$INSTALL_DIR/venv/bin/activate' && ($PIP_CPU_TORCH || true) && $PIP_REQS && deactivate" || failed=1
    run_step 3 3 "$(t restarting_dsub_service)" restart_service_and_wait "$DSUB_SERVICE" || failed=1
    draw_rule
    if [ "$failed" = "0" ] && systemctl is-active --quiet "$DSUB_SERVICE"; then
        echo -e "  ${GREEN}${BOLD}$(t dsub_update_done)${RESET}"
    else
        echo -e "  ${RED}$(t install_failed "$DSUB_SERVICE")${RESET}"
    fi
}

remove_dedicated_sub() {
    echo -e "${RED}${BOLD}$(t remove_dsub_warn)${RESET}"
    read -rp "$(t confirm_prompt)" CONFIRM
    [ "$CONFIRM" != "yes" ] && { echo -e "${YELLOW}$(t cancelled)${RESET}"; return; }
    dsub_cli disable > /dev/null
    DSUB_SERVICE="${SERVICE_NAME}-sub"
    sudo systemctl stop "$DSUB_SERVICE" 2>/dev/null || true
    sudo systemctl disable "$DSUB_SERVICE" 2>/dev/null || true
    sudo rm -f "/etc/systemd/system/${DSUB_SERVICE}.service"
    sudo systemctl daemon-reload
    read -rp "$(t prompt_domain_used_dsub)" DOMAIN
    if [ -n "$DOMAIN" ]; then
        sudo rm -f "/etc/nginx/sites-enabled/${DOMAIN}.conf" "/etc/nginx/sites-available/${DOMAIN}.conf"
        sudo systemctl reload nginx 2>/dev/null || true
    fi
    if [ -f "$INSTALL_DIR/.env" ]; then
        sed -i '/^DEDICATED_SUB_URL=/d;/^DEDICATED_SUB_PORT=/d' "$INSTALL_DIR/.env"
    fi
    sudo systemctl restart "$SERVICE_NAME" 2>/dev/null || true
    echo -e "${GREEN}$(t dsub_removed)${RESET}"
}

dedicated_sub_status() {
    local env_file="$INSTALL_DIR/.env" url d svc enabled cert code state
    url=""
    [ -f "$env_file" ] && url=$(grep -m1 "^DEDICATED_SUB_URL=" "$env_file" | cut -d= -f2-)
    d=$(printf '%s' "$url" | sed -E 's#^"?https?://##; s#[/"]+.*$##')
    if [ -z "$d" ]; then
        echo -e "${YELLOW}$(t dsub_status_none)${RESET}"
        return
    fi
    svc=$(t ws_no)
    systemctl is-active --quiet "${SERVICE_NAME}-sub" 2>/dev/null && svc=$(t ws_yes)
    enabled=$(t ws_no)
    [ -L "/etc/nginx/sites-enabled/${d}.conf" ] && enabled=$(t ws_yes)
    cert=$(t ws_no)
    [ -e "/etc/letsencrypt/live/${d}/fullchain.pem" ] && cert=$(t ws_yes)
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 --resolve "${d}:443:127.0.0.1" "https://${d}/healthz" 2>/dev/null)
    state=$(dsub_cli status | head -1)
    echo -e "${CYAN}${BOLD}$(t dsub_status_title)${RESET}"
    echo "  ${d}"
    echo "    $(t dsub_status_service): ${svc}"
    echo "    $(t dsub_status_state): ${state:-?}"
    echo "    $(t ws_status_enabled): ${enabled}"
    echo "    $(t ws_status_cert): ${cert}"
    echo "    $(t ws_status_store): ${code:-?}"
}

setup_web_store() {
    local STORE_SERVICE="${SERVICE_NAME}-store"
    if [ ! -f "$INSTALL_DIR/web_store/server.py" ] || [ ! -x "$INSTALL_DIR/venv/bin/uvicorn" ]; then
        echo -e "${YELLOW}$(t ws_need_miniapp)${RESET}"
        return 1
    fi
    read -rp "$(t ws_domain_prompt)" DOMAIN
    DOMAIN=$(printf '%s' "$DOMAIN" | tr -d '[:space:]')
    if [[ ! "$DOMAIN" =~ ^[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        echo -e "${RED}$(t ws_domain_invalid)${RESET}"; return 1
    fi
    echo -e "${CYAN}$(t ws_check_dns)${RESET}"
    SERVER_IP=$(curl -4 -fsSL --max-time 8 https://ifconfig.me 2>/dev/null || true)
    DOMAIN_IP=$(getent ahostsv4 "$DOMAIN" 2>/dev/null | awk 'NR==1{print $1}')
    if [ -z "$DOMAIN_IP" ]; then echo -e "${RED}$(t ws_dns_unresolved)${RESET}"; return 1; fi
    if [ -n "$SERVER_IP" ] && [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
        echo -e "${YELLOW}$(t ws_ip_mismatch "$DOMAIN_IP" "$SERVER_IP")${RESET}"
        read -rp "$(t ws_continue_anyway)" CONT
        [ "$CONT" = "yes" ] || return 1
    fi
    sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq || return 1
    timeout 120 sudo env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a NEEDRESTART_SUSPEND=1 \
        apt-get install -y -qq nginx certbot python3-certbot-nginx curl > /dev/null || return 1
    tune_nginx_for_scale
    cd "$INSTALL_DIR"
    source venv/bin/activate
    $PIP_CPU_TORCH || true
    $PIP_REQS
    deactivate
    EXEC_START="$(service_exec_start "$INSTALL_DIR/venv/bin/uvicorn" "web_store.server:app" "--host" "127.0.0.1" "--port" "8005")"
    sudo bash -c "cat > /etc/systemd/system/${STORE_SERVICE}.service" <<EOF
[Unit]
Description=ShopVPN Web Store
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$EXEC_START
Restart=always
RestartSec=5
User=$(whoami)

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable "$STORE_SERVICE" >/dev/null 2>&1
    repair_unit_execstart "/etc/systemd/system/${STORE_SERVICE}.service" \
        "$(unit_default_execstart "$STORE_SERVICE")" > /dev/null
    local CONF="/etc/nginx/sites-available/shopvpn-store-${DOMAIN}.conf"
    if [ -e "$CONF" ]; then
        echo -e "${YELLOW}$(t ws_conf_exists "$CONF")${RESET}"
        read -rp "$(t ws_replace_prompt)" CONT
        [ "$CONT" = "yes" ] || return 1
    fi
    sudo bash -c "cat > $CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 100m;
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
    location / {
        proxy_pass http://127.0.0.1:8005;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    sudo ln -sfn "$CONF" "/etc/nginx/sites-enabled/shopvpn-store-${DOMAIN}.conf"
    if ! sudo nginx -t; then echo -e "${RED}$(t ws_nginx_invalid "$CONF")${RESET}"; return 1; fi
    sudo systemctl reload nginx || return 1
    read -rp "$(t ws_cert_email_prompt)" CERT_EMAIL
    if [ -n "$CERT_EMAIL" ]; then
        sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$CERT_EMAIL" --redirect || return 1
    else
        sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect || return 1
    fi
    set_env_key SHOPVPN_SEO_SITE_URL "https://$DOMAIN"
    if ! grep -q "^SHOPVPN_TURNSTILE_SITE_KEY=." "$INSTALL_DIR/.env" 2>/dev/null; then
        set_env_key SHOPVPN_WEB_ALLOW_NO_TURNSTILE 1
    fi
    if ! restart_service_and_wait "$STORE_SERVICE"; then
        echo -e "${RED}$(t install_failed "$STORE_SERVICE")${RESET}"; return 1
    fi
    echo -e "${GREEN}${BOLD}$(t ws_ready "$DOMAIN")${RESET}"
    echo -e "${DIM}$(t ws_ports_hint)${RESET}"
}

setup_email_service() {
    if [ ! -f "$INSTALL_DIR/.env" ]; then echo -e "${RED}$(t env_missing_install_first)${RESET}"; return 1; fi
    echo -e "${CYAN}$(t smtp_intro)${RESET}"
    read -rp "$(t smtp_host_prompt)" SMTP_HOST
    read -rp "$(t smtp_port_prompt)" SMTP_PORT
    read -rp "$(t smtp_user_prompt)" SMTP_USER
    read -rsp "$(t smtp_pass_prompt)" SMTP_PASSWORD; echo
    read -rp "$(t smtp_from_prompt)" SMTP_FROM
    read -rp "$(t smtp_ssl_prompt)" SMTP_SSL
    SMTP_PORT=${SMTP_PORT:-587}; SMTP_FROM=${SMTP_FROM:-$SMTP_USER}
    if [[ ! "$SMTP_PORT" =~ ^[0-9]+$ ]] || [ -z "$SMTP_HOST" ] || [ -z "$SMTP_USER" ] || [ -z "$SMTP_PASSWORD" ]; then
        echo -e "${RED}$(t smtp_invalid)${RESET}"; return 1
    fi
    set_env_key SHOPVPN_SMTP_HOST "$SMTP_HOST"
    set_env_key SHOPVPN_SMTP_PORT "$SMTP_PORT"
    set_env_key SHOPVPN_SMTP_USER "$SMTP_USER"
    set_env_key SHOPVPN_SMTP_PASSWORD "$SMTP_PASSWORD"
    set_env_key SHOPVPN_SMTP_FROM "$SMTP_FROM"
    if [[ "$SMTP_SSL" =~ ^[Yy]$ ]] || [ "$SMTP_PORT" = "465" ]; then set_env_key SHOPVPN_SMTP_SSL 1; else set_env_key SHOPVPN_SMTP_SSL 0; fi
    if systemctl list-unit-files "${SERVICE_NAME}-miniapp.service" --no-legend 2>/dev/null | grep -q "${SERVICE_NAME}-miniapp.service"; then
        restart_service_and_wait "${SERVICE_NAME}-miniapp" || true
    fi
    if systemctl list-unit-files "${SERVICE_NAME}-store.service" --no-legend 2>/dev/null | grep -q "${SERVICE_NAME}-store.service"; then
        restart_service_and_wait "${SERVICE_NAME}-store" || true
    fi
    sudo systemctl restart "$SERVICE_NAME" >/dev/null 2>&1 || true
    echo -e "${GREEN}$(t smtp_saved)${RESET}"
    echo -e "${YELLOW}$(t smtp_fail_hint "$SERVICE_NAME")${RESET}"
}

setup_web_turnstile() {
    if [ ! -f "$INSTALL_DIR/.env" ]; then echo -e "${RED}$(t env_missing_install_first)${RESET}"; return 1; fi
    echo -e "${CYAN}$(t ts_intro)${RESET}"
    echo -e "${DIM}$(t ts_disable_hint)${RESET}"
    read -rp "Turnstile Site Key: " TS_SITE
    read -rsp "Turnstile Secret Key: " TS_SECRET; echo
    if [ -n "$TS_SITE" ] && [ -z "$TS_SECRET" ]; then echo -e "${RED}$(t ts_secret_required)${RESET}"; return 1; fi
    if [ -z "$TS_SITE" ] && [ -n "$TS_SECRET" ]; then echo -e "${RED}$(t ts_site_required)${RESET}"; return 1; fi
    set_env_key SHOPVPN_TURNSTILE_SITE_KEY "$TS_SITE"
    set_env_key SHOPVPN_TURNSTILE_SECRET_KEY "$TS_SECRET"
    if systemctl list-unit-files "${SERVICE_NAME}-miniapp.service" --no-legend 2>/dev/null | grep -q "${SERVICE_NAME}-miniapp.service"; then
        restart_service_and_wait "${SERVICE_NAME}-miniapp" || true
    fi
    if systemctl list-unit-files "${SERVICE_NAME}-store.service" --no-legend 2>/dev/null | grep -q "${SERVICE_NAME}-store.service"; then
        restart_service_and_wait "${SERVICE_NAME}-store" || true
    fi
    echo -e "${GREEN}$(t ts_saved)${RESET}"
}

web_store_domains() {
    local f d
    for f in /etc/nginx/sites-available/shopvpn-store-*.conf; do
        [ -e "$f" ] || continue
        d=$(basename "$f" .conf)
        echo "${d#shopvpn-store-}"
    done
}

web_store_status() {
    local d enabled cert svc miniapp_url code_store code_root
    local env_file="$INSTALL_DIR/.env"
    mapfile -t DOMAINS < <(web_store_domains)
    if [ "${#DOMAINS[@]}" -eq 0 ]; then
        echo -e "${YELLOW}$(t ws_status_none)${RESET}"
        return
    fi
    miniapp_url=""
    [ -f "$env_file" ] && miniapp_url=$(grep -m1 "^MINIAPP_URL=" "$env_file" | cut -d= -f2-)
    svc=$(t ws_no)
    systemctl is-active --quiet "${SERVICE_NAME}-store" 2>/dev/null && svc=$(t ws_yes)
    echo -e "${CYAN}${BOLD}$(t ws_status_title)${RESET}"
    for d in "${DOMAINS[@]}"; do
        enabled=$(t ws_no)
        [ -L "/etc/nginx/sites-enabled/shopvpn-store-${d}.conf" ] && enabled=$(t ws_yes)
        cert=$(t ws_no)
        [ -e "/etc/letsencrypt/live/${d}/fullchain.pem" ] && cert=$(t ws_yes)
        code_store=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 --resolve "${d}:443:127.0.0.1" "https://${d}/healthz" 2>/dev/null)
        code_root=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 --resolve "${d}:443:127.0.0.1" "https://${d}/" 2>/dev/null)
        echo "  ${d}"
        echo "    $(t ws_status_enabled): ${enabled}"
        echo "    $(t ws_status_cert): ${cert}"
        echo "    $(t ws_status_store): ${code_store:-—}"
        echo "    $(t ws_status_root): ${code_root:-—}"
    done
    echo "    MINIAPP_URL: ${miniapp_url:-—}"
    echo "    $(t ws_status_miniapp_svc): ${svc}"
}

remove_web_store() {
    local DOMAIN pick idx d
    mapfile -t DOMAINS < <(web_store_domains)
    if [ "${#DOMAINS[@]}" -eq 0 ]; then
        echo -e "${YELLOW}$(t ws_status_none)${RESET}"
        return 1
    fi
    if [ "${#DOMAINS[@]}" -eq 1 ]; then
        DOMAIN="${DOMAINS[0]}"
    else
        idx=1
        for d in "${DOMAINS[@]}"; do
            echo "  [${idx}] ${d}"
            idx=$((idx + 1))
        done
        read -rp "$(t ws_pick_domain)" pick
        if ! [[ "$pick" =~ ^[0-9]+$ ]] || [ "$pick" -lt 1 ] || [ "$pick" -gt "${#DOMAINS[@]}" ]; then
            echo -e "${YELLOW}$(t cancelled)${RESET}"; return
        fi
        DOMAIN="${DOMAINS[$((pick - 1))]}"
    fi
    echo -e "${RED}${BOLD}$(t ws_remove_warn "$DOMAIN")${RESET}"
    read -rp "$(t confirm_prompt)" CONFIRM
    [ "$CONFIRM" != "yes" ] && { echo -e "${YELLOW}$(t cancelled)${RESET}"; return; }
    sudo rm -f "/etc/nginx/sites-enabled/shopvpn-store-${DOMAIN}.conf" "/etc/nginx/sites-available/shopvpn-store-${DOMAIN}.conf"
    sudo systemctl reload nginx 2>/dev/null || true
    mapfile -t DOMAINS < <(web_store_domains)
    if [ "${#DOMAINS[@]}" -eq 0 ]; then
        sudo systemctl stop "${SERVICE_NAME}-store" 2>/dev/null || true
        sudo systemctl disable "${SERVICE_NAME}-store" 2>/dev/null || true
        sudo rm -f "/etc/systemd/system/${SERVICE_NAME}-store.service"
        sudo systemctl daemon-reload
    fi
    sudo systemctl restart "$SERVICE_NAME" >/dev/null 2>&1 || true
    echo -e "${GREEN}$(t ws_removed "$DOMAIN")${RESET}"
}

update_web_store() {
    local STORE_SERVICE="${SERVICE_NAME}-store"
    if ! systemctl list-units --full -all | grep -q "${STORE_SERVICE}.service"; then
        echo -e "${RED}$(t store_not_installed)${RESET}"
        return
    fi
    if [ ! -f "$INSTALL_DIR/main.py" ]; then
        echo -e "${RED}$(t bot_not_installed)${RESET}"
        return
    fi
    cd "$INSTALL_DIR"
    local failed=0
    section_header "$(t update_store_header)"
    run_step 1 3 "$(t fetching_latest)" fetch_project_code "$INSTALL_DIR" || failed=1
    run_step 2 3 "$(t updating_packages)" bash -c "source '$INSTALL_DIR/venv/bin/activate' && ($PIP_CPU_TORCH || true) && $PIP_REQS && deactivate" || failed=1
    run_step 3 3 "$(t restarting_store_service)" restart_service_and_wait "$STORE_SERVICE" || failed=1
    draw_rule
    if [ "$failed" = "0" ] && systemctl is-active --quiet "$STORE_SERVICE"; then
        echo -e "  ${GREEN}${BOLD}$(t store_update_done)${RESET}"
    else
        echo -e "  ${RED}$(t install_failed "$STORE_SERVICE")${RESET}"
    fi
}
