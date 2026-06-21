// SPDX-License-Identifier: GPL-2.0-only
/*
 * crypto_kernel.c - AES-256-CBC encryption/decryption via Linux Crypto API
 *
 * Creates /dev/crypto_kernel character device for user-space applications
 * to send data for encryption/decryption in kernel space.
 *
 * Architecture:
 *   User Application -> ioctl() -> Character Device -> Linux Crypto API -> AES-256-CBC
 */

#include <linux/module.h>
#include <linux/init.h>
#include <linux/fs.h>
#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/crypto.h>
#include <crypto/skcipher.h>
#include <linux/string.h>
#include <linux/err.h>
#include <linux/scatterlist.h>

#include "crypto_ioctl.h"

#define DEVICE_NAME	"crypto_kernel"
#define CLASS_NAME	"crypto_class"

#define AES256_KEY_SIZE	32
#define AES_BLOCK_SIZE	16

/* Hard-coded 256-bit key for demo purposes */
static const u8 aes_key[AES256_KEY_SIZE] = {
	0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
	0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c,
	0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
	0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c,
};

/* Hard-coded IV for demo purposes */
static const u8 aes_iv[AES_BLOCK_SIZE] = {
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
	0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
};

/* Per-file-descriptor context */
struct crypto_ctx {
	struct crypto_skcipher *tfm;
};

/* Character device structures */
static dev_t dev_num;
static struct cdev crypto_cdev;
static struct class *crypto_class;
static struct device *crypto_device;

/* Module parameters */
static int major;

/* Forward declarations */
static int crypto_open(struct inode *inode, struct file *filp);
static int crypto_release(struct inode *inode, struct file *filp);
static ssize_t crypto_read(struct file *filp, char __user *buf,
			   size_t len, loff_t *off);
static ssize_t crypto_write(struct file *filp, const char __user *buf,
			    size_t len, loff_t *off);
static long crypto_ioctl(struct file *filp, unsigned int cmd,
			 unsigned long arg);

/* File operations */
static const struct file_operations crypto_fops = {
	.owner          = THIS_MODULE,
	.open           = crypto_open,
	.release        = crypto_release,
	.read           = crypto_read,
	.write          = crypto_write,
	.unlocked_ioctl = crypto_ioctl,
};

/* ---- PKCS#7 Padding ---- */

static size_t padded_len(size_t input_len)
{
	size_t rem = input_len % AES_BLOCK_SIZE;
	size_t pad = AES_BLOCK_SIZE - rem;
	return input_len + pad;
}

static int pkcs7_pad(u8 *data, size_t input_len, size_t buf_size)
{
	size_t pad_len = padded_len(input_len) - input_len;
	size_t i;

	if (input_len + pad_len > buf_size)
		return -ENOSPC;

	for (i = 0; i < pad_len; i++)
		data[input_len + i] = (u8)pad_len;

	return (int)(input_len + pad_len);
}

static int pkcs7_unpad(u8 *data, size_t data_len)
{
	size_t pad_len;
	size_t i;

	if (data_len == 0 || data_len % AES_BLOCK_SIZE != 0)
		return -EINVAL;

	pad_len = data[data_len - 1];
	if (pad_len < 1 || pad_len > AES_BLOCK_SIZE)
		return -EINVAL;

	for (i = data_len - pad_len; i < data_len; i++)
		if (data[i] != pad_len)
			return -EINVAL;

	return (int)(data_len - pad_len);
}

/* ---- Cryptographic Operations ---- */

static int crypto_encrypt(struct crypto_skcipher *tfm,
			  const u8 *plaintext, size_t plaintext_len,
			  u8 *ciphertext, size_t *ciphertext_len)
{
	struct skcipher_request *req = NULL;
	u8 *iv = NULL;
	u8 *buf = NULL;
	struct scatterlist sg_src, sg_dst;
	size_t enc_len;
	int ret;

	enc_len = padded_len(plaintext_len);
	if (enc_len > CRYPTO_BUFFER_MAX + AES_BLOCK_SIZE)
		return -ENOSPC;

	buf = kmalloc(enc_len, GFP_KERNEL);
	if (!buf)
		return -ENOMEM;

	memcpy(buf, plaintext, plaintext_len);

	ret = pkcs7_pad(buf, plaintext_len, enc_len);
	if (ret < 0)
		goto out;
	enc_len = (size_t)ret;

	iv = kmemdup(aes_iv, AES_BLOCK_SIZE, GFP_KERNEL);
	if (!iv) {
		ret = -ENOMEM;
		goto out;
	}

	req = skcipher_request_alloc(tfm, GFP_KERNEL);
	if (!req) {
		ret = -ENOMEM;
		goto out;
	}

	skcipher_request_set_callback(req, CRYPTO_TFM_REQ_MAY_SLEEP,
				      NULL, NULL);

	sg_init_one(&sg_src, buf, enc_len);
	sg_init_one(&sg_dst, ciphertext, enc_len);

	skcipher_request_set_crypt(req, &sg_src, &sg_dst, enc_len, iv);

	ret = crypto_skcipher_encrypt(req);
	if (ret == 0)
		*ciphertext_len = enc_len;

out:
	if (req)
		skcipher_request_free(req);
	kfree(iv);
	kfree(buf);
	return ret;
}

