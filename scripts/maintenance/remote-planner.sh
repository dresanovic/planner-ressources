#!/usr/bin/env bash
# Invoked by Remote-Planner.ps1. Never prints container environment values.
set -euo pipefail
action=$1 work=$2 deployment=$3 container=$4 volume=$5 source=${6:-} new_name=${7:-} image=${8:-} apply=${9:-0}
umask 077
[[ "$work" == /* && "$work" != / && "$work" != *'..'* ]] || { echo 'Invalid maintenance directory.' >&2; exit 1; }
[[ "$container" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ && "$volume" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]] || exit 1
mkdir -p "$work/backups"
chmod 700 "$work" "$work/backups"
chmod 755 "$work/helpers"
chmod 644 "$work/helpers/backup_sqlite_db.py" "$work/helpers/restore_sqlite_db.py"
stamp=$(date +%Y%m%d-%H%M%S)-$$

fail() { echo "ERROR: $*" >&2; exit 1; }
inspect() { sudo docker inspect --format "$1" "$container"; }
check_mount() {
    local actual
    actual=$(inspect '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}}{{end}}{{end}}')
    [[ "$actual" == "$volume" ]] || fail "Container /data is not the expected volume: $volume"
    # Verify configured path without displaying any other environment values.
    inspect '{{json .Config.Env}}' | python3 -c 'import json,sys; env=dict(s.split("=",1) for s in json.load(sys.stdin) if "=" in s); sys.exit(0 if env.get("DATABASE_URL")=="sqlite:////data/planner.db" else "Unexpected DATABASE_URL; no changes made.")'
}
backup() {
    check_mount
    [[ $(inspect '{{.State.Running}}') == true ]] || fail 'Backup action requires a running container.'
    local inside="/data/backups/operator-$stamp" destination="$work/backups/operator-$stamp"
    sudo docker exec "$container" python scripts/backup_sqlite_db.py --database /data/planner.db --output-dir "$inside"
    sudo docker cp "$container:$inside" "$work/backups/"
    sudo chown "$(id -u):$(id -g)" "$destination" "$destination"/*.db
    chmod 700 "$destination"
    chmod 600 "$destination"/*.db
    echo "Host recovery copy: $destination"
}

case "$action" in
    status)
        sudo docker ps -a --filter "name=$container" --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
        sudo docker logs --tail 60 "$container"
        ;;
    backup) backup ;;
    list)
        echo "Host backups: $work/backups"
        find "$work/backups" -type f -name '*.db' -printf '%TY-%Tm-%Td %TH:%TM  %10s bytes  %p\n' | sort -r
        echo 'Volume backups (includes historical backups from the earlier deployment):'
        sudo docker run --rm --network none --mount "type=volume,source=$volume,target=/data,readonly" --entrypoint sh "$(inspect '{{.Image}}')" -c 'find /data/backups -type f -name "*.db" -print'
        ;;
    rename)
        [[ "$new_name" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*\.db$ ]] || fail 'NewName must be a simple .db filename.'
        source=$(realpath -e -- "$source")
        [[ "$source" == "$work/backups/"* && -f "$source" ]] || fail 'Rename is limited to host files inside the maintenance backups directory.'
        destination="$(dirname "$source")/$new_name"
        [[ ! -e "$destination" ]] || fail 'Destination already exists.'
        mv -n -- "$source" "$destination"
        echo "Renamed to: $destination"
        ;;
    restore)
        check_mount
        [[ -f "$source" && "$source" == /* ]] || fail 'BackupFile must be an existing absolute host file path.'
        image=$(inspect '{{.Image}}')
        # A private staging copy is readable by the image user without changing
        # permissions on the original backup. The parent work directory is 0700.
        staging=$(mktemp -d "$work/restore-XXXXXXXX")
        trap 'rm -f -- "$staging/input.db"; rmdir -- "$staging"' EXIT
        cp -- "$source" "$staging/input.db"
        chmod 755 "$staging"
        chmod 644 "$staging/input.db"
        restore_command=(sudo docker run --rm --network none
            --mount "type=volume,source=$volume,target=/data"
            --mount "type=bind,source=$work/helpers,target=/maintenance,readonly"
            --mount "type=bind,source=$staging,target=/restore,readonly"
            --entrypoint python "$image" /maintenance/restore_sqlite_db.py
            --backup /restore/input.db --database /data/planner.db --backup-dir /data/backups)
        "${restore_command[@]}"
        if [[ "$apply" == 1 ]]; then
            sudo docker stop --time 30 "$container"
            [[ -z $(sudo docker ps -q --filter "volume=$volume") ]] || fail 'Another running container uses the database volume. Application remains stopped.'
            "${restore_command[@]}" --apply --backend-stopped
            echo 'Restore succeeded. Restarting the application.'
            sudo docker start "$container"
            echo 'Run Status, then verify login and master data in the browser.'
        else
            echo 'Preview only. Use -Apply to stop the application, replace the database, and restart after success.'
        fi
        ;;
    update)
        [[ "$image" =~ ^ghcr\.io/dresanovic/planner-ressources:v[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'Use an exact vMAJOR.MINOR.PATCH release image.'
        [[ -s "$deployment/planner.env" && -f "$deployment/config/optimization/policy.json" ]] || fail 'Deployment env or optimization policy is missing.'
        check_mount
        [[ $(inspect '{{.HostConfig.RestartPolicy.Name}}') == unless-stopped ]] || fail 'Unexpected restart policy; inspect deployment manually.'
        bindings=$(inspect '{{json .HostConfig.PortBindings}}')
        python3 -c 'import json,sys; expected={"8080/tcp":[{"HostIp":"10.155.11.130","HostPort":"8081"}]}; sys.exit(0 if json.loads(sys.argv[1])==expected else "Unexpected port bindings; inspect deployment manually.")' "$bindings"
        mounts=$(inspect '{{json .Mounts}}')
        python3 -c 'import json,sys; m=json.loads(sys.argv[1]); expected=sys.argv[2]+"/config/optimization"; valid=len(m)==2 and any(x["Destination"]=="/config/optimization" and x["Type"]=="bind" and x["Source"]==expected and not x["RW"] for x in m); sys.exit(0 if valid else "Unexpected mounts; inspect deployment manually.")' "$mounts" "$deployment"
        # Fail rather than silently change the effective runtime configuration.
        inspect '{{json .Config.Env}}' | python3 -c 'import json,sys; from pathlib import Path; current=dict(s.split("=",1) for s in json.load(sys.stdin) if "=" in s); configured=dict(line.split("=",1) for line in Path(sys.argv[1]).read_text().splitlines() if line and not line.startswith("#")); keys=("APP_ENV","DATABASE_URL","INSTITUTION_TIMEZONE","LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY","TEACHING_OPTIMIZATION_POLICY_FILE"); sys.exit(0 if all(configured.get(k)==current.get(k) for k in keys) else "Saved planner.env differs from runtime; reconcile it before updating.")' "$deployment/planner.env"
        sudo docker pull "$image"
        # Pin this update to the downloaded immutable image ID.
        target=$(sudo docker image inspect --format '{{.Id}}' "$image")
        backup
        previous="$container-before-$stamp"
        sudo docker stop --time 30 "$container"
        [[ -z $(sudo docker ps -q --filter "volume=$volume") ]] || fail 'Another running container uses the volume. Application remains stopped.'
        sudo docker rename "$container" "$previous"
        echo "Retained old container (keep stopped): $previous"
        sudo docker run -d --name "$container" --restart unless-stopped --security-opt no-new-privileges:true --stop-timeout 30 \
            --env-file "$deployment/planner.env" --publish 10.155.11.130:8081:8080 \
            --mount "type=volume,source=$volume,target=/data" \
            --mount "type=bind,source=$deployment/config/optimization,target=/config/optimization,readonly" "$target"
        for ((attempt=0; attempt<40; attempt++)); do
            health=$(inspect '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}')
            if [[ "$health" == healthy ]]; then
                echo "Healthy: $image. Database and policy retained. Refresh the browser with Ctrl+F5."
                exit 0
            fi
            [[ "$health" != unhealthy && $(inspect '{{.State.Running}}') == true ]] || break
            sleep 3
        done
        sudo docker logs --tail 80 "$container"
        sudo docker stop --time 30 "$container"
        fail 'New container did not become healthy and was stopped. Recovery backup and old container retained. Do not start the old image against a migrated database without checking compatibility.'
        ;;
    *) fail 'Unknown action.' ;;
esac
