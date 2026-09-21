# Umbrel derives independent, stable secrets per installation.
# Preserve successful derivations, but never start with missing or failed ones.
rr_secret() (
  set -o pipefail
  local value
  value="$(derive_entropy "${app_entropy_identifier}-$1")" && [[ -n "$value" ]] || {
    echo "Reactive Resume: could not derive $1." >&2
    return 1
  }
  printf '%s' "$value"
)
export APP_KONINGKOFFIE_REACTIVE_RESUME_POSTGRES_PASSWORD=""
export APP_KONINGKOFFIE_REACTIVE_RESUME_AUTH_SECRET=""
export APP_KONINGKOFFIE_REACTIVE_RESUME_ENCRYPTION_SECRET=""
APP_KONINGKOFFIE_REACTIVE_RESUME_POSTGRES_PASSWORD="$(rr_secret postgres-password)" || return 1
APP_KONINGKOFFIE_REACTIVE_RESUME_AUTH_SECRET="$(rr_secret auth-secret)" || return 1
APP_KONINGKOFFIE_REACTIVE_RESUME_ENCRYPTION_SECRET="$(rr_secret encryption-secret)" || return 1
unset -f rr_secret

# Ask the host routing table for its preferred IPv4 source address.
# This route lookup does not send traffic to the destination.
rr_local_ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<NF;i++) if ($i == "src") {print $(i+1); exit}}')" || rr_local_ip=""
if [[ ! "$rr_local_ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "Reactive Resume: could not determine the host IPv4 address from its routing table." >&2
  rr_local_ip=""
fi
export APP_KONINGKOFFIE_REACTIVE_RESUME_LOCAL_IP="$rr_local_ip"
unset rr_local_ip
