# E 0.6.0：正式采用 P2PNet 与 D/B 执行单

日期：2026-10-15。根据用户明确确认，正式算法改为队长提供的P2PNet，停止DM-Count/P2PNet比较。人工标注后只需核验P2PNet自身误差；选择算法不等于准确率已验收。

## 新版契约与运行配置

| 内容 | 0.6.0值 |
|---|---|
| count_model | p2pnet；正式服务拒绝dm_count |
| weights_version | leader-SHTechA-50604773 |
| weights SHA256 | 506047732b128ff09efef18e94bfacbe35fcfef300e5e9eeeece259b0488c63f |
| model_source_revision | team-zip-2981dc75，收到材料的标识；上游提交未独立核验 |
| confidence_threshold | 0.5，保留严格大于关系，不在测试片上调参 |
| 已验证运行时 | PyTorch CPU；Python3.13.13、torch2.14.1+cpu、torchvision0.29.1+cpu |
| 计数 | 固定归一化ROI内的有效人头点数，camera_visible_people |
| 抽帧与聚合 | 默认10秒抽帧，完整5分钟窗的有效帧中位数；缺失/不足窗保持质量与空值规则 |

收到的7个模型源码文件及权重由正式P2PNetCounter校验摘要后加载，state_dict严格匹配。初次依赖/权重不匹配不入队；读旧DM分析明确拒绝，不将历史结果换模型名。原跟踪/越线累计不进入新流程。

模型目录包含原ZIP中的models/、util/及SHTechA.pth，保留目录结构和原始字节；不能用未经核验的其他源码目录替代。E只提供加载器，不重新分发收到的第三方源码或模型权重。

提供源码依据全局CUDA可用性选择锚点设备，因此未修改源码的CPU构建器在CUDA可用主机明确拒绝。GPU/OpenVINO等配置待单独实测后开放；不能把CPU试跑当GPU证明。真实推理需安装vision依赖，收到的源码/权重单独放在受信任本地目录，不随E发布包上传。

## D 必须同步的代码位置

依据已核对D `0cefaf3`，本轮未修改D仓库。

1. `app/schemas/videos.py`目前COUNT_MODELS/default仍为dm_count，改为只接受p2pnet；权重默认/枚举改为上述版本，confidence_threshold固定0.5并允许序列化读回。
2. `app/services/e_bindings.py:get_dm_counter`及Worker构造改为P2PNetCounter，从服务端配置的P2PNET_BUNDLE_DIR取得受信任目录；不接受HTTP上传任意Python构建器或源码路径。
3. API与Worker注入同一配置，validate_analysis使用p2p_counter.validate_config，dispatch_analysis_job传入该计数器；禁止继续把DM密度图传给点计数处理器。
4. 完整保留analysis里的p2pnet、权重版本、阈值、ROI、运行时/设备，另存counter.provenance用于审计；原P2P模型点和权重路径不直接暴露HTTP。
5. 旧analysis_id作为历史保留，新增P2P任务及analysis_id后重新计算；不将已存DM结果改名成P2P。新口径持久化与业务库联调仍需D/C完成。

```python
from intelligent_analysis import ServiceBindings, configure_services
from intelligent_analysis.vision.p2p_counter import P2PNetCounter

p2p_counter = P2PNetCounter.from_team_bundle(settings.p2pnet_bundle_dir)
configure_services(ServiceBindings(
    submit_job=submit_committed_job,
    load_counts=load_visible_counts,
    validate_analysis=p2p_counter.validate_config,
    knowledge_snapshot_loader=load_active_knowledge,
))
# D领取/续租/任务恢复后调用：
result = dispatch_analysis_job("video_analysis", payload, counter=p2p_counter)
```

知识库还需沿用此前C正式任务、原子激活+完成及旧租约保护的执行单，0.6.0不会自动修复D桥库事务。D/B同步后再联合发布；仅升级E的wheel会使旧视频请求不兼容。

## B 需要同步的内容

请求与展示模型固定P2PNet，默认权重用上述版本，阈值0.5，CPU/pytorch；去掉DM/P2P对照选择。D公开ROI转换形状沿用既有公共接口，E内部仍为points:[{x,y}]。5分钟中位数可能为1.5，显示保留小数；逐帧数量不能加总成人次。缺样不填零，manual_validation=null显示“未人工评估”；不同模型历史分析分开标识。B/D可参考 [合成结果样例](fixtures/visible-people-demo.json)，样例权重和数据为synthetic，不可作为真实分析提交。

## E 验证与交付入口

- [可安装wheel](../release/shumei_intelligent_analysis-0.6.0-py3-none-any.whl)、[完整ZIP](../release/E-visible-people-0.6.0-2026-10-15.zip)、[SHA回执](../release/E-visible-people-0.6.0-2026-10-15.receipt.json)。旧0.5.0/0.5.1包及原摘要保留。
- [P2P正式计数器CPU实跑](acceptance/P2PNet-CPU-060.json)：提供短片三个实际帧为31、41、31；没有人工真值，绝对录制时间未知、完整5分钟窗为0，不构造真实预测。
- [0.6.0全量测试](acceptance/E060-tests.json)、[实装wheel验证](acceptance/E060-wheel-installed.json)。知识格式与text-parser-0.5.0/keyword-tfidf-0.5.0不变，C真实资料回归继续执行。
- [0.6.0接收C真实资料](acceptance/E060-C020a2-knowledge.json)：独立SQLite的16文档、655片段、重启与失败保护；不代表正式D/C/MySQL接入完成。
- [P2P合成业务样例](fixtures/visible-people-demo.json)：覆盖帧点、5分钟中位数、读取和15/30/60跨度状态；合成数据不提升真实录像预测验收状态。

```powershell
python -m pip install ./release/shumei_intelligent_analysis-0.6.0-py3-none-any.whl
# 源码安装时一次安装vision依赖：python -m pip install -e ".[vision]"
python -X utf8 demo/check_p2pnet.py
python -X utf8 demo/end_to_end_demo.py
```

停止原比较工作流：不再运行prepare_leader_comparison、benchmark_frames或score_leader_comparison作为当前验收。已生成的6张原图仍可用于P2P单模型人工核验，原预测及旧对照证据保持历史。模型选择已确定，无需继续搜集DM比较标签。

真实P2P人工MAE、GPU、C新口径业务持久化、D/B正式视频HTTP及真实预测仍待验收。正式知识联调和旧E051独立桥HTTP记录分别管理，旧桥记录不代表0.6.0视频HTTP通过。
