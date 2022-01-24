# 系统类API /system

一切和系统相关的，工具性的API

### POST /system/encrypt

> 请求服务器用加密密码的方法加密一些明文（不可逆的加密）
>
> - 权限：0
> - 保护：中

请求报文：

```json
{
  "content": "待加密的内容"
}
```

成功返回：

```json
{
  "encrypted": "加密后的内容"
}
```

### GET /system/storage

> 获取服务器的存储状态
>
> - 权限：1
> - 保护：低

成功返回：

```json
{
	"full_capacity": 1919810, // 总存储空间 单位Bytes
  "used_capacity": 114514 // 已使用空间 单位Bytes
}
```

### GET /system/memory

> 获取服务器的内存状态
>
> - 权限：1
> - 保护：低

成功返回：

```json
{
  "total_capacity": 1919810, // 内存大小 单位Bytes
  "used_capacity": 114514 // 已使用的空间 单位Bytes
}
```

### *Socket IO* memory



### GET /system/



