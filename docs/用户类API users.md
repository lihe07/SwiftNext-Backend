# 用户类API /users

该部分API包含对用户的增删改查

### POST /users

> 创建新的用户
>
> 只有管理员和访客可以调用这个api
>
> - 权限：0,3
> - 保护：低

管理员请求报文：

```json
{
  "name": "张三", // 新用户的姓名
  "email": "san@114514.email", // 新用户的邮箱
  "password": "encrypted_password", // 新用户的密码 如果是false则要求新用户自己设置密码
  "group_id": ObjID(123),
  "permission": 1
}
```

管理员成功返回：

```json
{
  "uid": 114514
}
```



访客请求报文：

```json
{
  "code": "", // 邮箱验证码
}
```

访客失败返回：

- 验证码已过期 1001 => 406

```json
{
  "code": 1001,
  ...
}
```

- 邀请已过期 1002 => 406

```json
{
  "code": 1002,
  ...
}
```

访客成功返回：

```json
{
  "uid": "114514", // 成功后的UID
  "inviter": "114514", // 邀请者的ID
  "group_id": false or 114514, // 加入的小组ID
}
```



## POST /users/temp_user

> 创建一个需要验证的用户
>
> - 权限：0
> - 保护：中

请求报文：

```json
{
  "name": "张三", // 用户的姓名
  "email": "san@114514.email", // 用户的邮箱
  "passowrd": "encrypted_password", // 加密后的密码
  "invitation_id": "114514", // 邀请的id
}
```

后端会在inactive_users集合里写入一个新的文档，如果数据库里已经有一个invitation_id相同的文档，将会删除旧的

成功响应：

```json
{
  "expire_at": ISODate(), // 该临时用户过期的时间 
}
```

失败响应：

有无效的字段 1001 => 406

```json
{
  "code": 1001,
  "message": {
    "cn": "XXX无效",
    "en": "Field xxx is invalid"
  },
  "description": {
    "invalid_field": "xxx",
    "reason": "xxx"
  }
}
```

无效的邀请 1002 => 406

```json
{
  "code": 1002,
  "message": {
    "cn": "该邀请不存在或已过期!",
    "en": "This invitation isn't exists or has already expired!"
  },
  "description": {
    "invalid_invitation": "xxx" // 原先的邀请id
  }
}
```

无法发送验证邮箱 1003 => 500

```json
{
  "code": 1003,
  "message": {
    "cn": "服务器无法发送验证邮箱",
    "en": "Failed sending validation email"
  },
}
```

## POST /users/check_email

> 检查某个邮箱是否存在
>
> - 权限：0, 1, 2, 3（不限制）
> - 保护：中

请求报文：

```json
{
  "email": "san@114514.email"
}
```

成功响应报文：

```json
{
  user去掉password
}
```

失败响应报文：

- 不存在：1001 => 404

```json
{
  "code": 1001,
  "message": {
    ...
  },
}
```

## POST /users/register_invitations

> 创建新的注册邀请
>
> - 权限：1, 2, 3

请求报文：

```json
{
  "group_id": 小组ID 或者 false,
  "expire_at": 邀请过期时间 最大20天
}
```

对于权限1，2：检查发起邀请者是否属于该小组

成功响应：

```json
{
  "id": "邀请ID"
}
```

失败响应：

- 邀请发出者不属于该小组 1001 => 403

```json
{
  "code": 1001,
  "message": {
    ...
  }
}
```

- 过期时间不合法 1002 => 406

```json
{
  "code": 1002,
  ...
}
```



## GET /register_invitations/{id}

> 从数据库获取新的注册邀请
>
> 权限：无
>
> 保护：中

## PATCH /users/{id}

> 更新用户信息
>
> 权限：1，2，3
>
> 保护：低

## POST /users/login

> 请求登录

请求报文:

```json
{
  "email": "",
  "password": "e"
}
```

成功响应报文：

```json
{
  ... User的信息
}
```

- 邮箱或密码错误 1001 => 401

```json
{
  ...
}
```

- 被限制的用户 1002 => 410

```json
{
  "code": 1002,
  "message": {
    ...
  },
  "description": {
    "banned_time": ...,
    "reason": ...
  }
}
```

## GET /users/logout

> 登出
>
> - 权限：1, 2, 3

- 成功 204

