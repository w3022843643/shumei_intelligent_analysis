# 队长 P2PNet 测试包接收说明

日期：2026-10-15。输入是用户提供的`简单测试.zip`及单独的`testGPU_count.py`。原始源码、权重和录像隔离放在E的`artifacts/leader-p2pnet-original`，没有上传原视频/权重/第三方源码或修改队长原件。上游提交及训练来源未独立核验，不能直接称为已核验官方发布包。

## 包内实际内容及口径

| 文件 | 作用 |
|---|---|
| models/、util/ | P2PNet结构：vgg16_bn、row=2、line=2，输出人头点和分类置信度 |
| SHTechA.pth | 提供的模型权重，严格加载checkpoint.model；文件名不代替训练来源证明 |
| mytest.mp4 | 测试录像，1254×704、30fps、562帧，标称18.733秒；真实录制绝对时间未提供 |
| testGPU.py | 每帧置信度>0.5的人头点计数和窗口显示，自动选择CUDA/CPU |
| 单独testGPU_count.py | 在P2P点上加速度预测、匈牙利匹配和左右两条有向线，每条轨迹每条线最多累计一次 |

新契约要求固定ROI的估计可见人数。计数对照可以使用P2P点在ROI内的数量；Left/Right是累计越线量，不能变成camera_visible_people，也不能累计逐帧人数得到人次。脚本中的线位置、匹配45像素门限和半秒漏检容忍是该演示的配置，尚无项目标注证明其跟踪/越线精度。

## 本机实际试跑

已审核推理调用链，跳过ZIP内Python3.11编译缓存；保持提供源码不变，以weights_only=True、CPU、strict=True加载权重，使用E的实验P2PNetAdapter无窗口读取第0、281、561帧。实际估计为31、41、31，约1.6—1.8秒/帧（不含模型初始化，未预热，耗时仅代表本次机器）。报告见 [Leader-P2PNet-smoke.json](acceptance/Leader-P2PNet-smoke.json)。

运行环境Python3.13.13、torch2.14.1+cpu、torchvision0.29.1+cpu，补装了提供需求中的scipy1.16.1；其余实际依赖版本写入报告。没有整体降级到ZIP固定的torch2.8.0/torchvision0.23.0环境，因此不声称已复现其精确依赖组合。当前CUDA不可用，仅完成CPU试跑。

E适配器使用PIL LANCZOS缩放，原演示使用cv2默认INTER_LINEAR；本次31/41/31属于E适配器、全画面ROI、置信度>0.5结果，不是原GUI脚本逐帧输出一致性的证明。人工标签未提供，MAE为空；短片没有完整5分钟窗，不能凑预测历史。图像所有权及正式展示/发布范围仍需团队明确，本次仅做用户提供材料的本地试跑。

## 摘要与复现

- ZIP SHA256：`2981dc75e337a53fddf66307550dd86cceb738839f861133b8f52b31876790cc`
- SHTechA.pth SHA256：`506047732b128ff09efef18e94bfacbe35fcfef300e5e9eeeece259b0488c63f`
- mytest.mp4 SHA256：`a0e8a2b4bd0a0b5e7b56c1cffe552415d0ace6e2550238d81b30ace1f4ecbf3a`

隔离目录内E-receipt.json保留原始成员及单独越线脚本摘要；无窗口脚本会先复核全部成员。该实验工具另需torchvision和scipy；它们不属于E核心包的必装依赖。已经准备好该目录及上述实测依赖的本机可运行：

```powershell
python -X utf8 demo/check_leader_p2pnet.py
```

给统一同帧评测入口的构建器现为`demo.leader_p2p_factory:build`；将原模型目录加入PYTHONPATH即可。原AnchorPoints根据全局cuda.is_available而不是输入tensor.device选择设备，所以该未改动CPU构建器在CUDA可用主机明确拒绝；GPU接入及CPU/GPU混用需要另行验证，不能据本次CPU结果直接开放GPU正式配置。

```powershell
$env:PYTHONPATH=(Resolve-Path ./artifacts/leader-p2pnet-original).Path
python demo/benchmark_frames.py --manifest ./artifacts/evaluation/manifest.json --output ./artifacts/evaluation/leader-paired.json --p2p-factory demo.leader_p2p_factory:build --p2p-weights ./artifacts/leader-p2pnet-original/SHTechA.pth --p2p-sha256 506047732b128ff09efef18e94bfacbe35fcfef300e5e9eeeece259b0488c63f --p2p-version leader-SHTechA-50604773 --p2p-source-revision team-zip-2981dc75
```

team-zip摘要是收到材料的内容标识，不是上游Git提交。上面的命令仍要求真实复核标签及授权声明，不能把三个模型估计值当人工真值。下一步从这段视频按冻结ROI抽帧、双人标注，并与DM-Count使用同样本比较MAE；正式接口继续保持dm_count，模型选择待评测证据后再决定。
