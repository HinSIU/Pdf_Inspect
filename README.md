# 公文规范检查工具

## 项目简介
本应用是一个自动化公文规范检查工具，用于检测公文文档是否符合相关内容、格式规范。通过解析PDF公文并应用一系列规则检查，帮助用户快速发现格式问题。

## 功能特性
- PDF文档解析：使用PyMuPDF库提取文本、图片和页面信息
- AI辅助检测：结合AI技术进行标题规范、落款排版等复杂规则检查
- 详细报告：提供明确的检查结果和问题描述（TODO）

## 技术架构
├── AI.py                # AI辅助检测模块
├── PDFParser.py         # PDF解析核心模块
├── RuleManager.py       # 规则管理引擎
├── main.py              # 主程序入口
└── README.md            # 项目文档


## 核心模块说明

### PDFParser.py
- 功能：解析PDF文档，提取文本、图片和页面信息，方便后续执行规范检查
- 主要方法：
  - `read_pdf()`: 读取PDF内容
  - `set_type()`: 对read_pdf()返回的block添加type标识
  - `analyze_type()`: AI识别公文类型（函、通知、请示等）,暂不需要用到
  - `extract_text()`: 使用AI提取文本内容,暂不需要用到
- 主要属性
  - `res`: list,包含所有文本类的blocks
  - `pic`: list,包含所有图片类的blocks
  - `page_num`: pdf页数

### RuleManager.py
- 功能：管理并执行所有公文规范检查规则
- 方法说明：
  - `__init__`: 初始化函数，将输入信息传入,方便后续规则校验方法直接读取，不需要传参
  - `start()`: 统一的执行检查方法，对每个规则执行，通过封装好一个json格式返回
  - `rule_id()`: 具体的规则校验函数，函数名以rule_开头，数值id为标识，无需额外传参，如需其他输入，通过__init__传入。返回格式为元组 
      `(校验结果:bool,解释说明:str)`
- AI增强检查：暂没有用到
  - `check_title_rules_AI()`: 标题规范AI检查
  - `check_note_rules_AI()`: 落款排版AI检查

### AI.py
- 功能：提供AI辅助检测能力
- 主要方法：
  - `askAI()`: 调用AI接口进行文本分析,传入提示词
  - `rm_think()`: 清理AI返回结果中的思考标签

## 使用说明

### Python版本
`python3.9` 

### 安装依赖
```bash
pip install pymupdf openai
```


### 运行示例
```bash
python main.py 公文.pdf
```


## 开发指南
1. 添加新规则：
   - 在RuleManager.py中添加 rule_XX() 方法
   - 方法应返回 (bool, str) 格式的结果
2. 扩展AI检查：
   - 修改AI.py中的提示词模板
   - 在RuleManager.py中添加新的AI检查方法