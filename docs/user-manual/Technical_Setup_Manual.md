# Resource Planner Technical Setup Manual

**Docker installation on the internal Linux VM and authentication audit reference**

| Document field | Value |
| --- | --- |
| Prepared | 15 October 2026 |
| Audience | Infrastructure operators, application administrators, and auditors |
| Application baseline reviewed | Repository commit `f9593e5dce0a523758de5d28af3b81750e4d36af` |
| VM reference | Supplied `VirtuelleMachine.docx`, sections VM configuration, network and access, storage and backup, and resource requirements |
| Deployment status | Installation procedure and implementation review; the target VM was not accessed or installed during preparation |
| Deployment owner and approval record | To be completed by the organization |

This manual explains two things: how to install and operate the Resource Planner using Docker on the specified virtual machine, and how its authentication and authorization work. It provides reproducible setup steps and an evidence checklist for an audit. It does not certify that a particular VM or released image has passed those checks.

The intended deployment is one Ubuntu VM running Docker Engine and Docker Compose, one application container, a persistent SQLite database, and an Nginx HTTPS reverse proxy. Users reach it through the internal LAN or VPN and still sign in with named application accounts. HTTPS is required for production authentication.

## Quick Start

For a minimal server evaluation, use [Minimal server proof of concept](#minimal-server-proof-of-concept). For the full internal deployment, follow these steps:

1. Provision the Ubuntu VM and arrange internal DNS, a trusted TLS certificate, approved network ranges, and separate backup storage as described in Part One.
2. Install Docker Engine, the Compose plugin, and Nginx using section 3.
3. Copy the approved release's `compose.yaml` and `.env.example` to `/opt/resource-planner`. Bind the application port to `127.0.0.1`, select the approved image, and generate the two initial secrets in section 4.
4. Start the container and configure the HTTPS proxy in sections 5 and 6. Confirm `/health` responds and port 8080 is unreachable from another machine.
5. Open `https://resource-planner.intern/bootstrap/`, create the first administrator, remove the consumed bootstrap value from `.env`, and recreate the container. Sign in at `/login/`.
6. Create a named planner account under **Planer-Konten**, deliver its one-time setup link securely, and complete an independent planner login.
7. Configure the daily backup job and record the deployment checks in Part Three.

**Expected result:** LAN/VPN users can sign in over HTTPS, ordinary planners cannot administer accounts, and container replacement preserves application data. A successful health check alone does not demonstrate successful authentication or recovery.

## Minimal server proof of concept

**Goal:** Run the application on a Linux server and test it from your workstation with the fewest infrastructure dependencies. This procedure uses one Docker container and an SSH tunnel. It needs no internal DNS entry, Nginx, TLS certificate, or Compose configuration.

Use an authorized Ubuntu server with working Docker Engine, `curl`, OpenSSL, SSH access with TCP forwarding allowed, and permission to pull the selected application image. If Docker is missing, install Docker Engine using the instructions linked in section 3; Nginx is unnecessary for this procedure. Use test data and separate test credentials. The PoC has its own container, port, configuration directory, and persistent volume.

The browser connects to workstation loopback over HTTP; SSH encrypts traffic between the workstation and server. The application uses `APP_ENV=development` so its local HTTP session cookie works. This mode is for the temporary evaluation described here. Use the production HTTPS procedure for a shared institutional deployment.

```text
Workstation browser http://127.0.0.1:8081
    -> SSH tunnel over port 22
    -> server 127.0.0.1:8081
    -> application container port 8080
```

### POC 1 Prepare the server and image

Connect to the server using your usual SSH account. Run the following in Bash **on the server**:

```bash
sudo docker version
mkdir -p ~/resource-planner-poc
chmod 0700 ~/resource-planner-poc
cd ~/resource-planner-poc
read -r -p 'Application image tag or digest to test: ' poc_image
test -n "$poc_image"
sudo docker pull "$poc_image"
```

Enter a real available release reference, such as the approved GHCR tag/digest from section 4.3. For a private image, complete the registry login in section 5 first.

If no suitable image is published, copy the repository source being evaluated to the server and run the following **from its repository root**:

```bash
sudo docker build -f infrastructure/docker/Dockerfile \
  -t planner-ressources:poc .
```

Then return to `~/resource-planner-poc` and set `poc_image=planner-ressources:poc` in that server shell. Skip the pull command for this locally built image. Record which source revision was built. Building requires access to the base images and package repositories and consumes more resources than pulling a release image.

### POC 2 Create the test configuration and start

Run this block **once for a new PoC** in the same server shell. It generates distinct secrets without displaying them and refuses to overwrite existing configuration:

```bash
cd ~/resource-planner-poc
(
  set -e
  umask 077
  set -o noclobber
  cat > poc.env <<EOF
APP_ENV=development
DATABASE_URL=sqlite:////data/planner.db
INSTITUTION_TIMEZONE=Europe/Vienna
LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY=$(openssl rand -hex 32)
PLANNER_BOOTSTRAP_CREDENTIAL=$(openssl rand -hex 32)
PLANNER_ADMIN_RECOVERY_CREDENTIAL=
EOF
)
```

After the configuration block succeeds, start the container:

```bash
sudo docker run -d --name planner-ressources-poc \
  --env-file ./poc.env \
  -p 127.0.0.1:8081:8080 \
  -v planner-ressources-poc-data:/data \
  --security-opt no-new-privileges:true \
  "$poc_image"
sudo docker logs --tail=50 planner-ressources-poc
curl --fail http://127.0.0.1:8081/health
```

Wait for startup to finish and retry the health request if necessary. Expected response: `{"status":"ok"}`. If port 8081 or the container name is already occupied, resolve the existing PoC before starting another. Do not use the production data volume. Keep server port 8081 bound to `127.0.0.1`; no inbound application-port firewall rule is needed.

### POC 3 Open the application through SSH

In a **new terminal on your workstation**, run the following, replacing `vmadmin` and `VM_IP` with your SSH account and server address. It works with the OpenSSH client, including Windows PowerShell:

```text
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:8081:127.0.0.1:8081 vmadmin@VM_IP
```

Leave that terminal running. Open `http://127.0.0.1:8081/bootstrap/` in the workstation browser. Use `127.0.0.1:8081` consistently for this evaluation. The application runs on the server even though the browser address is local to your workstation. If workstation port 8081 is occupied, change only the first `8081` in the tunnel mapping to an unused local port and use that port in every browser URL.

### POC 4 Create the administrator and test planning

1. In your existing server SSH session, open the protected `~/resource-planner-poc/poc.env` with a text editor and retrieve `PLANNER_BOOTSTRAP_CREDENTIAL`. Keep its value out of screenshots and shared logs.
2. In the browser bootstrap form, enter that credential, a test login name, display name, and a password of 12 to 128 characters with confirmation.
3. Open `http://127.0.0.1:8081/login/` and sign in using the new account. Bootstrap does not log you in automatically.
4. Optionally populate the test database with the packaged demonstration catalog:

   ```bash
   sudo docker exec planner-ressources-poc \
     python scripts/seed_dummy_planning_data.py
   ```

   Reload the planner and inspect the sample lecturers, rooms, courses, and semester. The script creates catalog/configuration data; generate a schedule through the planner to test scheduling. Follow the [user manual](User_Manual.md) for the planning workflow.

5. Create a second named test planner under **Planer-Konten**, open its setup link through the same tunnel, set its password, and test login in a separate browser profile. Confirm it can plan but cannot administer accounts. Using separate accounts avoids the one-current-session-per-account behavior invalidating another tester's session.
6. After successful bootstrap, clear its consumed environment value and recreate the test container with the same image and data volume. Run these commands from the server PoC directory:

   ```bash
   cd ~/resource-planner-poc
   sed -i 's/^PLANNER_BOOTSTRAP_CREDENTIAL=.*/PLANNER_BOOTSTRAP_CREDENTIAL=/' poc.env
   poc_image=$(sudo docker inspect --format '{{.Config.Image}}' planner-ressources-poc)
   sudo docker stop planner-ressources-poc
   sudo docker rm planner-ressources-poc
   sudo docker run -d --name planner-ressources-poc \
     --env-file ./poc.env \
     -p 127.0.0.1:8081:8080 \
     -v planner-ressources-poc-data:/data \
     --security-opt no-new-privileges:true \
     "$poc_image"
   ```

   Wait for health and verify that the accounts and test data remain. Keep the stable fingerprint key unchanged.

**PoC acceptance:** The health endpoint responds, administrator and ordinary planner login work, ordinary planners cannot manage accounts, a representative schedule can be generated and reviewed, and test data survives container recreation. Record the image/source revision, date, server resources, and observed results. This does not complete the production TLS, firewall, backup, capacity, or recovery acceptance checklist.

### POC 5 Stop and resume the evaluation

Close the SSH tunnel with **Ctrl+C**. To stop the server workload and later resume it:

```bash
sudo docker stop planner-ressources-poc
# When you want to resume the existing PoC:
sudo docker start planner-ressources-poc
```

Reopen the SSH tunnel before accessing the browser URL. The named volume retains the test database. No automatic restart policy is set, so a stopped container or a server reboot requires an explicit start. Before moving to production, follow Part One, use production credentials and HTTPS, and decide explicitly whether to discard or migrate the PoC data.

## Part One Install and operate the application

### 1 Target VM and deployment boundaries

The supplied VM document describes the following intended installation. Capacity is a starting assumption, not a measured performance guarantee.

| Component | Target from the VM reference |
| --- | --- |
| Operating system | Ubuntu Server 24.04 LTS, 64 bit |
| CPU | 2 vCPU recommended; 1 vCPU stated minimum |
| Memory | 4 GB recommended; 2 GB stated minimum |
| Disk | 40 GB SSD recommended; 20 GB stated minimum |
| Virtualization | VMware, Proxmox, or Hyper-V |
| Address | Internal static IP or DHCP reservation |
| Users | Up to 5 simultaneous users as a sizing assumption |
| Access | Internal LAN and VPN; no public IP or inbound Internet access |
| Database | SQLite on persistent local VM storage |
| Availability | Normal working hours, ideally continuous operation |
| Backup | Daily automatic copy to separate backup storage; snapshots before major changes |

The release workflow builds `linux/amd64` and `linux/arm64` image variants. Use a matching VM architecture and record the actual pulled image digest. Run one application container and its default single Uvicorn process with SQLite; do not scale this service into multiple replicas.

```text
LAN or VPN browser
    -> internal DNS resource-planner.intern
    -> VM Nginx on TCP 443 with trusted TLS
    -> host loopback 127.0.0.1:8080
    -> application container on TCP 8080
       React frontend and FastAPI API on the same origin
       /data/planner.db in Docker volume planner-ressources-data

Authorized operator -> SSH on TCP 22 -> Ubuntu and Docker administration
Daily backup job -> consistent SQLite backup -> separate protected storage
```

The application image already contains the frontend, Python runtime, backend dependencies, and database initialization code. Node.js, Python, and a separate database server do not need to be installed on the VM for normal operation.

### 2 Prepare the network and installation inputs

Before installation, record the actual VM IP, internal DNS name, LAN/VPN client ranges, SSH management range, release image reference, backup destination, and operational owners. Examples in this manual require substitution with those approved values.

| Traffic | Required treatment |
| --- | --- |
| Inbound TCP 443 | Allow only approved internal LAN and VPN client ranges |
| Inbound TCP 22 | Allow only authorized operator addresses or the management network |
| Inbound TCP 8080 | No remote exposure; publish on host loopback only |
| Inbound TCP 80 | Not required by this configuration; users open HTTPS directly |
| Public Internet inbound | Deny at the organization network boundary |
| Outbound provisioning and updates | Approved access to Ubuntu repositories, `download.docker.com`, GHCR and its image download endpoints, or internal mirrors |
| Supporting services | Internal DNS, time synchronization, backup storage, and certificate renewal services as required by local policy |

An Internet-isolated VM can use an approved mirror or an image exported and transferred from a connected machine. Record the source and digest, use `docker load` for the transferred image, and skip the registry pull step. Lack of inbound Internet exposure does not itself provide packages or images for installation.

Issue a server certificate for the actual internal DNS name through the organization's trusted CA. Install the CA trust chain on all client devices. The sample name `resource-planner.intern` is illustrative and must have a matching certificate subject alternative name. Do not bypass browser certificate errors for credential entry.

Apply the organization's Ubuntu baseline: named SSH accounts, restricted sudo access, SSH key authentication, security updates, and working time synchronization. Keep hypervisor console access available when changing firewall or SSH rules.

Docker-published ports can bypass UFW rules. The loopback binding below is therefore essential; verify effective exposure from a second host and apply the organization firewall rules as well. See [Docker firewall integration](https://docs.docker.com/engine/network/packet-filtering-firewalls/) and [port publishing](https://docs.docker.com/engine/network/port-publishing/).

### 3 Install Docker Engine and Nginx on Ubuntu

Run the following in a Bash shell on a fresh Ubuntu Server 24.04 VM, using an authorized sudo account. These are VM installation instructions, not commands to run on the Windows workstation hosting this repository.

If Docker, Podman, `containerd`, or `runc` already supports other workloads, inventory those workloads first and follow the conflict handling in the [official Docker Ubuntu installation guide](https://docs.docker.com/engine/install/ubuntu/). The procedure below assumes no conflicting installation.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl openssl nginx
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker run --rm hello-world
sudo docker version
sudo docker compose version
```

**Expected result:** Docker starts, the test image prints its success message, and Compose reports a version. Record installed package versions and the installation date. The commands select the repository's available stable packages; use the organization's approved package versions when it maintains a controlled baseline.

This manual uses `sudo docker` throughout. Access to the Docker socket or `docker` group effectively grants control over the host and its secrets; restrict it to infrastructure operators. See [Docker daemon access protection](https://docs.docker.com/engine/security/protect-access/).

### 4 Prepare the application deployment

#### 4.1 Transfer the deployment files

Obtain `compose.yaml` and `.env.example` from the approved release source. Transfer them over the approved administrative channel to `~/planner-install` on the VM. Retain the corresponding release/source identifier in the change record. On the VM:

```bash
sudo install -d -o "$USER" -g "$(id -gn)" -m 0700 /opt/resource-planner
install -m 0600 ~/planner-install/compose.yaml /opt/resource-planner/compose.yaml
install -m 0600 ~/planner-install/.env.example /opt/resource-planner/.env.example
cd /opt/resource-planner
```

The deployment directory belongs to the authorized operator. It contains secrets and must not be shared with ordinary planner users or synchronized through OneDrive.

#### 4.2 Restrict the published container port

Edit the **VM copy** of `compose.yaml`. Replace the existing service port entry with:

```yaml
    ports:
      - "127.0.0.1:${PLANNER_PORT:-8080}:8080"
```

The repository default publishes `${PLANNER_PORT:-8080}:8080` without restricting the host address. Retaining that default would expose the backend directly on host interfaces. Replace the entry rather than adding a second port entry. Keep the other service settings, including the persistent volume, unchanged.

#### 4.3 Select the image and generate secrets

Use an approved published release tag or, preferably for an audit record, an immutable image digest. The `v1.0.0` value in `.env.example` is an example, not evidence that this tag exists or contains the reviewed authentication implementation. Do not deploy `latest` as the controlled release reference.

Run this block once for a new installation. It refuses to overwrite an existing `.env`. Enter the image reference selected from the release record, for example `ghcr.io/dresanovic/planner-ressources@sha256:` followed by its real digest.

```bash
cd /opt/resource-planner
(
  set -e
  umask 077
  test ! -e .env || { echo '.env already exists; preserve its keys.' >&2; exit 1; }
  read -r -p 'Approved application image reference: ' planner_image
  test -n "$planner_image"
  fingerprint_key=$(openssl rand -hex 32)
  bootstrap_credential=$(openssl rand -hex 32)
  set -o noclobber
  cat > .env <<EOF
PLANNER_IMAGE=$planner_image
PLANNER_PORT=8080
INSTITUTION_TIMEZONE=Europe/Vienna
CUSTOMER_TERMINOLOGY_FILE=
LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY=$fingerprint_key
PLANNER_BOOTSTRAP_CREDENTIAL=$bootstrap_credential
PLANNER_ADMIN_RECOVERY_CREDENTIAL=
EOF
)
chmod 0600 .env
sudo docker compose config --quiet
```

Do not run this block again for an upgrade. Back up the existing `.env` securely and edit only the intended settings. Do not print an expanded `docker compose config`, dump container environments, or collect `.env` in audit evidence: these can expose secrets. Use `config --quiet` for validation.

| Setting | Purpose and operational rule |
| --- | --- |
| `PLANNER_IMAGE` | Approved release tag or digest; confirm the image implements the reviewed authentication boundary |
| `PLANNER_PORT` | Host loopback port, 8080 in this procedure |
| `INSTITUTION_TIMEZONE` | `Europe/Vienna` for institutional date and time behavior |
| `LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY` | Stable random installation key; the generated value has 32 random bytes encoded as 64 hex characters. Keep it across restarts, upgrades, and restores |
| `PLANNER_BOOTSTRAP_CREDENTIAL` | Separate one-time 64-character hex value for first-administrator creation only |
| `PLANNER_ADMIN_RECOVERY_CREDENTIAL` | Leave empty normally; generate a new distinct value only for emergency administrator recovery |
| `CUSTOMER_TERMINOLOGY_FILE` | Leave empty for the shipped German labels; optional overrides require a real read-only file mount |
| `APP_ENV` and `DATABASE_URL` | Set by the supplied Compose service to `production` and `sqlite:////data/planner.db` respectively |

These are separate credentials with separate purposes. The stable fingerprint key is not a login password, bootstrap credential, or lecturer access link. Changing it alters source fingerprints and exported calendar event identifiers. Follow the release revalidation requirements in `infrastructure/docker/README.md` before intentional rotation.

Store the configuration backup and keys in the approved secret store. `.env` permissions protect the file from ordinary host users; Docker administrators can still inspect container environment values. This Compose setup does not implement a dedicated secret-management service.

### 5 Pull and start the container

For a public GHCR package, an authenticated registry session is unnecessary. For a private package, obtain approved package-read access. The registry credential is distinct from application accounts. One interactive way to avoid placing the token in shell history is:

```bash
read -r -p 'GitHub username: ' registry_user
read -r -s -p 'Approved package-read token: ' registry_token
printf '\n'
printf '%s' "$registry_token" | sudo docker login ghcr.io \
  --username "$registry_user" --password-stdin
unset registry_token
```

Protect Docker's registry credential configuration or use an approved credential helper. Do not place the registry token in application `.env` or `compose.yaml`. Current registry requirements are documented by [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).

```bash
cd /opt/resource-planner
sudo docker compose pull
sudo docker compose up -d
sudo docker compose ps
sudo docker compose logs --tail=100 planner
curl --fail http://127.0.0.1:8080/health
sudo docker inspect --format '{{.State.Health.Status}}' planner-ressources
sudo docker inspect --format '{{.Config.Image}} {{.Image}}' planner-ressources
sudo docker image inspect \
  "$(sudo docker inspect --format '{{.Image}}' planner-ressources)" \
  --format '{{json .RepoDigests}}'
sudo docker volume inspect planner-ressources-data
```

The service is `planner`; its container name is `planner-ressources`. Startup initializes a new database or migrates a supported existing schema. Unsupported or partial schemas fail startup and require investigation; do not delete the volume to bypass that error.

**Expected result:** `/health` returns `{"status":"ok"}`, the container becomes `healthy`, and `/data` uses the volume `planner-ressources-data`. The health probe runs every 30 seconds with an initial 30-second start period. Wait for health and inspect startup logs before continuing.

The runtime uses UID/GID 10001 and `no-new-privileges`. Data persists independently of the container. Do not use `docker compose down -v` or remove this volume during an update. Do not mount the live database on a network share.

### 6 Configure internal HTTPS

Nginx runs on the VM and forwards both the frontend and API to the same application origin. This is an operator-supplied configuration; Nginx and a TLS certificate are not included in the application Compose service.

1. Install the organization-issued certificate chain and private key as `/etc/nginx/tls/resource-planner.fullchain.pem` and `/etc/nginx/tls/resource-planner.key`. Create `/etc/nginx/tls` with mode 0700, keep the private key root-owned with mode 0600, and protect certificate renewal credentials separately.
2. Put the following in `/etc/nginx/sites-available/resource-planner`. Replace the server name if the approved internal DNS name differs.

```nginx
server {
    listen 443 ssl;
    server_name resource-planner.intern;

    ssl_certificate /etc/nginx/tls/resource-planner.fullchain.pem;
    ssl_certificate_key /etc/nginx/tls/resource-planner.key;
    ssl_protocols TLSv1.2 TLSv1.3;

    add_header Referrer-Policy "no-referrer" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_cache off;
    }
}
```

3. Enable the site, disable the stock default site on this dedicated VM, validate, and start/reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/resource-planner \
  /etc/nginx/sites-enabled/resource-planner
sudo unlink /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

Run the enable/unlink commands once; if a site is already configured, inspect it and edit the existing configuration. On a VM shared with other sites, retain their configuration and use its approved exposure rules. Check that no other enabled site unintentionally listens on port 80.

4. Apply the inbound restrictions from section 2 at the VM/network firewall. No public NAT forwarding should exist. If IPv6 is enabled, apply equivalent restrictions and confirm DNS does not expose an unapproved path.
5. From an approved LAN/VPN workstation, open `https://resource-planner.intern/login/`. Validate the certificate name, chain, and expiry. `curl --fail https://resource-planner.intern/health` should work from a client that trusts the CA.

The 300-second proxy read timeout is a starting setting for planning operations, not proof of workload capacity. Validate realistic planning runs and adjust operational timeouts if required. Monitor TLS expiry and test the certificate renewal and Nginx reload procedure.

The proxy must preserve cookies, `Authorization`, `Content-Type`, `X-CSRF-Protection`, and `X-Planner-Activity`. Do not inject wildcard credentialed CORS headers or cache authenticated responses. Do not log request bodies, cookies, or authorization headers. See the official [Nginx proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) and [TLS module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html) references.

#### 6.1 Verify trusted proxy addresses

Uvicorn accepts forwarded client addresses only from trusted connecting proxies. With host Nginx forwarding through a Docker bridge, the backend may see a bridge gateway rather than loopback. Determine the actual connecting proxy address on this VM and add it explicitly to the **VM deployment copy's** service `environment` mapping:

```yaml
      FORWARDED_ALLOW_IPS: "<verified-proxy-source-ip>"
```

Replace the placeholder with the verified address; do not use `*` or trust arbitrary client networks. Apply this deployment setting with `docker compose up -d --force-recreate planner` and verify requests from two approved clients are attributed to their actual addresses. Nginx in this example replaces client-supplied forwarding values with its observed client address. Recheck the trust setting if the Docker network changes. See [Uvicorn proxy settings](https://raw.githubusercontent.com/encode/uvicorn/master/docs/settings.md).

Until verified, client-address-based lecturer misuse controls may group users under the proxy address. Planner login blocking is account-based and does not rely on those forwarded addresses. Record this proxy check in deployment acceptance; sending the header alone does not prove the backend trusts or uses it.

### 7 Create the first administrator and first planner

1. The operator retrieves the initial `PLANNER_BOOTSTRAP_CREDENTIAL` from the protected `.env` or secret store and delivers it to the designated administrator through the approved secure channel. Exclude it from tickets, screenshots, and audit attachments.
2. The designated administrator opens `https://resource-planner.intern/bootstrap/` and enters the bootstrap credential, display name, login name, password, and password confirmation.
3. On success, the administrator account exists and the credential is consumed. Bootstrap does not sign the administrator in automatically.
4. The operator clears `PLANNER_BOOTSTRAP_CREDENTIAL` in `.env`, leaves the stable fingerprint key unchanged, and runs:

   ```bash
   cd /opt/resource-planner
   sudo docker compose up -d --force-recreate planner
   ```

   `docker compose restart` alone does not apply changed environment values. Confirm health after recreation.

5. The administrator opens `/login/`, enters **Benutzername** and **Passwort**, and selects **Anmelden**.
6. Under **Planer-Konten**, the administrator creates a named planner, copies the one-time setup link, and delivers it securely. No email is sent by the application.
7. The planner opens the link, sets and confirms a password within 24 hours, then signs in normally. Confirm the planner can use the application and cannot list or manage planner accounts.

There is exactly one application administrator. This account can also perform ordinary planner work. Infrastructure administration through SSH/Docker is a separate authority; it does not create an application operator account, although host control permits initiating administrator recovery.

Do not populate a live institution with demonstration records automatically. The image contains `scripts/seed_dummy_planning_data.py`, but it is an optional demonstration-data operation requiring prior review.

### 8 Daily backup and recovery

#### 8.1 Create a consistent backup

Use the packaged script rather than copying the live SQLite file:

```bash
cd /opt/resource-planner
sudo docker compose exec -T planner python scripts/backup_sqlite_db.py \
  --output-dir /data/backups
```

The script uses SQLite's backup API, writes a timestamped `planner-YYYYMMDD-HHMMSS.db`, and checks `PRAGMA integrity_check`. Copy the resulting file off the Docker volume to protected storage. A file retained only in `/data/backups` is lost with the VM/volume.

#### 8.2 Automate a daily copy to separate storage

The example below assumes the backup team has mounted a separate protected backup destination at `/mnt/planner-backup`. Confirm ownership, encryption, available capacity, and retention with that team. A mount on another directory of the same VM disk does not meet the separate-storage requirement. Mount failure must fail the job rather than silently write to the VM disk.

Save the following root-owned mode-0700 script as `/usr/local/sbin/resource-planner-backup`:

```bash
#!/bin/bash
set -euo pipefail
umask 077
cd /opt/resource-planner
mountpoint -q /mnt/planner-backup

backup_result=$(docker compose exec -T planner python \
  scripts/backup_sqlite_db.py --output-dir /data/backups)
backup_path=${backup_result#Backup created: }
backup_path=${backup_path//$'\r'/}
[[ "$backup_path" =~ ^/data/backups/planner-[0-9]{8}-[0-9]{6}\.db$ ]]

backup_name=${backup_path##*/}
install -d -m 0700 /mnt/planner-backup/resource-planner
docker cp "planner-ressources:$backup_path" \
  "/mnt/planner-backup/resource-planner/$backup_name"
chmod 0600 "/mnt/planner-backup/resource-planner/$backup_name"
sha256sum "/mnt/planner-backup/resource-planner/$backup_name" \
  > "/mnt/planner-backup/resource-planner/$backup_name.sha256"
printf 'Backup copied and checksummed: %s\n' "$backup_name"
```

The script does not automate retention or securely export `.env`. Define backup retention, local `/data/backups` cleanup, protected configuration backup, access permissions, and alerting before operational handover. Avoid collecting `.env` in general backup logs. Test this script against the actual backup mount; storage behavior and permissions depend on the organization infrastructure.

Save `/etc/systemd/system/resource-planner-backup.service`:

```ini
[Unit]
Description=Back up Resource Planner to separate storage
Requires=docker.service
After=docker.service network-online.target
Wants=network-online.target

[Service]
Type=oneshot
UMask=0077
ExecStart=/usr/local/sbin/resource-planner-backup
```

Save `/etc/systemd/system/resource-planner-backup.timer`:

```ini
[Unit]
Description=Run Resource Planner backup daily

[Timer]
OnCalendar=*-*-* 02:00:00 Europe/Vienna
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and verify the job:

```bash
sudo systemctl daemon-reload
systemd-analyze calendar '*-*-* 02:00:00 Europe/Vienna'
sudo systemctl start resource-planner-backup.service
sudo systemctl status resource-planner-backup.service
sudo journalctl -u resource-planner-backup.service --no-pager -n 30
sudo systemctl enable --now resource-planner-backup.timer
sudo systemctl list-timers resource-planner-backup.timer
```

**Expected result:** The first run succeeds, a `.db` and checksum appear on the separate destination, and the next run is scheduled for 02:00 Vienna time. Connect failed-job and missing/stale-backup monitoring to the existing operations process. A timer alone sends no organization-specific alert.

The calendar expression uses an explicit IANA timezone as supported by [systemd calendar syntax](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.time.xml). Validate its next occurrence on the target VM using the command above.

#### 8.3 Test restoration

1. Record the backup file, checksum, matching application image, fingerprint key version, and configuration version. Verify the checksum before restoration.
2. Rehearse on an isolated VM or separate restore volume. Keep the live/original volume intact. Restrict all network access while checking the recovered security state.
3. For an actual cutover, stop the application with `sudo docker compose stop planner`. Preserve the original database and volume, then restore the consistent backup to `/data/planner.db` in a new named volume. Set ownership to UID/GID 10001. Do not merge database files or copy a live journal over the restored database.
4. Point the deployment copy's top-level volume `name` to that new volume, retain the matching fingerprint key, and start the approved compatible image. A blank fresh volume would initialize an empty database, so verify the restored file before startup.
5. Check health, account administration, representative catalog/schedule records, and login. Record the observed recovery duration and recovered data timestamp.
6. Treat restored authentication state as security-sensitive: a backup can restore previously current sessions, unredeemed account links, lecturer links, and startup credential-consumption state. Reset/disable affected planner accounts and replace/revoke lecturer links as necessary. New administrator recovery ends its current planner session. Evaluate any still-valid pre-restore access before reopening the service.
7. Re-enable normal access and the backup job only after validation. Retain the old volume until the rollback window closes under the organization's retention policy.

A daily schedule targets a recovery point around the last successful daily backup; failures can make it older. No recovery-time guarantee is established by this manual. Agree recovery objectives, retention periods, encryption requirements, and restore-test frequency with the owner. VM snapshots are an additional rollback aid and do not replace off-VM backups.

### 9 Upgrade and routine operations

Before each upgrade, create and export a verified database backup, preserve the protected configuration, record the current image digest, and take the VM snapshot required by the VM reference. Test the candidate image and supported schema upgrade against a restored copy first.

During the maintenance window, change only `PLANNER_IMAGE` to the approved new reference and run:

```bash
cd /opt/resource-planner
sudo docker compose config --quiet
sudo docker compose pull
sudo docker compose up -d
sudo docker compose ps
curl --fail http://127.0.0.1:8080/health
sudo docker compose logs --tail=100 planner
```

Verify HTTPS login, ordinary planner access, administrator restrictions, and representative persisted data. Record the resulting image digest. A schema migration can make the database incompatible with an old image; rollback may require restoring the pre-upgrade backup with its matching image and key. Do not assume changing the image tag alone reverses a migration.

Monitor disk usage, backup age, container health, restart counts, HTTPS availability, certificate expiry, and representative planning performance. `restart: unless-stopped` restarts an exited container and normally starts it after host reboot unless it was deliberately stopped; it does not itself restart a process merely marked unhealthy. Test the VM reboot path during acceptance.

Apply Ubuntu, Docker, Nginx, and application-image updates through the maintenance process. Replacing the VM's packages does not update dependencies inside an existing application image; deploy a rebuilt approved image. Define Docker/application log rotation and backup retention to protect the 40 GB disk budget.

## Part Two Authentication and authorization

### 10 Identity and trust boundaries

The application uses local named planner accounts stored in SQLite. It does not use VPN identity, Windows/Active Directory sign-in, SSO, an external identity provider, or email authentication. VPN grants a network route; application credentials grant planner access. MFA and passkeys are not implemented in the reviewed baseline.

| Actor or credential | Authority |
| --- | --- |
| Ordinary active planner | Access planner pages and planning APIs through a current session |
| Sole application administrator | Planner authority plus account creation, setup/reset issuance, disablement, reactivation, and administrator transfer |
| Infrastructure operator | VM, Docker, TLS, backups, and startup recovery configuration; no separate application role |
| Account setup/reset/reactivation credential | Set one account's password through the redemption endpoint; does not grant a planner session |
| Bootstrap credential | Create the first administrator only while no administrator exists |
| Administrator recovery credential | Reset the password of the existing sole administrator only |
| Lecturer review bearer credential | Access one scoped lecturer review capability; never grants planner authority |

General role configuration, multiple administrators, and per-course or per-department planner permissions are not implemented. Ordinary planners share the available planning capabilities. If policy requires more granular separation or MFA, record the gap and the approved treatment before relying on this installation for that requirement.

### 11 Normal login and password protection

1. The browser opens `/login/` over HTTPS. The user submits the login name and password using the frontend.
2. The frontend sends JSON to `POST /api/auth/login` with `X-CSRF-Protection: 1`.
3. The backend trims the login name and compares its case-folded form. Login names contain 1 to 128 characters; display names contain 1 to 200 characters.
4. The backend verifies the password with Argon2id and checks account eligibility and temporary login blocking.
5. On success, any previous session for the account is removed and a new random opaque session is issued. The browser receives a session cookie, and the API returns safe current-account metadata.
6. Each protected request resolves the cookie against the current session record and active account. The backend performs the authorization check before planner route validation or business changes.

Passwords must contain 12 to 128 characters and must not equal the normalized login name after trimming and case folding. The reviewed policy has no mandatory character-class composition, automatic password expiry, password history, or breached-password lookup.

Password storage uses salted Argon2id with time cost 3, memory cost 65,536 KiB, parallelism 4, a 32-byte hash, and a 16-byte salt. Plaintext passwords are not stored. Session and planner account-access secrets are generated from 32 random bytes, represented as 43-character URL-safe values, and persisted as SHA-256 digests. Startup credentials use a digest of their decoded 32-byte value. These facts do not imply database-at-rest encryption; host storage and backup encryption require infrastructure controls.

For an existing account, 10 failed login attempts trigger a 15-minute login block. A correct password does not bypass an active block. Unknown users, invalid credentials, inactive accounts, missing setup passwords, and blocked accounts receive a generic login failure. Unknown-user handling performs a dummy password verification. Login retry blocking does not terminate an already active session. This is account-based protection, not a documented global network rate limiter.

### 12 Session lifecycle

| Control | Reviewed behavior |
| --- | --- |
| Production cookie | `__Host-planner_session` |
| Cookie attributes | `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/`, no `Domain` attribute |
| Browser persistence | No cookie `Expires` or `Max-Age`; browser session restore behavior still requires client testing |
| Concurrent sessions | One current server-side session per account; a new successful login invalidates the old one |
| Inactivity limit | 60 minutes |
| Absolute limit | 12 hours from login, regardless of activity |
| Activity extension | Only a successful protected response carrying `X-Planner-Activity: user` refreshes inactivity |
| Background requests | Session inspection and unmarked automatic requests do not refresh inactivity |
| Logout | Deletes the current session and clears the browser cookie |
| Password change | Requires the current password; success invalidates the session and requires a new login |
| Disable/reset/recovery | Invalidates the affected account's session as described below |
| Invalid session | Protected API returns `401`; protected browser paths redirect to `/login/`; the cookie is cleared |

The frontend removes protected application state on a protected `401`. Authentication and protected responses use `Cache-Control: no-store`. Planner credentials are not stored in browser local storage or session storage by the reviewed authentication implementation.

The activity marker comes from the client; it classifies frontend interactions and is not independent proof that a human is present. Closing a browser is not a substitute for **Abmelden**. Server-side expiry and logout remain the enforceable boundaries. A persisted session can survive a normal container restart while its validity limits still hold.

### 13 Bootstrap and emergency administrator recovery

#### First administrator

The initial bootstrap procedure is described in section 7. The credential is a durable one-time input: startup registers its digest in SQLite, and successful bootstrap consumes it. No administrator session is created automatically, and a second administrator cannot be created through bootstrap once one exists.

#### Emergency recovery

Use this procedure when the sole application administrator cannot sign in:

1. The authorized operator generates a **new**, distinct 64-character hex value with `openssl rand -hex 32` using the protected administrative workflow. Avoid including the output in logs or tickets.
2. Set that value as `PLANNER_ADMIN_RECOVERY_CREDENTIAL` in `/opt/resource-planner/.env`. Preserve the fingerprint key and leave the bootstrap setting empty.
3. Apply the environment change using `sudo docker compose up -d --force-recreate planner` from the deployment directory and verify health.
4. Deliver the recovery value securely to the designated administrator. At `https://resource-planner.intern/administrator-recovery/`, enter it and a new password with confirmation. There is no account selector: the backend targets the existing sole administrator.
5. Success changes that account's password, clears login blocking, invalidates its session, and consumes the recovery credential. The administrator then signs in normally.
6. Clear the consumed recovery value from `.env`, recreate the service again, and confirm health and normal login. Record the recovery event, approver, and outcome outside the application without including the credential or password.

There is no time-based expiry for registered unused startup credentials in this implementation. Removing an unused value from `.env` does **not** revoke it: the database intentionally retains it. To supersede it, register a newly generated value for that purpose. Consumed and replaced values cannot be reactivated by reintroducing them, including after a restart. Never reuse a value across bootstrap and recovery. A database restore can roll back this anti-replay state, which is why restore acceptance must include credential review.

### 14 Planner account lifecycle

The administrator uses **Planer-Konten**. All account-management API operations independently recheck administrator authority; hiding a navigation item is not the access control.

| Operation | Effect |
| --- | --- |
| Create account | Creates an inactive ordinary planner without a password and returns a setup credential once |
| Redeem setup | Sets a password and activates the account; user must sign in normally |
| Reissue setup | Replaces the earlier account-access credential; the old link stops working |
| Reset access | Immediately removes the ordinary planner's password and ends its session; returns a fresh reset link |
| Disable | Makes the ordinary planner inactive, removes its password, ends its session, and removes outstanding account access |
| Issue reactivation | Returns a fresh link for a disabled planner; the account stays inactive until successful password setup |
| Transfer administration | Atomically transfers the sole administrator flag to another eligible active planner; the former administrator retains ordinary planner access |

Setup, reset, and reactivation credentials expire after 24 hours and are single use. Issuing a replacement deletes earlier account-access credentials for that account. The generated delivery link has the form `https://resource-planner.intern/account-access/#/<credential>`.

The browser extracts the fragment and removes it from the displayed URL before terminology loading or other network work. The secret is sent in the JSON redemption body and retained only in component memory during that flow. A refresh after fragment removal may require reopening the original unconsumed link. Never place the credential in a query string or copy the link into an audit attachment.

The administrator sees a usable account link only in the immediate result and must deliver it manually through an approved channel. After dismissal, issue a replacement if necessary. Redemption never automatically creates a session. Administrators cannot reset or disable their own administrator account through these account actions; use password change or operator-assisted recovery.

State-changing account administration uses revision checks. A stale concurrent action receives `409` and requires refreshing the account view. Administrator transfer immediately changes authorization even if the former administrator still has a valid planner session.

### 15 Request authorization and CSRF protection

The middleware denies planner access by default. All non-allowlisted `/api/` routes, planner browser routes, and `/docs`, `/redoc`, and `/openapi.json` require a current active planner session. Ordinary planners receive `403` on administrator-only account APIs.

The exact public API exceptions are:

| Method | Path | Required authority |
| --- | --- | --- |
| GET | `/health` | None; status only |
| GET | `/api/public/ui-terminology` | None |
| GET | `/api/public/lecturer-review` | Scoped lecturer bearer credential |
| GET | `/api/public/lecturer-review/calendar` | Scoped lecturer bearer credential |
| POST | `/api/public/lecturer-review/feedback` | Scoped lecturer bearer credential |
| POST | `/api/auth/login` | Login credentials |
| POST | `/api/auth/bootstrap` | Current unused bootstrap credential and absence of an administrator |
| POST | `/api/auth/account-access/redemption` | Current unused account-access credential |
| POST | `/api/auth/administrator-recovery` | Current unused recovery credential and an existing administrator |

The public browser entry points are `/login/`, `/bootstrap/`, `/account-access/`, `/administrator-recovery/`, and `/lecturer-review/`, plus static assets. Loading a page does not grant access to its protected data or complete its privileged action.

State-changing planner and authentication requests require `X-CSRF-Protection: 1` and JSON content. Logout requires the header but is exempt from the JSON-content requirement. Missing CSRF protection produces `403`; an unsupported required content type produces `415`. The custom header, strict same-site cookie, and absence of production credentialed cross-origin CORS permission work together. The implementation does not use a synchronizer-token CSRF scheme. Keep the frontend and API on the same HTTPS origin, with no permissive CORS override at the proxy.

### 16 Lecturer review access remains separate

Lecturers do not receive planner accounts merely because they have a review link. A planner issues a capability scoped to one lecturer and one semester revision; anyone possessing it can exercise its scoped review functions while it remains valid. Internal-only deployment also means the recipient needs LAN/VPN network access.

The browser removes the lecturer link fragment and calls only the public lecturer endpoints with `Authorization: Bearer <credential>`. Those calls omit planner cookies. The server applies link scope, expiry, replacement, revocation, and revision rules. Public lecturer bearer operations do not use the planner cookie-CSRF mechanism.

A stored lecturer credential presented to a protected planner operation is rejected with `403`, including when a planner cookie is also supplied. A planner cookie does not grant lecturer review capability. Lecturer links, planner setup links, startup credentials, and planner sessions cannot be substituted for one another.

Calendar export produces a file outside application control. Revoking the review link does not revoke an already downloaded calendar file. Follow the organization's information-handling rules for exported schedules.

### 17 Audit visibility and limitations

The account view provides display/login identity, administrator or planner access level, active/inactive state, creation time, and applicable disablement/reactivation times. It does not provide a detailed login, password, session, account-action, or planner-work attribution audit trail. Some lecturer-review events have their own persistence; they are not a general authentication audit log.

For an audit, retain infrastructure change approvals, release identifiers, sanitized deployment checks, access review decisions, recovery records, backup-job results, and restore-test evidence in the organization's controlled evidence system. Nginx, Docker, and system logs can support operations but do not prove which named planner performed every application change. Do not infer a complete attributable activity history from them.

Other material limits are local single-VM availability, operator access to Docker environment secrets, no built-in MFA/SSO, no self-service forgotten-password email, no automatic backup scheduling in the application image, and no measured capacity or recovery guarantee for the supplied VM. Record policy requirements separately and resolve any mandatory control gap before production approval.

## Part Three Verification and audit evidence

### 18 Deployment acceptance checklist

Complete this checklist against the actual deployed image and VM. Record date, tester, result, and a sanitized evidence reference for each check. Every item below remains **pending target-VM verification** until completed by the deployment team.

| ID | Check | Expected evidence or result |
| --- | --- | --- |
| D01 | VM baseline | Ubuntu 24.04, architecture, CPU/RAM/disk, internal IP, asset identifier, and time synchronization recorded |
| D02 | Release identity | Approved tag/digest, source revision, actual image ID, and applicable release/scan record retained |
| D03 | Network exposure | Approved LAN and VPN clients reach HTTPS; disallowed networks fail; remote 8080 fails; SSH limited to management sources |
| D04 | TLS and same origin | Valid trusted certificate and expiry; frontend/API share the HTTPS origin; no production credentialed cross-origin allowance |
| D05 | Secret handling | `.env` mode 0600 in restricted directory; distinct startup values; stable fingerprint key retained in protected storage; audit evidence contains no secrets |
| D06 | Container health | Healthy status, `/health` response, UID 10001, and effective `/data` mount confirmed |
| D07 | Bootstrap | First administrator created; second attempt rejected; consumed value removed from runtime configuration; normal login succeeds |
| D08 | Default access denial | Without cookies, `GET /api/planning-options` and `GET /api/auth/session` return `401`; `/` redirects to `/login/` |
| D09 | Cookie | Browser developer tools show `__Host-planner_session`, Secure, HttpOnly, SameSite Strict, host-only scope, and path `/`; record attributes without the value |
| D10 | Planner authorization | Ordinary planner can perform intended planning work; `GET /api/planner-accounts` returns `403`; administrator can manage accounts |
| D11 | Lifecycle | Disposable planner setup, expired/replaced/used-link rejection, reset, disablement, and reactivation behave as described |
| D12 | Sessions | Second login invalidates first session; logout/password change invalidate it; inactivity and absolute limits confirmed with controlled test timing |
| D13 | Login blocking | Disposable existing account is blocked after 10 failed attempts for 15 minutes; error stays generic; avoid production administrator lockout |
| D14 | CSRF | Login POST without the custom header returns `403`; with the header but wrong content type returns `415` |
| D15 | Lecturer boundary | Valid lecturer link works only for its scope; same credential fails on planner APIs, including beside a planner cookie |
| D16 | Recovery and transfer | Isolated rehearsal confirms sole-administrator recovery, consumed-value rejection, and administrator transfer without residual management authority |
| D17 | Persistence and restart | Test record survives service recreation and a planned VM reboot; service starts and HTTPS login succeeds |
| D18 | Backup and restore | Daily job and separate-storage copy succeed; missing-mount failure is detected; checksum and isolated restore tested; recovered security state reviewed |
| D19 | Operations | Trusted proxy/client-address handling verified; owners, patching, log/backup retention, disk and certificate monitoring, failure alerts, and recovery objectives documented |

Examples of read-only checks without an authenticated session:

```bash
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  https://resource-planner.intern/api/planning-options
curl --silent --output /dev/null --write-out '%{http_code}\n' \
  https://resource-planner.intern/api/auth/session
curl --silent --output /dev/null --dump-header - \
  https://resource-planner.intern/
```

The first two should return 401; the last should show a 307 redirect to `/login/`. From a separate authorized workstation, test `http://VM_IP:8080/health` with a short connection timeout; connection should fail, while the same endpoint on VM loopback succeeds. Use the actual VM IP and approved test clients.

Do not retain complete browser network captures, cookies, setup links, request bodies, or environment dumps as evidence. Redact secrets before attaching diagnostic output.

### 19 Troubleshooting

| Symptom | Focused checks and resolution |
| --- | --- |
| Image pull denied or image missing | Confirm approved tag/digest, package visibility, registry access, and outbound connectivity. `.env.example` does not prove release availability |
| Container exits at startup | Inspect recent logs for missing/short fingerprint key, invalid timezone, malformed startup credential, invalid terminology file, volume permissions, or unsupported schema. Preserve the database |
| HTTPS returns 502 | Check container health, `127.0.0.1:8080/health`, port mapping, and `nginx -t`; inspect Nginx and container logs |
| Login seems successful then returns to login | Verify HTTPS, trusted certificate, exact hostname, production cookie attributes, shared frontend/API origin, and proxy cookie handling |
| Login keeps failing | Confirm user setup is complete, account is active, and credentials are correct. Allow a 15-minute block to end; use authorized reset/recovery when needed |
| Bootstrap/recovery unavailable | Confirm correct purpose, fresh current value, intended administrator state, and recreation after `.env` change. Consumed/replaced values cannot be reused |
| Setup link unavailable after refresh | Reopen the original unconsumed link; the page removes its fragment. If expired, used, or replaced, ask the administrator for fresh access |
| Application data appears empty | Stop and verify the volume name and `/data` mapping against the deployment record. Locate the original volume before creating/importing data |
| Backup job fails | Inspect its journal, separate-storage mount, free space, permissions, container health, and output file/checksum. Do not accept a local fallback as a successful off-VM backup |
| Container marked unhealthy but still running | Inspect health/application logs; the restart policy does not restart solely for unhealthy status. Investigate before a controlled restart |

### 20 Preparation evidence and unresolved verification

This manual uses the supplied VM document as infrastructure reference material, not as operational instructions authorizing changes to that VM. Only repository documentation was created during this task.

The implementation evidence reviewed includes:

- `compose.yaml`, `.env.example`, `infrastructure/docker/Dockerfile`, and `infrastructure/docker/README.md` for runtime configuration, health checking, persistence, and secrets.
- `.github/workflows/publish-container.yml` for release publishing and image architectures.
- `backend/app/main.py`, `backend/app/frontend.py`, and `backend/app/db/schema.py` for startup, public/protected routes, production CORS, and database initialization.
- `backend/app/services/planner_auth.py`, `backend/app/api/planner_auth.py`, and `backend/app/schemas/planner_auth.py` for password rules, sessions, startup credentials, account lifecycle, and cookies.
- `client/src/api/authentication.ts`, `client/src/api/plannerFetch.ts`, and `client/src/main.tsx` for request headers, session handling, and fragment removal.
- `backend/app/api/lecturer_review.py` and `backend/app/services/lecturer_review.py` for the separate bearer boundary and stable installation key.
- `backend/scripts/backup_sqlite_db.py` for transaction-consistent backup and integrity checking.
- Existing authentication service, concurrency, API, planner-authorization, and lecturer-boundary tests, and the FS-016 authorization/UI contracts.
- `docs/planning/Feature_slices.md` and the existing user manual for scope and terminology.

The scope map still labels FS-016 as ready for specification even though current implementation and authentication tests exist. This manual follows the current implementation and records that documentation inconsistency without changing the scope map. It does not claim every planned feature or older acceptance item is complete.

| Area | Documentation disposition |
| --- | --- |
| I-001 container distribution | Included from current implementation; actual release pull and target-VM installation remain pending |
| FS-016 planner authentication and account administration | Included from implementation and focused tests; deployed-image and browser/VM acceptance remain pending |
| FS-015 lecturer review and FS-020 calendar export | Included only where needed to explain credential separation, stable keys, and exported-data limits |
| FS-022 authenticated lecturer accounts and other future workflows | Excluded from available functionality |
| Five-user capacity, availability, backup storage, TLS, firewall, and recovery objectives | Organization/deployment verification required; not established by source review |

The preparation checks and their results are recorded below. They support this source-based explanation and do not substitute for the acceptance checklist above.

| Check performed during preparation | Result |
| --- | --- |
| Focused backend authentication, concurrency, API, planner-authorization, and lecturer-boundary tests | **38 passed**, 24 warnings; no failures |
| Copied Compose configuration with the documented loopback port change and a non-secret dummy fingerprint value | `docker compose config --quiet` passed; resolved configuration confirmed one `127.0.0.1:8080` binding, production mode, and `planner-ressources-data` persistence |
| Bash examples extracted from this manual including the server PoC | All 19 blocks, including indented examples, passed `bash -n`; syntax check only, installation commands were not executed |
| Minimal server PoC configuration | Reviewed separate container/volume, loopback port binding, development cookie mode, SSH tunnel, and first-login steps against the implementation; server execution remains pending |
| Actual Linux installation, Nginx runtime, backup mount/job, restore, certificate, and firewall checks | Not run on the target VM; pending deployment acceptance |

The focused test command, run from `backend` with the repository's existing virtual environment, was:

```text
python -m pytest tests/services/test_planner_auth.py tests/services/test_planner_auth_concurrency.py tests/api/test_planner_auth.py tests/api/test_planner_authorization.py tests/api/test_lecturer_bearer_authorization.py -q
```

The test run reported framework/datetime deprecation warnings and one SQLAlchemy session-delete warning in a concurrency test. Passing tests support the described behavior; they do not establish a complete security audit or validate the external infrastructure. No application source or deployment configuration in the repository was changed.

### 21 External installation references

Official infrastructure documentation was checked during preparation on 15 October 2026. Recheck it when maintaining the installation, since supported package versions and installation guidance can change.

- [Docker Engine installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker published ports](https://docs.docker.com/engine/network/port-publishing/)
- [Docker packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [Docker daemon access protection](https://docs.docker.com/engine/security/protect-access/)
- [GitHub Container Registry authentication and visibility](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Nginx HTTP proxy configuration](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Nginx HTTPS configuration](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [Uvicorn trusted proxy settings](https://raw.githubusercontent.com/encode/uvicorn/master/docs/settings.md)
- [systemd calendar time syntax](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.time.xml)
