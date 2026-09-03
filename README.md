# 政策监控看板 · Policy Monitor Dashboard

一个覆盖中国大陆 31 个省级行政区（22 省 + 5 自治区 + 4 直辖市，不含港澳台）的
人力资源 / 税务 / 社保 / 灵活用工 / 合规 政策监控看板。看板为**单文件 HTML**，
内联 vanilla JS 与 SVG 地图，无任何外部 CDN 依赖，可离线打开。

## 功能概览

- 交互式中国省级地图（按风险等级着色，可点击筛选省份）
- 政策法规时间线、分类统计、告警提醒
- 每日自动刷新状态标记（`lastUpdated` / `todayNewCount`），保证每天打开都显示"今日已刷新"

## 目录结构

```
.
├── outputs/
│   ├── policy-monitor-dashboard.html   # 看板主文件（单文件，含数据与渲染逻辑）
│   └── PRD-政策监控看板.md              # 产品需求文档
├── china_map_paths.js                  # 31 省 SVG 边界路径源数据（GeoJSON 转换而来）
├── geojson_to_svg.py                   # 抓取中国 GeoJSON 并转换为 SVG path 数据
├── merge_map.py                        # 将 china_map_paths.js 中的路径合并写回看板 HTML
├── update_timeline.py                  # 更新看板时间线数据
└── README.md
```

## 地图数据处理

1. `geojson_to_svg.py` 从阿里 DataV GeoJSON（备用：longwosion/geojson-map-china）拉取省界，
   按 `x=(lon-73)*10, y=(54-lat)*11.5` 做坐标变换，输出 `china_map_paths.js`。
2. `merge_map.py` 读取 `china_map_paths.js` 与看板 HTML，将省级路径注入 `provGeoJSON`，
   并重写地图渲染逻辑。

地图数据统一维护为 **31 个省级行政区**，与看板中的 `provGeoJSON`、`riskMap` 保持一致。

## 每日自动更新

配套 QoderWork 定时任务「政策监控看板每日更新」，每天检索新发布的官方政策法规并更新看板。
核心约束：**无论当天是否检索到新政策，都会刷新 `lastUpdated` 并写回文件**，确保"今日已刷新"状态。

## 本地打开

直接用浏览器打开 `outputs/policy-monitor-dashboard.html` 即可，无需构建或依赖安装。

## 数据说明

- 仅收录国务院、人社部、财政部、国税总局、各省市人社厅/税务局等官方来源已发布的政策法规
- 省份命名与 `riskMap` 保持一致（如使用「内蒙古」而非「内蒙」）
