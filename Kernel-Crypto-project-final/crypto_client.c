/*
 * crypto_client.c - User-space program to test crypto_kernel module
 *
 * Usage:
 *   ./crypto_client encrypt "plaintext message"
 *   ./crypto_client decrypt <hex_ciphertext>
 *
 * Architecture:
 *   opens /dev/crypto_kernel -> ioctl(CRYPTO_ENCRYPT|CRYPTO_DECRYPT)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/types.h>

#include "crypto_ioctl.h"

static int hex2byte(char c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

static size_t hex2bin(const char *hex, unsigned char *bin, size_t max_len)
{
	size_t len = strlen(hex);
	size_t i, j;

	if (len % 2 != 0)
		return 0;

	len /= 2;
	if (len > max_len)
		len = max_len;

	for (i = 0, j = 0; i < len; i++, j += 2) {
		int hi = hex2byte(hex[j]);
		int lo = hex2byte(hex[j + 1]);
		if (hi < 0 || lo < 0)
			return 0;
		bin[i] = (unsigned char)((hi << 4) | lo);
	}

	return len;
}

int main(int argc, char *argv[])
{
	const char *op;
	unsigned char input_buf[CRYPTO_BUFFER_MAX];
	unsigned char output_buf[CRYPTO_BUFFER_MAX + 16];
	struct crypto_data cd;
	int fd;
	int ret;

	if (argc < 3) {
		fprintf(stderr, "Usage:\n");
		fprintf(stderr, "  %s encrypt \"plain text\"\n", argv[0]);
		fprintf(stderr, "  %s decrypt <hex_ciphertext>\n", argv[0]);
		return 1;
	}

	op = argv[1];

	fd = open(CRYPTO_DEVICE_PATH, O_RDWR);
	if (fd < 0) {
		perror("Failed to open " CRYPTO_DEVICE_PATH);
		fprintf(stderr, "Make sure the kernel module is loaded:\n");
		fprintf(stderr, "  sudo insmod crypto_kernel.ko\n");
		return 1;
	}

	if (strcmp(op, "encrypt") == 0) {
		size_t len = strlen(argv[2]);

		if (len > CRYPTO_BUFFER_MAX) {
			fprintf(stderr, "Input too long (max %d bytes)\n",
				CRYPTO_BUFFER_MAX);
			close(fd);
			return 1;
		}

		memcpy(input_buf, argv[2], len);

		cd.input      = input_buf;
		cd.input_len  = (__u32)len;
		cd.output     = output_buf;
		cd.output_len = sizeof(output_buf);

		ret = ioctl(fd, CRYPTO_ENCRYPT, &cd);
		if (ret < 0) {
			perror("ioctl CRYPTO_ENCRYPT failed");
			close(fd);
			return 1;
		}

		printf("Plaintext:  %s\n", argv[2]);
		printf("Ciphertext: ");
		{
			size_t i;
			for (i = 0; i < cd.output_len; i++)
				printf("%02x", output_buf[i]);
			printf("\n");
		}
		printf("(ciphertext length: %u bytes)\n", cd.output_len);

	} else if (strcmp(op, "decrypt") == 0) {
		size_t bin_len;

		bin_len = hex2bin(argv[2], input_buf, sizeof(input_buf));
		if (bin_len == 0) {
			fprintf(stderr, "Invalid hex string\n");
			close(fd);
			return 1;
		}

		cd.input      = input_buf;
		cd.input_len  = (__u32)bin_len;
		cd.output     = output_buf;
		cd.output_len = sizeof(output_buf);

		ret = ioctl(fd, CRYPTO_DECRYPT, &cd);
		if (ret < 0) {
			perror("ioctl CRYPTO_DECRYPT failed");
			close(fd);
			return 1;
		}

		output_buf[cd.output_len] = '\0';
		printf("Ciphertext (hex): %s\n", argv[2]);
		printf("Decrypted text:   %s\n", (char *)output_buf);
		printf("(decrypted length: %u bytes)\n", cd.output_len);

	} else {
		fprintf(stderr, "Unknown operation: %s\n", op);
		fprintf(stderr, "Use 'encrypt' or 'decrypt'\n");
		close(fd);
		return 1;
	}

	close(fd);
	return 0;
}
