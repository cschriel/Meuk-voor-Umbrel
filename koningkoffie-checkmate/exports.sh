# Umbrel derives independent, stable secrets per installation.
export APP_KONINGKOFFIE_CHECKMATE_MONGO_PASSWORD="$(derive_entropy "${app_entropy_identifier}-mongo-password")"
export APP_KONINGKOFFIE_CHECKMATE_JWT_SECRET="$(derive_entropy "${app_entropy_identifier}-jwt-secret")"

# Checkmate requires exactly 32 bytes encoded as padded standard base64.
# Hash the derived secret to that length without depending on its text encoding.
export APP_KONINGKOFFIE_CHECKMATE_ENCRYPTION_KEY="$(derive_entropy "${app_entropy_identifier}-encryption-key" | openssl dgst -sha256 -binary | openssl base64 -A)"

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
