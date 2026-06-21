#include <linux/module.h>
#include <linux/export-internal.h>
#include <linux/compiler.h>

MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};



static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x0c92f06e, "cdev_del" },
	{ 0x0bc5fb0d, "unregister_chrdev_region" },
	{ 0xfd4b4a36, "class_destroy" },
	{ 0x23f25c0a, "__dynamic_pr_debug" },
	{ 0x30a11079, "device_destroy" },
	{ 0xd0632e1b, "crypto_destroy_tfm" },
	{ 0xcb8b6ec6, "kfree" },
	{ 0xbd03ed67, "__ref_stack_chk_guard" },
	{ 0xd710adbf, "__kmalloc_noprof" },
	{ 0xa53f4e29, "memcpy" },
	{ 0x386e4ba3, "kmemdup_noprof" },
	{ 0x66526f72, "sg_init_one" },
	{ 0xc2f4e68e, "crypto_skcipher_encrypt" },
	{ 0xf8faa012, "kfree_sensitive" },
	{ 0xd272d446, "__stack_chk_fail" },
	{ 0xbd03ed67, "random_kmalloc_seed" },
	{ 0x08bfc903, "kmalloc_caches" },
	{ 0xecd17989, "__kmalloc_cache_noprof" },
	{ 0x281aa90f, "crypto_alloc_skcipher" },
	{ 0x07dd2c9a, "crypto_skcipher_setkey" },
	{ 0xc2f4e68e, "crypto_skcipher_decrypt" },
	{ 0xe54e0a6b, "__fortify_panic" },
	{ 0x092a35a2, "_copy_from_user" },
	{ 0x334e7b26, "memdup_user" },
	{ 0x546c19d9, "validate_usercopy_range" },
	{ 0xa61fd7aa, "__check_object_size" },
	{ 0x092a35a2, "_copy_to_user" },
	{ 0xf64ac983, "__copy_overflow" },
	{ 0xd272d446, "__fentry__" },
	{ 0x9f222e1e, "alloc_chrdev_region" },
	{ 0x4c075f7d, "cdev_init" },
	{ 0x6459621a, "cdev_add" },
	{ 0xb6c08e4c, "class_create" },
	{ 0xf350d701, "device_create" },
	{ 0xe8213e80, "_printk" },
	{ 0xd272d446, "__x86_return_thunk" },
	{ 0x814e12e5, "module_layout" },
};

static const u32 ____version_ext_crcs[]
__used __section("__version_ext_crcs") = {
	0x0c92f06e,
	0x0bc5fb0d,
	0xfd4b4a36,
	0x23f25c0a,
	0x30a11079,
	0xd0632e1b,
	0xcb8b6ec6,
	0xbd03ed67,
	0xd710adbf,
	0xa53f4e29,
	0x386e4ba3,
	0x66526f72,
	0xc2f4e68e,
	0xf8faa012,
	0xd272d446,
	0xbd03ed67,
	0x08bfc903,
	0xecd17989,
	0x281aa90f,
	0x07dd2c9a,
	0xc2f4e68e,
	0xe54e0a6b,
	0x092a35a2,
	0x334e7b26,
	0x546c19d9,
	0xa61fd7aa,
	0x092a35a2,
	0xf64ac983,
	0xd272d446,
	0x9f222e1e,
	0x4c075f7d,
	0x6459621a,
	0xb6c08e4c,
	0xf350d701,
	0xe8213e80,
	0xd272d446,
	0x814e12e5,
};
static const char ____version_ext_names[]
__used __section("__version_ext_names") =
	"cdev_del\0"
	"unregister_chrdev_region\0"
	"class_destroy\0"
	"__dynamic_pr_debug\0"
	"device_destroy\0"
	"crypto_destroy_tfm\0"
	"kfree\0"
	"__ref_stack_chk_guard\0"
	"__kmalloc_noprof\0"
	"memcpy\0"
	"kmemdup_noprof\0"
	"sg_init_one\0"
	"crypto_skcipher_encrypt\0"
	"kfree_sensitive\0"
	"__stack_chk_fail\0"
	"random_kmalloc_seed\0"
	"kmalloc_caches\0"
	"__kmalloc_cache_noprof\0"
	"crypto_alloc_skcipher\0"
	"crypto_skcipher_setkey\0"
	"crypto_skcipher_decrypt\0"
	"__fortify_panic\0"
	"_copy_from_user\0"
	"memdup_user\0"
	"validate_usercopy_range\0"
	"__check_object_size\0"
	"_copy_to_user\0"
	"__copy_overflow\0"
	"__fentry__\0"
	"alloc_chrdev_region\0"
	"cdev_init\0"
	"cdev_add\0"
	"class_create\0"
	"device_create\0"
	"_printk\0"
	"__x86_return_thunk\0"
	"module_layout\0"
;

MODULE_INFO(depends, "");


MODULE_INFO(srcversion, "C8E2AE6AB916A0E8D6C69E6");
