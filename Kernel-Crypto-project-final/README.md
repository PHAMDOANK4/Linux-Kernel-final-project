# Kernel Crypto Project

Hệ thống mã hóa AES-256-CBC sử dụng Linux Kernel Module kết hợp Linux Crypto API.

## Kiến trúc hệ thống

```
User Application (crypto_client)
        |
        | ioctl()
        v
Character Device (/dev/crypto_kernel)
        |
        | Linux Crypto API (skcipher)
        v
   AES-256-CBC
        |
   Linux Kernel
```

## Cấu trúc source code

```
.
├── crypto_ioctl.h       # Header chung (kernel + user-space)
├── crypto_kernel.c      # Kernel module
├── crypto_client.c      # User-space test program
├── Makefile             # Build script
└── README.md            # Tài liệu dự án
```

## Yêu cầu hệ thống

- Ubuntu Server 24.04 (hoặc bất kỳ distro nào với kernel 6.x)
- Linux kernel headers (`linux-headers-$(uname -r)`)
- GCC, GNU Make
- Quyền root (để insmod/rmmod module)

### Cài đặt kernel headers

```bash
sudo apt update
sudo apt install linux-headers-$(uname -r) build-essential
```

## Build

```bash
make clean && make
```

Lệnh trên sẽ build đồng thời:
- `crypto_kernel.ko` — kernel module
- `crypto_client` — user-space program

## Cách sử dụng

### 1. Nạp kernel module

```bash
sudo insmod crypto_kernel.ko
```

Sau khi nạp, kernel tự động tạo device node `/dev/crypto_kernel`.
Kiểm tra:

```bash
ls -l /dev/crypto_kernel
lsmod | grep crypto_kernel
```

Phân quyền cho user thường (tùy chọn):

```bash
sudo chmod 666 /dev/crypto_kernel
```

### 2. Mã hóa dữ liệu

```bash
./crypto_client encrypt "Hello Linux"
```

Output mẫu:

```
Plaintext:  Hello Linux
Ciphertext: 1a2b3c4d5e6f... (dạng hex)
(ciphertext length: 16 bytes)
```

### 3. Giải mã dữ liệu

```bash
./crypto_client decrypt 1a2b3c4d5e6f...
```

Output mẫu:

```
Ciphertext (hex): 1a2b3c4d5e6f...
Decrypted text:   Hello Linux
(decrypted length: 11 bytes)
```

### 4. Gỡ kernel module

```bash
sudo rmmod crypto_kernel
```

### 5. Xem log kernel

```bash
sudo dmesg -w
```

Khi module được nạp/gỡ hoặc có lỗi, kernel sẽ ghi log qua `printk()`, có thể xem bằng `dmesg`.

## Bug fixes

### Fix decrypt returning wrong output_len

**Bug:** `crypto_decrypt()` dùng chung biến `ret` cho cả `crypto_skcipher_decrypt()` và `pkcs7_unpad()`. Khi `pkcs7_unpad` thành công, nó trả về unpadded length (số dương), ghi đè lên `ret`. Hàm `crypto_decrypt()` trả về số dương này thay vì 0, khiến ioctl handler bỏ qua bước cập nhật `cd.output_len` -> user-space nhận `output_len` không đổi (4112).

**Fix:** Dùng biến riêng `unpadded` cho kết quả của `pkcs7_unpad`, đặt `ret = 0` trước khi return.

## Giải thích chi tiết

### Luồng dữ liệu từ user-space sang kernel-space

```
crypto_client (user-space)
  |  open("/dev/crypto_kernel")     -> syscall -> kernel: crypto_open()
  |                                    - cap phat struct crypto_ctx
  |                                    - crypto_alloc_skcipher("cbc(aes)")
  |                                    - crypto_skcipher_setkey(key)
  |                                    - luu ctx -> filp->private_data
  |
  |  ioctl(fd, CRYPTO_ENCRYPT, &cd) -> syscall -> kernel: crypto_ioctl()
  |    |- copy_from_user(&cd, arg)           // copy struct crypto_data
  |    |- memdup_user(cd.input, cd.input_len) // copy input data
  |    |- kmalloc(output_buffer)
  |    |- pkcs7_pad(plaintext)               // PKCS#7 padding
  |    |- sg_init_one(&src_sg, buf, len)
  |    |- sg_init_one(&dst_sg, out, len)
  |    |- skcipher_request_alloc(tfm)
  |    |- crypto_skcipher_encrypt(req)       // AES-256-CBC encrypt
  |    |- copy_to_user(cd.output, out, len)  // copy output ve user
  |    |- copy_to_user(arg, &cd)             // cap nhat output_len
  |
  |  close(fd)               -> syscall -> kernel: crypto_release()
  |                                    - crypto_free_skcipher(tfm)
  |                                    - kfree(ctx)
  v
Kernel Space
```

### Linux Crypto API hoạt động như thế nào

```
                     +---------------------------+
                     | crypto_alloc_skcipher(     |
                     |   "cbc(aes)", 0, 0)        |
                     +-------------+-------------+
                                   |
                  +----------------+----------------+
                  |                |                |
                  v                v                v
            +----------+    +----------+    +----------+
            | Software |    | AES-NI  |    |   ARM    |
            |   AES    |    | (x86_64)|    | Crypto   |
            +----------+    +----------+    +----------+
```

1. **`crypto_alloc_skcipher("cbc(aes)", 0, 0)`**: Kernel tim implementation "cbc(aes)". Neu CPU co AES-NI -> hardware-accelerated, nguoc lai -> software.
2. **`crypto_skcipher_setkey(tfm, key, 32)`**: Set key AES-256. Key duoc key expansion.
3. **Moi lan encrypt/decrypt**: Tao `skcipher_request`, gan scatterlist, goi `crypto_skcipher_encrypt/decrypt()`.

### struct file_operations

```c
static const struct file_operations crypto_fops = {
    .owner          = THIS_MODULE,
    .open           = crypto_open,
    .release        = crypto_release,
    .read           = crypto_read,
    .write          = crypto_write,
    .unlocked_ioctl = crypto_ioctl,
};
```

Moi lan `open()` tao context rieng voi tfm rieng -> isolation giua cac process.

### Co che ioctl()

`_IOWR` tao ma 32-bit gom: type (8), nr (8), direction (2), size (14). Kernel dung `copy_from_user()` doc struct, `copy_to_user()` ghi ket qua.

### copy_from_user() va copy_to_user()

```c
unsigned long copy_from_user(void *to, const void __user *from, unsigned long n);
unsigned long copy_to_user(void __user *to, const void *from, unsigned long n);
```

- Kiem tra con tro user-space hop le
- Xu ly page fault an toan (co the sleep khi swap)
- Return 0 = thanh cong, non-zero = so byte chua copy duoc

### PKCS#7 Padding

AES-CBC yeu cau du lieu la boi so cua 16 bytes. PKCS#7 them N bytes, moi byte = N. Khi giai ma, doc byte cuoi de biet so padding va loai bo.

## Lenh thuong dung

```bash
make                     # Build toan bo
sudo insmod crypto_kernel.ko   # Nap module
sudo chmod 666 /dev/crypto_kernel  # Phan quyen
lsmod | grep crypto_kernel     # Kiem tra
./crypto_client encrypt "test" # Ma hoa
sudo rmmod crypto_kernel       # Go module
make clean                     # Don dep
```

## License

GPL v2
