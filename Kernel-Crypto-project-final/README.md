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
(ciphertext length: 32 bytes)
```

### 3. Giải mã dữ liệu

```bash
./crypto_client decrypt 1a2b3c4d5e6f...
```

Output mẫu:

```
Ciphertext (hex): 1a2b3c4d5e6f...
Decrypted text:   Hello Linux
(decrypted length: 12 bytes)
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

## Giải thích chi tiết

### Luồng dữ liệu từ user-space sang kernel-space

```
crypto_client (user-space)
  │  open("/dev/crypto_kernel")     → syscall → kernel: crypto_open()
  │                                    - cấp phát struct crypto_ctx
  │                                    - crypto_alloc_skcipher("cbc(aes)")
  │                                    - crypto_skcipher_setkey(key)
  │                                    - lưu ctx → filp->private_data
  │
  │  ioctl(fd, CRYPTO_ENCRYPT, &cd) → syscall → kernel: crypto_ioctl()
  │    ├─ copy_from_user(&cd, arg)           // copy struct crypto_data
  │    ├─ memdup_user(cd.input, cd.input_len) // copy input data
  │    ├─ kmalloc(output_buffer)
  │    ├─ pkcs7_pad(plaintext)               // PKCS#7 padding
  │    ├─ sg_init_one(&src_sg, buf, len)
  │    ├─ sg_init_one(&dst_sg, out, len)
  │    ├─ skcipher_request_alloc(tfm)
  │    ├─ crypto_skcipher_encrypt(req)       // AES-256-CBC encrypt
  │    ├─ copy_to_user(cd.output, out, len)  // copy output về user
  │    └─ copy_to_user(arg, &cd)             // cập nhật output_len
  │
  │  close(fd)               → syscall → kernel: crypto_release()
  │                                    - crypto_free_skcipher(tfm)
  │                                    - kfree(ctx)
  v
Kernel Space
```

Dữ liệu được copy **hai lớp**:
1. **Lớp 1** — copy struct `crypto_data` chứa các con trỏ (input, output) từ user-space
2. **Lớp 2** — copy dữ liệu thật mà các con trỏ trỏ tới

Đây là kỹ thuật **double-indirect copy** phổ biến trong device driver khi cần truyền lượng dữ liệu lớn qua ioctl.

### Linux Crypto API hoạt động như thế nào

Linux Crypto API là framework trừu tượng hóa các thuật toán mã hóa trong kernel:

```
                     ┌──────────────────────┐
                     │   crypto_alloc_skcipher("cbc(aes)")  │
                     └──────────┬───────────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ Software │   │ AES-NI  │   │   ARM    │
         │   AES    │   │(x86_64) │   │ Crypto   │
         └──────────┘   └──────────┘   └──────────┘
```

Quy trình:

1. **`crypto_alloc_skcipher("cbc(aes)", 0, 0)`**
   - Kernel tìm implementation "cbc(aes)" trong danh sách crypto đã đăng ký
   - Nếu CPU hỗ trợ AES-NI → dùng hardware-accelerated implementation
   - Nếu không → fallback về software implementation
   - Trả về `struct crypto_skcipher *` (tfm — transform object)

2. **`crypto_skcipher_setkey(tfm, key, 32)`**
   - Set key AES-256 (32 bytes) vào tfm
   - Key được key expansion (mở rộng thành round keys) tùy implementation

3. **Mỗi lần encrypt/decrypt:**
   - Tạo `skcipher_request` bằng `skcipher_request_alloc(tfm)`
   - Gắn scatterlist (SG) — mô tả vùng nhớ vật lý dạng DMA-able
   - Gọi `crypto_skcipher_encrypt(req)` hoặc `crypto_skcipher_decrypt(req)`
   - Với AES-NI, kernel gọi trực tiếp instruction `aesenc` / `aesenclast` / `aesdec` / `aesdeclast`

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

| Hàm | Mục đích |
|-----|----------|
| `open` | Cấp phát `struct crypto_ctx`, tạo tfm, set key, lưu vào `filp->private_data` |
| `release` | Giải phóng tfm và context |
| `read` | (Demo) — đọc dữ liệu từ kernel |
| `write` | (Demo) — ghi dữ liệu xuống kernel |
| `unlocked_ioctl` | Xử lý encrypt/decrypt |

Mỗi lần `open()` tạo một **context riêng** với một **tfm riêng**, đảm bảo isolation giữa các process.

### Cơ chế ioctl()

`ioctl()` là system call cho phép user-space gửi command + data xuống device driver.

```c
// Định nghĩa IOCTL command:
// _IOWR(type, nr, struct_type)
//   IOW = kernel đọc từ user (user write → kernel read)
//   IOR = kernel ghi cho user (user read → kernel write)
#define CRYPTO_ENCRYPT _IOWR(CRYPTO_MAGIC, 1, struct crypto_data)
#define CRYPTO_DECRYPT _IOWR(CRYPTO_MAGIC, 2, struct crypto_data)
```

Cơ chế:
- `_IOWR` tạo mã 32-bit gồm: type (8), nr (8), direction (2), size (14)
- Kernel dùng `copy_from_user()` đọc struct, `copy_to_user()` ghi kết quả
- `unlocked_ioctl` — không có BKL (Big Kernel Lock) — được dùng từ kernel 2.6.36+

