# Umbrel derives independent, stable secrets per installation.
export APP_KONINGKOFFIE_REACTIVE_RESUME_POSTGRES_PASSWORD="$(derive_entropy "${app_entropy_identifier}-postgres-password")"
export APP_KONINGKOFFIE_REACTIVE_RESUME_AUTH_SECRET="$(derive_entropy "${app_entropy_identifier}-auth-secret")"
export APP_KONINGKOFFIE_REACTIVE_RESUME_ENCRYPTION_SECRET="$(derive_entropy "${app_entropy_identifier}-encryption-secret")"

# Ask the host routing table for its preferred IPv4 source address.
# This route lookup does not send traffic to the destination.
rr_local_ip="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<NF;i++) if ($i == "src") {print $(i+1); exit}}')" || rr_local_ip=""
if [[ ! "$rr_local_ip" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "Reactive Resume: could not determine the host IPv4 address from its routing table." >&2
  rr_local_ip=""
fi
export APP_KONINGKOFFIE_REACTIVE_RESUME_LOCAL_IP="$rr_local_ip"
unset rr_local_ip
