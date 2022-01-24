# 识别类API /detector

与系统的识别核心相关的操作

### POST /detector/images

> 提交一个新的识别任务
>
> 最大上传大小：100MB
>
> - 权限：1
> - 保护：高

请求报文：文件内容，mimetype：multipart/form-data

成功响应：202 Accepted

```json
{
  "task_id": 114514, // 本次识别任务的标识符
}
```

失败：

1. 客户端文件问题：415 Unsupported Media Type

   ```json
   {
     "code": 1001,
     "description": "Can't decode image", // 对错误的细节描述
     "message": "无法处理这种格式的文件!"
   }
   ```

2. 文件过大：413 Request Entity Too Large

   ```json
   {
     "code": 1002,
     "description": {
       "max_size": 114514, // 服务器支持的最大大小
       "received": 1919810 // 客户端发送来的
     },
     "message": "上传的内容过大! 支持的最大大小: 100Mb"
   }
   ```

### GET /detector/images/{task_id}

> 获取某一个任务的图片（inline）
>
> - 权限：1
> - 保护：低

成功响应：200 Ok 文件本身

失败响应：404 Not Found 找不到相应任务

### GET /detector/results/{task_id}

> 获取某一个任务的结果
>
> - 权限：1
> - 保护：中

成功响应：

1. 已经处理完毕 200 Ok

```json
{
  "task_id": 114514, // 客户端请求的task_id
  "bboxs": [
    {
      "xmin": 1,
      "ymin": 1,
      "xmax": 4,
      "ymax": 5
    }, // 每一个检测框
  ]
}
```

2. 还没有处理完 202 Accepted

```json
{}
```

失败响应：

1. 找不到这个任务 404 Not Found
2. 任务由于各种原因失败 