static int crypto_decrypt(struct crypto_skcipher *tfm,
			  const u8 *ciphertext, size_t ciphertext_len,
			  u8 *plaintext, size_t *plaintext_len)
{
	struct skcipher_request *req = NULL;
	u8 *iv = NULL;
	u8 *buf = NULL;
	struct scatterlist sg_src, sg_dst;
	int ret;

	if (ciphertext_len == 0 || ciphertext_len % AES_BLOCK_SIZE != 0)
		return -EINVAL;

	buf = kmalloc(ciphertext_len, GFP_KERNEL);
	if (!buf)
		return -ENOMEM;

	iv = kmemdup(aes_iv, AES_BLOCK_SIZE, GFP_KERNEL);
	if (!iv) {
		ret = -ENOMEM;
		goto out;
	}

	req = skcipher_request_alloc(tfm, GFP_KERNEL);
	if (!req) {
		ret = -ENOMEM;
		goto out;
	}

	skcipher_request_set_callback(req, CRYPTO_TFM_REQ_MAY_SLEEP,
				      NULL, NULL);

	sg_init_one(&sg_src, ciphertext, ciphertext_len);
	sg_init_one(&sg_dst, buf, ciphertext_len);

	skcipher_request_set_crypt(req, &sg_src, &sg_dst,
				   ciphertext_len, iv);

	ret = crypto_skcipher_decrypt(req);
	if (ret)
		goto out;

	ret = pkcs7_unpad(buf, ciphertext_len);
	if (ret < 0)
		goto out;

	*plaintext_len = (size_t)ret;
	memcpy(plaintext, buf, *plaintext_len);

out:
	if (req)
		skcipher_request_free(req);
	kfree(iv);
	kfree(buf);
	return ret;
}

/* ---- File Operations ---- */

static int crypto_open(struct inode *inode, struct file *filp)
{
	struct crypto_ctx *ctx;
	int ret;

	ctx = kzalloc(sizeof(*ctx), GFP_KERNEL);
	if (!ctx)
		return -ENOMEM;

	ctx->tfm = crypto_alloc_skcipher("cbc(aes)", 0, 0);
	if (IS_ERR(ctx->tfm)) {
		ret = PTR_ERR(ctx->tfm);
		pr_err("crypto_kernel: failed to alloc skcipher: %d\n", ret);
		kfree(ctx);
		return ret;
	}

	ret = crypto_skcipher_setkey(ctx->tfm, aes_key, AES256_KEY_SIZE);
	if (ret) {
		pr_err("crypto_kernel: failed to set key: %d\n", ret);
		crypto_free_skcipher(ctx->tfm);
		kfree(ctx);
		return ret;
	}

	filp->private_data = ctx;
	pr_debug("crypto_kernel: opened (ctx=%p)\n", ctx);
	return 0;
}

static int crypto_release(struct inode *inode, struct file *filp)
{
	struct crypto_ctx *ctx = filp->private_data;

	if (ctx) {
		crypto_free_skcipher(ctx->tfm);
		kfree(ctx);
		filp->private_data = NULL;
		pr_debug("crypto_kernel: released\n");
	}
	return 0;
}

static ssize_t crypto_read(struct file *filp, char __user *buf,
			   size_t len, loff_t *off)
{
	pr_debug("crypto_kernel: read called (len=%zu)\n", len);
	return 0;
}

static ssize_t crypto_write(struct file *filp, const char __user *buf,
			    size_t len, loff_t *off)
{
	pr_debug("crypto_kernel: write called (len=%zu)\n", len);
	return len;
}

