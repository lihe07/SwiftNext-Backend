# 项目类API /projects

关于系统全局项目的配置，只有管理员动的了

### POST /projects

> 新建一个调查项目
>
> 权限：3

请求报文：

```json
{
  "title": ..., // 项目的标题
  "start_week": (年, 月, 第几周), // 比如 2022年3月第一周: 2022, 3, 1
	"duration": 周数, // 项目持续多少周
  "running": true/false // 是否一并设为当前运行的项目
}
```

成功响应：

```json
{
  "id": ... // 新项目的id
}
```

### POST /projects/{pid}/set_running

> 设置某个项目的活性
>
> 权限：3

请求报文：

```json
{
  "running": true/false // 设置为?
}
```

成功响应：

```json
[
  // 与GET /project/ 一样的响应
]
```

## PATCH /projects/{pid}

> 修改某个项目的信息
>
> 权限：3

请求报文：

```json
{
  "title": ... // 新的title
}
```

响应报文：

```json
{
  "id": ..., // 这个proj的新信息
  ...
}
```



## GET /projects/

> 获取全部项目的状态
>
> 权限：无

成功响应：

```json
[
  全部projects
]
```

