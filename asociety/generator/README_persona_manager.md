# PersonaManager Module

## 概述

PersonaManager模块为Agentic Society项目提供了两个核心功能：

1. **添加骨架画像**：在当前数据库中批量生成并添加基于人口普查数据的骨架画像
2. **丰富空白画像**：扫描数据库中缺少描述的画像，使用LLM生成详细描述并更新

## 功能特性

- ✅ 基于真实人口普查数据生成骨架画像
- ✅ 使用LLM丰富画像描述
- ✅ 支持进度回调和UI反馈
- ✅ 完整的错误处理机制
- ✅ 批量操作支持
- ✅ 便捷函数接口

## 安装和导入

```python
from asociety.generator.persona_manager import PersonaManagerFactory
from asociety.generator.persona_manager import add_skeleton_personas, enrich_empty_personas
```

## 基本使用

### 1. 添加骨架画像

```python
from asociety.generator.persona_manager import PersonaManagerFactory

# 创建管理器实例
manager = PersonaManagerFactory.create()

# 添加10个骨架画像
count = manager.add_skeleton_personas(n=10)
print(f"成功添加 {count} 个骨架画像")
```

### 2. 丰富空白画像

```python
# 扫描并丰富所有缺少描述的画像
count = manager.enrich_empty_personas()
print(f"成功丰富 {count} 个画像")
```

### 3. 使用便捷函数

```python
from asociety.generator.persona_manager import add_skeleton_personas, enrich_empty_personas

# 直接使用便捷函数
skeleton_count = add_skeleton_personas(n=5)
enriched_count = enrich_empty_personas()
```

## 高级使用

### 1. 带进度回调

```python
def progress_callback(current, total, message):
    percentage = (current / total) * 100
    print(f"进度: {percentage:.1f}% - {message}")

manager = PersonaManagerFactory.create()
count = manager.add_skeleton_personas(
    n=20, 
    progress_callback=progress_callback
)
```

### 2. 带UI反馈

```python
class MyUI:
    def message(self, msg):
        print(f"[UI] {msg}")

ui = MyUI()
manager = PersonaManagerFactory.create(ui=ui)
count = manager.add_skeleton_personas(n=10)
```

### 3. 批量操作

```python
# 先添加骨架，再丰富描述
manager = PersonaManagerFactory.create()

# 步骤1：添加骨架画像
skeleton_count = manager.add_skeleton_personas(n=50)

# 步骤2：丰富所有空白画像
enriched_count = manager.enrich_empty_personas()

print(f"批量操作完成：添加 {skeleton_count} 个骨架，丰富 {enriched_count} 个画像")
```

## API 参考

### PersonaManager 类

#### `__init__(ui=None)`
- `ui`: 可选的UI回调接口，需要实现`message(msg)`方法

#### `add_skeleton_personas(n, progress_callback=None)`
- `n`: 要生成的骨架画像数量
- `progress_callback`: 可选的进度回调函数 `(current, total, message)`
- 返回: 成功添加的画像数量

#### `enrich_empty_personas(progress_callback=None)`
- `progress_callback`: 可选的进度回调函数 `(current, total, message)`
- 返回: 成功丰富的画像数量

### 便捷函数

#### `add_skeleton_personas(n, ui=None, progress_callback=None)`
直接添加骨架画像的便捷函数

#### `enrich_empty_personas(ui=None, progress_callback=None)`
直接丰富空白画像的便捷函数

## 数据流程

### 骨架画像生成流程
```
人口普查数据 → 加权随机采样 → 骨架数据 → 数据库存储
```

### 画像丰富流程
```
数据库扫描 → 识别空白画像 → LLM生成描述 → 更新数据库
```

## 错误处理

模块提供完整的错误处理机制：

```python
try:
    count = manager.add_skeleton_personas(n=10)
    print(f"成功添加 {count} 个画像")
except Exception as e:
    print(f"操作失败: {e}")
```

## 配置要求

1. **数据库**: 需要正确配置的SQLite数据库
2. **LLM**: 需要在`asociety.config`中配置LLM模型
3. **数据文件**: 需要`data/census.csv`人口普查数据文件
4. **提示模板**: 需要`prompts/generation.json`提示模板文件

## 性能考虑

- **骨架生成**: 速度较快，主要受数据库写入速度限制
- **LLM丰富**: 速度较慢，受LLM响应时间限制
- **批量操作**: 建议使用进度回调监控长时间运行的操作

## 示例脚本

查看以下文件获取完整示例：
- `persona_manager_example.py`: 详细使用示例
- `persona_manager_test.py`: 测试脚本

## 注意事项

1. 确保数据库连接正常
2. LLM配置正确且可访问
3. 大批量操作时注意监控进度
4. 定期备份数据库
5. 注意API调用限制（如果使用外部LLM服务）

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库路径和权限
   - 确保数据库schema正确

2. **LLM调用失败**
   - 检查LLM配置
   - 验证API密钥和网络连接

3. **字段映射错误**
   - 确保人口普查数据格式正确
   - 检查数据库schema与代码一致性

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用测试模式
manager = PersonaManagerFactory.create(ui=MyUI())
```
