cd /Volumes/E_disk/Project/MACAU_TOURISM_DESIGN
conda activate WebDesign
python manage.py check
python manage.py migrate
python manage.py runserver 127.0.0.1:8008



cd /Volumes/E_disk/Project/MACAU_TOURISM_DESIGN/frontend
npm run dev


http://127.0.0.1:5173/





## ==============================================



python -m pip install "Django==6.1.3"

python -m django startproject djangovue .
python manage.py startapp backend



cd /Volumes/E_disk/Project/MACAU_TOURISM_DESIGN
npm create vite@latest frontend -- --template vue
cd frontend
npm install


npm install leaflet@1.9.4



cd frontend
npm install leaflet

cd frontend
npm install element-plus


## 推荐数据基础（2026-11-26）

在 `WebDesign` 环境中执行：

```bash
python manage.py migrate
python manage.py seed_interest_tags --dry-run
python manage.py seed_interest_tags
python manage.py test backend
cd frontend
npm test
npm run build
```

`backend/interests.py` 是 15 个推荐兴趣标签的统一词表。`Attraction.tags`
和 `LocalListing.tags` 均为 JSON 字符串列表，后台可用复选框跨类别多选。
注册兴趣使用这套词表并保存到原有 `Profile.interests`；旧用户的兴趣不会
自动改写。旧版 `food` 偏好仍可在后台保留，不推断成某一种具体美食偏好。
景点原有 `Category`、筛选和行程规划的 `PlanForm` 继续使用原来的四类。

`seed_interest_tags` 根据目录已有文字及分类生成可编辑的初始建议，只填
空标签，保留人工标签；含糊的内容留空。它不是推荐算法，也不会创建用户
或行为记录。新目录导入后可再次运行；管理员可以在后台复核和调整标签。

`POST /api/interactions/` 仅接受登录用户主动打开详情的记录：

```json
{"target_type": "attraction", "target_id": 1, "action": "view"}
```

`target_type` 也可为 `listing`。必须使用 JSON、会话登录和 CSRF token，
不接受客户端指定用户、时间或收藏行为。可选的 `impression_id` 必须为
UUID 字符串；当前界面没有推荐曝光系统，因此不会发送该字段。字段仅为
未来曝光关联预留，不能据此把“没有点击”当成“已经看到但不感兴趣”。

前端只在“查看详情”入口上报：列表加载、筛选、地图定位、评论提交后的
自动刷新都不生成浏览记录。匿名浏览不记录；记录失败不会阻断页面，也不
重试或补造历史事件。每次重新主动打开详情可以产生一条新的浏览记录。

收藏/取消收藏由原有收藏接口在实际状态变化时记录 `bookmark` /
`unbookmark`，与收藏增删处于同一事务。重复收藏或取消不会产生重复事件。
`UserInteraction` 由数据库约束保证只关联一个景点或餐饮文创对象，并限制
合法 action；后台仅供查看/删除，不能手工添加或改写事件。

开发测试只在独立测试数据库中生成测试记录。不得把测试或模拟点击混入
正式训练、评估数据；本次没有从已有收藏反向补造历史行为。
