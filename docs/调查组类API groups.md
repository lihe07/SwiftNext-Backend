# 调查组类API groups



## GET /groups/check_invitation/{code}

> 检查某个邀请是否有效
>
> - 权限：>0

成功响应：200

```json
{
  "group": {
    ...
  }
}
```



失败响应：404

## POST /groups/invitation

> 创建入组邀请
>
> - 权限：1, 2

请求报文：

```json
{
  "group_id": ...,
  "expire_at": ...
}
```

## GET /groups/manageable

> 获取可管理的小组
>
> - 权限：2，2