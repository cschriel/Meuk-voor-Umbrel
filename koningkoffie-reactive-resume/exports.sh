# Umbrel derives independent, stable secrets per installation.
export APP_KONINGKOFFIE_REACTIVE_RESUME_POSTGRES_PASSWORD="$(derive_entropy "${app_entropy_identifier}-postgres-password")"
export APP_KONINGKOFFIE_REACTIVE_RESUME_AUTH_SECRET="$(derive_entropy "${app_entropy_identifier}-auth-secret")"
export APP_KONINGKOFFIE_REACTIVE_RESUME_ENCRYPTION_SECRET="$(derive_entropy "${app_entropy_identifier}-encryption-secret")"
