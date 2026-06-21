savedcmd_crypto_kernel.mod := printf '%s\n'   crypto_kernel.o | awk '!x[$$0]++ { print("./"$$0) }' > crypto_kernel.mod