**Phân biệt `ioctl` vs `unlocked_ioctl`:**
- `ioctl` (cũ) — có BKL, deprecated, không còn trong kernel 6.x
- `unlocked_ioctl` — không có BKL, là API chuẩn hiện tại

### copy_from_user() và copy_to_user()

```c
unsigned long copy_from_user(void *to, const void __user *from, unsigned long n);
unsigned long copy_to_user(void __user *to, const void *from, unsigned long n);
```

| Đặc điểm | Giải thích |
|----------|------------|
| **Safety** | Kiểm tra con trỏ user-space có hợp lệ không (NULL, out-of-bounds) |
| **Page fault handling** | User-space page có thể bị swapped out — kernel xử lý page fault, sleep, swap in rồi tiếp tục |
| **access_ok()** | Kiểm tra vùng nhớ user có nằm trong segment user không |
| **Return value** | 0 = success, non-zero = số byte chưa copy được |

**Tại sao không dùng `memcpy()` trực tiếp?**
- `memcpy()` không kiểm tra con trỏ user → gây kernel panic nếu địa chỉ không hợp lệ
- `copy_from_user()` / `copy_to_user()` xử lý page fault an toàn, có thể ngủ (sleep) khi cần swap, handle signal nếu cần

**Trong module này:**
```c
// Copy struct crypto_data từ user-space
ret = copy_from_user(&cd, (void __user *)arg, sizeof(cd));
if (ret)
    return -EFAULT;

// Copy input data từ user-space (tự động kmalloc + copy)
k_input = memdup_user(cd.input, cd.input_len);

// Copy output về user-space
if (copy_to_user(cd.output, k_output, out_len))
    ret = -EFAULT;
```

### PKCS#7 Padding

AES-CBC yêu cầu dữ liệu đầu vào là bội số của 16 bytes (AES_BLOCK_SIZE).

```c
// Padding: thêm N bytes, mỗi byte có giá trị N
// input = "Hello" (5 bytes)
// padded: "Hello" + 0x0b 0x0b 0x0b 0x0b 0x0b 0x0b 0x0b 0x0b 0x0b 0x0b 0x0b
//         (padding 11 bytes, value = 11)

// Unpad: đọc byte cuối → biết số padding → loại bỏ
```

### AES-256-CBC (Cipher Block Chaining)

```
Encryption:
  C0 = E_k(P0 ⊕ IV)
  C1 = E_k(P1 ⊕ C0)
  C2 = E_k(P2 ⊕ C1)
  ...

Decryption:
  P0 = D_k(C0) ⊕ IV
  P1 = D_k(C1) ⊕ C0
  P2 = D_k(C2) ⊕ C1
  ...
```

- **Key**: 32 bytes (256-bit)
- **Block size**: 16 bytes (128-bit)
- **IV**: 16 bytes, hardcoded trong module (demo), mỗi file cần IV riêng trong production
- **Mode**: CBC — plaintext được XOR với ciphertext block trước trước khi encrypt → tăng tính bảo mật

## IOCTL reference

```c
struct crypto_data {
    __u8  *input;       // [in]  con trỏ input data (user-space)
    __u32  input_len;   // [in]  độ dài input
    __u8  *output;      // [out] con trỏ output buffer (user-space)
    __u32  output_len;  // [in]  kích thước buffer / [out] độ dài output
};

#define CRYPTO_ENCRYPT  _IOWR('C', 1, struct crypto_data)
#define CRYPTO_DECRYPT  _IOWR('C', 2, struct crypto_data)
```

## Mở rộng

### 1. Thêm key management

Thay thế hardcode key bằng:
- `/sys` entry để set key từ user-space
- Kernel keyring (`keyctl` subsystem)

### 2. Per-file IV

Trong thực tế, mỗi file cần IV riêng (lưu cùng file). Có thể dùng inode number + random salt.

### 3. Kết hợp VFS — mã hóa file thực tế

Các hướng tiếp cận:

| Phương pháp | Mô tả |
|-------------|-------|
| **fscrypt** | Built-in trong ext4/f2fs. Gắn key vào directory. Tự động encrypt/decrypt ở page cache layer. |
| **ecryptfs** | Stacked filesystem. Overlay lên filesystem có sẵn, mã hóa từng file riêng. |
| **dm-crypt (LUKS)** | Block-level encryption. Mã hóa toàn bộ partition. |
| **VFS ioctl hook** | Thêm ioctl vào filesystem driver, gọi trực tiếp crypto API. |

### 4. Zero-copy với DMA

Trong production, có thể dùng DMA buffer để tránh copy dữ liệu nhiều lần.

## Debug

### dmesg

```bash
# Theo dõi log real-time
sudo dmesg -w

# Xem log liên quan đến module
sudo dmesg | grep crypto_kernel
```

### printk levels

Trong code:

```c
pr_info("crypto_kernel: loaded\n");    // KERN_INFO
pr_err("crypto_kernel: error %d\n", ret);  // KERN_ERR
pr_debug("crypto_kernel: opened\n");   // KERN_DEBUG (cần debug=y)
```

### strace

```bash
strace -e openat,ioctl ./crypto_client encrypt "test"
```

## Lệnh thường dùng

```bash
# Build
make

# Nạp module
sudo insmod crypto_kernel.ko

# Kiểm tra
lsmod | grep crypto_kernel
ls -l /dev/crypto_kernel

# Log
sudo dmesg | tail -20

# Gỡ module
sudo rmmod crypto_kernel

# Clean build artifacts
make clean
```

## License

GPL v2
