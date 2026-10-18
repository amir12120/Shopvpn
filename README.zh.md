[🇬🇧 English](README.md) | [🇮🇷 فارسی](README.fa.md) | [🇷🇺 Русский](README.ru.md) | [🇨🇳 中文](README.zh.md)

<div align="center">

# 🛰️ ShopVPN — 智能 V2Ray 配置销售机器人

**一个自动化的 Telegram V2Ray 销售平台，配备专属小程序、AI 客服助手、Android 管理应用、Web 管理后台、多级代理支持以及多语言界面。**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-MiniApp%20%2B%20Panel-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

</div>

---

## 📚 目录

- [📖 概述](#overview)
- [✨ 功能](#features)
- [🧠 AI 客服助手](#ai-support)
- [💼 Telegram Business](#business)
- [💳 支付网关](#payment-gateways)
- [📲 Telegram 小程序](#miniapp)
- [🖥️ 独立 Web 管理后台](#admin-panel)
- [📱 Android 管理应用](#android-app)
- [🔌 支持的 VPN 面板](#vpn-panels)
- [🖥️ 系统要求](#requirements)
- [🚀 一键自动安装](#auto-install)
- [🛠️ 手动安装](#manual-install)
- [⚙️ 环境变量](#env-vars)
- [🧰 manage.sh](#manage-sh)
- [🗂️ 项目结构](#project-structure)
- [🧪 技术栈](#tech-stack)
- [🆕 新增功能](#new-features)
- [🔎 更多功能](#additional-features)
- [🤝 贡献与许可证](#contributing)

---

<a id="overview"></a>

## 📖 概述

**ShopVPN** 是一个面向生产环境的 Telegram 机器人，用于销售和管理 V2Ray/VPN 配置。它集成了自动开通、多种支付方式、代理管理、AI 客服、Telegram 小程序、独立的 Web 管理后台以及 Android 管理基础设施。

该项目按照真实运营场景设计，具备钱包、推荐奖励、折扣、支持工单、监控、备份、报表、可配置商品以及多机器人代理支持。

### 📢 官方链接

- 📢 **项目：** [@celenorbot](https://t.me/celenorbot)
- 👤 **作者：** [@celenor](https://t.me/celenor)

### ⚡ 快速概览

- 🔑 在支持的 VPN 面板上自动交付配置
- 💳 多种自动支付方式
- 🧠 AI 客服助手
- 🔄 灵活的服务续费
- 🏢 独立与关联两种代理模式
- 🖥️ Telegram 管理端 + Web 管理后台 + Android 管理应用
- 📲 Telegram 小程序商店
- 🌍 服务器地图与面板健康监控
- 🌐 支持轮询（Polling）与 Webhook
- 🚀 反垃圾信息、报表、备份、返现、金币、抽奖、赠品及集成 API

> **详细内容已折叠，点击任意小节即可展开。**

---

<a id="features"></a>

## ✨ 功能

<details>
<summary><strong>🤖 主机器人 — 点击展开</strong></summary>

- 🔑 每位用户独立的配置库存，自动开通
- 🔗 商品与面板直接绑定
- 🔄 按流量/时长自由续费
- 👤 统一的**我的账户**，涵盖已购买、赠送和测试服务
- 🧪 多个可配置的测试套餐
- 🔢 支持多数量购买并自动计算总价
- 💱 自动获取 USD/USDT 汇率，并提供备用汇率
- 💰 内置钱包，支持充值申请与管理员审批
- 🗂️ 商品/分类管理，含定价与库存控制
- 🚫 用户封禁与强制频道加入
- 📊 实时订阅信息及到期/流量提醒
- ⚠️ 低库存提醒管理员
- 📱 以文本 + 二维码形式交付配置
- 🎫 支持工单与实时客服聊天
- 🎨 可自定义主菜单布局、按钮文字和颜色
- 🏷️ 店铺品牌设置
- 🏢 拥有独立数据库的独立代理机器人
- 🌐 轮询或 Webhook 模式
- 💾 基于 SQLite 的持久化状态机
- ⏳ 临时/敏感消息清理
- 📣 频道广告与深链接工具

</details>

<details>
<summary><strong>🤝 代理、推荐、折扣与钱包 — 点击展开</strong></summary>

- 🏢 主机器人内的关联代理模式
- 🤖 独立代理机器人
- 👥 具备多种奖励模型的推荐链接
- 💸 按比例佣金及固定钱包奖励
- 🎁 达到推荐门槛后赠送免费配置
- 🏷️ 带有限制、有效期及商品/分类范围的折扣码
- 🎡 可配置奖品与冷却时间的幸运转盘
- 🪜 代理等级、费用、有效期、提醒及信用额度
- 📦 基于商品的代理供货
- 💰 钱包与返现功能

</details>

<details>
<summary><strong>👑 Telegram 管理面板 — 点击展开</strong></summary>

- 👑 拥有者、管理员、中级管理员与客服角色
- 📢 群发消息
- 📈 带日期筛选的销售统计
- 📝 完整的管理员操作日志
- 🗄️ 每日自动备份至 Telegram
- ♻️ 即时备份与完整数据库恢复
- 📅 支持贾拉利/波斯历
- 👥 用户、商品、分类、支付网关、面板及代理管理
- 🎫 客服工单、报障与系统设置

</details>

<details>
<summary><strong>🚀 增长、安全与监控 — 点击展开</strong></summary>

### 🔐 安全

- 🛡️ 用户反垃圾信息/频率限制
- 🎟️ 高级折扣码限制
- 🔒 清理敏感的付款/卡片信息消息

### 📊 运营

- 🩺 VPN 面板健康监控与恢复提醒
- 📊 每日销售报表
- 📣 基于话题的报表群组
- 🎁 批量赠送流量/时长
- 🧹 自动清理过期服务
- 🔌 基于令牌的集成 API

### 💰 销售与留存

- ⏸️ 首次连接才开始计时的挂起服务
- 📦 按面板设置容量上限
- 📍 服务位置/面板迁移
- 💰 批量修改商品价格并可撤销
- 💸 续费/钱包返现
- 🎁 钱包充值赠送码
- 🪙 金币与定时抽奖
- 🎫 按部门划分的客服工单与故障报告

</details>

---

<a id="ai-support"></a>

## 🧠 AI 客服助手

<details>
<summary><strong>点击展开</strong></summary>

AI 层在升级至人工客服之前，会先回答客户的重复性问题。

- 🔌 可选服务商：Gemini、Groq 或 OpenRouter
- 📚 由管理员维护的常见问题知识库
- 🔎 针对服务、到期时间、钱包和订单的真实、个性化回答
- 🛒 附带实时价格与支付按钮的真实购买卡片
- 🔒 钱包购买/续费和服务变更仅在用户明确确认后通过机器人经过验证的流程执行；退款和投诉交由人工客服
- 🙋 遇到财务投诉或用户明确要求人工时自动升级
- ⚡ 若未配置任何 API 服务商，请求可直接转交人工客服

</details>

---

<a id="business"></a>

## 💼 Telegram Business

<details>
<summary><strong>点击展开</strong></summary>

卖家可以把主机器人连接到自己的 Telegram Business 账号（设置 → Telegram Business → 聊天机器人），之后机器人会在卖家的私聊中代表卖家回复客户。该功能仅限主机器人（不含代理机器人），在管理员开启之前**默认关闭**。

- 🔗 **连接管理** — 按连接保存 `business_connection` 和 `business_message` 更新（所有者、回复/读取权限、启用/停用）；连接启用或断开时会通知管理员
- 🤖 **AI 自动回复** — 通过 AI 客服助手基于真实数据回复客户消息；此处仅提供只读工具：价格与商品、支付方式、服务状态、服务器国家、服务历史和免费测试配置
- 🔒 **商务聊天中不执行任何财务操作** — 钱包购买、续费和服务变更均被禁用；此类请求会转交卖家
- 🛡 **安全过滤** — 机器人会忽略卖家本人、管理员、其他机器人和已封禁用户的消息；防垃圾和全局机器人开关同样适用于此通道；非文本消息会被忽略
- 🤝 **转人工** — 助手升级后会在该聊天中保持静默，卖家会在主机器人收到包含最近消息的通知，以及“打开聊天”和“恢复自动模式”按钮
- ✏️ **编辑/删除追踪** — 已转人工聊天中客户的编辑和删除会通知卖家（可关闭）；消息日志几天后自动清理
- ✅ **标记已读** — 可选；需要账号所有者授予 `can_read_messages` 权限
- 🛒 **购买卡片（可选，默认关闭）** — 客户想购买时，机器人发送商品卡片（名称、价格、流量、时长、说明），并附带一个链接按钮，打开机器人并定位到该商品。支付和交付始终在机器人内完成，商务聊天中不进行任何支付
- ⚙️ **管理面板** — **管理员与权限 → 💼 Telegram Business**：总开关、标记已读、编辑/删除通知、购买卡片开关、活跃连接列表、每个连接的自动回复开关、首条消息（每个新聊天开始时发送一次）、客户 ID 例外列表以及已转人工的聊天列表

> 商务聊天中有意不使用内联 callback 按钮，而是使用 URL 按钮，因为商务聊天中的 callback 投递尚未得到验证。

</details>

---

<a id="payment-gateways"></a>

## 💳 支付网关

<details>
<summary><strong>支持的支付方式 — 点击展开</strong></summary>

| 方式 | 确认方式 | 备注 |
|---|---|---|
| 💳 人工卡对卡转账 | 管理员 | 凭收据/截图流程 |
| 📲 银行短信卡对卡 | 自动 | 唯一账单金额与轮换卡号 |
| 🏧 Aban 网关 | 自动 | 基于 API 的账单与验证 |
| 💎 Plisio | 自动 | 加密货币，含回调/签名验证 |
| 🔵 Blupal | 自动 | 自动化卡对卡转账 |
| ⭐ NoaPay / Telegram Stars | 自动 | Telegram Stars |
| 🟡 ZarinPal | 自动 | 主机器人 |
| 🔵 Mr. Pardakht | 自动 | 主机器人 |
| 💸 Tetra98 | 自动 | 主机器人 |
| 💳 CubePay | 自动 | 主机器人 |
| 💰 NowPayments | 自动 | 加密货币账单 + IPN |
| ⭐ Telegram Stars | 自动 | 原生 `XTR` 发票 |
| 🧩 通用网关 | 自动 | 无需编写代码即可配置 HTTP API |

所有网关相互独立，可单独启用或禁用。

</details>

---

<a id="miniapp"></a>

## 📲 Telegram 小程序

<details>
<summary><strong>点击展开</strong></summary>

`miniapp/` 目录包含一个完整的 Telegram 小程序，既有客户端商店，也有 Web 管理端。

### 🛍️ 客户端

- ⚡ 基于 FastAPI 的后端，安全验证 Telegram `initData`
- 🎨 响应式商店界面
- 🛒 商品、购物车、钱包、幸运转盘、推荐及测试配置
- 🔔 到期与流量提醒
- 📲 通过深链接将订阅添加到主流 VPN 应用
- 🎫 支持工单与实时客服聊天
- 🌐 语言切换，自动适配 RTL/LTR 方向

### 🛠️ Web 管理端

- 📊 仪表盘与订单导出
- 🗂️ 分类、商品、面板及配置管理
- 🏢 代理管理
- 🏷️ 折扣、幸运转盘、推荐及提醒
- 👥 用户搜索、封禁及定向群发
- 💰 钱包查询与余额调整
- 🎨 品牌与主题自定义
- 🧩 Telegram 主菜单布局管理
- 🎫 工单/客服管理
- 📝 系统与管理员日志
- 🗄️ 备份与数据库恢复

</details>

---

<a id="admin-panel"></a>

## 🖥️ 独立 Web 管理后台

<details>
<summary><strong>点击展开</strong></summary>

`admin_panel/` 软件包提供一个独立于 Telegram 的 Web 管理后台。

- 🔐 用户名/密码登录，独立会话
- 👥 独立的 Web 管理员角色与权限
- 📊 销售、订单、钱包及系统仪表盘
- 🎨 多种视觉主题
- 📱 可在移动端安装为 PWA
- 🌍 全球服务器地图与健康检查
- 💱 汇率管理
- ✅ 订单、钱包及支付审批
- 🏢 代理管理与数据分析
- 🎫 支持工单与对话
- 📢 群发消息
- 🗄️ 备份与恢复
- 🔔 Web 推送通知
- 📱 Android 应用令牌管理
- 📝 Web 管理员操作日志
- 🌐 多语言界面，自动 RTL/LTR

### 快速设置

**自动方式：** 在 `manage.sh` 中选择对应的 Web 面板选项。

**手动方式：**

```bash
python -m admin_panel.create_admin <username> <password>
uvicorn admin_panel.server:app --host 127.0.0.1 --port 8002
```

</details>

---

<a id="android-app"></a>

## 📱 Android 管理应用

<details>
<summary><strong>点击展开</strong></summary>

后端为原生 Android 管理应用提供了基础设施。

- 🔑 安全的长期管理员令牌（PAT）
- 🧩 服务端驱动 UI（Server-Driven UI）
- 🔔 通过 Firebase Cloud Messaging（FCM）推送通知
- 📋 订单、工单、用户、商品、折扣、VPN 面板及 Web 管理员
- 🌍 通过 WebView 展示服务器地图
- 🎨 明暗双主题界面
- 🔕 按板块设置通知开关

</details>

---

<a id="vpn-panels"></a>

## 🔌 支持的 VPN 面板

<details>
<summary><strong>点击展开</strong></summary>

| 面板 | 状态 | 备注 |
|---|---|---|
| PasarGuard | ✅ 完全支持 | 自动开通 |
| Marzban | ✅ 完全支持 | 自动开通 |
| Marzneshin | ✅ 完全支持 | 基于服务的开通方式 |
| Hiddify | ✅ 完全支持 | 基于 API 密钥 |
| 3X-UI | ✅ 完全支持 | Bearer API 令牌 |
| Alireza X-UI | ✅ 完全支持 | 基于 Cookie 登录 |
| Rebecca | ✅ 完全支持 | 基于 Marzban 的提供方 |
| S-UI | ✅ 完全支持 | 基于令牌的 API |
| WGDashboard | ✅ 完全支持 | 基于配置文件 |
| MikroTik / User Manager | ⚠️ 有限支持 | 基于配置档案 |
| IBSng | ⚠️ 有限支持 | 通过管理面板集成 |
| 其他面板 | ➕ 可扩展 | 可自行添加提供方 |

</details>

---

<a id="requirements"></a>

## 🖥️ 系统要求

- 🐧 推荐 Ubuntu 20.04+ / Debian 11+
- 🐍 Python 3.10+
- 🖥️ 具有稳定公网 IP 的 Linux VPS/服务器
- 🤖 Telegram 机器人令牌
- 🌐 面向小程序/Web 面板/Webhook 功能的公网 HTTPS 域名
- 🔑 已启用的支付/VPN 服务商的 API 凭证

> 🔒 切勿公开机器人令牌、`.env` 文件、API 密钥或生产环境的任何密钥。

---

<a id="auto-install"></a>

## 🚀 一键自动安装

> 🌿 这是个人分支 `amir12120/Shopvpn`。安装器轻量：默认不安装庞大的 LibreTranslate，也不保留 pip 缓存。完整指南：[`INSTALL.md`](INSTALL.md)（英文）或 [`INSTALL.fa.md`](INSTALL.fa.md)（波斯文）。

**在全新的 Ubuntu/Debian 服务器上，只需一条命令。** 它会安装所有缺失的依赖、安装或更新机器人、添加 `shopvpn` 命令，并在安装完成后**自动打开管理菜单**：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/amir12120/Shopvpn/main/install.sh)
```

安装后，输入 `shopvpn` 可随时打开同一个管理菜单：

```bash
shopvpn
```

> 🧪 所有安装步骤均以英文显示。

<details>
<summary><strong>安装脚本做了什么？</strong></summary>

1. 安装系统依赖
2. 克隆或更新项目
3. 创建 Python 虚拟环境
4. 安装所需软件包
5. 自动安装/更新本地翻译引擎与语言模型
6. 创建/配置 `.env`
7. 创建 systemd 服务
8. 启动机器人，并确保服务器重启后自动继续运行
9. 安装 `shopvpn` 命令并打开管理菜单

### 常用服务命令

```bash
sudo systemctl status v2raybot
sudo journalctl -u v2raybot -f
sudo systemctl restart v2raybot
sudo systemctl stop v2raybot
```

以后升级时，可再次运行同一条一键安装命令。

</details>

---

<a id="manual-install"></a>

## 🛠️ 手动安装

<details>
<summary><strong>点击展开</strong></summary>

### 1. 克隆项目

```bash
git clone https://github.com/mehdirafatpanah/Shopvpn.git
cd Shopvpn
```

### 2. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置 `.env`

```bash
cp .env.example .env
nano .env
```

最基本配置：

```env
BOT_TOKEN=your_bot_token
OWNER_ID=your_numeric_telegram_id
```

### 4. 启动

```bash
python main.py
```

生产环境请使用自动安装脚本/systemd，或其他进程管理工具。

</details>

---

<a id="env-vars"></a>

## ⚙️ 环境变量

<details>
<summary><strong>点击展开</strong></summary>

具体所需变量取决于已启用的功能。常见配置区域包括：

| 类别 | 示例 |
|---|---|
| Telegram | `BOT_TOKEN`、`OWNER_ID` |
| 数据库 | 数据库/存储路径 |
| Web | 域名、身份验证、Webhook 设置 |
| 支付 | 网关 API 密钥 |
| VPN 面板 | URL、凭证、令牌、ID |
| AI | 服务商 API 密钥 |
| 备份 | 目标地址与 SFTP 凭证 |
| Android | FCM 凭证 |

请将生产环境的密钥保存在代码仓库之外。

</details>

---

<a id="manage-sh"></a>

## 🧰 `manage.sh`

<details>
<summary><strong>点击展开</strong></summary>

`manage.sh` 是主要的安装与维护助手脚本。

根据项目版本不同，它可以处理：

- 🚀 安装与依赖设置
- ⚙️ 环境/配置管理
- ▶️ 启动/停止/重启
- 📲 小程序与 Web 面板设置
- 🗄️ 备份/恢复
- 🔌 VPN 面板设置
- 📋 日志与诊断
- 🔗 集成 API 设置
- 🌐 多语言管理菜单
- 🌐 本地翻译运行环境的安装/修复与不需要语言的清理
- 🏭 完整清理 / 恢复出厂设置

安装后只需输入 `shopvpn`：

```bash
shopvpn
```

或直接从仓库运行（无需安装）：

```bash
chmod +x manage.sh
./manage.sh
```

> 脚本本身是当前菜单选项的权威来源。

</details>

---

<a id="project-structure"></a>

## 🗂️ 项目结构

<details>
<summary><strong>点击展开</strong></summary>

```text
Shopvpn/
├── server.py
├── bot_manager.py
├── handlers_admin.py
├── payment_*.py
├── ai_support.py
├── business_chat.py
├── db/
├── miniapp/
│   ├── server.py
│   └── static/
├── admin_panel/
│   ├── server.py
│   └── static/
├── manage.sh
├── requirements*.txt
├── VERSION
├── README.md
└── README.fa.md
```

</details>

---

<a id="tech-stack"></a>

## 🧪 技术栈

<details>
<summary><strong>点击展开</strong></summary>

- **Python 3.10+**
- **aiogram 3.x**
- **FastAPI**
- **SQLite**
- **HTML/CSS/JavaScript**
- **Telegram 小程序 / WebApp 身份验证**
- **Firebase Cloud Messaging**
- **面向 VPN 面板、支付及 AI 服务商的 HTTP/API 集成**

</details>

---

<a id="new-features"></a>

## 🆕 新增功能

<details>
<summary><strong>点击展开</strong></summary>

### 🧾 AI 假/重复回单检测

手动银行卡转账的回单在到达管理员聊天前会先被检查。大多数发现仅作为提示，最终决定权在管理员。

- 🔁 通过文件 SHA-256 哈希与回单流水号检测完全重复，并用感知哈希 (dHash) 发现重新压缩或裁剪后的复用（仅警告）
- 🤖 多模型视觉分析：Gemini，配置密钥后 Groq 与 OpenRouter 并行运行
- 🔢 确定性 OCR 校验：卡号 (Luhn + 伊朗银行前缀)、IBAN 校验和、以土曼或里亚尔核对金额、流水号重复使用
- 🕵️ 取证分析：JPEG 误差级别分析 (ELA)、图片元数据扫描、截图状态栏时间与发送时间比对、银行/户名与文字金额一致性
- ⚖️ 仅在完全重复（开启自动拒绝时）或至少两个独立信号一致时才自动拒绝
- 🎛️ 管理员可开关检测、自动拒绝、严格模式与多模型；学习报告根据管理员的通过/拒绝决定调整各模型权重

### 🌐 自动翻译引擎与 16 种语言

- 🗺️ 内置语言目录：波斯语、英语、土耳其语、阿拉伯语、俄语、德语、法语、西班牙语、意大利语、葡萄牙语、中文、日语、韩语、荷兰语、波兰语和乌克兰语
- 🏠 离线优先：本地 Argos Translate 与 LibreTranslate 无需 API 密钥；除非明确允许，否则不使用公共翻译 API；Gemini/OpenRouter 为可选提供商
- 🛡️ 质量保护：占位符、链接、标记、代码和表情符号会被保护并在翻译后校验，异常的提供商输出会被拒绝
- ⚡ 语言目录中缺失的文本会在消息发送前即时翻译
- 📊 网页管理面板中的翻译仪表盘：状态、健康度、提供商、历史、实时日志、单语言与批量同步
- ✍️ 管理员撰写的内容（群发消息、商品名称等）绝不会被自动翻译；后台通知使用每位接收者的语言
- 🧰 语言在安装时选择；`manage.sh` 的选项 27、28、30 可修复运行环境、移除 LibreTranslate 并删除不需要的语言以释放磁盘空间

### 🧠 AI 助手的账户操作

除回答问题外，助手还可以准备账户操作，由机器人通过自身经过验证的流程执行。

- 🛒 钱包购买与 🔄 钱包续费（含费用计算），仅在用户另行明确确认后执行
- 🔁 自动续费开关、二维码、单个配置、启用/停用、重命名、新访问链接、转让给其他用户以及服务历史
- 🗑️ 删除服务始终以最终确认按钮结束
- 🎟️ 优惠码检查、推荐信息、最近工单和服务器国家
- 🙋 退款、投诉和资金纠纷仍会升级给人工客服

### ➕ 添加已有账户

- 🔗 用户粘贴订阅链接或（可选）配置用户名，即可把已拥有的服务绑定到自己的账户；系统会在已连接的面板中匹配
- 🔒 冲突保护：已绑定到其他账户的配置会被拒绝，连续失败会暂时封锁该用户
- 🎛️ 管理面板中可分别关闭该按钮和用户名选项

### 📚 情境化教程

- 📍 教程可以绑定到机器人的具体位置：主菜单按钮、购买流程、每种支付方式、钱包操作等
- 📚 对应页面下方会自动出现“教程”按钮，无需修改处理程序
- 🎁 教程还可以在购买成功后立即推荐

### 📜 条款与条件

- ✅ 管理员可要求用户在使用机器人前接受书面条款
- 📲 Mini App 有自己的接受流程，同意状态在两端共享

### 🧾 续费提醒与日志

- ⚠️ 用户在确认续费前会看到服务的当前状态（剩余时间与流量）
- 📣 每次续费（完整、流量、时间或增加用户）都会连同前后数值记录到管理员报告群

### 🧰 `manage.sh` 新选项

| 选项 | 操作 |
|:---:|---|
| 27 | 自动安装/修复本地翻译运行环境 |
| 28 | 移除 LibreTranslate |
| 29 | 完整清理 / 恢复出厂设置 |
| 30 | 移除不需要的翻译语言（释放磁盘空间） |

</details>

---

<a id="additional-features"></a>

## 🔎 更多功能

<details>
<summary><strong>点击展开</strong></summary>

- 🩺 VPN 面板健康监控
- 📊 高级销售与活动分析
- 📣 基于话题的报表
- 🎁 批量赠送
- 🧹 清理过期服务
- 🔌 基于令牌的集成 API
- ⏸️ 挂起服务
- 📦 面板容量限制
- 📍 服务迁移
- 💰 批量改价并可撤销
- 💸 返现
- 🎁 钱包赠送码
- 🪙 金币与抽奖
- ⭐ 订单/服务评价
- 💸 钱包间转账
- 🧾 钱包交易流水
- 📦 可配置的交付方式与二维码背景
- 🔗 多域名订阅链接
- 🧩 自定义配置构建商品
- 🛠️ 3X-UI 实用工具
- 🗄️ 多机器人备份/恢复
- 📨 备用备份目标
- 🏭 仅限拥有者的出厂重置
- ⏰ 定时群发
- 🔘 自动同步小程序菜单按钮
- 🔗 广告/深链接追踪
- 🟢 基于管理员在线状态的路由
- 🔔 待处理账单推送通知
- 🖼️ 小程序横幅/商品目录管理
- 🔀 多级推荐佣金与反作弊暂停机制
- 💳 代理后付费信用额度
- 📉 按代理等级的数量折扣
- 🌐 通过 Web API 支持无需自建 Telegram 机器人的代理

</details>

---

<a id="contributing"></a>

## 🤝 贡献与许可证

<details>
<summary><strong>点击展开</strong></summary>

欢迎提交错误报告、功能建议、文档改进以及 Pull Request。

在提交 Pull Request 之前：

1. 请勿将密钥和生产环境凭证提交到代码仓库。
2. 尽可能保持数据库兼容性。
3. 运行相关的 Python/JavaScript 检查。
4. 通过 i18n 层保持各语言的用户界面文本同步。

### 📄 许可证

本项目基于 **MIT 许可证** 发布。

### 👤 作者

由 **Mehdi Rafatpanah** 创建

- Telegram：[@celenor](https://t.me/celenor)
- GitHub：[@mehdirafatpanah](https://github.com/mehdirafatpanah)

</details>

---

## 🌍 文档语言

- 🇬🇧 **English:** `README.md`
- 🇮🇷 **فارسی:** `README.fa.md`
- 🇷🇺 **Русский:** `README.ru.md`
- 🇨🇳 **中文:** `README.zh.md`

应用支持多语言界面，会保留用户的语言选择并自动切换 RTL/LTR 方向；管理员可在管理面板中启用更多语言。
