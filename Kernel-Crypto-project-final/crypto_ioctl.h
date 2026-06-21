#ifndef _CRYPTO_IOCTL_H
#define _CRYPTO_IOCTL_H

#ifdef __KERNEL__
#include <linux/ioctl.h>
#else
#include <sys/ioctl.h>
#endif

#include <linux/types.h>

#define CRYPTO_DEVICE_PATH	"/dev/crypto_kernel"
#define CRYPTO_BUFFER_MAX	4096

struct crypto_data {
	__u8  *input;
	__u32  input_len;
	__u8  *output;
	__u32  output_len;
};

#define CRYPTO_MAGIC	'C'
#define CRYPTO_ENCRYPT	_IOWR(CRYPTO_MAGIC, 1, struct crypto_data)
#define CRYPTO_DECRYPT	_IOWR(CRYPTO_MAGIC, 2, struct crypto_data)

#endif
