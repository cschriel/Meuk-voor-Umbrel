# Fail closed without changing any bytes of the existing successful derivations.
checkmate_secret() (
  set -o pipefail
  local value
  value="$(derive_entropy "${app_entropy_identifier}-$1")" || return 1
  [[ -n "$value" ]] || return 1
  printf '%s' "$value"
)
export APP_KONINGKOFFIE_CHECKMATE_MONGO_PASSWORD=""
export APP_KONINGKOFFIE_CHECKMATE_JWT_SECRET=""
export APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY=""
export APP_KONINGKOFFIE_CHECKMATE_DB_PASSWORD=""
APP_KONINGKOFFIE_CHECKMATE_MONGO_PASSWORD="$(checkmate_secret mongo-password)" || return 1
APP_KONINGKOFFIE_CHECKMATE_JWT_SECRET="$(checkmate_secret jwt-secret)" || return 1
APP_KONINGKOFFIE_CHECKMATE_DB_PASSWORD="$(checkmate_secret database-user-password)" || return 1
# Preserve the original pipeline's trailing newline, if derive_entropy emits one.
# A temporary file lets us check derivation success without stripping its bytes.
checkmate_encryption_key() (
  set -o pipefail
  umask 077
  local secret_file
  secret_file="$(mktemp)" || return 1
  trap 'rm -f "$secret_file"' EXIT
  derive_entropy "${app_entropy_identifier}-encryption-key" > "$secret_file" || return 1
  [[ -s "$secret_file" ]] || return 1
  openssl dgst -sha256 -binary < "$secret_file" | openssl base64 -A
)
APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY="$(checkmate_encryption_key)" || return 1
[[ "$APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY" =~ ^[A-Za-z0-9+/]{43}=$ ]] || return 1
unset -f checkmate_secret checkmate_encryption_key

# Ask the host routing table for its preferred IPv4 source address.
# This route lookup does not send traffic to the destination.
checkmate_local_ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<NF;i++) if ($i == "src") {print $(i+1); exit}}')" || checkmate_local_ip=""
if [[ ! "$checkmate_local_ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "Checkmate: could not determine the host IPv4 address from its routing table." >&2
  checkmate_local_ip=""
fi
export APP_KONINGKOFFIE_CHECKMATE_LOCAL_IP="$checkmate_local_ip"
unset checkmate_local_ip

# Docker's socket group varies between hosts. Add its numeric GID to the
# container's supplementary groups so the image's node user can connect.
checkmate_docker_gid="$(stat -c '%g' /var/run/docker.sock 2>/dev/null)" || checkmate_docker_gid=""
if [[ ! "$checkmate_docker_gid" =~ ^[0-9]+$ ]]; then
  echo "Checkmate: could not determine the group of /var/run/docker.sock." >&2
  checkmate_docker_gid=""
fi
export APP_KONINGKOFFIE_CHECKMATE_DOCKER_GID="$checkmate_docker_gid"
unset checkmate_docker_gid

# A plain-text setting survives app upgrades; never source it as shell code.
export APP_KONINGKOFFIE_CHECKMATE_PUBLIC_URL="${APP_KONINGKOFFIE_CHECKMATE_PUBLIC_URL:-}"
if [[ -z "$APP_KONINGKOFFIE_CHECKMATE_PUBLIC_URL" && -n "${EXPORTS_APP_DATA_DIR:-}" && -f "$EXPORTS_APP_DATA_DIR/public-url" ]]; then
  APP_KONINGKOFFIE_CHECKMATE_PUBLIC_URL="$(cat "$EXPORTS_APP_DATA_DIR/public-url")" || return 1
fi
if [[ -n "$APP_KONINGKOFFIE_CHECKMATE_PUBLIC_URL" && ! "$APP_KONINGKOFFIE_CHECKMATE_PUBLIC_URL" =~ ^https?://[^[:space:]]+$ ]]; then
  echo "Checkmate: data/public-url must contain one HTTP or HTTPS URL." >&2
  return 1
fi
