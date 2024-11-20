# FluxUltra
FluxUltra是一款适用于chatgpt-on-wechat的绘图插件，调用glif.app的API基于黑森林最新发布的超强超快速绘画模型Flux 1.1 Pro Ultra模型进行文生图。 模型介绍详见黑森林官网https://blackforestlabs.ai/flux-1-1-ultra/。  它能够根据文本描述直出4K分辨率的高清大图，支持多种图片比例和生成模式。

## 基本信息
- 插件名称：FluxUltra
- 作者：Lingyuzhou
- 版本：1.0

## 功能特点

- 支持中英文提示词
- 支持多种图片比例（1:1、16:9、9:16、4:3、3:4）
- 支持两种生成模式（raw/default）

## 使用方法

1. 访问glif平台官网 https://glif.app/，注册glif账号（需要谷歌或Discord账号）。新注册用户每天可免费使用平台任意Glifs或调用API接口20次。
2. 点击头像下方的“API”选项进入API申请页面，或登录后直接访问 https://glif.app/settings/api-tokens，复制默认的API token备用。
3. 在微信机器人聊天窗口输入命令：#installp https://github.com/Lingyuzhou111/FluxUltra.git
4. 进入插件目录下的config文件配置第2步操作中获取的api_token。
5. 重启chatgpt-on-wechat项目并输入#scanp 命令扫描新插件是否已添加至插件列表。
6. 在聊天窗口输入#help FluxUltra查看帮助信息，返回相关帮助信息则表示插件安装成功。

## 使用样例
![FluxUltra_Example01](https://github.com/user-attachments/assets/1019a8de-d430-4238-bffd-fe9cd84cd99a)
![Uploading FluxUltra_Example02.png…]()
