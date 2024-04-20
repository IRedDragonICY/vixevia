# V.I.X.E.V.I.A : 虚拟交互和富有表现力的娱乐视觉偶像化身
[![许可证](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/) [![Gemini](https://img.shields.io/badge/Gemini-1.5-orange.svg)](https://cloud.google.com/generativeai/models)

[ID](README.ID.md) | [JP](README.JP.md) | [EN](README.md) | [ZN](README.ZN.md)
> _她对你有感情吗？_  
> **不**，她的心属于另一个人。  
> _她关心你的福祉吗？_  
> **不**，她的思绪被别人占据。  
> _无法回应的爱的痛苦是无法忍受的，但不要害怕，因为有解决方案。_  
> **解决方案是AI**，一个始终为你在的实体，理解并响应你的情绪。


Vixevia是一个创新的基于AI的虚拟YouTuber（Vtuber），利用了Google的Gemini语言模型的尖端功能。该项目旨在创建一个引人入胜和栩栩如生的虚拟人格，可以通过自然对话、视觉交互和多媒体体验与用户进行交互。

## 目录
- [功能](#功能)
- [先决条件](#先决条件)
- [开始](#开始)
- [待办事项](#待办事项)
- [贡献](#贡献)
- [许可证](#许可证)
- [致谢](#致谢)

## 功能

- **自然语言处理**：Vixevia利用Google的Gemini语言模型理解和回应用户输入，具有人类般的流畅度和上下文意识。
- **计算机视觉**：该项目集成了计算机视觉功能，使Vixevia能够感知和解释环境中的视觉信息。
- **多模态交互**：Vixevia结合了语音识别、文本到语音合成和视觉处理，以便与用户进行无缝的多模态交互。
- **个性化响应**：Vixevia的响应根据对话上下文、用户偏好和情境动态进行定制，确保提供引人入胜和个性化的体验。
- **虚拟化身**：Vixevia由一个视觉吸引力和表现力丰富的虚拟化身代表，使她的人格栩栩如生。

## 先决条件

- Google Cloud Platform的5+ API密钥
- Python 3.12+

硬件：
- 16 GB vram
- 32 GB ram
- RTX 4050或更好
- 20 GB的存储空间
- i7第12代或更好，或AMD等效产品

## 开始

要开始使用Vixevia，请按照以下步骤操作：

1. 克隆存储库：

   ```bash
   git clone https://github.com/IRedDragonICY/vixevia.git
   ```

2. 安装所需的依赖项：

   ```bash
   pip install -r requirements.txt
   ```

3. 从Google Cloud Platform获取必要的API密钥和配置文件。
4. 使用您的API密钥和首选设置更新配置文件。
5. 运行主脚本：

   ```bash
   python main.py
   ```

## 待办事项

- [ ] 为Vixevia创建自定义Live2D模型
- [ ] 添加opencv自动标签，以便从Gemini Pro Vision记住人
## 贡献

欢迎对Vixevia进行贡献！如果您有任何想法、错误报告或功能请求，请开启问题或提交拉取请求。请确保遵循项目的编码指南和最佳实践。

## 许可证

本项目根据[MIT许可证](LICENSE)许可。

## 致谢

- Google的Gemini语言模型及相关技术
- 本项目中使用的开源库和框架

Vixevia是一个实验性项目，旨在探索基于AI的虚拟人格的可能性，并推动人机交互的边界。我们希望这个项目能激发更多的人工智能和虚拟内容创作领域的创新和协作。