# 填报类API /records

~~重头戏~~，系统的核心APIs

## GET /records/user/<uid>

> 获取某个用户的全部填报
>
> - 权限：>0

成功响应：

```json
[
  {
    ...
  }
]
```

## POST /records

> 新建填报
>
> - 权限：>0

## GET /records ? uid = * & from = * & to = * & project = * & group = *

> 选取符合条件的record
