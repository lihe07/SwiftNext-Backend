# 调查点API /positions

## GET /positions/<position_id>

> 获取某个调查点的经纬度信息
>
> - 权限：>0

成功响应：

```json
{
  "longitude": ...,
  "latitude": ...
}
```

## POST /positions

> 创建一个新的调查点
>
> - 权限：2, 3

请求报文：

```json
{
  "group_id": ..., // 调查小组
  "longitude": ..., // 经度
  "latitude": ..., // 纬度
  "name": ... // 为其命名
}
```

## GET /positions/by_group/<group_id>

> 查询这个小组的全部调查点
>
> - 权限：1，2，3

