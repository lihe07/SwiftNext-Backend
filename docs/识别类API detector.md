# 识别类API /detector

与系统的识别核心相关的操作

## POST /detector/task

> 新任务
>
> - 权限：1, 2, 3

请求报文：

```json
{
  "attachment_id": ..., // 附件的ID
}
```



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

