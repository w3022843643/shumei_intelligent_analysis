# 回复 D（杨天瑞）：E 侧当前状态与 12 号交付评估

> 来源：E 仓库 `shumei_intelligent_analysis`
> 版本：`0.4.0`
> 最新提交：`3cef391`
> 测试：`26 passed`，Ruff 通过

---

## 1. E 现在能做什么

不等真实视频和文档，E 这边已经把不依赖外部素材的代码全部写完并测试通过：

- **RAG 问答**：PDF/TXT/MD 解析、切分、TF-IDF 检索、引用返回、证据不足状态
- **知识索引**：支持 JSON 持久化，Worker 可异步建索引
- **视频计数算法**：质心跟踪器 + 虚拟线越线判断 + 左右侧进出方向 + 人工标注 MAE 校验
- **短时预测**：滚动基线、预测区间（lower/upper）、walk-forward 回测
- **包装层**：YOLOv8 检测、OpenVINO 设备查询、视频帧读取，都是延迟加载，不装重型依赖也能导入

统一入口 `intelligent_analysis.service` 已导出 11 个函数，包可以直接 `pip install -e` 安装。

## 2. E 现在不能做什么

以下必须等素材，E 不会编假数据：

- 真实 RAG 问答效果 → 等 C 给授权知识文档
- 真实进出计数 → 等 C 给授权录像 + 入口虚拟线配置
- 计数误差评估 → 等 C 给人工标注样本
- 真实预测 → 等 C 给 `camera_entries` / `camera_exits` 历史序列

## 3. 我检查了 C 的仓库，有两个发现

### 发现一：C 仓库里没有真实素材

C 的 `source_registry.json` 是空数组，仓库内无 PDF、无视频、无标注 CSV。C 自己在交付记录里也写了"真实业务资料未完成"。

但 C 的 **DE 调用契约写得很清楚**：
- 知识：`begin_index` → `write_chunks` → `activate_index_version`
- 视频：`create_analysis` → `begin_analysis` → `write_counts` → `complete_analysis`
- 预测：`save_short_forecast`
- 作业：`jobs.claim_job` 领 `knowledge_index` / `video_analysis`

E 接下来就按这个契约写 Worker 适配层，把算法结果写回 C store。

### 发现二：D 和 C 的包导出函数名对不上

D 的 `app/core/providers.py` 里写的是：

```python
from data_foundation import new_auth_store
```

但 C 仓库的 `04-DE调用契约.md` 和代码实际导出的是：

```python
from data_foundation import create_store
```

这个不一致会导致 D worker 启动时导入 C 包直接报错。需要你们确认：
- 要么 D 侧改成 `create_store`
- 要么 C 补一个 `new_auth_store()` 别名

## 4. 12 号交付评估

| 交付项 | E 侧状态 | 12 号能否交付 |
|---|---|---|
| 可安装的空壳包 | ✅ 已完成 | ✅ |
| 稳定函数签名 | ✅ 已对齐 D Schema | ✅ |
| RAG 文档流水线 | ✅ PDF/TXT/MD 已支持 | ✅ |
| 视频计数算法框架 | ✅ 跟踪+越线+方向+校验 | ✅ |
| 短时预测基线+回测 | ✅ 已完成 | ✅ |
| Worker 对接 C store | 🔄 正在写 | ✅ 12 号前能写完 |
| 真实文档问答 | ⏳ 等 C 文档 | ❌ 取决于 C |
| 真实视频计数 | ⏳ 等 C 视频+标注 | ❌ 取决于 C |
| 真实预测结果 | ⏳ 等 C 历史计数 | ❌ 取决于 C |

**结论：E 侧代码和接口部分 12 号能交，真实结果取决于 C 什么时候给素材。**

如果 C 12 号前能给一份知识文档 + 一个样例视频 + 入口配置，E 可以当天串出端到端 demo。如果素材不到，E 交的是算法框架 + 测试 + 契约，不编造真实客流数字。

## 5. E 接下来做什么

1. 按 C 的 DE 契约写 Worker 适配层（领作业 → 解析/计数 → 写回 C store）
2. 等 D 确认函数签名和路由映射
3. 等 C 给素材后接真实数据

---

**E 仓库地址：** https://github.com/w3022843643/shumei_intelligent_analysis
**服务契约：** 仓库内 `E_SERVICE_CONTRACT.md`
**需求清单：** 仓库内 `E部分接口与数据需求确认清单.md`