static long crypto_ioctl(struct file *filp, unsigned int cmd,
			 unsigned long arg)
{
	struct crypto_ctx *ctx = filp->private_data;
	struct crypto_data cd;
	u8 *k_input = NULL;
	u8 *k_output = NULL;
	int ret;

	if (!ctx)
		return -EINVAL;

	if (_IOC_TYPE(cmd) != CRYPTO_MAGIC)
		return -ENOTTY;
	if (_IOC_NR(cmd) < 1 || _IOC_NR(cmd) > 2)
		return -ENOTTY;

	ret = copy_from_user(&cd, (void __user *)arg, sizeof(cd));
	if (ret)
		return -EFAULT;

	if (!cd.input || !cd.output || cd.input_len == 0)
		return -EINVAL;

	if (cd.input_len > CRYPTO_BUFFER_MAX)
		return -EINVAL;

	k_input = memdup_user(cd.input, cd.input_len);
	if (IS_ERR(k_input))
		return PTR_ERR(k_input);

	k_output = kmalloc(CRYPTO_BUFFER_MAX + AES_BLOCK_SIZE, GFP_KERNEL);
	if (!k_output) {
		kfree(k_input);
		return -ENOMEM;
	}

	switch (cmd) {
	case CRYPTO_ENCRYPT: {
		size_t out_len = 0;
		ret = crypto_encrypt(ctx->tfm, k_input, cd.input_len,
				     k_output, &out_len);
		if (ret == 0) {
			cd.output_len = out_len;
			if (copy_to_user(cd.output, k_output, out_len)) {
				ret = -EFAULT;
			} else if (copy_to_user((void __user *)arg, &cd,
						sizeof(cd))) {
				ret = -EFAULT;
			}
		}
		break;
	}
	case CRYPTO_DECRYPT: {
		size_t out_len = 0;
		ret = crypto_decrypt(ctx->tfm, k_input, cd.input_len,
				     k_output, &out_len);
		if (ret == 0) {
			cd.output_len = out_len;
			if (copy_to_user(cd.output, k_output, out_len)) {
				ret = -EFAULT;
			} else if (copy_to_user((void __user *)arg, &cd,
						sizeof(cd))) {
				ret = -EFAULT;
			}
		}
		break;
	}
	default:
		ret = -ENOTTY;
		break;
	}

	kfree(k_output);
	kfree(k_input);
	return ret;
}

/* ---- Module Init / Exit ---- */

static int __init crypto_module_init(void)
{
	int ret;

	ret = alloc_chrdev_region(&dev_num, 0, 1, DEVICE_NAME);
	if (ret < 0) {
		pr_err("crypto_kernel: failed to alloc chrdev region: %d\n",
		       ret);
		return ret;
	}

	major = MAJOR(dev_num);

	cdev_init(&crypto_cdev, &crypto_fops);
	crypto_cdev.owner = THIS_MODULE;

	ret = cdev_add(&crypto_cdev, dev_num, 1);
	if (ret < 0) {
		pr_err("crypto_kernel: failed to add cdev: %d\n", ret);
		unregister_chrdev_region(dev_num, 1);
		return ret;
	}

	crypto_class = class_create(CLASS_NAME);
	if (IS_ERR(crypto_class)) {
		ret = PTR_ERR(crypto_class);
		pr_err("crypto_kernel: failed to create class: %d\n", ret);
		cdev_del(&crypto_cdev);
		unregister_chrdev_region(dev_num, 1);
		return ret;
	}

	crypto_device = device_create(crypto_class, NULL, dev_num, NULL,
				      DEVICE_NAME);
	if (IS_ERR(crypto_device)) {
		ret = PTR_ERR(crypto_device);
		pr_err("crypto_kernel: failed to create device: %d\n", ret);
		class_destroy(crypto_class);
		cdev_del(&crypto_cdev);
		unregister_chrdev_region(dev_num, 1);
		return ret;
	}

	pr_info("crypto_kernel: loaded (major=%d), device /dev/%s\n",
		major, DEVICE_NAME);
	return 0;
}

static void __exit crypto_module_exit(void)
{
	device_destroy(crypto_class, dev_num);
	class_destroy(crypto_class);
	cdev_del(&crypto_cdev);
	unregister_chrdev_region(dev_num, 1);

	pr_info("crypto_kernel: unloaded\n");
}

module_init(crypto_module_init);
module_exit(crypto_module_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Linux Kernel Developer");
MODULE_DESCRIPTION("AES-256-CBC encryption/decryption via Linux Crypto API");
MODULE_VERSION("1.0");
